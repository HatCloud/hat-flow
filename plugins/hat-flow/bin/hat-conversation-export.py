#!/usr/bin/env python3
"""Parse Claude Code JSONL conversation and export to Markdown + consumption report."""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime


def parse_timestamp(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts[:19])
    except (ValueError, TypeError):
        return None


def detect_phase_from_subject(subject):
    m = re.search(r'▶P(\d):(\w+)', subject)
    if m:
        return int(m.group(1)), m.group(2)
    return None, None


def _read_lines(path):
    with open(path, "r") as f:
        return f.readlines()


def extract_messages_and_stats(jsonl_paths):
    # 接受单个路径或路径列表；多 session 任务按传入顺序合并，current_phase 跨文件延续
    if isinstance(jsonl_paths, str):
        jsonl_paths = [jsonl_paths]
    messages = []
    phase_stats = defaultdict(lambda: {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read": 0, "cache_create": 0,
        "assistant_turns": 0, "user_turns": 0,
        "tool_calls": 0, "start_ts": None, "end_ts": None,
    })
    tool_stats = defaultdict(lambda: {"count": 0, "tokens_after": 0})
    current_phase = (0, "Pre-Init")
    total_stats = {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read": 0, "cache_create": 0,
        "assistant_turns": 0, "user_turns": 0,
        "tool_calls": 0,
    }

    for _jp in jsonl_paths:
        for line in _read_lines(_jp):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg_type = obj.get("type", "")
            if msg_type not in ("user", "assistant"):
                continue

            timestamp = obj.get("timestamp", "")
            ts = parse_timestamp(timestamp)
            msg = obj.get("message", {})
            content = msg.get("content", "")
            usage = msg.get("usage", {})

            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
            cache_r = usage.get("cache_read_input_tokens", 0)
            cache_c = usage.get("cache_creation_input_tokens", 0)

            phase_key = f"P{current_phase[0]}:{current_phase[1]}"

            if msg_type == "assistant":
                total_stats["input_tokens"] += in_tok
                total_stats["output_tokens"] += out_tok
                total_stats["cache_read"] += cache_r
                total_stats["cache_create"] += cache_c
                total_stats["assistant_turns"] += 1
                phase_stats[phase_key]["input_tokens"] += in_tok
                phase_stats[phase_key]["output_tokens"] += out_tok
                phase_stats[phase_key]["cache_read"] += cache_r
                phase_stats[phase_key]["cache_create"] += cache_c
                phase_stats[phase_key]["assistant_turns"] += 1
            else:
                total_stats["user_turns"] += 1
                phase_stats[phase_key]["user_turns"] += 1

            if ts:
                if phase_stats[phase_key]["start_ts"] is None:
                    phase_stats[phase_key]["start_ts"] = ts
                phase_stats[phase_key]["end_ts"] = ts

            content_parts = []
            if isinstance(content, str):
                content_parts.append(content)
            elif isinstance(content, list):
                # 计算该 turn 的 tool_use 块数，用于边际归因（避免把整 turn 的
                # output_tokens 重复累加给每个工具）
                n_tools = sum(
                    1 for b in content
                    if isinstance(b, dict) and b.get("type") == "tool_use"
                )
                tok_per_tool = out_tok // n_tools if n_tools > 0 else 0
                for block in content:
                    if isinstance(block, str):
                        content_parts.append(block)
                    elif isinstance(block, dict):
                        btype = block.get("type", "")
                        if btype == "text":
                            content_parts.append(block.get("text", ""))
                        elif btype == "tool_use":
                            name = block.get("name", "unknown")
                            inp = block.get("input", {})

                            if name in ("TaskCreate", "TaskUpdate"):
                                subj = inp.get("subject", "")
                                pn, pname = detect_phase_from_subject(subj)
                                if pn is not None:
                                    current_phase = (pn, pname)
                                    phase_key = f"P{pn}:{pname}"

                            total_stats["tool_calls"] += 1
                            phase_stats[phase_key]["tool_calls"] += 1
                            tool_stats[name]["count"] += 1
                            # 边际归因：该 turn 的 output_tokens 均摊给每个工具
                            tool_stats[name]["tokens_after"] += tok_per_tool

                            inp_str = json.dumps(inp, ensure_ascii=False)
                            if len(inp_str) > 300:
                                inp_str = inp_str[:300] + "..."
                            content_parts.append(f"[Tool: {name}] {inp_str}")
                        elif btype == "tool_result":
                            tr_content = block.get("content", "")
                            if isinstance(tr_content, str) and tr_content:
                                result_text = tr_content
                            elif isinstance(tr_content, list):
                                result_text = "\n".join(
                                    b.get("text", "") for b in tr_content
                                    if isinstance(b, dict) and b.get("type") == "text"
                                )
                            else:
                                result_text = ""
                            if result_text:
                                if len(result_text) > 500:
                                    result_text = result_text[:500] + "..."
                                content_parts.append(f"[Tool Result] {result_text}")
                            else:
                                content_parts.append("[Tool Result]")

            text = "\n".join(content_parts).strip()
            if not text:
                continue
            messages.append({"role": msg_type, "timestamp": timestamp, "text": text})

    return messages, dict(phase_stats), dict(tool_stats), total_stats


