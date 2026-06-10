"""
TDD tests for bin/hat-plugin-hook robustness fixes.
Run: python3 -m pytest bin/test_plugin_hook.py -x -q
"""
import subprocess
import json
from pathlib import Path

HOOK_BIN = Path(__file__).parent / "hat-plugin-hook"


def run_hook(*args, **kwargs):
    """Helper: run hat-plugin-hook with given args, return CompletedProcess."""
    return subprocess.run(
        [str(HOOK_BIN)] + list(args),
        capture_output=True,
        text=True,
    )


def test_insufficient_args():
    """No arguments: should exit 1."""
    result = run_hook()
    assert result.returncode == 1, (
        f"Expected exit 1 for no args, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )


def test_missing_task_folder():
    """Non-existent task folder path: should exit 1 with 'error' in stderr."""
    result = run_hook("/nonexistent/path/that/does/not/exist", "P1.phase-start")
    assert result.returncode == 1, (
        f"Expected exit 1 for missing folder, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert "error" in result.stderr.lower(), (
        f"Expected 'error' (case-insensitive) in stderr, got: {result.stderr!r}"
    )


def test_missing_config_file(tmp_path):
    """Existing folder but no task-config.json: should exit 0 with WARN in stderr."""
    result = run_hook(str(tmp_path), "P1.phase-start")
    assert result.returncode == 0, (
        f"Expected exit 0 for missing config, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert "WARN" in result.stderr, (
        f"Expected 'WARN' in stderr, got: {result.stderr!r}"
    )


def test_malformed_json(tmp_path):
    """Malformed task-config.json: should exit 1 with 'error' in stderr."""
    config = tmp_path / "task-config.json"
    config.write_text("{invalid json here")
    result = run_hook(str(tmp_path), "P1.phase-start")
    assert result.returncode == 1, (
        f"Expected exit 1 for malformed JSON, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert "error" in result.stderr.lower(), (
        f"Expected 'error' (case-insensitive) in stderr, got: {result.stderr!r}"
    )


def test_valid_no_plugins(tmp_path):
    """Valid config with empty plugins dict: should exit 0, stdout empty."""
    config = tmp_path / "task-config.json"
    config.write_text(json.dumps({"plugins": {}}))
    result = run_hook(str(tmp_path), "P1.phase-start")
    assert result.returncode == 0, (
        f"Expected exit 0 for valid config with no plugins, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert result.stdout.strip() == "", (
        f"Expected empty stdout, got: {result.stdout!r}"
    )


# --- Happy path integration tests ---


def _setup_plugin_env(tmp_path, hook_point="P1.phase-start"):
    """Create a minimal plugin environment for happy-path testing.

    Returns (task_folder, plugins_dir) where plugins_dir contains a
    test plugin with a manifest and .md instruction file.
    """
    task_folder = tmp_path / "task"
    task_folder.mkdir()

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Manifest: single hook registration
    manifest = {
        "name": "testplugin",
        "description": "test",
        "hooks": {
            hook_point: {
                "priority": 10,
                "section": "## Test Section",
                "on_error": "graceful",
            }
        },
    }
    (plugins_dir / "testplugin.manifest.json").write_text(json.dumps(manifest))

    # Instruction file with matching section
    md_content = "## Test Section\n\nThis is test instruction content.\n\nWith multiple lines.\n\n## Other Section\n\nShould not appear.\n"
    (plugins_dir / "testplugin.md").write_text(md_content)

    # task-config.json enabling the plugin
    config = {"plugins": {"testplugin": {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))

    return task_folder, plugins_dir


def _run_hook_with_plugins_dir(task_folder, hook_point, plugins_dir):
    """Run hat-plugin-hook with a custom PLUGINS_DIR."""
    import os

    env = os.environ.copy()
    # Read the script source to understand how to override PLUGINS_DIR
    # The script hardcodes PLUGINS_DIR="${CLAUDE_PLUGIN_ROOT}/skills/task/plugins"
    # We need to modify the script invocation — use env var or sed.
    # Simpler: create a wrapper that overrides PLUGINS_DIR.
    wrapper = task_folder.parent / "hook-wrapper.sh"
    wrapper.write_text(
        f'#!/usr/bin/env bash\n'
        f'export PLUGINS_DIR="{plugins_dir}"\n'
        f'source "{HOOK_BIN}" "$@"\n'
    )
    wrapper.chmod(0o755)

    # Actually, sourcing won't work because hat-plugin-hook calls exit.
    # Instead, use sed to replace PLUGINS_DIR in a copy of the script.
    import shutil

    hook_copy = task_folder.parent / "hat-plugin-hook-test"
    shutil.copy2(HOOK_BIN, hook_copy)
    hook_copy.chmod(0o755)

    # Replace the PLUGINS_DIR line
    content = hook_copy.read_text()
    content = content.replace(
        'PLUGINS_DIR="$SKILL_ROOT/skills/task/plugins"',
        f'PLUGINS_DIR="{plugins_dir}"',
    )
    hook_copy.write_text(content)

    return subprocess.run(
        [str(hook_copy), str(task_folder), hook_point],
        capture_output=True,
        text=True,
    )


def test_happy_path_single_plugin(tmp_path):
    """Enabled plugin with matching hook: should output section content."""
    task_folder, plugins_dir = _setup_plugin_env(tmp_path)
    result = _run_hook_with_plugins_dir(task_folder, "P1.phase-start", plugins_dir)
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert "plugin:testplugin" in result.stdout
    assert "test instruction content" in result.stdout
    assert "Should not appear" not in result.stdout


def test_happy_path_no_matching_hook(tmp_path):
    """Enabled plugin but no handler for this hook point: exit 0, empty stdout."""
    task_folder, plugins_dir = _setup_plugin_env(tmp_path, hook_point="P1.phase-start")
    result = _run_hook_with_plugins_dir(task_folder, "P2.phase-start", plugins_dir)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_happy_path_disabled_plugin(tmp_path):
    """Plugin exists but disabled in config: exit 0, empty stdout."""
    task_folder, plugins_dir = _setup_plugin_env(tmp_path)
    config = {"plugins": {"testplugin": {"enabled": False}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))
    result = _run_hook_with_plugins_dir(task_folder, "P1.phase-start", plugins_dir)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_happy_path_multiple_plugins_priority(tmp_path):
    """Two plugins with different priorities: lower priority number first."""
    task_folder = tmp_path / "task"
    task_folder.mkdir()
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    for name, prio, content in [
        ("alpha", 20, "Alpha output"),
        ("beta", 5, "Beta output"),
    ]:
        manifest = {
            "name": name,
            "hooks": {
                "P1.phase-start": {
                    "priority": prio,
                    "section": "## Hook",
                    "on_error": "graceful",
                }
            },
        }
        (plugins_dir / f"{name}.manifest.json").write_text(json.dumps(manifest))
        (plugins_dir / f"{name}.md").write_text(f"## Hook\n\n{content}\n")

    config = {"plugins": {"alpha": {"enabled": True}, "beta": {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))

    result = _run_hook_with_plugins_dir(task_folder, "P1.phase-start", plugins_dir)
    assert result.returncode == 0
    # beta (priority 5) should appear before alpha (priority 20)
    beta_pos = result.stdout.index("Beta output")
    alpha_pos = result.stdout.index("Alpha output")
    assert beta_pos < alpha_pos, (
        f"Expected beta (prio 5) before alpha (prio 20), "
        f"but beta at {beta_pos}, alpha at {alpha_pos}"
    )


def test_happy_path_missing_md_file_graceful(tmp_path):
    """Plugin enabled, manifest exists, but .md file missing: graceful skip."""
    task_folder = tmp_path / "task"
    task_folder.mkdir()
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    manifest = {
        "name": "broken",
        "hooks": {
            "P1.phase-start": {
                "priority": 10,
                "section": "## Hook",
                "on_error": "graceful",
            }
        },
    }
    (plugins_dir / "broken.manifest.json").write_text(json.dumps(manifest))
    # Intentionally no broken.md file

    config = {"plugins": {"broken": {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))

    result = _run_hook_with_plugins_dir(task_folder, "P1.phase-start", plugins_dir)
    assert result.returncode == 0
    assert "not found" in result.stderr.lower()


# --- execution mode filtering tests ---


def _setup_execution_env(tmp_path, hooks, plugin_name="execplugin", subagents=None):
    """Create a plugin env where `hooks` maps hook_point -> hook config.

    A hook config may be a single dict (object form) or a list of dicts
    (array form). Each config may include an `execution` field. `subagents`,
    if given, is written as the manifest's top-level subagents block (so
    subagent:NAME hooks can resolve model/subagent_type/context_section for
    the DISPATCH directive). The .md file gets one section per config's
    `section` title. Returns (task_folder, plugins_dir).
    """
    task_folder = tmp_path / "task"
    task_folder.mkdir()
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    manifest = {"name": plugin_name, "description": "test", "hooks": hooks}
    if subagents is not None:
        manifest["subagents"] = subagents
    (plugins_dir / f"{plugin_name}.manifest.json").write_text(json.dumps(manifest))

    md_parts = []
    for value in hooks.values():
        configs = value if isinstance(value, list) else [value]
        for cfg in configs:
            title = cfg["section"]
            md_parts.append(f"{title}\n\nContent for {title}.\n")
    (plugins_dir / f"{plugin_name}.md").write_text("\n".join(md_parts))

    config = {"plugins": {plugin_name: {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))
    return task_folder, plugins_dir


def _run_hook_copy(task_folder, plugins_dir, *args):
    """Run a PLUGINS_DIR-overridden copy of hat-plugin-hook with arbitrary args."""
    import shutil

    hook_copy = task_folder.parent / "hat-plugin-hook-test"
    shutil.copy2(HOOK_BIN, hook_copy)
    hook_copy.chmod(0o755)
    content = hook_copy.read_text().replace(
        'PLUGINS_DIR="$SKILL_ROOT/skills/task/plugins"',
        f'PLUGINS_DIR="{plugins_dir}"',
    )
    hook_copy.write_text(content)
    return subprocess.run(
        [str(hook_copy), str(task_folder)] + list(args),
        capture_output=True,
        text=True,
    )


def test_execution_inline_in_header(tmp_path):
    """Hook with execution=inline: comment header shows execution:inline."""
    hooks = {
        "P1.phase-start": {
            "priority": 10,
            "section": "## Inline Hook",
            "on_error": "graceful",
            "execution": "inline",
        }
    }
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks)
    result = _run_hook_copy(task_folder, plugins_dir, "P1.phase-start")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "execution:inline" in result.stdout
    assert "Content for ## Inline Hook" in result.stdout


def test_execution_subagent_emits_dispatch_by_default(tmp_path):
    """Hook with execution=subagent:* emits a DISPATCH directive (not its body)."""
    hooks = {
        "P2.phase-end": {
            "priority": 10,
            "section": "## Subagent Hook",
            "on_error": "graceful",
            "execution": "subagent:foo",
        }
    }
    subagents = {"foo": {"model": "haiku", "subagent_type": "general-purpose",
                         "context_section": "## Foo Context"}}
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks, subagents=subagents)
    result = _run_hook_copy(task_folder, plugins_dir, "P2.phase-end")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # DISPATCH directive emitted; per-hook body NOT emitted inline
    assert "<!-- DISPATCH" in result.stdout
    assert "name:foo" in result.stdout
    assert "Content for ## Subagent Hook" not in result.stdout
    assert "dispatched async" in result.stderr.lower()


def test_dispatch_directive_includes_subagent_config(tmp_path):
    """DISPATCH directive carries model/subagent_type/context_section from manifest."""
    hooks = {
        "P3.phase-end": {
            "priority": 10,
            "section": "## P3 Hook",
            "on_error": "graceful",
            "execution": "subagent:linear-sync",
        }
    }
    subagents = {"linear-sync": {"model": "haiku", "subagent_type": "general-purpose",
                                 "context_section": "## Subagent Context"}}
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks, subagents=subagents)
    result = _run_hook_copy(task_folder, plugins_dir, "P3.phase-end")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "model:haiku" in result.stdout
    assert "subagent_type:general-purpose" in result.stdout
    assert "section:## Subagent Context" in result.stdout
    assert "hook:P3.phase-end" in result.stdout


def test_no_filter_outputs_subagent_hook_inline(tmp_path):
    """With --no-filter, subagent hook body is emitted inline (no DISPATCH)."""
    hooks = {
        "P2.phase-end": {
            "priority": 10,
            "section": "## Subagent Hook",
            "on_error": "graceful",
            "execution": "subagent:foo",
        }
    }
    subagents = {"foo": {"model": "haiku", "subagent_type": "general-purpose",
                         "context_section": "## Foo Context"}}
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks, subagents=subagents)
    result = _run_hook_copy(task_folder, plugins_dir, "P2.phase-end", "--no-filter")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Content for ## Subagent Hook" in result.stdout
    assert "<!-- DISPATCH" not in result.stdout


def test_missing_execution_defaults_inline(tmp_path):
    """Hook without execution field defaults to inline (backward compat)."""
    hooks = {
        "P1.phase-start": {
            "priority": 10,
            "section": "## Legacy Hook",
            "on_error": "graceful",
        }
    }
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks)
    result = _run_hook_copy(task_folder, plugins_dir, "P1.phase-start")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "execution:inline" in result.stdout
    assert "Content for ## Legacy Hook" in result.stdout


def test_default_mode_routes_by_config_not_env(tmp_path):
    """Default mode routing depends only on manifest config, not any env var.

    A manifest mixing one inline + one subagent hook at the same hook point
    (array form) emits the inline body AND a DISPATCH directive for the
    subagent — but never the subagent hook's body inline.
    """
    hooks = {
        "P2.phase-end": [
            {
                "priority": 10,
                "section": "## Inline Part",
                "on_error": "graceful",
                "execution": "inline",
            },
            {
                "priority": 20,
                "section": "## Subagent Part",
                "on_error": "graceful",
                "execution": "subagent:linear-sync",
            },
        ]
    }
    subagents = {"linear-sync": {"model": "haiku", "subagent_type": "general-purpose",
                                 "context_section": "## Subagent Context"}}
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks, subagents=subagents)
    result = _run_hook_copy(task_folder, plugins_dir, "P2.phase-end")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Content for ## Inline Part" in result.stdout
    assert "<!-- DISPATCH" in result.stdout
    assert "name:linear-sync" in result.stdout
    assert "Content for ## Subagent Part" not in result.stdout
