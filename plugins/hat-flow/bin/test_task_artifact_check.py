"""
Characterization tests for bin/hat-task-artifact-check.

Run with:  python3 -m pytest bin/test_task_artifact_check.py -x -q
"""
import json
import os
import shutil
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


def _path_without_jq(tmp_path):
    """Build a PATH dir holding the pre-guard externals (env/bash/dirname) but no jq.

    Locks the dependency declaration: a clean environment lacking jq must fail
    loudly, not silently degrade. Regression for the clean-env packaging defect
    where jq was an undeclared hard dependency.
    """
    bindir = tmp_path / "nojq-bin"
    bindir.mkdir()
    for cmd in ("env", "bash", "dirname", "pwd"):
        p = shutil.which(cmd)
        if p:
            os.symlink(p, bindir / cmd)
    return {"PATH": str(bindir)}


def test_missing_jq_fails_loudly(tmp_path):
    """jq absent → exit 1 with an actionable error (not a silent timing misfire)."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")
    result = subprocess.run(
        [str(SCRIPT), str(tmp_path), "1"],
        capture_output=True,
        text=True,
        env=_path_without_jq(tmp_path),
    )
    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "jq" in result.stderr.lower()


# ---------------------------------------------------------------------------
# 1. test_phase1_pass
# ---------------------------------------------------------------------------
def test_phase1_pass(tmp_path):
    """Phase 1 with prompt.md + phases.md present → exit 0, stdout contains PASS."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    (tmp_path / "phases.md").write_text("# Phases\n")

    result = run_check(str(tmp_path), "1")

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


