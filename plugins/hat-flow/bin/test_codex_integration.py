"""ISSUE codex 接入集成/规格测试。

注意范围（reviewer R1-I2 / R2-I3）：dirty-state 矩阵①-⑥、resume 三选项、engine 解析漏斗
（`resolve_engine` / `pause_dirty_conflict` / `resume_resolution` / `cwd_eligible` 等 helper）是
**协议算法的可执行规格（spec-by-example）**——dirty-state 协议的 owner 是 task-execute SKILL.md
的 prose（无独立 production 脚本），故这些断言验证的是「协议算法本身安全/自洽」（如能抓住「全局
git clean」这类危险规定），**不是对某个 bin 脚本调用链的回归**。真正调被测脚本的是 FALLBACK E2E
的 `codex-quota` 与 cwd-sandbox 三组的 `git rev-parse`。未来若抽出 `bin/codex-dirty-state` 脚本，
可把这些 helper 换成对该脚本的真实调用。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_QUOTA = ROOT / "bin" / "codex-quota"


def _hermetic_env() -> dict[str, str]:
    """剥离所有 GIT_* 环境变量，使临时 repo 操作 hermetic。

    在 pre-commit hook 中跑 pytest 时，外层 `git commit` 已导出
    GIT_DIR / GIT_INDEX_FILE / GIT_WORK_TREE 等——子进程 git 会继承并指向
    主仓库，破坏 tmp_path 临时 repo 的 worktree/index 操作。
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=_hermetic_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = run(["git", "-C", str(repo), *args])
    assert result.returncode == 0, result.stderr
    return result


def git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=_hermetic_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    result = run(["git", "-c", "init.defaultBranch=main", "init", str(path)])
    assert result.returncode == 0, result.stderr
    git(path, "config", "user.email", "codex@example.test")
    git(path, "config", "user.name", "Codex Test")
    return path


def commit_file(repo: Path, rel: str, content: str = "initial\n") -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", rel)
    git(repo, "commit", "-m", f"add {rel}")
    return path


def artifact_path(artifact_dir: Path, rel: str) -> Path:
    return artifact_dir / rel.replace("/", "__")


def copy_artifact(repo: Path, artifact_dir: Path, rel: str) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    dest = artifact_path(artifact_dir, rel)
    shutil.copy2(repo / rel, dest)
    return dest


def baseline(repo: Path, artifact_dir: Path) -> dict[str, object]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    tracked = git(repo, "rev-parse", "HEAD").stdout.strip()
    status = git_bytes(repo, "status", "--porcelain=v1", "-z")
    ignored_status = git_bytes(repo, "status", "--ignored", "--porcelain=v1", "-z")
    diff = git_bytes(repo, "diff", "--binary")
    snapshot = {
        "head": tracked,
        "status": status,
        "ignored_status": ignored_status,
        "diff": diff,
        "artifacts": {},
    }

    for entry in status.split(b"\0"):
        if not entry:
            continue
        text = entry.decode()
        rel = text[3:]
        if (repo / rel).is_file():
            copied = copy_artifact(repo, artifact_dir, rel)
            snapshot["artifacts"][rel] = copied

    for entry in ignored_status.split(b"\0"):
        if not entry:
            continue
        text = entry.decode()
        if text.startswith("!! "):
            rel = text[3:]
            copied = copy_artifact(repo, artifact_dir, rel)
            snapshot["artifacts"][rel] = copied

    return snapshot


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_log(path: Path, **record: object) -> None:
    required = {
        "phase": "P4-4a",
        "integration_point": "codex-task-workflow",
        "requested_engine": "codex",
        "actual_engine": "claude",
        "reason": "dirty-state conflict",
    }
    required.update(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(required, separators=(",", ":")) + "\n")


