import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

# codex-quota 是 codex 可选 helper，靠 jq 解析 rollout 快照。核心任务流程不需要 jq；
# 无 jq 的干净环境（如 hat-flow 发布前 Docker 验证）下这些测试不适用，整体跳过。
pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None,
    reason="codex-quota 依赖 jq（codex 可选 helper）；无 jq 环境跳过",
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "codex-quota"
FIXTURES = ROOT / "bin" / "fixtures" / "codex"


def run_quota(tmp_path: Path, fixture: str) -> subprocess.CompletedProcess[str]:
    shutil.copy(FIXTURES / fixture, tmp_path / fixture)
    env = os.environ.copy()
    env["CODEX_SESSIONS_DIR"] = str(tmp_path)
    return subprocess.run(
        [str(SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_rollout_used(tmp_path: Path) -> None:
    result = run_quota(tmp_path, "rollout-used.jsonl")

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["h"]["used"] == 92
    assert data["reached"] is None
    assert data["credits"]["has_credits"] is False


def test_rollout_reached(tmp_path: Path) -> None:
    result = run_quota(tmp_path, "rollout-reached.jsonl")

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["reached"] == "primary"


def test_rollout_credit0(tmp_path: Path) -> None:
    result = run_quota(tmp_path, "rollout-credit0.jsonl")

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["credits"]["has_credits"] is True
    assert data["credits"]["balance"] == 0
    assert isinstance(data["credits"]["balance"], int)


def test_rollout_empty(tmp_path: Path) -> None:
    result = run_quota(tmp_path, "rollout-empty.jsonl")

    assert result.returncode == 1
    assert result.stdout == ""


def test_stale_when_snapshot_is_older_than_six_hours(tmp_path: Path) -> None:
    target = tmp_path / "rollout-used.jsonl"
    shutil.copy(FIXTURES / "rollout-used.jsonl", target)
    seven_hours_ago = time.time() - (7 * 60 * 60)
    os.utime(target, (seven_hours_ago, seven_hours_ago))

    env = os.environ.copy()
    env["CODEX_SESSIONS_DIR"] = str(tmp_path)
    result = subprocess.run(
        [str(SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["stale"] is True
