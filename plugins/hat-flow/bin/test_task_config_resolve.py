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


# ---------------------------------------------------------------------------
# todo_sync enum (off | overview | full) + legacy boolean normalization
# ---------------------------------------------------------------------------
def test_todo_sync_enum_passthrough(tmp_path):
    # guards the SHIPPED template: preset enum values resolve as expected
    # (regression guard against a preset accidentally reverting to legacy boolean)
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "full"
    r = run_resolve(tmp_path, "--preset", "hotfix")
    assert json.loads(r.stdout)["todo_sync"] == "off"


def test_todo_sync_overview_via_layer(tmp_path):
    _write(tmp_path / "task-defaults.json", {"todo_sync": "overview"})
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "overview"


def test_todo_sync_legacy_boolean_migrates(tmp_path):
    # legacy true → full
    _write(tmp_path / "task-defaults.json", {"todo_sync": True})
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "full"
    # legacy false → off
    _write(tmp_path / "task-defaults.json", {"todo_sync": False})
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "off"


def test_todo_sync_illegal_value_falls_back_to_full(tmp_path):
    _write(tmp_path / "task-defaults.json", {"todo_sync": "bogus"})
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "full"
    assert r.stderr == ""  # config-layer illegal value falls back silently (no warning)


def test_todo_sync_json_null_falls_back_to_full(tmp_path):
    # key present but value JSON null (Python None) → not bool, not in enum → full
    _write(tmp_path / "task-defaults.json", {"todo_sync": None})
    r = run_resolve(tmp_path, "--preset", "standard")
    assert json.loads(r.stdout)["todo_sync"] == "full"


def test_todo_sync_missing_defaults_to_full(tmp_path):
    # run_resolve uses the real TEMPLATE (always sets todo_sync); call subprocess
    # directly with a minimal template to exercise the missing-key path
    tmpl = tmp_path / "tmpl.json"
    _write(tmpl, {"preset": "standard", "presets": {"standard": {}}})
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--template", str(tmpl),
         "--project-root", str(tmp_path), "--global-local", "/nonexistent/g.json",
         "--preset", "standard"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["todo_sync"] == "full"


def test_todo_sync_flag_overrides_config(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard", "--todo-sync", "overview")
    assert json.loads(r.stdout)["todo_sync"] == "overview"


def test_todo_sync_flag_beats_flags_json(tmp_path):
    # --todo-sync is more specific than a --flags JSON todo_sync
    r = run_resolve(
        tmp_path, "--preset", "standard",
        "--flags", json.dumps({"todo_sync": "off"}),
        "--todo-sync", "full",
    )
    assert json.loads(r.stdout)["todo_sync"] == "full"


def test_todo_sync_flag_illegal_falls_back_to_config(tmp_path):
    r = run_resolve(tmp_path, "--preset", "standard", "--todo-sync", "bogus")
    assert r.returncode == 0
    assert json.loads(r.stdout)["todo_sync"] == "full"  # config (standard) value kept
    assert "invalid value" in r.stderr
