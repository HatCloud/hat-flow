#!/usr/bin/env python3
"""
测试 hat-task-scaffold 空路径检查。
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), "hat-task-scaffold")


def run(args, *, input=None):
    """运行脚本，返回 (returncode, stdout, stderr)。"""
    cmd = [sys.executable, SCRIPT] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input,
    )
    return result.returncode, result.stdout, result.stderr


def test_no_args():
    """不传参数时 exit code == 1。"""
    code, _, stderr = run([])
    assert code == 1, f"Expected exit code 1, got {code}"
    parsed = json.loads(stderr)
    assert "error" in parsed


def test_empty_path():
    """空字符串路径 exit code == 1，stderr 是 JSON 格式（非 traceback）。"""
    code, _, stderr = run([""])
    assert code == 1, f"Expected exit code 1, got {code}"
    parsed = json.loads(stderr)  # 若是 traceback 则此处抛出 JSONDecodeError
    assert "error" in parsed


def test_whitespace_path():
    """纯空白字符串路径 exit code == 1，stderr 是 JSON 格式。"""
    code, _, stderr = run(["   "])
    assert code == 1, f"Expected exit code 1, got {code}"
    parsed = json.loads(stderr)
    assert "error" in parsed


def test_normal_create():
    """正常路径 exit code == 0，目录已创建。"""
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "test-task")
        code, stdout, _ = run([target])
        assert code == 0, f"Expected exit code 0, got {code}"
        assert os.path.isdir(target), f"Directory not created: {target}"
        result = json.loads(stdout)
        assert result["path"] == target
        assert result["created"] is True


def test_with_linear_json():
    """传入 --linear JSON 时，exit code == 0，linear.json 存在且内容正确。"""
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "test-task2")
        linear_data = {"issueId": "TEST-1"}
        code, stdout, _ = run([target, "--linear", json.dumps(linear_data)])
        assert code == 0, f"Expected exit code 0, got {code}"
        linear_path = os.path.join(target, "linear.json")
        assert os.path.isfile(linear_path), "linear.json not found"
        with open(linear_path, encoding="utf-8") as f:
            written = json.load(f)
        assert written == linear_data, f"Unexpected content: {written}"
        result = json.loads(stdout)
        assert result["linearWritten"] is True
