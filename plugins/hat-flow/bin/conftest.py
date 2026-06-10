"""
Shared pytest fixtures for bin/ tests.
"""
import os
import subprocess

import pytest


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
