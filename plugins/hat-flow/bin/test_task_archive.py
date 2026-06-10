"""
Characterization tests for bin/hat-task-archive.

Run with:  python3 -m pytest bin/test_task_archive.py -x -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ARCHIVE_SCRIPT = Path(__file__).parent / "hat-task-archive"
SCAFFOLD_SCRIPT = Path(__file__).parent / "hat-task-scaffold"
DETECT_SCRIPT = Path(__file__).parent / "hat-task-detect"


def _git_env(env):
    """Extend env with git identity vars to avoid GPG/user issues."""
    extra = {
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@test.com",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@test.com",
        # Disable GPG signing via env — hat-task-archive calls git commit
        # without -c commit.gpgsign=false, so we rely on GIT_CONFIG_NOSYSTEM
        # + isolated HOME (already set by tmp_git_repo) to prevent signing.
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    merged = dict(env)
    merged.update(extra)
    return merged


def run_archive(args, *, cwd, env):
    """Run hat-task-archive and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(ARCHIVE_SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


def run_scaffold(task_dir_path):
    """Run hat-task-scaffold and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), str(task_dir_path)],
        capture_output=True,
        text=True,
    )


def run_detect(base_path):
    """Run hat-task-detect and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(DETECT_SCRIPT), str(base_path)],
        capture_output=True,
        text=True,
    )


