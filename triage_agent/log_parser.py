
import re
from pathlib import Path


ERROR_PATTERNS = [
    r"FAILED",
    r"ERROR",
    r"AssertionError",
    r"Traceback",
    r"Segmentation fault",
    r"ModuleNotFoundError",
]


def redact_secrets(text: str) -> str:
    """Remove common credentials before external analysis."""

    patterns = [
        (r"(?i)(api[_-]?key\s*[:=]\s*)[^\s]+", r"\1[REDACTED]"),
        (r"(?i)(password\s*[:=]\s*)[^\s]+", r"\1[REDACTED]"),
        (r"(?i)(token\s*[:=]\s*)[^\s]+", r"\1[REDACTED]"),
        (r"gh[pousr]_[A-Za-z0-9_]{20,}", "[REDACTED]"),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)

    return text


def extract_failures(content: str) -> list:
    """Extract structured failures from pytest output."""

    failures = []

    summary_pattern = re.compile(
        r"^FAILED\s+(?P<nodeid>\S+?)\s+-\s+(?P<message>.+)$",
        re.MULTILINE
    )

    for match in summary_pattern.finditer(content):

        nodeid = match.group("nodeid")
        message = match.group("message")

        parts = nodeid.split("::")

        test_file = parts[0]
        test_name = parts[-1]

        # Find the assertion location in the test file.
        location_pattern = re.compile(
            rf"^{re.escape(test_file)}:(\d+):\s*(\w+)",
            re.MULTILINE
        )

        location = location_pattern.search(content)

        line_number = (
            int(location.group(1)) if location else None
        )

        failure_type = (
            location.group(2) if location else "Unknown"
        )

        # Extract actual and expected values.
        assertion = re.search(
            r"^\s*E\s+assert\s+(.+?)\s*==\s*(.+)$",
            content,
            re.MULTILINE
        )

        actual = assertion.group(1) if assertion else None
        expected = assertion.group(2) if assertion else None

        failures.append({
            "failure_type": failure_type,
            "test_name": test_name,
            "test_file": test_file,
            "line": line_number,
            "actual": actual,
            "expected": expected,
            "error_message": message,
        })

    return failures


def parse_log(log_path: str) -> dict:
    """Parse a test log and return structured diagnostics."""

    path = Path(log_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Log file not found: {log_path}"
        )

    content = path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    # Redact secrets before further processing.
    content = redact_secrets(content)

    lines = content.splitlines()

    error_lines = []

    for index, line in enumerate(lines):

        if any(
            re.search(pattern, line, re.IGNORECASE)
            for pattern in ERROR_PATTERNS
        ):

            start = max(0, index - 5)
            end = min(len(lines), index + 6)

            error_lines.extend(lines[start:end])

    error_lines = list(dict.fromkeys(error_lines))

    failures = extract_failures(content)

    return {
        "error_count": len(failures),
        "failures": failures,
        "extracted_log": "\n".join(error_lines),
    }

