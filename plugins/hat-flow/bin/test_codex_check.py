import os
import stat
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_CHECK = REPO_ROOT / "bin" / "codex-check"


def write_executable(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def make_fake_home(tmp_path: Path) -> Path:
    fake_home = tmp_path / "home"
    plugin = (
        fake_home
        / ".claude"
        / "plugins"
        / "marketplaces"
        / "openai-codex"
        / "plugins"
        / "codex"
        / "scripts"
    )
    plugin.mkdir(parents=True)
    (plugin / "codex-companion.mjs").write_text("// fake\n", encoding="utf-8")
    return fake_home


def make_fake_node(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_executable(
        bin_dir / "node",
        """\
        #!/usr/bin/env bash
        printf '%s\n' '{"ready":true,"auth":{"loggedIn":true}}'
        """,
    )
    return bin_dir


def make_quota(tmp_path: Path, body: str, exit_code: int = 0) -> Path:
    quota = tmp_path / "codex-quota"
    if exit_code == 0:
        content = f"""\
        #!/usr/bin/env bash
        printf '%s\\n' '{body}'
        """
    else:
        content = f"""\
        #!/usr/bin/env bash
        exit {exit_code}
        """
    return write_executable(quota, content)


def run_codex_check(tmp_path: Path, quota: Path, *args: str) -> subprocess.CompletedProcess:
    fake_home = make_fake_home(tmp_path)
    bin_dir = make_fake_node(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(fake_home),
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "CODEX_QUOTA_BIN": str(quota),
        }
    )
    return subprocess.run(
        [str(CODEX_CHECK), *args],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_quota_healthy_keeps_stdout_ready(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":20},"reached":null,"credits":{"has_credits":false},"stale":false}',
    )

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 0
    assert result.stdout == "READY\n"


def test_hourly_usage_over_threshold_falls_back(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":92},"reached":null,"credits":{"has_credits":false},"stale":false}',
    )

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 1
    assert result.stdout.startswith("FALLBACK:")


def test_reached_primary_falls_back(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":20},"reached":"primary","credits":{"has_credits":false},"stale":false}',
    )

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 1
    assert result.stdout.startswith("FALLBACK:")


def test_zero_credit_balance_falls_back(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":20},"reached":null,"credits":{"has_credits":true,"balance":0},"stale":false}',
    )

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 1
    assert result.stdout.startswith("FALLBACK:")


def test_quota_unknown_warns_on_stderr_and_allows_ready(tmp_path: Path) -> None:
    quota = make_quota(tmp_path, "", exit_code=1)

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 0
    assert result.stdout == "READY\n"
    assert result.stdout.strip() == "READY"
    assert "quota unknown" in result.stderr
    assert "quota unknown" not in result.stdout


def test_no_quota_skips_quota_gate(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":99},"reached":"primary","credits":{"has_credits":true,"balance":0},"stale":false}',
    )

    result = run_codex_check(tmp_path, quota, "--no-quota")

    assert result.returncode == 0
    assert result.stdout == "READY\n"


def test_stale_quota_warns_on_stderr_and_allows_ready(tmp_path: Path) -> None:
    quota = make_quota(
        tmp_path,
        '{"h":{"used":20},"reached":null,"credits":{"has_credits":false},"stale":true}',
    )

    result = run_codex_check(tmp_path, quota)

    assert result.returncode == 0
    assert result.stdout == "READY\n"
    assert result.stdout.strip() == "READY"
    assert "stale" in result.stderr
    assert "stale" not in result.stdout