def git_add_commit(repo_path, env, paths, message="add task files"):
    """Helper: git add given paths and commit in the repo."""
    for p in paths:
        subprocess.run(
            ["git", "add", str(p)],
            cwd=str(repo_path),
            env=env,
            check=True,
            capture_output=True,
        )
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            message,
        ],
        cwd=str(repo_path),
        env=env,
        check=True,
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# 1. test_archive_done
# ---------------------------------------------------------------------------
def test_archive_done(tmp_git_repo):
    """Archive an open task to done/ → exit 0, JSON archived=true, dir exists."""
    repo_path, base_env = tmp_git_repo
    env = _git_env(base_env)

    # Create the task folder and a minimal phases.md
    task_name = "2026-01-01-test"
    task_dir = repo_path / ".tasks" / "open" / task_name
    task_dir.mkdir(parents=True)
    (task_dir / "phases.md").write_text("# Task Progress\n**Task**: 2026-01-01-test\n")

    # Commit the new task folder so git knows about it
    git_add_commit(repo_path, env, [task_dir], "add test task")

    # Run archive
    result = run_archive([task_name, "done"], cwd=repo_path, env=env)

    assert result.returncode == 0, (
        f"Expected exit 0.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    data = json.loads(result.stdout)
    assert data["archived"] is True, f"Expected archived=true: {data}"

    done_dir = repo_path / ".tasks" / "done" / task_name
    assert done_dir.is_dir(), f"Expected done dir to exist: {done_dir}"


# ---------------------------------------------------------------------------
# 2. test_archive_source_not_found
# ---------------------------------------------------------------------------
def test_archive_source_not_found(tmp_git_repo):
    """Archiving a nonexistent task → exit 1, stderr contains error."""
    repo_path, base_env = tmp_git_repo
    env = _git_env(base_env)

    result = run_archive(["nonexistent", "done"], cwd=repo_path, env=env)

    assert result.returncode == 1, (
        f"Expected exit 1.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stderr.strip(), "Expected non-empty stderr with error message"
    # stderr should be valid JSON with an error key
    err_data = json.loads(result.stderr)
    assert "error" in err_data, f"Expected 'error' key in stderr JSON: {err_data}"


# ---------------------------------------------------------------------------
# 3. test_archive_invalid_destination
# ---------------------------------------------------------------------------
def test_archive_invalid_destination(tmp_git_repo):
    """Passing an invalid destination → exit 1, stderr contains error."""
    repo_path, base_env = tmp_git_repo
    env = _git_env(base_env)

    # Create the task folder so source-not-found doesn't fire first
    task_name = "2026-01-01-test"
    task_dir = repo_path / ".tasks" / "open" / task_name
    task_dir.mkdir(parents=True)
    (task_dir / "phases.md").write_text("# Task Progress\n")

    result = run_archive([task_name, "invalid_dest"], cwd=repo_path, env=env)

    assert result.returncode == 1, (
        f"Expected exit 1.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stderr.strip(), "Expected non-empty stderr with error message"
    err_data = json.loads(result.stderr)
    assert "error" in err_data, f"Expected 'error' key in stderr JSON: {err_data}"


# ---------------------------------------------------------------------------
# 4. test_archive_destination_exists
# ---------------------------------------------------------------------------
def test_archive_destination_exists(tmp_git_repo):
    """Archive when destination already exists → exit 1, stderr contains 'exists'."""
    repo_path, base_env = tmp_git_repo
    env = _git_env(base_env)

    task_name = "2026-01-01-test"
    # Create the source task
    task_dir = repo_path / ".tasks" / "open" / task_name
    task_dir.mkdir(parents=True)
    (task_dir / "phases.md").write_text("# Task Progress\n")

    # Pre-create the done destination to trigger the conflict
    done_dir = repo_path / ".tasks" / "done" / task_name
    done_dir.mkdir(parents=True)

    result = run_archive([task_name, "done"], cwd=repo_path, env=env)

    assert result.returncode == 1, (
        f"Expected exit 1.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert result.stderr.strip(), "Expected non-empty stderr with error message"
    err_data = json.loads(result.stderr)
    assert "error" in err_data, f"Expected 'error' key in stderr JSON: {err_data}"
    # The error message should mention "exists"
    assert "exists" in err_data["error"].lower(), (
        f"Expected 'exists' in error message: {err_data['error']}"
    )


# ---------------------------------------------------------------------------
# 5. test_lifecycle
# ---------------------------------------------------------------------------
def test_lifecycle(tmp_git_repo):
    """
    Full lifecycle: scaffold → detect → archive → detect.

    Verifies that:
    - scaffold creates the task folder
    - detect shows it in open[]
    - archive moves it to done/ and commits
    - detect then shows open[] empty and done[] contains the task
    """
    repo_path, base_env = tmp_git_repo
    env = _git_env(base_env)

    task_name = "2026-01-01-lifecycle"
    task_dir = repo_path / ".tasks" / "open" / task_name

    # --- Step 1: scaffold ---
    scaffold_result = run_scaffold(str(task_dir))
    assert scaffold_result.returncode == 0, (
        f"scaffold failed.\nstdout: {scaffold_result.stdout}\nstderr: {scaffold_result.stderr}"
    )
    scaffold_data = json.loads(scaffold_result.stdout)
    assert scaffold_data["created"] is True
    assert task_dir.is_dir(), f"Scaffold did not create directory: {task_dir}"

    # --- Step 2: detect (should see 1 open task) ---
    tasks_base = repo_path / ".tasks"
    detect_result = run_detect(str(tasks_base))
    assert detect_result.returncode == 0, (
        f"detect failed.\nstdout: {detect_result.stdout}\nstderr: {detect_result.stderr}"
    )
    detect_data = json.loads(detect_result.stdout)
    open_names = [t["name"] for t in detect_data["open"]]
    assert task_name in open_names, (
        f"Expected {task_name!r} in open tasks: {open_names}"
    )

    # --- Step 3: commit the scaffolded folder so archive can git-move it ---
    # git cannot track empty directories, so write a minimal phases.md first
    (task_dir / "phases.md").write_text(
        f"# Task Progress\n**Task**: {task_name}\n"
    )
    git_add_commit(repo_path, env, [task_dir], "add lifecycle task")

    # --- Step 4: archive → done ---
    archive_result = run_archive([task_name, "done"], cwd=repo_path, env=env)
    assert archive_result.returncode == 0, (
        f"archive failed.\nstdout: {archive_result.stdout}\nstderr: {archive_result.stderr}"
    )
    archive_data = json.loads(archive_result.stdout)
    assert archive_data["archived"] is True, f"Expected archived=true: {archive_data}"

    done_dir = repo_path / ".tasks" / "done" / task_name
    assert done_dir.is_dir(), f"Expected done dir to exist: {done_dir}"

    # --- Step 5: detect again (open should be empty, done should contain task) ---
    detect_result2 = run_detect(str(tasks_base))
    assert detect_result2.returncode == 0, (
        f"detect (2nd) failed.\nstdout: {detect_result2.stdout}\nstderr: {detect_result2.stderr}"
    )
    detect_data2 = json.loads(detect_result2.stdout)

    open_names2 = [t["name"] for t in detect_data2["open"]]
    assert open_names2 == [], (
        f"Expected open[] to be empty after archive, got: {open_names2}"
    )
    assert task_name in detect_data2["done"], (
        f"Expected {task_name!r} in done[]: {detect_data2['done']}"
    )
