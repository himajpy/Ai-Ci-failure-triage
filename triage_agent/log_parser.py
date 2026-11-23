
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
    """Extract structured failures independently from pytest output."""

    failures = []

    # Find each FAILED entry in the short test summary.
    summary_pattern = re.compile(
        r"^FAILED\s+(?P<nodeid>\S+?)\s+-\s+(?P<message>.+)$",
        re.MULTILINE
    )

    summaries = list(summary_pattern.finditer(content))

    # Find the beginning of each detailed failure section.
    section_pattern = re.compile(
        r"^_{5,}\s+(?P<test_name>.*?)\s+_{5,}\s*$",
        re.MULTILINE
    )

    sections = list(section_pattern.finditer(content))

    for summary in summaries:

        nodeid = summary.group("nodeid")
        message = summary.group("message")

        parts = nodeid.split("::")
        test_file = parts[0]
        test_name = parts[-1]

        # Match the detailed section belonging to this test.
        matching_section = None

        for index, section in enumerate(sections):

            section_name = section.group("test_name")

            if section_name == test_name:
                matching_section = section
                break

        block = ""

        if matching_section is not None:

            section_index = sections.index(matching_section)

            block_start = matching_section.end()

            if section_index + 1 < len(sections):
                block_end = sections[section_index + 1].start()
            else:
                block_end = summary.start()

            block = content[block_start:block_end]

        # Extract the traceback location from this failure only.
        location_pattern = re.compile(
            r"^(?P<file>.+\.py):(?P<line>\d+):\s*(?P<type>\w+)",
            re.MULTILINE
        )

        locations = list(location_pattern.finditer(block))

        location = locations[-1] if locations else None

        line_number = (
            int(location.group("line")) if location else None
        )

        failure_type = (
            location.group("type") if location else "Unknown"
        )

        # Extract assertion values from this failure only.
        assertion = re.search(
            r"^\s*E\s+assert\s+(.+?)\s*==\s*(.+)$",
            block,
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

