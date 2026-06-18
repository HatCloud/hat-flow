import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("codex-findings-count")


def run_counter(text):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def parsed_output(result):
    return json.loads(result.stdout)


def test_summary_counts_converged_with_minor_findings():
    result = run_counter("...\nCritical=0 Important=0 Minor=2")
    assert result.returncode == 0
    assert parsed_output(result) == {
        "critical": 0,
        "important": 0,
        "minor": 2,
        "converged": True,
    }


def test_summary_important_blocks_convergence():
    result = run_counter("Critical=0 Important=1 Minor=0")
    assert result.returncode == 0
    data = parsed_output(result)
    assert (data["critical"], data["important"], data["minor"]) == (0, 1, 0)
    assert data["converged"] is False


def test_summary_critical_and_important_block_convergence():
    result = run_counter("Critical=3 Important=2 Minor=5")
    assert result.returncode == 0
    data = parsed_output(result)
    assert (data["critical"], data["important"], data["minor"]) == (3, 2, 5)
    assert data["converged"] is False


def test_section_counts_when_summary_missing():
    text = "## Critical\n- bug A\n- bug B\n## Important\n- thing\n## Minor\n"
    result = run_counter(text)
    assert result.returncode == 0
    data = parsed_output(result)
    assert data["critical"] == 2
    assert data["important"] == 1
    assert data["minor"] == 0
    assert data["converged"] is False


def test_empty_or_no_signal_exits_one_with_zero_counts():
    result = run_counter("")
    assert result.returncode == 1
    assert parsed_output(result) == {
        "critical": 0,
        "important": 0,
        "minor": 0,
        "converged": True,
    }
