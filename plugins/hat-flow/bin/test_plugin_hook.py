"""
TDD tests for bin/hat-plugin-hook robustness fixes.
Run: python3 -m pytest bin/test_plugin_hook.py -x -q
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

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


def _write_plugin(plugins_dir, name, manifest, md_body):
    """Write a plugin as a single .md with JSON frontmatter (the migrated format):
    the manifest lives in a leading `---`-fenced block, the instruction body follows."""
    fm = json.dumps(manifest, ensure_ascii=False, indent=2)
    (plugins_dir / f"{name}.md").write_text(f"---\n{fm}\n---\n\n{md_body}", encoding="utf-8")


def _setup_plugin_env(tmp_path, hook_point="P1.phase-start"):
    """Create a minimal plugin environment for happy-path testing.

    Returns (task_folder, plugins_dir) where plugins_dir contains a
    test plugin whose .md carries the manifest in frontmatter.
    """
    task_folder = tmp_path / "task"
    task_folder.mkdir()

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

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
    md_body = "## Test Section\n\nThis is test instruction content.\n\nWith multiple lines.\n\n## Other Section\n\nShould not appear.\n"
    _write_plugin(plugins_dir, "testplugin", manifest, md_body)

    # task-config.json enabling the plugin
    config = {"plugins": {"testplugin": {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))

    return task_folder, plugins_dir


def _run_hook_with_plugins_dir(task_folder, hook_point, plugins_dir):
    """Run hat-plugin-hook with a custom PLUGINS_DIR (env override)."""
    env = {**os.environ, "PLUGINS_DIR": str(plugins_dir)}
    return subprocess.run(
        [str(HOOK_BIN), str(task_folder), hook_point],
        capture_output=True,
        text=True,
        env=env,
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
        _write_plugin(plugins_dir, name, manifest, f"## Hook\n\n{content}\n")

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


def test_happy_path_missing_section_graceful(tmp_path):
    """Frontmatter declares a hook section the body lacks: graceful skip, exit 0.

    Post-migration the manifest lives in the .md frontmatter, so 'manifest present
    but .md missing' is unrepresentable; the surviving graceful path is a declared
    section with no matching `## ` heading in the body.
    """
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
    # Body intentionally lacks the declared `## Hook` heading.
    _write_plugin(plugins_dir, "broken", manifest, "## Other\n\nUnrelated.\n")

    config = {"plugins": {"broken": {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))

    result = _run_hook_with_plugins_dir(task_folder, "P1.phase-start", plugins_dir)
    assert result.returncode == 0
    assert "not found" in result.stderr.lower()


# --- execution mode filtering tests ---


def _setup_execution_env(tmp_path, hooks, plugin_name="execplugin"):
    """Create a plugin env where `hooks` maps hook_point -> hook config.

    A hook config may be a single dict (object form) or a list of dicts
    (array form). The .md file gets one section per config's `section`
    title. Returns (task_folder, plugins_dir).
    """
    task_folder = tmp_path / "task"
    task_folder.mkdir()
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    manifest = {"name": plugin_name, "description": "test", "hooks": hooks}

    md_parts = []
    for value in hooks.values():
        configs = value if isinstance(value, list) else [value]
        for cfg in configs:
            title = cfg["section"]
            md_parts.append(f"{title}\n\nContent for {title}.\n")
    _write_plugin(plugins_dir, plugin_name, manifest, "\n".join(md_parts))

    config = {"plugins": {plugin_name: {"enabled": True}}}
    (task_folder / "task-config.json").write_text(json.dumps(config))
    return task_folder, plugins_dir


def _run_hook_copy(task_folder, plugins_dir, *args):
    """Run hat-plugin-hook with a PLUGINS_DIR env override and arbitrary args."""
    env = {**os.environ, "PLUGINS_DIR": str(plugins_dir)}
    return subprocess.run(
        [str(HOOK_BIN), str(task_folder)] + list(args),
        capture_output=True,
        text=True,
        env=env,
    )


def test_header_format_has_no_execution_field(tmp_path):
    """Comment header is `<!-- plugin:P hook:H on_error:E -->` — no execution field."""
    hooks = {
        "P1.phase-start": {
            "priority": 10,
            "section": "## Inline Hook",
            "on_error": "graceful",
        }
    }
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks)
    result = _run_hook_copy(task_folder, plugins_dir, "P1.phase-start")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "<!-- plugin:execplugin hook:P1.phase-start on_error:graceful -->" in result.stdout
    assert "execution:" not in result.stdout
    assert "Content for ## Inline Hook" in result.stdout


def test_stray_execution_field_is_ignored(tmp_path):
    """A leftover `execution` field is inert: body emitted inline, never a DISPATCH."""
    hooks = {
        "P2.phase-end": {
            "priority": 10,
            "section": "## Hook",
            "on_error": "graceful",
            "execution": "subagent:foo",
        }
    }
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks)
    result = _run_hook_copy(task_folder, plugins_dir, "P2.phase-end")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Content for ## Hook" in result.stdout
    assert "DISPATCH" not in result.stdout


def test_missing_priority_falls_back_to_zero(tmp_path):
    """A handler without `priority` sorts as 0 (no TypeError); replicates bash `// 0`."""
    hooks = {
        "P1.phase-start": [
            {"priority": 10, "section": "## A", "on_error": "graceful"},
            {"section": "## B", "on_error": "graceful"},
        ]
    }
    task_folder, plugins_dir = _setup_execution_env(tmp_path, hooks)
    result = _run_hook_copy(task_folder, plugins_dir, "P1.phase-start")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # B (no priority -> 0) sorts before A (10)
    assert result.stdout.index("## B") < result.stdout.index("## A")


def test_blocking_missing_section_exits_1(tmp_path):
    """on_error=blocking + section absent from .md body -> exit 1 with ERROR on stderr."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    task_folder = tmp_path / "task"
    task_folder.mkdir()
    manifest = {
        "name": "blk", "description": "test",
        "hooks": {"P6.pre-archive": {"priority": 10, "section": "## Absent",
                                     "on_error": "blocking"}},
    }
    _write_plugin(plugins_dir, "blk", manifest, "## Present\n\nbody.\n")
    (task_folder / "task-config.json").write_text(
        json.dumps({"plugins": {"blk": {"enabled": True}}}))
    result = _run_hook_copy(task_folder, plugins_dir, "P6.pre-archive")
    assert result.returncode == 1
    assert "ERROR" in result.stderr
    assert "Absent" in result.stderr