def write_conversation(messages, output_path, session_id):
    with open(output_path, "w") as out:
        out.write("# Conversation Log\n\n")
        out.write(f"**Session**: {session_id}\n")
        out.write(f"**Messages**: {len(messages)}\n\n---\n\n")
        for msg in messages:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            ts = msg["timestamp"][:19].replace("T", " ") if msg["timestamp"] else ""
            out.write(f"## {role_label}")
            if ts:
                out.write(f" ({ts})")
            out.write("\n\n")
            out.write(msg["text"])
            out.write("\n\n---\n\n")


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_duration_secs(total_seconds):
    if total_seconds is None:
        return "—"
    mins = total_seconds / 60
    if mins < 1:
        return f"{total_seconds:.0f}s"
    if mins < 60:
        return f"{mins:.0f}m"
    return f"{mins / 60:.1f}h"


def fmt_duration(start, end):
    if not start or not end:
        return "—"
    return fmt_duration_secs((end - start).total_seconds())


def compute_idle_seconds(timestamps, start, end, threshold=1800):
    """计算窗口 [start, end) 内的 idle gap 总秒数。

    过滤落在半开窗口 [start, end) 内的时间戳；若为空直接返回 0（C1：不插锚点）；
    否则把 start/end 作为锚点拼入并排序，对相邻间隔 > threshold 的整段 gap 累加。

    参数：
        timestamps: 已 parse 的 datetime 列表（naive）
        start, end: 已 parse 的 naive datetime，界定窗口
        threshold: idle 阈值（秒），默认 1800（30min）

    返回：
        idle 总秒数（float/int）
    """
    window = [t for t in timestamps if start <= t < end]
    if not window:
        return 0
    anchored = sorted(set([start] + window + [end]))
    idle = 0
    for i in range(len(anchored) - 1):
        gap = (anchored[i + 1] - anchored[i]).total_seconds()
        if gap > threshold:
            idle += gap
    return idle


