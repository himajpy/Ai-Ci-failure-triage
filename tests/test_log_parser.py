
from triage_agent.log_parser import redact_secrets, parse_log


def test_secret_redaction():

    text = "api_key=ABC123 password=secret123"

    result = redact_secrets(text)

    assert "ABC123" not in result
    assert "secret123" not in result


def test_parse_failure_log():

    result = parse_log("examples/failure.log")

    assert result["error_count"] > 0
    assert "AssertionError" in result["extracted_log"]
    assert "50.0" in result["extracted_log"]



def test_structured_failure_extraction():

    result = parse_log("examples/failure.log")

    assert result["error_count"] == 1

    failure = result["failures"][0]

    assert failure["test_name"] == "test_decode_voltage_and_current"
    assert failure["test_file"] == "tests/test_sensor_decoder.py"
    assert failure["line"] == 16
    assert failure["actual"] == "50.0"
    assert failure["expected"] == "500.0"


def test_extract_multiple_failures_independently():

    from triage_agent.log_parser import extract_failures

    log_content = """
=================================== FAILURES ===================================

________________________ test_voltage _________________________

E       assert 50.0 == 500.0
tests/test_sensor_decoder.py:16: AssertionError

________________________ test_current _________________________

E       assert 10.0 == 100.0
tests/test_sensor_decoder.py:28: AssertionError

================================ short test summary info ========================
FAILED tests/test_sensor_decoder.py::test_voltage - AssertionError
FAILED tests/test_sensor_decoder.py::test_current - AssertionError
"""

    failures = extract_failures(log_content)

    assert len(failures) == 2

    assert failures[0]["test_name"] == "test_voltage"
    assert failures[0]["line"] == 16
    assert failures[0]["actual"] == "50.0"
    assert failures[0]["expected"] == "500.0"

    assert failures[1]["test_name"] == "test_current"
    assert failures[1]["line"] == 28
    assert failures[1]["actual"] == "10.0"
    assert failures[1]["expected"] == "100.0"
