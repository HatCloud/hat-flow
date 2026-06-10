"""
Tests for bin/hat-timing-stamp (core timing helper).

observability 去插件化后，timing 由各 phase SKILL 内联经此 helper 写入。
helper 自带顶层 observability.enabled 门控（单一收口点）。

Run with:  python3 -m pytest bin/test_hat_timing_stamp.py -x -q
"""
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent / "hat-timing-stamp"


def run_stamp(*args):
    """Run hat-timing-stamp and return CompletedProcess."""
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def _write_config(tmp_path, enabled=True):
    """Write a task-config.json with top-level observability.enabled."""
    (tmp_path / "task-config.json").write_text(
        json.dumps({"observability": {"enabled": enabled}})
    )


def _timing_lines(tmp_path):
    f = tmp_path / "timing.jsonl"
    if not f.exists():
        return []
    return [ln for ln in f.read_text().splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# 1. first call creates the file
# ---------------------------------------------------------------------------
def test_first_call_creates_file(tmp_path):
    """First call creates timing.jsonl with a phase_start P1 entry."""
    _write_config(tmp_path, enabled=True)
    result = run_stamp(str(tmp_path), "phase_start", "P1")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    lines = _timing_lines(tmp_path)
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["event"] == "phase_start"
    assert obj["phase"] == "P1"
    assert "ts" in obj and "wall_clock" in obj


# ---------------------------------------------------------------------------
# 2. second call appends, does not overwrite
# ---------------------------------------------------------------------------
def test_second_call_appends(tmp_path):
    """Second call appends without overwriting (2 lines)."""
    _write_config(tmp_path, enabled=True)
    run_stamp(str(tmp_path), "phase_start", "P1")
    run_stamp(str(tmp_path), "phase_end", "P1")
    lines = _timing_lines(tmp_path)
    assert len(lines) == 2
    assert json.loads(lines[0])["event"] == "phase_start"
    assert json.loads(lines[1])["event"] == "phase_end"


# ---------------------------------------------------------------------------
# 3. disabled at top level → no-op
# ---------------------------------------------------------------------------
def test_disabled_toplevel_is_noop(tmp_path):
    """Top-level observability.enabled=false → no-op (no file, exit 0)."""
    _write_config(tmp_path, enabled=False)
    result = run_stamp(str(tmp_path), "phase_start", "P1")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert not (tmp_path / "timing.jsonl").exists()


# ---------------------------------------------------------------------------
# 4. written line is grep-matchable (compact JSON, no spaces)
# ---------------------------------------------------------------------------
def test_line_grep_matchable(tmp_path):
    """Written line matchable by both `"phase":"P1"` and `"event":"phase_start"`."""
    _write_config(tmp_path, enabled=True)
    run_stamp(str(tmp_path), "phase_start", "P1")
    content = (tmp_path / "timing.jsonl").read_text()
    assert '"phase":"P1"' in content
    assert '"event":"phase_start"' in content


# ---------------------------------------------------------------------------
# 5. custom event + k=v passthrough with type preservation
# ---------------------------------------------------------------------------
def test_custom_event_and_kv_fields(tmp_path):
    """Custom event (tdd_cycle) + k=v passthrough; bool stays JSON literal, string stays quoted."""
    _write_config(tmp_path, enabled=True)
    result = run_stamp(
        str(tmp_path), "tdd_cycle", "P4",
        "task=Task 1", "mode=full", "red_pass=false", "green_pass=true",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    obj = json.loads(_timing_lines(tmp_path)[0])
    assert obj["event"] == "tdd_cycle"
    assert obj["task"] == "Task 1"
    assert obj["mode"] == "full"
    assert obj["red_pass"] is False      # JSON boolean, not the string "false"
    assert obj["green_pass"] is True


# ---------------------------------------------------------------------------
# 6. default enabled when no config present
# ---------------------------------------------------------------------------
def test_default_enabled_when_no_config(tmp_path):
    """No task-config.json → default enabled (writes timing)."""
    result = run_stamp(str(tmp_path), "phase_start", "P1")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert (tmp_path / "timing.jsonl").exists()


# ---------------------------------------------------------------------------
# 7. control chars in a value must not break the single JSONL line
# ---------------------------------------------------------------------------
def test_value_with_control_chars_stays_valid_jsonl(tmp_path):
    """A value containing a newline is escaped, keeping the entry on ONE valid JSON line."""
    _write_config(tmp_path, enabled=True)
    result = run_stamp(str(tmp_path), "task_end", "P4", "note=line1\nline2", "status=done")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    lines = _timing_lines(tmp_path)
    assert len(lines) == 1, "newline in value must not split the JSONL line"
    obj = json.loads(lines[0])
    assert obj["note"] == "line1\nline2"
    assert obj["status"] == "done"


# ---------------------------------------------------------------------------
# 8. missing task-folder → clear error, exit 1
# ---------------------------------------------------------------------------
def test_missing_task_folder_errors(tmp_path):
    """Nonexistent task-folder (observability default-on) → exit 1 with a clear message."""
    missing = tmp_path / "does-not-exist"
    result = run_stamp(str(missing), "phase_start", "P1")
    assert result.returncode == 1
    assert "not found" in result.stderr
