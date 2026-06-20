"""
Characterization tests for bin/hat-task-artifact-check.

Run with:  python3 -m pytest bin/test_task_artifact_check.py -x -q
"""
import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent / "hat-task-artifact-check"


def run_check(*args):
    """Run hat-task-artifact-check and return CompletedProcess."""
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def _write_config(tmp_path, plugins):
    """plugins: dict like {"linear": {"enabled": True}} → task-config.json."""
    p = tmp_path / "task-config.json"
    p.write_text(json.dumps({"plugins": plugins}))
    return p


# ---------------------------------------------------------------------------
# Core file gates
# ---------------------------------------------------------------------------
def test_phase1_pass(tmp_path):
    """Phase 1 with prompt.md + phases.md present → exit 0, PASS."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")

    result = run_check(str(tmp_path), "1")

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase1_missing_file(tmp_path):
    """Phase 1 with prompt.md but NO phases.md → exit 1, FAIL."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")

    result = run_check(str(tmp_path), "1")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout


def test_invalid_phase(tmp_path):
    """Phase number outside 1-6 → exit 1, stderr contains 'must be between'."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")

    result = run_check(str(tmp_path), "9")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "must be between" in result.stderr


def test_missing_task_dir():
    """Nonexistent task directory → exit 1, stderr contains 'not found'."""
    result = run_check("/nonexistent/task/dir", "1")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "not found" in result.stderr


# ---------------------------------------------------------------------------
# Plugin-conditional gate: linear → linear.json (the only config-reading path)
# ---------------------------------------------------------------------------
def test_phase1_linear_enabled_requires_linear_json(tmp_path):
    """linear enabled + linear.json absent → FAIL (plugin file gate active)."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")
    cfg = _write_config(tmp_path, {"linear": {"enabled": True}})

    result = run_check(str(tmp_path), "1", "--config", str(cfg))

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout
    assert "linear.json" in result.stdout


def test_phase1_linear_enabled_with_file_pass(tmp_path):
    """linear enabled + linear.json present → PASS."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")
    (tmp_path / "linear.json").write_text("{}\n")
    cfg = _write_config(tmp_path, {"linear": {"enabled": True}})

    result = run_check(str(tmp_path), "1", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase1_linear_disabled_skips_gate(tmp_path):
    """linear disabled + linear.json absent → PASS (gate inactive)."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")
    cfg = _write_config(tmp_path, {"linear": {"enabled": False}})

    result = run_check(str(tmp_path), "1", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


# ---------------------------------------------------------------------------
# Per-phase core gates (no timing/observability machinery)
# ---------------------------------------------------------------------------
def test_phase4_no_gate_pass(tmp_path):
    """Phase 4 has no required artifacts → PASS even on an empty folder."""
    result = run_check(str(tmp_path), "4")

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase5_pass(tmp_path):
    """Phase 5 with acceptance-checklist.md present → PASS."""
    (tmp_path / "acceptance-checklist.md").write_text("# checklist\n")

    result = run_check(str(tmp_path), "5")

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase5_missing_fail(tmp_path):
    """Phase 5 without acceptance-checklist.md → FAIL."""
    result = run_check(str(tmp_path), "5")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout


def test_phase6_pass(tmp_path):
    """Phase 6 with final.md + conversation.md + consumption-report.md → PASS (no timing.jsonl)."""
    (tmp_path / "final.md").write_text("# final\n")
    (tmp_path / "conversation.md").write_text("# conv\n")
    (tmp_path / "consumption-report.md").write_text("# cons\n")

    result = run_check(str(tmp_path), "6")

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase6_missing_consumption_fail(tmp_path):
    """Phase 6 missing consumption-report.md → FAIL (token report still gated)."""
    (tmp_path / "final.md").write_text("# final\n")
    (tmp_path / "conversation.md").write_text("# conv\n")

    result = run_check(str(tmp_path), "6")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout
