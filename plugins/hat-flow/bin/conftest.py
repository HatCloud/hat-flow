"""
Shared pytest fixtures for bin/ tests.
"""
import os
import subprocess

import pytest


@pytest.fixture(scope="session", autouse=True)
def _scrub_git_env():
    """移除测试进程的 GIT_*，保证从 git hook（pre-commit）跑 pytest 时，
    父 git 进程的 GIT_DIR/GIT_INDEX_FILE 不泄漏进子进程——否则 shell 到 git 的
    脚本会操作真实 repo 而非 tmp 隔离仓库，破坏空项目 fallback / git log 等断言。"""
    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("GIT_")}
    yield
    os.environ.update(saved)


@pytest.fixture
def tmp_git_repo(tmp_path):
    """创建隔离的临时 git 仓库，不影响真实 git 历史"""
    repo = tmp_path / "repo"
    repo.mkdir()

    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["HOME"] = str(tmp_path)  # 避免读取用户 ~/.gitconfig

    subprocess.run(
        ["git", "init", str(repo)],
        env=env,
        capture_output=True,
        check=True,
    )
    # 在 commit 前设置 user identity，确保 commit 不因缺少 user 而失败
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test"],
        env=env,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@test.com"],
        env=env,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-m",
            "initial",
        ],
        env=env,
        capture_output=True,
        check=True,
    )

    return repo, env
