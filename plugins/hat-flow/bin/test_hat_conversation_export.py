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
write_report = _mod.write_report


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
