
from triage_agent.failure_classifier import classify_failure


def test_detect_possible_code_regression():

    log_report = {
        "failures": [
            {
                "failure_type": "AssertionError",
                "test_name": "test_decode_voltage_and_current",
                "test_file": "tests/test_sensor_decoder.py",
                "expected": "500.0",
                "actual": "50.0"
            }
        ]
    }

    git_report = {
        "changed_files": ["src/sensor_decoder.py"],
        "diff": """
diff --git a/src/sensor_decoder.py b/src/sensor_decoder.py
--- a/src/sensor_decoder.py
+++ b/src/sensor_decoder.py
@@ -14,1 +14,1 @@
-    voltage = raw_voltage * 0.1
+    voltage = raw_voltage * 0.01
"""
    }

    result = classify_failure(log_report, git_report)

    assert result["failure_count"] == 1

    diagnosis = result["diagnoses"][0]

    assert diagnosis["category"] == "POSSIBLE_CODE_REGRESSION"

    assert diagnosis["modified_files"] == [
        "src/sensor_decoder.py"
    ]

    assert diagnosis["modified_lines"][0]["line"] == 14

    assert diagnosis["expected"] == "500.0"

    assert diagnosis["actual"] == "50.0"

