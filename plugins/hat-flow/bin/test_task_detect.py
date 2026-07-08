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
    linear_data = {"id": "ISSUE", "title": "Test issue"}
    (task_dir / "linear.json").write_text(json.dumps(linear_data))

    result = run_detect(str(tmp_path))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert len(data["open"]) > 0
    task_entry = next(t for t in data["open"] if t["name"] == "2026-01-01-linear-task")
    assert task_entry["linear"] is not None
    assert task_entry["linear"]["id"] == "ISSUE"


# ---------------------------------------------------------------------------
# 6. test_worktree_pointer
# ---------------------------------------------------------------------------
def test_worktree_pointer(tmp_path):
    """Stub task dir with a .worktree pointer surfaces a 'worktree' field."""
    task_dir = tmp_path / "open" / "2026-06-17-wt-task"
    task_dir.mkdir(parents=True)
    (task_dir / ".worktree").write_text("/abs/path/.claude/worktrees/2026-06-17-wt-task\n")

    result = run_detect(str(tmp_path))

    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    task_entry = next(t for t in data["open"] if t["name"] == "2026-06-17-wt-task")
    assert task_entry["worktree"] == "/abs/path/.claude/worktrees/2026-06-17-wt-task"


def test_no_worktree_field_when_absent(tmp_path):
    """A normal open task has no 'worktree' key."""
    task_dir = tmp_path / "open" / "2026-06-17-plain"
    task_dir.mkdir(parents=True)
    (task_dir / "plan.md").write_text("- [ ] x\n")

    result = run_detect(str(tmp_path))
    data = json.loads(result.stdout)
    task_entry = next(t for t in data["open"] if t["name"] == "2026-06-17-plain")
    assert "worktree" not in task_entry


def test_worktree_artifacts_read_from_worktree(tmp_path):
    """产物住在 worktree 内时，从 worktree（非 stub）探测 design/plan/progress。"""
    stub_dir = tmp_path / "open" / "2026-06-17-wt-relocate"
    stub_dir.mkdir(parents=True)
    wt_dir = tmp_path / "worktrees" / "2026-06-17-wt-relocate"
    wt_dir.mkdir(parents=True)
    (wt_dir / "design.md").write_text("# design\n")
    (wt_dir / "plan.md").write_text("- [x] a\n- [ ] b\n")
    (stub_dir / ".worktree").write_text(f"{wt_dir}\n")

    result = run_detect(str(tmp_path))
    data = json.loads(result.stdout)
    task_entry = next(t for t in data["open"] if t["name"] == "2026-06-17-wt-relocate")
    assert task_entry["hasDesign"] is True
    assert task_entry["hasPlan"] is True
    assert task_entry["planProgress"] == {"total": 2, "checked": 1, "unchecked": 1}
    assert task_entry["worktree"] == str(wt_dir)
    assert "worktreeMissing" not in task_entry


def test_worktree_pointer_stale_marks_missing(tmp_path):
    """worktree 指针指向不存在的目录 → 回退 stub 并标 worktreeMissing。"""
    stub_dir = tmp_path / "open" / "2026-06-17-wt-stale"
    stub_dir.mkdir(parents=True)
    (stub_dir / ".worktree").write_text("/nonexistent/worktrees/2026-06-17-wt-stale\n")

    result = run_detect(str(tmp_path))
    data = json.loads(result.stdout)
    task_entry = next(t for t in data["open"] if t["name"] == "2026-06-17-wt-stale")
    assert task_entry["worktreeMissing"] is True
    assert task_entry["hasPlan"] is False
