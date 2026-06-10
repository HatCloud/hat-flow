"""
Characterization tests for bin/hat-git-conventions.

Run with:  python3 -m pytest bin/test_hat_git_conventions.py -x -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "hat-git-conventions"


def run_conv(project_root):
    """Run hat-git-conventions on project_root, return parsed JSON dict."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(project_root)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"non-zero exit; stderr: {result.stderr}"
    return json.loads(result.stdout)


def _git(repo, env, *args):
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_repo(tmp_path):
    """隔离临时 git 仓库（不含初始 commit，便于测试自行造 commit 历史）。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["HOME"] = str(tmp_path)
    subprocess.run(["git", "init", str(repo)], env=env, capture_output=True, check=True)
    _git(repo, env, "config", "user.name", "Test")
    _git(repo, env, "config", "user.email", "test@test.com")
    return repo, env


def _commit(repo, env, message):
    _git(repo, env, "commit", "--allow-empty", "-m", message)


# ---------------------------------------------------------------------------
# 1. fallback：空项目（非 git、无 CLAUDE.md）→ found=false，exit 0，结构完整
# ---------------------------------------------------------------------------
def test_empty_project_fallback(tmp_path):
    data = run_conv(tmp_path)
    assert data["found"] is False
    assert data["source"] is None
    assert data["format"] is None
    assert data["claudeMdSection"] is None
    assert data["implicitPatterns"] == []
    assert data["recentCommits"] == []
    assert data["hasCommitlint"] is False
    assert data["hasHusky"] is False
    # formatting 子结构始终存在
    assert data["formatting"]["hookManaged"] is False
    assert data["formatting"]["formatter"] is None


# ---------------------------------------------------------------------------
# 2. CLAUDE.md 解析：含 git 规范 + 格式模板 → found, source=CLAUDE.md, format 提取
# ---------------------------------------------------------------------------
def test_claude_md_section_and_format(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "# Project\n\n"
        "## Git 规范\n\n"
        "遵循 Conventional Commits，格式为 `<type>(<scope>): <description>`。\n\n"
        "## 其他\n\n无关内容\n",
        encoding="utf-8",
    )
    data = run_conv(tmp_path)
    assert data["found"] is True
    assert data["source"] == "CLAUDE.md"
    # detect_format_from_section 的正则 `<type>.*?<\w+>` 为非贪婪，
    # 仅截取到第一个闭合尖括号标签 → `<type>(<scope>`（characterization：记录现有行为）
    assert data["format"] == "<type>(<scope>"
    assert "Git 规范" in data["claudeMdSection"]
    # 段落提取应止于下一个 ## 标题，不含「## 其他」正文
    assert "无关内容" not in data["claudeMdSection"]


# ---------------------------------------------------------------------------
# 3. CLAUDE.md 仅含分支策略（无格式规则）→ 不误判为 found
# ---------------------------------------------------------------------------
def test_claude_md_section_without_format_rules(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "## Git 规范\n\n所有功能在 feature 分支开发，合并到 main。\n",
        encoding="utf-8",
    )
    data = run_conv(tmp_path)
    # 段落不含 format/前缀/<type> 关键词 → find_claude_md_section 返回 None
    assert data["claudeMdSection"] is None
    assert data["source"] != "CLAUDE.md"


# ---------------------------------------------------------------------------
# 4. implicitPatterns：git 历史多条 feat:/fix: → 推断隐含前缀（出现 ≥2 次）
# ---------------------------------------------------------------------------
def test_implicit_patterns_from_git_log(git_repo):
    repo, env = git_repo
    _commit(repo, env, "feat(audio): add BGM")
    _commit(repo, env, "feat: second feature")
    _commit(repo, env, "fix: bug one")
    _commit(repo, env, "fix(ui): bug two")
    _commit(repo, env, "chore: one-off")  # 仅 1 次，不应进入 implicit
    data = run_conv(repo)
    assert data["found"] is True
    assert data["source"] == "implicit (git log)"
    assert "feat:" in data["implicitPatterns"]
    assert "fix:" in data["implicitPatterns"]
    assert "chore:" not in data["implicitPatterns"]
    assert len(data["recentCommits"]) <= 5
    # CLAUDE.md 优先级高于 implicit；此处无 CLAUDE.md，format 取首个 implicit 前缀
    assert data["format"] == data["implicitPatterns"][0]


# ---------------------------------------------------------------------------
# 5. commitlint 检测：存在配置文件 → hasCommitlint，且作为 source 兜底
# ---------------------------------------------------------------------------
def test_commitlint_detection(tmp_path):
    (tmp_path / ".commitlintrc.json").write_text("{}", encoding="utf-8")
    data = run_conv(tmp_path)
    assert data["hasCommitlint"] is True
    assert data["found"] is True
    assert data["source"] == ".commitlintrc.json"


# ---------------------------------------------------------------------------
# 6. formatting 检测：prettier 配置 → formatter=prettier + 默认命令
# ---------------------------------------------------------------------------
def test_formatting_prettier_detection(tmp_path):
    (tmp_path / ".prettierrc.json").write_text("{}", encoding="utf-8")
    data = run_conv(tmp_path)
    fmt = data["formatting"]
    assert fmt["formatter"] == "prettier"
    assert ".prettierrc.json" in fmt["configFiles"]
    assert fmt["formatCommand"] is not None  # 无 script 时给默认命令


# ---------------------------------------------------------------------------
# 7. husky commit-msg hook 检测
# ---------------------------------------------------------------------------
def test_husky_commit_msg_detection(tmp_path):
    husky = tmp_path / ".husky"
    husky.mkdir()
    (husky / "commit-msg").write_text("#!/bin/sh\nnpx commitlint --edit\n", encoding="utf-8")
    data = run_conv(tmp_path)
    assert data["hasHusky"] is True
