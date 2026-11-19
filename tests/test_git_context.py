
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