# ---------------------------------------------------------------------------
# 2. test_phase1_missing_file
# ---------------------------------------------------------------------------
def test_phase1_missing_file(tmp_path):
    """Phase 1 with prompt.md but NO phases.md → exit 1, stdout contains FAIL."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")
    # phases.md intentionally not created

    result = run_check(str(tmp_path), "1")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# 3. test_invalid_phase
# ---------------------------------------------------------------------------
def test_invalid_phase(tmp_path):
    """Phase number outside 1-6 → exit 1, stderr contains 'must be between'."""
    (tmp_path / "prompt.md").write_text("# Prompt\n")

    result = run_check(str(tmp_path), "9")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "must be between" in result.stderr


# ---------------------------------------------------------------------------
# 4. test_missing_task_dir
# ---------------------------------------------------------------------------
def test_missing_task_dir():
    """Nonexistent task directory → exit 1, stderr contains 'not found'."""
    result = run_check("/nonexistent/task/dir", "1")

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "not found" in result.stderr


# ---------------------------------------------------------------------------
# Timing trace checks (WS-D Layer 2)
# ---------------------------------------------------------------------------
def _write_config(tmp_path, observability=True):
    # observability is a top-level core key (ISSUE: de-pluginized), no longer under plugins.*
    config = {
        "observability": {"enabled": observability},
    }
    p = tmp_path / "task-config.json"
    p.write_text(json.dumps(config))
    return p


def _write_timing(tmp_path, events):
    """events: list of (event, phase) tuples → one compact JSON object per line (matches hook output)."""
    lines = [
        json.dumps(
            {"event": ev, "phase": ph, "ts": "2026-05-24T00:00:00Z"},
            separators=(",", ":"),
        )
        for ev, ph in events
    ]
    (tmp_path / "timing.jsonl").write_text("\n".join(lines) + "\n")


def test_phase4_timing_complete_pass(tmp_path):
    """observability on; P4 timing has start+end → PASS (Phase 4 has no required file gate, only timing)."""
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(tmp_path, [("phase_start", "P4"), ("phase_end", "P4")])

    result = run_check(str(tmp_path), "4", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout
    assert "P4 phase_start+phase_end" in result.stdout


def test_phase4_timing_missing_start_fail(tmp_path):
    """observability on; timing.jsonl has NO phase_start P4 → FAIL (phase hook never ran)."""
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(tmp_path, [("phase_start", "P3"), ("phase_end", "P3")])

    result = run_check(str(tmp_path), "4", "--config", str(cfg))

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout
    assert "no phase_start for P4" in result.stdout


def test_phase5_timing_missing_start_fail(tmp_path):
    """observability on; P5 files present but timing.jsonl has NO phase_start P5 → FAIL (hook never ran — the meta-bug)."""
    (tmp_path / "acceptance-checklist.md").write_text("# checklist\n")
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(tmp_path, [("phase_start", "P4"), ("phase_end", "P4")])

    result = run_check(str(tmp_path), "5", "--config", str(cfg))

    assert result.returncode == 1, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "FAIL" in result.stdout
    # pin the failure to the timing check (missing phase_start), not a missing file
    assert "no phase_start for P5" in result.stdout


def test_phase5_timing_complete_pass(tmp_path):
    """observability on; P5 files present + timing has P5 start+end → PASS."""
    (tmp_path / "acceptance-checklist.md").write_text("# checklist\n")
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(tmp_path, [("phase_start", "P5"), ("phase_end", "P5")])

    result = run_check(str(tmp_path), "5", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout
    assert "P5 phase_start+phase_end" in result.stdout


def test_phase5_timing_completed_no_end_warns(tmp_path):
    """P5 has start but no end, and P6 already started → non-blocking WARNING, exit 0.

    Mid-flow phase-end hooks are not reliably emitted, so a missing phase_end on an
    already-completed phase is a soft signal — not the meta-bug. The meta-bug (hook never
    ran) is a missing phase_start, caught by test_phase5_timing_missing_start_fail.
    """
    (tmp_path / "acceptance-checklist.md").write_text("# checklist\n")
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(tmp_path, [("phase_start", "P5"), ("phase_start", "P6")])

    result = run_check(str(tmp_path), "5", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout
    # the missing end is surfaced as a non-blocking warning, not a FAIL
    assert "no phase_end" in result.stdout
    assert "not blocking" in result.stdout


def test_phase6_timing_in_progress_pass(tmp_path):
    """P6 has start, no end, no later phase started → in-progress exemption → PASS (terminal-gate scenario)."""
    (tmp_path / "final.md").write_text("# final\n")
    (tmp_path / "conversation.md").write_text("# conv\n")
    (tmp_path / "consumption-report.md").write_text("# cons\n")
    cfg = _write_config(tmp_path, observability=True)
    _write_timing(
        tmp_path,
        [("phase_start", "P5"), ("phase_end", "P5"), ("phase_start", "P6")],
    )

    result = run_check(str(tmp_path), "6", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase_timing_observability_off_failopen_toplevel(tmp_path):
    """Top-level observability.enabled=false + timing.jsonl missing → check_timing fail-open → PASS.

    Locks the migrated signal source: artifact-check reads the top-level `observability` switch,
    not `plugins.observability`. With obs off the timing gate is skipped (no false positive).
    P4 has no required-file gate, so this isolates the check_timing path.
    """
    cfg = _write_config(tmp_path, observability=False)
    # timing.jsonl intentionally NOT created

    result = run_check(str(tmp_path), "4", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase_timing_no_config_failopen(tmp_path):
    """Configless (no task-config.json) + timing.jsonl missing → obs_enabled fail-open → PASS.

    obs_enabled() returns disabled when CONFIG_FILE is absent (preserving prior configless
    behavior). Isolates that branch via P4 (no required-file gate), with no --config flag.
    """
    # neither task-config.json nor timing.jsonl created
    result = run_check(str(tmp_path), "4")  # no --config flag → CONFIG_FILE absent

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout


def test_phase6_timing_observability_off_failopen(tmp_path):
    """observability OFF; timing.jsonl absent → timing check skipped (fail-open) → PASS, no false positive."""
    (tmp_path / "final.md").write_text("# final\n")
    (tmp_path / "conversation.md").write_text("# conv\n")
    (tmp_path / "consumption-report.md").write_text("# cons\n")
    cfg = _write_config(tmp_path, observability=False)
    # timing.jsonl intentionally NOT created

    result = run_check(str(tmp_path), "6", "--config", str(cfg))

    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    assert "PASS" in result.stdout