# --- Frontmatter schema: the migrated manifest lives in each plugin .md ---

_PLUGINS_DIR = Path(__file__).parent.parent / "skills" / "task" / "plugins"
_PLUGIN_NAMES = ("git", "linear", "retrospective", "review", "tdd")


def _read_frontmatter(md_path):
    """Extract + parse the leading `---`-fenced JSON block (mirrors the engine)."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    assert lines and lines[0].strip() == "---", f"{md_path.name}: no frontmatter"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return json.loads("\n".join(lines[1:i]))
    raise AssertionError(f"{md_path.name}: unterminated frontmatter")


def test_no_manifest_json_files_remain():
    """The migration removed every standalone .manifest.json."""
    assert list(_PLUGINS_DIR.glob("*.manifest.json")) == []


@pytest.mark.parametrize("name", _PLUGIN_NAMES)
def test_plugin_frontmatter_schema(name):
    """Each real plugin's frontmatter carries a well-typed manifest and no leftover
    subagents block (the subagent-async machinery was dropped in migration)."""
    fm = _read_frontmatter(_PLUGINS_DIR / f"{name}.md")

    assert fm.get("name") == name
    assert isinstance(fm.get("description"), str) and fm["description"]
    assert "subagents" not in fm, f"{name}: subagents block should have been dropped"
    for key in ("recommend_disable_when", "recommend_enable_when"):
        if key in fm:
            assert isinstance(fm[key], list)
            assert all(isinstance(x, str) for x in fm[key])

    hooks = fm.get("hooks")
    assert isinstance(hooks, dict) and hooks, f"{name}: missing hooks"
    for point, value in hooks.items():
        entries = value if isinstance(value, list) else [value]
        for entry in entries:
            assert isinstance(entry, dict), f"{name}/{point}: hook entry not a map"
            assert isinstance(entry.get("priority"), int), f"{name}/{point}: priority not int"
            assert isinstance(entry.get("section"), str) and entry["section"].startswith("## "), \
                f"{name}/{point}: section must be a '## ' heading"
            if "on_error" in entry:
                assert entry["on_error"] in ("graceful", "blocking")
            if "execution" in entry:
                assert isinstance(entry["execution"], str)


# --- Golden corpus: byte-identical regression vs the original bash engine ---

_ROOT = Path(__file__).parent.parent
_GOLDEN_DIR = Path(__file__).parent / "fixtures" / "plugin_hook_golden"
_ALL5 = ("git", "review", "linear", "tdd", "retrospective")


def _norm(text, task):
    return text.replace(str(_ROOT), "<ROOT>").replace(str(task), "<TASK>")


def _golden_cases():
    return sorted(p.stem for p in _GOLDEN_DIR.glob("*.json"))


@pytest.mark.parametrize("case", _golden_cases())
def test_golden_corpus_byte_identical(case, tmp_path):
    """Python 引擎对真实 5 插件全部 hook-point + 缺 config/frontmatter 用例，输出
    （returncode/stdout/stderr）与冻结 golden 逐字节一致。golden 初版由旧 bash 冻结、
    锁定引擎重写的路由/抽取/排序行为；后续插件正文的有意编辑同步重生（引擎行为不变）。"""
    golden = json.loads((_GOLDEN_DIR / f"{case}.json").read_text())

    task = tmp_path / "task"
    task.mkdir()
    if case == "_missing-config":
        args = [str(task), "P1.phase-start"]
    elif case == "_missing-manifest":
        (task / "task-config.json").write_text(
            json.dumps({"plugins": {"ghost": {"enabled": True}}}))
        args = [str(task), "P1.phase-start"]
    else:
        (task / "task-config.json").write_text(
            json.dumps({"plugins": {p: {"enabled": True} for p in _ALL5}}))
        args = [str(task), case]

    # 不继承外部 PLUGINS_DIR：让引擎自定位到真实 repo plugins（与 golden 生成时一致）
    env = {k: v for k, v in os.environ.items() if k != "PLUGINS_DIR"}
    env["LC_ALL"] = "C"
    r = subprocess.run([str(HOOK_BIN)] + args, capture_output=True, text=True, env=env)

    assert r.returncode == golden["returncode"], f"{case}: rc {r.returncode} != {golden['returncode']}"
    assert _norm(r.stdout, task) == golden["stdout"], f"{case}: stdout mismatch"
    assert _norm(r.stderr, task) == golden["stderr"], f"{case}: stderr mismatch"
