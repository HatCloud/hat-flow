"""
Characterization tests for bin/hat-task-detect.

Run with:  python3 -m pytest bin/test_task_detect.py -x -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "hat-task-detect"


def run_detect(*args):
    """Run hat-task-detect and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# 1. test_empty_scan
# ---------------------------------------------------------------------------
def test_empty_scan(tmp_path):
    """Empty directory → exit 0, valid JSON, open array is empty."""
    result = run_detect(str(tmp_path))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert isinstance(data["open"], list)
    assert len(data["open"]) == 0


# ---------------------------------------------------------------------------
# 2. test_with_open_task
# ---------------------------------------------------------------------------
def test_with_open_task(tmp_path):
    """Open task directory with plan.md is included in the 'open' list."""
    task_dir = tmp_path / ".tasks" / "open" / "2026-01-01-test"
    task_dir.mkdir(parents=True)
    (task_dir / "plan.md").write_text("- [ ] step one\n- [x] step two\n")

    result = run_detect(str(tmp_path / ".tasks"))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    names = [t["name"] for t in data["open"]]
    assert "2026-01-01-test" in names


# ---------------------------------------------------------------------------
# 3. test_nonexistent_base_path
# ---------------------------------------------------------------------------
def test_nonexistent_base_path():
    """Nonexistent base path → exit 0, open array is empty (not an error)."""
    result = run_detect("/nonexistent/base/path")

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert isinstance(data["open"], list)
    assert len(data["open"]) == 0


# ---------------------------------------------------------------------------
# 4. test_with_done_task
# ---------------------------------------------------------------------------
def test_with_done_task(tmp_path):
    """Done task directory is listed in the 'done' array by name."""
    done_dir = tmp_path / "done" / "2026-01-01-done-task"
    done_dir.mkdir(parents=True)

    result = run_detect(str(tmp_path))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "2026-01-01-done-task" in data["done"]


# ---------------------------------------------------------------------------
# 5. test_with_linear_json
# ---------------------------------------------------------------------------
def test_with_linear_json(tmp_path):
    """Open task with linear.json has non-null 'linear' field in result."""
    task_dir = tmp_path / "open" / "2026-01-01-linear-task"
    task_dir.mkdir(parents=True)
    (task_dir / "plan.md").write_text("- [ ] do something\n")
    linear_data = {"id": "HAT-42", "title": "Test issue"}
    (task_dir / "linear.json").write_text(json.dumps(linear_data))

    result = run_detect(str(tmp_path))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert len(data["open"]) > 0
    task_entry = next(t for t in data["open"] if t["name"] == "2026-01-01-linear-task")
    assert task_entry["linear"] is not None
    assert task_entry["linear"]["id"] == "HAT-42"
