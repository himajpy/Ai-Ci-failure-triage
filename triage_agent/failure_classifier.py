
import re
from pathlib import Path



def get_imported_files(test_file: str) -> set:
    """Identify project source files imported by a test."""

    import ast
    from pathlib import Path

    path = Path(test_file)

    if not path.is_file():
        return set()

    tree = ast.parse(path.read_text(encoding="utf-8"))

    imported_files = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module

        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_path = alias.name.replace(".", "/") + ".py"

                if Path(module_path).is_file():
                    imported_files.add(module_path)

            continue

        else:
            continue

        module_path = module.replace(".", "/") + ".py"

        if Path(module_path).is_file():
            imported_files.add(module_path)

    return imported_files




def extract_changed_lines(diff: str) -> list:
    """Extract added source lines from a unified Git diff."""

    changed_lines = []
    current_file = None
    new_line = None

    for line in diff.splitlines():

        if line.startswith("+++ b/"):
            current_file = line[6:]
            new_line = None
            continue

        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)

            if match:
                new_line = int(match.group(1))

            continue

        if new_line is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed_lines.append({
                "file": current_file,
                "line": new_line,
                "content": line[1:].strip()
            })
            new_line += 1

        elif line.startswith("-") and not line.startswith("---"):
            continue

        elif line.startswith("\\"):
            continue

        else:
            new_line += 1

    return changed_lines



def classify_failure(log_report: dict, git_report: dict) -> dict:
    """Correlate test failures with imported and modified source files."""

    failures = log_report.get("failures", [])
    changed_files = git_report.get("changed_files", [])
    diff = git_report.get("diff", "")

    changed_lines = extract_changed_lines(diff)

    results = []

    for failure in failures:

        test_file = failure.get("test_file", "")
        test_name = failure.get("test_name")

        imported_files = get_imported_files(test_file)

        matching_files = sorted(
            set(changed_files) & imported_files
        )

        relevant_changes = [
            change for change in changed_lines
            if change["file"] in matching_files
        ]

        evidence = []

        for change in relevant_changes:
            evidence.append(
                f'{change["file"]}:{change["line"]}: '
                f'{change["content"]}'
            )

        if (
            failure.get("failure_type") == "AssertionError"
            and relevant_changes
        ):
            category = "POSSIBLE_CODE_REGRESSION"

            explanation = (
                "The failing test imports a source file "
                "that contains modified lines."
            )

        else:
            category = "UNKNOWN"

            explanation = (
                "Insufficient evidence to identify "
                "the root cause."
            )

        results.append({
            "test_name": test_name,
            "category": category,
            "modified_files": matching_files,
            "modified_lines": relevant_changes,
            "expected": failure.get("expected"),
            "actual": failure.get("actual"),
            "evidence": evidence,
            "explanation": explanation
        })

    return {
        "failure_count": len(results),
        "diagnoses": results
    }

