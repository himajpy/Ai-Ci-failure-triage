
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



def test_unrelated_modified_function_is_not_classified(
    tmp_path, monkeypatch
):
    """A change in an unrelated function must not be attributed
    to the failing test.
    """

    source_dir = tmp_path / "src"
    tests_dir = tmp_path / "tests"

    source_dir.mkdir()
    tests_dir.mkdir()

    source_file = source_dir / "sensor_decoder.py"

    source_file.write_text(
        "def decode_sensor_data(data):\n"
        "    return data\n"
        "\n"
        "\n"
        "def decode_temperature(data):\n"
        "    return data * 0.1\n",
        encoding="utf-8"
    )

    test_file = tests_dir / "test_sensor_decoder.py"

    test_file.write_text(
        "from src.sensor_decoder import decode_sensor_data\n"
        "\n"
        "def test_decode_sensor_data():\n"
        "    result = decode_sensor_data(10)\n"
        "    assert result == 10\n",
        encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)

    log_report = {
        "failures": [
            {
                "failure_type": "AssertionError",
                "test_name": "test_decode_sensor_data",
                "test_file": "tests/test_sensor_decoder.py",
                "expected": "10",
                "actual": "9"
            }
        ]
    }

    git_report = {
        "changed_files": ["src/sensor_decoder.py"],
        "diff": """
diff --git a/src/sensor_decoder.py b/src/sensor_decoder.py
--- a/src/sensor_decoder.py
+++ b/src/sensor_decoder.py
@@ -6,1 +6,1 @@
-    return data * 0.1
+    return data * 0.2
"""
    }

    result = classify_failure(log_report, git_report)

    diagnosis = result["diagnoses"][0]

    assert diagnosis["category"] == "UNKNOWN"
    assert diagnosis["modified_files"] == []
    assert diagnosis["modified_lines"] == []
