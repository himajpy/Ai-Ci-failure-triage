
import subprocess

from triage_agent.git_context import (
    get_changed_files,
    get_current_commit,
    get_git_diff,
)


def test_get_current_commit():

    commit = get_current_commit()

    assert len(commit) >= 40


def test_get_changed_files():

    commit = get_current_commit()

    result = get_changed_files(commit)

    assert isinstance(result, list)


def test_get_git_diff():

    commit = get_current_commit()

    result = get_git_diff(commit)

    assert isinstance(result, str)



from triage_agent.git_context import (
    categorize_file,
    categorize_changed_files,
)


def test_categorize_file():
    assert categorize_file("src/sensor_decoder.py") == "SOURCE_CODE"
    assert categorize_file("tests/test_sensor_decoder.py") == "TEST_CODE"
    assert categorize_file("triage_agent/main.py") == "DIAGNOSTIC_TOOL"
    assert categorize_file("scripts/run_local.py") == "SCRIPT"
    assert categorize_file("README.md") == "OTHER"


def test_categorize_changed_files():

    changed_files = [
        "src/sensor_decoder.py",
        "tests/test_sensor_decoder.py",
        "triage_agent/main.py",
    ]

    result = categorize_changed_files(changed_files)

    assert result == [
        {
            "file": "src/sensor_decoder.py",
            "category": "SOURCE_CODE",
        },
        {
            "file": "tests/test_sensor_decoder.py",
            "category": "TEST_CODE",
        },
        {
            "file": "triage_agent/main.py",
            "category": "DIAGNOSTIC_TOOL",
        },
    ]
