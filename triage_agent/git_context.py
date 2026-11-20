
import subprocess
from pathlib import Path


def run_git_command(arguments: list[str]) -> str:
    """Execute a Git command and return its output."""

    result = subprocess.run(
        ["git", *arguments],
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout


def get_current_commit() -> str:
    """Return the current Git commit hash."""

    return run_git_command(
        ["rev-parse", "HEAD"]
    ).strip()


def get_changed_files(base_commit: str) -> list[str]:
    """Identify files changed since the baseline commit."""

    output = run_git_command([
        "diff",
        "--name-only",
        f"{base_commit}...HEAD"
    ])

    return [
        line for line in output.splitlines()
        if line.strip()
    ]


def categorize_file(file_path: str) -> str:
    """Classify a changed file according to its project directory."""

    path = Path(file_path)
    parts = path.parts

    if not parts:
        return "OTHER"

    directory = parts[0]

    categories = {
        "src": "SOURCE_CODE",
        "tests": "TEST_CODE",
        "triage_agent": "DIAGNOSTIC_TOOL",
        "scripts": "SCRIPT"
    }

    return categories.get(directory, "OTHER")


def categorize_changed_files(changed_files: list[str]) -> list[dict]:
    """Attach a category to every changed file."""

    return [
        {
            "file": file_path,
            "category": categorize_file(file_path)
        }
        for file_path in changed_files
    ]


def get_git_diff(base_commit: str) -> str:
    """Extract source-code changes."""

    return run_git_command([
        "diff",
        "--no-ext-diff",
        "--unified=5",
        f"{base_commit}...HEAD"
    ])


def get_file_context(
    file_path: str,
    start_line: int,
    end_line: int
) -> str:
    """Extract a source-code section."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(file_path)

    if start_line < 1 or end_line < start_line:
        raise ValueError("Invalid line range")

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    return "\n".join(
        lines[start_line - 1:end_line]
    )


def get_git_context(base_commit: str) -> dict:
    """Collect Git information for AI diagnosis."""

    current_commit = get_current_commit()

    changed_files = get_changed_files(base_commit)

    categorized_files = categorize_changed_files(changed_files)

    diff = get_git_diff(base_commit)

    return {
        "base_commit": base_commit,
        "current_commit": current_commit,
        "changed_files": changed_files,
        "categorized_changed_files": categorized_files,
        "diff": diff
    }
