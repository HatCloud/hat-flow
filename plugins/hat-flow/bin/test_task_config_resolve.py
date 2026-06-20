"""Tests for bin/hat-task-config-resolve (three-layer task config resolver).

Run with:  python3 -m pytest bin/test_task_config_resolve.py -x -q
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "hat-task-config-resolve"
TEMPLATE = Path(__file__).parent.parent / "skills" / "task" / "task-defaults.json"


def run_resolve(project_root, *args, global_local=None):
    cmd = [
        sys.executable, str(SCRIPT),
        "--template", str(TEMPLATE),
        "--project-root", str(project_root),
    ]
    if global_local is not None:
        cmd += ["--global-local", str(global_local)]
    else:
        cmd += ["--global-local", "/nonexistent/global.json"]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


def _write(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


# ---------------------------------------------------------------------------
# branch.worktree sentinel resolution
# ---------------------------------------------------------------------------
def test_worktree_ask_stays_ask_interactive(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["branch"]["worktree"] == "ask"
    assert d["branch"]["mode"] == "keep"


def test_worktree_ask_resolves_true_in_quiet(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard", "--quiet")
    d = json.loads(r.stdout)
    assert d["branch"]["worktree"] is True


def test_explicit_worktree_false_wins_in_quiet(tmp_path):
    _write(tmp_path / "task-defaults.json", {"branch": {"worktree": False}})
    r = run_resolve(tmp_path, "--preset", "standard", "--quiet")
    d = json.loads(r.stdout)
    assert d["branch"]["worktree"] is False


# ---------------------------------------------------------------------------
# three-layer precedence: project ③ > global ② > template ①
# ---------------------------------------------------------------------------
def test_project_local_beats_global_local(tmp_path):
    glob = tmp_path / "global.json"
    _write(glob, {"branch": {"worktree": True}})
    _write(tmp_path / "task-defaults.json", {"branch": {"worktree": False}})
    r = run_resolve(tmp_path, "--preset", "standard", "--quiet", global_local=glob)
    d = json.loads(r.stdout)
    assert d["branch"]["worktree"] is False  # project local wins


def test_global_local_overrides_template(tmp_path):
    glob = tmp_path / "global.json"
    _write(glob, {"headless": {"degrade_policy": "headless"}})
    r = run_resolve(tmp_path, "--preset", "standard", global_local=glob)
    d = json.loads(r.stdout)
    assert d["headless"]["degrade_policy"] == "headless"


def test_flags_beat_project_local(tmp_path):
    _write(tmp_path / "task-defaults.json", {"branch": {"worktree": False}})
    r = run_resolve(
        tmp_path, "--preset", "standard",
        "--flags", json.dumps({"branch": {"worktree": True}}),
    )
    d = json.loads(r.stdout)
    assert d["branch"]["worktree"] is True


# ---------------------------------------------------------------------------
# preset block merges onto top-level defaults
# ---------------------------------------------------------------------------
def test_preset_block_applied(tmp_path):
    r = run_resolve(tmp_path, "--preset", "hotfix")
    d = json.loads(r.stdout)
    assert d["preset"] == "hotfix"
    assert d["plugins"]["review"]["enabled"] is False


def test_layer_override_survives_preset(tmp_path):
    # project local turns retrospective off; preset standard has it on
    _write(tmp_path / "task-defaults.json", {"plugins": {"retrospective": {"enabled": False}}})
    r = run_resolve(tmp_path, "--preset", "standard")
    d = json.loads(r.stdout)
    assert d["plugins"]["retrospective"]["enabled"] is False
    # untouched preset value remains
    assert d["plugins"]["review"]["code_review"] == "medium"


# ---------------------------------------------------------------------------
# auto values preserved for the skill to resolve
# ---------------------------------------------------------------------------
def test_auto_values_preserved(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard")
    d = json.loads(r.stdout)
    assert d["plugins"]["linear"]["enabled"] == "auto"
    assert d["plugins"]["git"]["enabled"] == "auto"


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------
def test_missing_template_errors(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--template", "/nonexistent/t.json",
         "--project-root", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert r.returncode == 2


def test_bad_flags_json_errors(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard", "--flags", "{not json")
    assert r.returncode == 2