def read_log(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def clean_status(repo: Path) -> str:
    return git(repo, "status", "--porcelain=v1").stdout


def resolve_engine(
    reviewer_or_engine: str, codex_check_stdout: str, codex_check_rc: int
) -> str:
    if reviewer_or_engine in {"claude", "sonnet", "opus"}:
        return reviewer_or_engine
    fallback = codex_check_rc != 0 or codex_check_stdout.startswith("FALLBACK:")
    if reviewer_or_engine in {"auto", "codex"} and fallback:
        return "claude"
    if reviewer_or_engine == "auto" and codex_check_rc == 0 and codex_check_stdout == "READY":
        return "codex"
    return reviewer_or_engine


def pause_dirty_conflict(
    repo: Path,
    artifact_dir: Path,
    log_path: Path,
    rel: str,
    unattended: bool = False,
) -> bool:
    if not artifact_path(artifact_dir, rel).exists():
        copy_artifact(repo, artifact_dir, rel)
    write_log(
        log_path,
        action="paused_dirty_conflict" if unattended else "ask_user_question",
    )
    return False


def resume_resolution(
    env: dict[str, str],
    repo: Path,
    baseline_snapshot: dict[str, object],
    log_path: Path,
) -> tuple[str, bool]:
    choice = env["TASK_RESUME_CHOICE"]
    if choice == "keep":
        write_log(log_path, action="resume", resolution="keep")
        return "keep", True
    if choice == "rollback":
        for rel, source in baseline_snapshot["artifacts"].items():
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        write_log(log_path, action="resume", resolution="rollback")
        return "rollback", True
    if choice == "cancel":
        write_log(log_path, action="resume", resolution="cancel")
        return "cancel", False
    raise ValueError(choice)


def git_root(path: Path) -> Path:
    cwd = path if path.is_dir() else path.parent
    result = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"])
    assert result.returncode == 0, result.stderr
    return Path(result.stdout.strip()).resolve()


def cwd_eligible(launch_cwd: Path, target_path: Path) -> bool:
    return git_root(launch_cwd) == git_root(target_path)


def test_fallback_e2e_quota_empty_and_engine_funnel(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    env = os.environ.copy()
    env["CODEX_SESSIONS_DIR"] = str(sessions)

    result = subprocess.run(
        [str(CODEX_QUOTA)],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert resolve_engine("auto", "FALLBACK: Codex plugin not found", 1) == "claude"
    assert resolve_engine("auto", "FALLBACK: quota low", 1) == "claude"
    assert resolve_engine("auto", "READY", 0) == "codex"
    assert resolve_engine("codex", "FALLBACK: quota low", 1) == "claude"
    assert resolve_engine("claude", "FALLBACK: quota low", 1) == "claude"
    assert resolve_engine("sonnet", "READY", 0) == "sonnet"
    assert resolve_engine("opus", "READY", 0) == "opus"


def test_dirty_state_disjoint_path_reverses_only_codex_change(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    target = commit_file(repo, "tracked.txt", "pre\n")
    artifact_dir = tmp_path / "artifacts"
    baseline(repo, artifact_dir)

    target.write_text("codex\n", encoding="utf-8")
    git(repo, "checkout", "--", "tracked.txt")

    assert target.read_text(encoding="utf-8") == "pre\n"
    assert clean_status(repo) == ""


def test_dirty_state_same_path_hunk_pauses_without_reverse(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    target = commit_file(repo, "tracked.txt", "base\n")
    target.write_text("pre-dirty\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    before = baseline(repo, artifact_dir)
    artifact_hash = sha256(before["artifacts"]["tracked.txt"])

    target.write_text("pre-dirty\ncodex\n", encoding="utf-8")
    continued = pause_dirty_conflict(repo, artifact_dir, tmp_path / "fallback-log.jsonl", "tracked.txt")

    assert continued is False
    assert target.read_text(encoding="utf-8") == "pre-dirty\ncodex\n"
    assert sha256(before["artifacts"]["tracked.txt"]) == artifact_hash
    assert read_log(tmp_path / "fallback-log.jsonl")[0]["action"] == "ask_user_question"


def test_dirty_state_pre_existing_untracked_same_path_pauses(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    commit_file(repo, "tracked.txt")
    rel = "new.txt"
    (repo / rel).write_text("pre-untracked\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    before = baseline(repo, artifact_dir)
    artifact_hash = sha256(before["artifacts"][rel])

    (repo / rel).write_text("pre-untracked\ncodex\n", encoding="utf-8")
    continued = pause_dirty_conflict(repo, artifact_dir, tmp_path / "fallback-log.jsonl", rel)

    assert continued is False
    assert (repo / rel).read_text(encoding="utf-8") == "pre-untracked\ncodex\n"
    assert sha256(before["artifacts"][rel]) == artifact_hash
    assert read_log(tmp_path / "fallback-log.jsonl")[0]["action"] == "ask_user_question"


def test_dirty_state_codex_created_untracked_removes_single_file_only(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    commit_file(repo, "tracked.txt")
    unrelated = repo / "pre-existing.txt"
    unrelated.write_text("keep me\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    baseline(repo, artifact_dir)

    created = repo / "codex-created.txt"
    created.write_text("new content\n", encoding="utf-8")
    copied = copy_artifact(repo, artifact_dir, "codex-created.txt")
    os.remove(created)

    assert copied.read_text(encoding="utf-8") == "new content\n"
    assert not created.exists()
    assert unrelated.read_text(encoding="utf-8") == "keep me\n"
    assert "pre-existing.txt" in clean_status(repo)
    assert "codex-created.txt" not in clean_status(repo)


def test_dirty_state_gitignored_path_snapshots_and_escalates(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    commit_file(repo, ".gitignore", "*.cache\n")
    ignored = repo / "result.cache"
    ignored.write_text("ignored codex output\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    before = baseline(repo, artifact_dir)
    log_path = tmp_path / "fallback-log.jsonl"
    write_log(log_path, action="ask_user_question")

    ignored_status = before["ignored_status"].decode()
    assert "!! result.cache" in ignored_status
    assert before["artifacts"]["result.cache"].read_text(encoding="utf-8") == "ignored codex output\n"
    assert ignored.exists()
    assert read_log(log_path)[0]["action"] == "ask_user_question"


def test_dirty_state_unattended_hard_stop(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    target = commit_file(repo, "tracked.txt", "base\n")
    target.write_text("pre-dirty\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts"
    before = baseline(repo, artifact_dir)
    target.write_text("pre-dirty\ncodex\n", encoding="utf-8")

    continued = pause_dirty_conflict(
        repo,
        artifact_dir,
        tmp_path / "fallback-log.jsonl",
        "tracked.txt",
        unattended=True,
    )

    log = read_log(tmp_path / "fallback-log.jsonl")[0]
    assert log["action"] == "paused_dirty_conflict"
    assert before["artifacts"]["tracked.txt"].exists()
    assert continued is False


def test_resume_choice_keep_continues_executor(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    target = commit_file(repo, "tracked.txt", "base\n")
    target.write_text("pre-dirty\n", encoding="utf-8")
    before = baseline(repo, tmp_path / "artifacts")

    resolution, continued = resume_resolution(
        {"TASK_RESUME_CHOICE": "keep"},
        repo,
        before,
        tmp_path / "fallback-log.jsonl",
    )

    assert (resolution, continued) == ("keep", True)
    assert target.read_text(encoding="utf-8") == "pre-dirty\n"
    assert read_log(tmp_path / "fallback-log.jsonl")[0]["resolution"] == "keep"


def test_resume_choice_rollback_restores_baseline_and_continues(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    target = commit_file(repo, "tracked.txt", "base\n")
    target.write_text("pre-dirty\n", encoding="utf-8")
    before = baseline(repo, tmp_path / "artifacts")
    target.write_text("pre-dirty\ncodex\n", encoding="utf-8")

    resolution, continued = resume_resolution(
        {"TASK_RESUME_CHOICE": "rollback"},
        repo,
        before,
        tmp_path / "fallback-log.jsonl",
    )

    assert (resolution, continued) == ("rollback", True)
    assert target.read_text(encoding="utf-8") == "pre-dirty\n"
    assert read_log(tmp_path / "fallback-log.jsonl")[0]["resolution"] == "rollback"


def test_resume_choice_cancel_stops_executor(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    commit_file(repo, "tracked.txt", "base\n")
    before = baseline(repo, tmp_path / "artifacts")

    resolution, continued = resume_resolution(
        {"TASK_RESUME_CHOICE": "cancel"},
        repo,
        before,
        tmp_path / "fallback-log.jsonl",
    )

    assert (resolution, continued) == ("cancel", False)
    assert read_log(tmp_path / "fallback-log.jsonl")[0]["resolution"] == "cancel"


def test_fallback_log_jsonl_required_fields(tmp_path: Path) -> None:
    log_path = tmp_path / "fallback-log.jsonl"
    write_log(
        log_path,
        phase="P3",
        integration_point="engine-resolution",
        requested_engine="codex",
        actual_engine="claude",
        reason="FALLBACK: Codex plugin not found",
        action="ask_user_question",
        resolution="keep",
    )

    record = read_log(log_path)[0]
    assert set(record) >= {
        "phase",
        "integration_point",
        "requested_engine",
        "actual_engine",
        "reason",
        "action",
        "resolution",
    }
    assert record["phase"] in {"P2", "P3", "P4-4a"}


def test_cwd_sandbox_outer_cwd_target_inner_hard_fallback(tmp_path: Path) -> None:
    outer = init_repo(tmp_path / "outer")
    commit_file(outer, "outer.txt")
    inner = init_repo(outer / "inner")
    commit_file(inner, "inner.txt")

    assert git_root(outer) == outer.resolve()
    assert git_root(inner) == inner.resolve()
    assert cwd_eligible(outer, inner / "inner.txt") is False


def test_cwd_sandbox_inner_cwd_target_inner_is_verified(tmp_path: Path) -> None:
    outer = init_repo(tmp_path / "outer")
    commit_file(outer, "outer.txt")
    inner = init_repo(outer / "inner")
    commit_file(inner, "inner.txt")

    assert cwd_eligible(inner, inner / "inner.txt") is True


def test_cwd_sandbox_worktree_resolves_to_worktree_root(tmp_path: Path) -> None:
    main = init_repo(tmp_path / "main")
    commit_file(main, "tracked.txt")
    worktree = tmp_path / "linked-worktree"
    git(main, "worktree", "add", str(worktree))

    assert git_root(worktree) == worktree.resolve()
    assert git_root(worktree) != main.resolve()
