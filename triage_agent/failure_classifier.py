
import ast
import re
from pathlib import Path


def get_imported_functions(test_file: str) -> dict:
    """Return imported functions and their source module paths."""

    path = Path(test_file)

    if not path.is_file():
        return {}

    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported_functions = {}

    for node in ast.walk(tree):

        if not isinstance(node, ast.ImportFrom):
            continue

        if not node.module:
            continue

        module_path = node.module.replace(".", "/") + ".py"

        if not Path(module_path).is_file():
            continue

        for alias in node.names:

            local_name = alias.asname or alias.name

            imported_functions.setdefault(
                module_path, {}
            )[local_name] = alias.name

    return imported_functions


def get_called_functions(test_file: str) -> set:
    """Identify function names called by a test."""

    path = Path(test_file)

    if not path.is_file():
        return set()

    tree = ast.parse(path.read_text(encoding="utf-8"))

    called_functions = set()

    for node in ast.walk(tree):

        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):
            called_functions.add(node.func.id)

        elif isinstance(node.func, ast.Attribute):
            called_functions.add(node.func.attr)

    return called_functions


def get_function_for_line(source_file: str, line_number: int):
    """Find the function containing a particular source line."""

    path = Path(source_file)

    if not path.is_file():
        return None

    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):

        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        if node.lineno <= line_number <= node.end_lineno:
            return node.name

    return None


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
    """Correlate test failures with modified functions."""

    failures = log_report.get("failures", [])
    changed_files = git_report.get("changed_files", [])
    diff = git_report.get("diff", "")

    changed_lines = extract_changed_lines(diff)

    results = []

    for failure in failures:

        test_file = failure.get("test_file", "")
        test_name = failure.get("test_name")

        imported_functions = get_imported_functions(test_file)
        called_functions = get_called_functions(test_file)

        relevant_changes = []

        for change in changed_lines:

            source_file = change["file"]

            if source_file not in changed_files:
                continue

            imported_from_file = imported_functions.get(
                source_file, {}
            )

            changed_function = get_function_for_line(
                source_file,
                change["line"]
            )

            if changed_function is None:
                continue

            imported_local_names = {
                local_name
                for local_name, original_name
                in imported_from_file.items()
                if original_name == changed_function
            }

            if not imported_local_names.intersection(called_functions):
                continue

            relevant_changes.append({
                **change,
                "function": changed_function
            })

        matching_files = sorted({
            change["file"]
            for change in relevant_changes
        })

        evidence = [
            (
                f'{change["file"]}:{change["line"]}: '
                f'{change["content"]} '
                f'(function: {change["function"]})'
            )
            for change in relevant_changes
        ]

        if (
            failure.get("failure_type") == "AssertionError"
            and relevant_changes
        ):
            category = "POSSIBLE_CODE_REGRESSION"

            explanation = (
                "The failing test calls an imported function "
                "containing modified source lines."
            )

        else:
            category = "UNKNOWN"

            explanation = (
                "Insufficient function-level evidence "
                "to identify the root cause."
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