def load_phase_brackets(timing_path):
    """从 timing.jsonl 配对 phase_start/phase_end，返回 {phase_num: (start_dt, end_dt)}。

    文件缺失/损坏时返回 {}。
    """
    if not timing_path or not os.path.exists(timing_path):
        return {}
    starts, ends = {}, {}
    try:
        with open(timing_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                m = re.match(r'P(\d+)', str(ev.get("phase", "")))
                if not m:
                    continue
                pn = int(m.group(1))
                ts = parse_timestamp(ev.get("ts", ""))
                if ts is None:
                    continue
                event = ev.get("event")
                if event == "phase_start":
                    if pn not in starts or ts < starts[pn]:
                        starts[pn] = ts
                elif event == "phase_end":
                    if pn not in ends or ts > ends[pn]:
                        ends[pn] = ts
    except OSError:
        return {}
    return {pn: (starts[pn], ends[pn]) for pn in starts if pn in ends}


def _durations_from_brackets(brackets):
    """{pn: (start_dt, end_dt)} → {pn: duration_seconds}。bracket→时长 的单一计算来源，
    供 load_phase_durations 与 main 共用，避免两处各自内联同一公式日后分叉。"""
    return {pn: (e - s).total_seconds() for pn, (s, e) in brackets.items()}


def load_phase_durations(timing_path):
    """从 timing.jsonl 配对 phase_start/phase_end，返回 {phase_num: duration_seconds}。

    timing.jsonl 由 core timing（各 phase SKILL 在 phase 边界内联经 hat-timing-stamp）记录，是真实 phase 时长（不含
    compact 后挂起空闲）。消息墙钟差会把 idle gap 错算进 phase——故优先用此数据。
    文件缺失/损坏时返回 {}，调用方回退到消息墙钟差。
    """
    return _durations_from_brackets(load_phase_brackets(timing_path))


def write_report(phase_stats, tool_stats, total_stats, report_path, session_id, phase_durations=None, phase_idle=None):
    phase_durations = phase_durations or {}
    phase_idle = phase_idle or {}
    total_out = max(total_stats["output_tokens"], 1)
    total_in = max(total_stats["input_tokens"] + total_stats["cache_read"] + total_stats["cache_create"], 1)
    total_all = total_in + total_out

    with open(report_path, "w") as out:
        out.write("# Consumption Report\n\n")
        out.write(f"**Session**: {session_id}\n\n")

        out.write("## 总量\n\n")
        out.write(f"- Input tokens: {fmt_tokens(total_stats['input_tokens'])} (uncached)\n")
        out.write(f"- Cache read: {fmt_tokens(total_stats['cache_read'])}\n")
        out.write(f"- Cache create: {fmt_tokens(total_stats['cache_create'])}\n")
        out.write(f"- Output tokens: {fmt_tokens(total_stats['output_tokens'])}\n")
        out.write(f"- Assistant turns: {total_stats['assistant_turns']}\n")
        out.write(f"- User turns: {total_stats['user_turns']}\n")
        out.write(f"- Tool calls: {total_stats['tool_calls']}\n\n")

        out.write("## 阶段消耗\n\n")
        if phase_durations:
            out.write("> Duration 来源：timing.jsonl phase bracket，已扣除 >30min 的 idle gap（active 时长）。"
                      "无 timing 记录的 phase 回退消息墙钟差，标 ~。\n\n")
        else:
            out.write("> ⚠️ Duration = phase 内首末消息墙钟差，**不扣 idle**。"
                      "同目录无 timing.jsonl 时的回退口径，可能把挂起空闲错算进 phase。\n\n")
        out.write("| Phase | Duration | Output Tokens | Input (uncached) | Cache Read | Tool Calls | Output % |\n")
        out.write("|-------|----------|---------------|-----------------|------------|------------|----------|\n")

        phase_order = sorted(phase_stats.keys(), key=lambda k: int(re.search(r'P(\d)', k).group(1)) if re.search(r'P(\d)', k) else 0)
        for phase in phase_order:
            s = phase_stats[phase]
            m = re.search(r'P(\d+)', phase)
            pn = int(m.group(1)) if m else None
            if pn is not None and pn in phase_durations:
                bracket_secs = phase_durations[pn]
                idle = phase_idle.get(pn, 0)
                active = bracket_secs - idle
                if active < 0:
                    # idle>bracket = 算法 bug；clamp 并给唯一的异常标注（不再叠加正常"扣 idle"，二者互斥）
                    active = 0
                    print(f"WARNING: {phase} active<0 (bracket={bracket_secs}s, idle={idle}s) — clamped to 0", file=sys.stderr)
                    dur = fmt_duration_secs(active) + "（active 已 clamp 0：idle>bracket，数据异常）"
                else:
                    dur = fmt_duration_secs(active)
                    if idle > 0:
                        dur += f"（扣 idle {fmt_duration_secs(idle)}）"
            else:
                dur = fmt_duration(s["start_ts"], s["end_ts"])
                if phase_durations:
                    dur += "~"
            pct = s["output_tokens"] / total_out * 100 if total_out else 0
            out.write(f"| {phase} | {dur} | {fmt_tokens(s['output_tokens'])} | {fmt_tokens(s['input_tokens'])} | {fmt_tokens(s['cache_read'])} | {s['tool_calls']} | {pct:.0f}% |\n")

        out.write("\n## 工具调用统计\n\n")
        out.write("| Tool | Count | Avg Output Tokens |\n")
        out.write("|------|-------|------------------|\n")

        sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1]["count"], reverse=True)
        for name, ts in sorted_tools[:15]:
            avg = ts["tokens_after"] // max(ts["count"], 1)
            out.write(f"| {name} | {ts['count']} | {avg} |\n")

        out.write("\n## 高消耗行为分析\n\n")

        expensive_phases = sorted(phase_stats.items(), key=lambda x: x[1]["output_tokens"], reverse=True)
        if expensive_phases:
            top = expensive_phases[0]
            out.write(f"- **最大输出阶段**: {top[0]} — {fmt_tokens(top[1]['output_tokens'])} output tokens ({top[1]['output_tokens'] / total_out * 100:.0f}%)\n")

        expensive_tools = sorted(tool_stats.items(), key=lambda x: x[1]["tokens_after"], reverse=True)
        if expensive_tools:
            top_t = expensive_tools[0]
            out.write(f"- **最多调用工具**: {top_t[0]} — {top_t[1]['count']} 次\n")

        heavy_tools = [(n, t) for n, t in tool_stats.items() if t["count"] >= 3 and t["tokens_after"] // max(t["count"], 1) > 500]
        heavy_tools.sort(key=lambda x: x[1]["tokens_after"] // max(x[1]["count"], 1), reverse=True)
        if heavy_tools:
            out.write("- **高 token 工具** (avg > 500 output/call):\n")
            for n, t in heavy_tools[:5]:
                avg = t["tokens_after"] // max(t["count"], 1)
                out.write(f"  - {n}: {t['count']} calls, avg {avg} tokens\n")

        cache_ratio = total_stats["cache_read"] / total_in * 100 if total_in else 0
        out.write(f"- **Cache 命中率**: {cache_ratio:.0f}%\n")

    return phase_stats, total_stats


def main():
    if len(sys.argv) < 3:
        print("Usage: hat-conversation-export.py <jsonl-path> [<jsonl-path> ...] <output-path>", file=sys.stderr)
        sys.exit(1)

    # 最后一个参数为 output，其余全部为 jsonl 路径（支持多 session 合并，按传入顺序）
    jsonl_paths = sys.argv[1:-1]
    output_path = sys.argv[-1]
    ids = [os.path.splitext(os.path.basename(p))[0] for p in jsonl_paths]
    session_id = ids[0] if len(ids) == 1 else f"{ids[0]} (+{len(ids) - 1} more)"

    messages, phase_stats, tool_stats, total_stats = extract_messages_and_stats(jsonl_paths)

    if not messages:
        print("Warning: No conversation messages found in JSONL", file=sys.stderr)
        sys.exit(1)

    write_conversation(messages, output_path, session_id)
    print(f"Exported {len(messages)} messages to {output_path}")

    report_dir = os.path.dirname(os.path.abspath(output_path))
    report_path = os.path.join(report_dir, "consumption-report.md")
    timing_path = os.path.join(report_dir, "timing.jsonl")
    brackets = load_phase_brackets(timing_path)
    phase_durations = _durations_from_brackets(brackets)
    msg_ts = sorted({t for m in messages if (t := parse_timestamp(m["timestamp"])) is not None})
    phase_idle = {pn: compute_idle_seconds(msg_ts, s, e) for pn, (s, e) in brackets.items()}
    write_report(phase_stats, tool_stats, total_stats, report_path, session_id, phase_durations, phase_idle)
    print(f"Generated consumption report to {report_path}")


if __name__ == "__main__":
    main()
