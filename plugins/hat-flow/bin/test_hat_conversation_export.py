"""
Tests for bin/hat-conversation-export.py — token attribution bug fix.

Covers:
  - tokens_after 不把整 turn output_tokens 重复累加给每个 tool_use 块
  - 边际归因：一个 turn 含 N 个工具时，每个工具只分到 out_tok / N

Run with:  pytest bin/test_hat_conversation_export.py -x -q
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ── import hat-conversation-export.py（文件名含连字符，不能直接 import） ──────
_SCRIPT = Path(__file__).parent / "hat-conversation-export.py"
_spec = importlib.util.spec_from_file_location("hat_conversation_export", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

extract_messages_and_stats = _mod.extract_messages_and_stats
load_phase_durations = _mod.load_phase_durations
load_phase_brackets = _mod.load_phase_brackets
compute_idle_seconds = _mod.compute_idle_seconds
write_report = _mod.write_report
fmt_duration_secs = _mod.fmt_duration_secs
parse_timestamp = _mod.parse_timestamp


def _phase_marker_turn(phase_num: int, phase_name: str, ts: str = "2026-05-25T10:00:00.000Z") -> dict:
    """构造一条含 ▶P 标记 TaskUpdate 的 assistant turn，用于切换 current_phase。"""
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "content": [{
                "type": "tool_use", "id": "tu_0", "name": "TaskUpdate",
                "input": {"subject": f"[t] ▶P{phase_num}:{phase_name} ◻rest"},
            }],
            "usage": {"input_tokens": 10, "output_tokens": 10,
                      "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
        },
    }


def _write_timing(tmp_path: Path, events: list[dict]) -> Path:
    p = tmp_path / "timing.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return p


# ── fixture helpers ─────────────────────────────────────────────────────────

def _make_jsonl(tmp_path: Path, lines: list[dict]) -> Path:
    """将多个 dict 写成 JSONL 文件并返回路径。"""
    p = tmp_path / "test_conversation.jsonl"
    p.write_text("\n".join(json.dumps(obj) for obj in lines) + "\n")
    return p


def _assistant_turn_with_tools(
    output_tokens: int,
    tool_names: list[str],
    input_tokens: int = 1000,
) -> dict:
    """构造一条 assistant turn，content 含多个 tool_use 块。"""
    content = []
    for i, name in enumerate(tool_names):
        content.append({
            "type": "tool_use",
            "id": f"tool_{i}",
            "name": name,
            "input": {"file_path": f"/tmp/file_{i}"},
        })
    return {
        "type": "assistant",
        "timestamp": "2026-05-25T10:00:00.000Z",
        "message": {
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        },
    }


# ── tests ────────────────────────────────────────────────────────────────────

class TestTokenAttribution:
    """tokens_after 边际归因：不得重复累加 out_tok 给同一 turn 的多个工具。"""

    def test_three_tools_in_one_turn_no_duplicate_accumulation(self, tmp_path):
        """
        一条 assistant turn：output_tokens=300，包含 3 个 tool_use（Read/Read/Bash）。

        期望：
          - Read 的 tokens_after 不等于 300*2=600（即没有被重复累加 2 次）
          - Read 的 tokens_after 不等于 300*3=900（整 turn 给了 3 次）
          - 所有工具的 tokens_after 合计不超过 300（不超过单 turn 输出）
        """
        out_tok = 300
        tool_names = ["Read", "Read", "Bash"]
        turn = _assistant_turn_with_tools(output_tokens=out_tok, tool_names=tool_names)
        jsonl = _make_jsonl(tmp_path, [turn])

        _, _, tool_stats, _ = extract_messages_and_stats(str(jsonl))

        read_tokens = tool_stats.get("Read", {}).get("tokens_after", 0)
        bash_tokens = tool_stats.get("Bash", {}).get("tokens_after", 0)

        # 关键断言：Read 工具的 tokens_after 不能等于 out_tok * 2（重复累加 bug 的结果）
        assert read_tokens != out_tok * 2, (
            f"Read.tokens_after={read_tokens} 等于 out_tok*2={out_tok * 2}，"
            f"说明 L112 重复累加 bug 仍存在"
        )

        # 所有工具 tokens_after 总和 ≤ out_tok（不超出这一 turn 的实际输出）
        total_attributed = read_tokens + bash_tokens
        assert total_attributed <= out_tok, (
            f"所有工具 tokens_after 总和 {total_attributed} 超过了单 turn output_tokens={out_tok}，"
            f"存在重复累加（Read={read_tokens}, Bash={bash_tokens}）"
        )

    def test_single_tool_gets_full_turn_output(self, tmp_path):
        """
        一条 turn 只含 1 个工具时，该工具应分得全部 out_tok（边际归因 = 100%）。
        """
        out_tok = 500
        turn = _assistant_turn_with_tools(output_tokens=out_tok, tool_names=["Write"])
        jsonl = _make_jsonl(tmp_path, [turn])

        _, _, tool_stats, _ = extract_messages_and_stats(str(jsonl))

        write_tokens = tool_stats.get("Write", {}).get("tokens_after", 0)
        assert write_tokens == out_tok, (
            f"单工具 turn：Write.tokens_after={write_tokens}，期望={out_tok}"
        )

    def test_two_turns_each_with_one_tool(self, tmp_path):
        """
        两条 turn，各含 1 个工具，互不干扰。
        """
        turn1 = _assistant_turn_with_tools(output_tokens=200, tool_names=["Read"])
        turn2 = _assistant_turn_with_tools(output_tokens=400, tool_names=["Bash"])
        jsonl = _make_jsonl(tmp_path, [turn1, turn2])

        _, _, tool_stats, _ = extract_messages_and_stats(str(jsonl))

        assert tool_stats["Read"]["tokens_after"] == 200
        assert tool_stats["Bash"]["tokens_after"] == 400

    def test_marginal_attribution_divides_evenly(self, tmp_path):
        """
        边际归因：out_tok=300，3 个工具（Read×2 + Bash×1）。
        每个工具各分 100 token，Read（2次）合计 200，Bash 100。
        """
        out_tok = 300
        tool_names = ["Read", "Read", "Bash"]
        turn = _assistant_turn_with_tools(output_tokens=out_tok, tool_names=tool_names)
        jsonl = _make_jsonl(tmp_path, [turn])

        _, _, tool_stats, _ = extract_messages_and_stats(str(jsonl))

        read_tokens = tool_stats.get("Read", {}).get("tokens_after", 0)
        bash_tokens = tool_stats.get("Bash", {}).get("tokens_after", 0)

        # 边际归因：每个工具分得 out_tok // n_tools = 100
        # Read 出现 2 次 → 200，Bash 出现 1 次 → 100
        assert read_tokens == 200, (
            f"Read（2次）边际归因期望 200，实际 {read_tokens}"
        )
        assert bash_tokens == 100, (
            f"Bash（1次）边际归因期望 100，实际 {bash_tokens}"
        )

    def test_text_only_turn_no_tools_no_error(self, tmp_path):
        """
        一条 turn 只含 text 块、无 tool_use（n_tools=0）：除零保护应生效，
        不抛异常，且不产生任何工具归因。
        """
        turn = {
            "type": "assistant",
            "timestamp": "2026-05-25T10:00:00.000Z",
            "message": {
                "content": [{"type": "text", "text": "纯文本回复，无工具调用"}],
                "usage": {
                    "input_tokens": 500,
                    "output_tokens": 200,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                },
            },
        }
        jsonl = _make_jsonl(tmp_path, [turn])

        # 不应抛 ZeroDivisionError
        _, _, tool_stats, _ = extract_messages_and_stats(str(jsonl))

        # 无 tool_use → 无任何工具被归因
        assert all(s.get("tokens_after", 0) == 0 for s in tool_stats.values()), (
            f"text-only turn 不应产生工具归因，实际 tool_stats={dict(tool_stats)}"
        )


class TestLoadPhaseDurations:
    """load_phase_durations：从 timing.jsonl 配对 phase_start/phase_end 算真实时长。"""

    def test_basic_pairing(self, tmp_path):
        timing = _write_timing(tmp_path, [
            {"event": "phase_start", "phase": "P2", "ts": "2026-05-26T10:00:00Z"},
            {"event": "phase_end", "phase": "P2", "ts": "2026-05-26T11:37:00Z"},
            {"event": "phase_start", "phase": "P4", "ts": "2026-05-26T12:00:00Z"},
            {"event": "phase_end", "phase": "P4", "ts": "2026-05-26T13:22:00Z"},
        ])
        d = load_phase_durations(str(timing))
        assert d[2] == 97 * 60      # P2 = 1h37m = 5820s
        assert d[4] == 82 * 60      # P4 = 1h22m = 4920s

    def test_brackets_return_datetime_tuples(self, tmp_path):
        """load_phase_brackets 直接断言：返回 {pn: (start_dt, end_dt)} 元组、字段顺序正确（start<end）。

        防字段顺序颠倒回归——若返回 (end, start)，间接经 load_phase_durations 只会得负时长，
        小 bracket 不触 active<0 时旧测试仍绿，故须直接断言元组。"""
        from datetime import datetime
        timing = _write_timing(tmp_path, [
            {"event": "phase_start", "phase": "P4", "ts": "2026-05-26T08:00:00Z"},
            {"event": "phase_end", "phase": "P4", "ts": "2026-05-26T10:00:00Z"},
        ])
        b = load_phase_brackets(str(timing))
        assert b[4] == (datetime(2026, 5, 26, 8, 0, 0), datetime(2026, 5, 26, 10, 0, 0))
        start_dt, end_dt = b[4]
        assert start_dt < end_dt, "start 必须早于 end（字段顺序正确）"

    def test_brackets_missing_file_returns_empty(self, tmp_path):
        assert load_phase_brackets(str(tmp_path / "nope.jsonl")) == {}

    def test_missing_file_returns_empty(self, tmp_path):
        assert load_phase_durations(str(tmp_path / "nope.jsonl")) == {}

    def test_malformed_lines_skipped(self, tmp_path):
        p = tmp_path / "timing.jsonl"
        p.write_text(
            '{"event":"phase_start","phase":"P1","ts":"2026-05-26T10:00:00Z"}\n'
            'NOT JSON GARBAGE\n'
            '\n'
            '{"event":"phase_end","phase":"P1","ts":"2026-05-26T10:00:30Z"}\n'
        )
        d = load_phase_durations(str(p))
        assert d == {1: 30}

    def test_earliest_start_latest_end(self, tmp_path):
        # 同一 phase 多次 start/end（如 revise 重入）：取最早 start、最晚 end
        timing = _write_timing(tmp_path, [
            {"event": "phase_start", "phase": "P4", "ts": "2026-05-26T12:00:00Z"},
            {"event": "phase_end", "phase": "P4", "ts": "2026-05-26T12:30:00Z"},
            {"event": "phase_start", "phase": "P4", "ts": "2026-05-26T12:10:00Z"},
            {"event": "phase_end", "phase": "P4", "ts": "2026-05-26T13:00:00Z"},
        ])
        d = load_phase_durations(str(timing))
        assert d[4] == 60 * 60      # 12:00 → 13:00 = 3600s

    def test_unpaired_start_ignored(self, tmp_path):
        timing = _write_timing(tmp_path, [
            {"event": "phase_start", "phase": "P5", "ts": "2026-05-26T14:00:00Z"},
        ])
        assert load_phase_durations(str(timing)) == {}


class TestMultiJsonlMerge:
    """extract_messages_and_stats 接受多个 jsonl：按序合并、current_phase 跨文件延续。"""

    def test_two_files_message_counts_add(self, tmp_path):
        f1 = tmp_path / "s1.jsonl"
        f1.write_text("\n".join(json.dumps(t) for t in [
            _assistant_turn_with_tools(100, ["Read"]),
            _assistant_turn_with_tools(100, ["Bash"]),
        ]) + "\n")
        f2 = tmp_path / "s2.jsonl"
        f2.write_text(json.dumps(_assistant_turn_with_tools(100, ["Write"])) + "\n")

        messages, _, tool_stats, total = extract_messages_and_stats([str(f1), str(f2)])
        assert len(messages) == 3
        assert total["assistant_turns"] == 3
        assert tool_stats["Read"]["count"] == 1 and tool_stats["Write"]["count"] == 1

    def test_phase_carries_across_files(self, tmp_path):
        # file1 末尾切到 P4，file2 开头无 ▶P 标记 → file2 的消息应仍归 P4，不回 Pre-Init
        f1 = tmp_path / "s1.jsonl"
        f1.write_text("\n".join(json.dumps(t) for t in [
            _phase_marker_turn(4, "Execute"),
            _assistant_turn_with_tools(100, ["Read"]),
        ]) + "\n")
        f2 = tmp_path / "s2.jsonl"
        f2.write_text(json.dumps(_assistant_turn_with_tools(100, ["Bash"])) + "\n")

        _, phase_stats, _, _ = extract_messages_and_stats([str(f1), str(f2)])
        # P4 精确含 3 次 tool_call：▶P4 标记 turn(TaskUpdate) + file1 Read + file2 Bash
        # 用 == 3 而非 >= 2：若 file2 的 Bash 掉回 Pre-Init，>=2 仍会通过、漏过回归
        assert "P4:Execute" in phase_stats
        assert phase_stats["P4:Execute"]["tool_calls"] == 3
        # 不应出现 file2 的消息掉回 P0:Pre-Init
        assert phase_stats.get("P0:Pre-Init", {}).get("tool_calls", 0) == 0

    def test_single_string_backward_compat(self, tmp_path):
        # 传单个字符串路径（非 list）应仍可用（向后兼容）
        f = _make_jsonl(tmp_path, [_assistant_turn_with_tools(200, ["Read"])])
        messages, _, tool_stats, _ = extract_messages_and_stats(str(f))
        assert len(messages) == 1
        assert tool_stats["Read"]["count"] == 1


class TestReportTimingDuration:
    """write_report 的 Duration 列：有 timing 用真实时长，无则回退裸差并标 ~。"""

    def _phase_stats_one(self):
        from datetime import datetime
        return {"P4:Execute": {
            "input_tokens": 100, "output_tokens": 1000, "cache_read": 0, "cache_create": 0,
            "assistant_turns": 5, "user_turns": 0, "tool_calls": 10,
            "start_ts": datetime(2026, 5, 26, 12, 0, 0),
            "end_ts": datetime(2026, 5, 26, 12, 5, 0),   # 裸差 = 5m
        }}

    def test_timing_overrides_message_diff(self, tmp_path):
        report = tmp_path / "consumption-report.md"
        total = {"input_tokens": 100, "output_tokens": 1000, "cache_read": 0,
                 "cache_create": 0, "assistant_turns": 5, "user_turns": 0, "tool_calls": 10}
        # timing 给 P4 = 82m，应覆盖消息裸差的 5m
        write_report(self._phase_stats_one(), {}, total, str(report), "sid",
                     phase_durations={4: 82 * 60})
        text = report.read_text()
        assert "1.4h" in text or "82m" in text, f"应显示 timing 时长，实际:\n{text}"
        assert "timing.jsonl" in text   # 来源说明

    def test_fallback_marks_tilde(self, tmp_path):
        report = tmp_path / "consumption-report.md"
        total = {"input_tokens": 100, "output_tokens": 1000, "cache_read": 0,
                 "cache_create": 0, "assistant_turns": 5, "user_turns": 0, "tool_calls": 10}
        # 无 phase_durations（空 dict）→ 回退消息裸差 5m，且带 idle 警告
        write_report(self._phase_stats_one(), {}, total, str(report), "sid",
                     phase_durations={})
        text = report.read_text()
        assert "5m" in text
        assert "不扣 idle" in text or "墙钟差" in text


class TestIdleSubtraction:
    """compute_idle_seconds 纯函数单测 + 渲染层集成测试。"""

    # ── 纯函数单测 ──────────────────────────────────────────────────────────────

    def test_gap_over_threshold_counted(self):
        """时间戳序列含一个 40min gap，其余 <30min → 返回 2400s（整段计入）。"""
        from datetime import datetime
        base = datetime(2026, 5, 26, 10, 0, 0)
        # 4 条消息：10:00 → 10:05 → 10:45 (+40min) → 10:50
        timestamps = [
            datetime(2026, 5, 26, 10, 0, 0),
            datetime(2026, 5, 26, 10, 5, 0),
            datetime(2026, 5, 26, 10, 45, 0),
            datetime(2026, 5, 26, 10, 50, 0),
        ]
        start = datetime(2026, 5, 26, 9, 55, 0)   # 窗口开始
        end = datetime(2026, 5, 26, 10, 55, 0)    # 窗口结束
        result = compute_idle_seconds(timestamps, start, end)
        # 40min gap → 2400s
        assert result == 2400, f"期望 2400，实际 {result}"

    def test_all_gaps_under_threshold_zero(self):
        """相邻间隔均 <30min → 返回 0。"""
        from datetime import datetime
        timestamps = [
            datetime(2026, 5, 26, 10, 0, 0),
            datetime(2026, 5, 26, 10, 10, 0),
            datetime(2026, 5, 26, 10, 20, 0),
        ]
        start = datetime(2026, 5, 26, 9, 55, 0)
        end = datetime(2026, 5, 26, 10, 25, 0)
        result = compute_idle_seconds(timestamps, start, end)
        assert result == 0, f"期望 0，实际 {result}"

    def test_head_tail_anchor(self):
        """start→msg 间隔 >30min → 该段计入 idle（验证锚点插入）。"""
        from datetime import datetime
        # start 在 10:00，消息在 10:40（+40min），end 在 10:45
        msg_ts = datetime(2026, 5, 26, 10, 40, 0)
        start = datetime(2026, 5, 26, 10, 0, 0)
        end = datetime(2026, 5, 26, 10, 45, 0)
        result = compute_idle_seconds([msg_ts], start, end)
        # start → msg 间隔 40min = 2400s
        assert result == 2400, f"期望 2400，实际 {result}"

    def test_empty_window_returns_zero(self):
        """窗口内 0 条消息且 end-start >30min → 返回 0（C1：不插锚点）。"""
        from datetime import datetime
        start = datetime(2026, 5, 26, 8, 0, 0)
        end = datetime(2026, 5, 26, 10, 0, 0)   # 2h 差距
        result = compute_idle_seconds([], start, end)
        assert result == 0, f"零消息窗口应返回 0，实际 {result}"

    def test_uniform_naive_no_mixing(self):
        """含 Z 的串经 parse_timestamp 解析后均为 naive → 比较不抛 TypeError。"""
        ts_a = parse_timestamp("2026-05-26T10:00:00Z")
        ts_b = parse_timestamp("2026-05-26T10:45:00Z")
        ts_start = parse_timestamp("2026-05-26T09:55:00Z")
        ts_end = parse_timestamp("2026-05-26T10:50:00Z")
        # 不应抛 TypeError（naive/aware 混比）
        result = compute_idle_seconds([ts_a, ts_b], ts_start, ts_end)
        assert isinstance(result, (int, float)), f"期望数值，实际 {result!r}"

    def test_phase_gap_not_double_counted(self):
        """两个相邻 bracket 中间的消息不被任一 phase 的窗口重复计入（半开窗口轻断言）。"""
        from datetime import datetime
        # Phase A: [10:00, 11:00)，Phase B: [11:00, 12:00)
        # 有一条消息在 10:50，另一条在 11:05
        msg_at_1050 = datetime(2026, 5, 26, 10, 50, 0)
        msg_at_1105 = datetime(2026, 5, 26, 11, 5, 0)
        all_ts = [msg_at_1050, msg_at_1105]

        start_a = datetime(2026, 5, 26, 10, 0, 0)
        end_a = datetime(2026, 5, 26, 11, 0, 0)
        start_b = datetime(2026, 5, 26, 11, 0, 0)
        end_b = datetime(2026, 5, 26, 12, 0, 0)

        idle_a = compute_idle_seconds(all_ts, start_a, end_a)
        idle_b = compute_idle_seconds(all_ts, start_b, end_b)

        # A 窗口 [10:00,11:00) 只含 msg_at_1050；加锚点序列 [10:00, 10:50, 11:00]：
        #   head gap 10:00→10:50 = 50min = 3000s（>30min 计入）；10:50→11:00 = 10min（不计）→ idle_a = 3000
        # B 窗口 [11:00,12:00) 只含 msg_at_1105；加锚点序列 [11:00, 11:05, 12:00]：
        #   11:00→11:05 = 5min（不计）；tail gap 11:05→12:00 = 55min = 3300s（>30min 计入）→ idle_b = 3300
        # 精确断言：两条消息各自只落入自己的半开窗口，无跨窗双算
        assert idle_a == 3000, f"A 窗口期望 3000，实际 {idle_a}"
        assert idle_b == 3300, f"B 窗口期望 3300，实际 {idle_b}"

    # ── 渲染层集成测试 ────────────────────────────────────────────────────────

    def _total_stats(self):
        return {"input_tokens": 100, "output_tokens": 1000, "cache_read": 0,
                "cache_create": 0, "assistant_turns": 5, "user_turns": 0, "tool_calls": 10}

    def _phase_stats_p4(self, start, end):
        return {"P4:Execute": {
            "input_tokens": 100, "output_tokens": 1000, "cache_read": 0, "cache_create": 0,
            "assistant_turns": 5, "user_turns": 0, "tool_calls": 10,
            "start_ts": start, "end_ts": end,
        }}

    def test_render_active_with_idle_annotation(self, tmp_path):
        """timing bracket 约 6h、bracket 内消息含 5.8h gap → report 行含"扣 idle"标注。"""
        from datetime import datetime, timedelta
        report = tmp_path / "consumption-report.md"
        bracket_start = datetime(2026, 5, 26, 8, 0, 0)
        bracket_end = datetime(2026, 5, 26, 14, 0, 0)    # 6h bracket
        phase_durations = {4: 6 * 3600}                  # 6h
        # idle = 5.8h = 20880s（仅 1 条消息，在 bracket 结尾处，头部 gap >30min）
        idle_secs = int(5.8 * 3600)   # 20880
        phase_idle = {4: idle_secs}

        write_report(
            self._phase_stats_p4(bracket_start, bracket_end),
            {}, self._total_stats(), str(report), "sid",
            phase_durations=phase_durations,
            phase_idle=phase_idle,
        )
        text = report.read_text()
        assert "扣 idle" in text or "idle" in text.lower(), f"应含 idle 标注，实际:\n{text}"
        # active = 6h - 5.8h = 0.2h = 12m
        assert "12m" in text or "720" in text, f"应含 active≈12m，实际:\n{text}"

    def test_render_no_idle_no_annotation(self, tmp_path):
        """bracket 内 gap 均<30min → Duration==bracket、无'扣 idle'标注。"""
        from datetime import datetime
        report = tmp_path / "consumption-report.md"
        bracket_start = datetime(2026, 5, 26, 10, 0, 0)
        bracket_end = datetime(2026, 5, 26, 10, 30, 0)
        phase_durations = {4: 30 * 60}
        phase_idle = {4: 0}

        write_report(
            self._phase_stats_p4(bracket_start, bracket_end),
            {}, self._total_stats(), str(report), "sid",
            phase_durations=phase_durations,
            phase_idle=phase_idle,
        )
        text = report.read_text()
        assert "30m" in text, f"应含 30m，实际:\n{text}"
        assert "扣 idle" not in text, f"无 idle 时不应含'扣 idle'标注，实际:\n{text}"

    def test_render_empty_bracket_shows_full(self, tmp_path):
        """bracket >30min 但 phase_idle 为 0（无消息窗口）→ Duration==bracket（非 active=0）。"""
        from datetime import datetime
        report = tmp_path / "consumption-report.md"
        bracket_start = datetime(2026, 5, 26, 8, 0, 0)
        bracket_end = datetime(2026, 5, 26, 10, 0, 0)    # 2h bracket
        phase_durations = {4: 2 * 3600}
        phase_idle = {4: 0}   # 零消息窗口 → compute_idle_seconds 返回 0

        write_report(
            self._phase_stats_p4(bracket_start, bracket_end),
            {}, self._total_stats(), str(report), "sid",
            phase_durations=phase_durations,
            phase_idle=phase_idle,
        )
        text = report.read_text()
        assert "2.0h" in text or "120m" in text, f"应含 2h，实际:\n{text}"
        assert "active=0" not in text, f"不应出现 active=0 警告"

    def test_header_reflects_idle_rule(self, tmp_path):
        """有 timing 时表头含 idle 扣减说明；无 timing 时表头含'不扣 idle'。"""
        from datetime import datetime
        report1 = tmp_path / "r1.md"
        report2 = tmp_path / "r2.md"
        bracket_start = datetime(2026, 5, 26, 10, 0, 0)
        bracket_end = datetime(2026, 5, 26, 10, 30, 0)
        total = self._total_stats()
        ps = self._phase_stats_p4(bracket_start, bracket_end)

        # 有 timing
        write_report(ps, {}, total, str(report1), "sid", phase_durations={4: 1800})
        # 无 timing
        write_report(ps, {}, total, str(report2), "sid", phase_durations={})

        t1 = report1.read_text()
        t2 = report2.read_text()
        assert "已扣除 >30min 的 idle gap" in t1, f"有 timing 时表头应含 idle 扣减说明:\n{t1}"
        assert "不扣 idle" in t2, f"无 timing 时表头应含'不扣 idle':\n{t2}"

    def test_render_active_clamped_when_idle_exceeds_bracket(self, tmp_path):
        """active<0（idle>bracket，算法异常）→ clamp 到 0 + 唯一异常标注，**不叠加**正常'扣 idle'标注。"""
        from datetime import datetime
        report = tmp_path / "consumption-report.md"
        bracket_start = datetime(2026, 5, 26, 10, 0, 0)
        bracket_end = datetime(2026, 5, 26, 10, 30, 0)
        phase_durations = {4: 1000}     # bracket 1000s
        phase_idle = {4: 2000}          # idle > bracket → active = -1000 → clamp

        write_report(
            self._phase_stats_p4(bracket_start, bracket_end),
            {}, self._total_stats(), str(report), "sid",
            phase_durations=phase_durations,
            phase_idle=phase_idle,
        )
        text = report.read_text()
        assert "active 已 clamp 0" in text, f"应含 clamp 异常标注，实际:\n{text}"
        # 互斥：clamp 路径不得再叠加正常"扣 idle"标注（修复双注解矛盾）
        assert "扣 idle" not in text, f"clamp 路径不应叠加'扣 idle'标注，实际:\n{text}"
