
import argparse
import json
import sys
from pathlib import Path

from triage_agent.log_parser import parse_log
from triage_agent.git_context import get_git_context
from triage_agent.failure_classifier import classify_failure


def run_diagnostics(log_file: str, base_commit: str) -> dict:
    """Execute the complete diagnostic pipeline."""

    # 1. Parse CI test log
    log_report = parse_log(log_file)

    # 2. Collect Git information
    git_report = get_git_context(base_commit)

    # 3. Correlate failures with source changes
    classification = classify_failure(
        log_report,
        git_report
    )

    # 4. Assemble final report
    return {
        "project": "AI-CI-Failure-Triage",
        "summary": {
            "total_failures": log_report["error_count"],
            "changed_files": len(git_report["changed_files"]),
            "diagnoses": classification["failure_count"]
        },
        "failures": log_report["failures"],
        "git_context": git_report,
        "classification": classification
    }


def main():
    parser = argparse.ArgumentParser(
        description="AI-assisted CI failure diagnosis"
    )

    parser.add_argument(
        "--log-file",
        default="examples/failure.log"
    )

    parser.add_argument(
        "--base-commit",
        default="4a53a72"
    )

    args = parser.parse_args()

    report = run_diagnostics(
        args.log_file,
        args.base_commit
    )

    print(json.dumps(report, indent=4))


if __name__ == "__main__":
    main()
