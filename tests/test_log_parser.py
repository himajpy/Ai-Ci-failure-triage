
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
