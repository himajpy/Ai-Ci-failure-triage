
from triage_agent.main import run_diagnostics


def test_run_diagnostics_summary(monkeypatch):

    import triage_agent.main as main_module

    monkeypatch.setattr(
        main_module,
        "parse_log",
        lambda log_file: {
            "error_count": 1,
            "failures": [{"test_name": "test_example"}]
        }
    )

    monkeypatch.setattr(
        main_module,
        "get_git_context",
        lambda base_commit: {
            "changed_files": [
                "src/sensor_decoder.py",
                "tests/test_sensor_decoder.py",
                "triage_agent/main.py"
            ],
            "categorized_changed_files": [
                {"file": "src/sensor_decoder.py",
                 "category": "SOURCE_CODE"},
                {"file": "tests/test_sensor_decoder.py",
                 "category": "TEST_CODE"},
                {"file": "triage_agent/main.py",
                 "category": "DIAGNOSTIC_TOOL"}
            ]
        }
    )

    monkeypatch.setattr(
        main_module,
        "classify_failure",
        lambda log_report, git_report: {
            "failure_count": 1,
            "diagnoses": []
        }
    )

    report = run_diagnostics(
        "examples/failure.log",
        "4a53a72"
    )

    assert report["summary"]["total_failures"] == 1
    assert report["summary"]["changed_files"] == 3
    assert report["summary"]["diagnoses"] == 1

    assert report["summary"]["changed_file_categories"] == {
        "SOURCE_CODE": 1,
        "TEST_CODE": 1,
        "DIAGNOSTIC_TOOL": 1
    }
