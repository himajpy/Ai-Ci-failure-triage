
from src.sensor_decoder import decode_sensor_data


def test_decode_voltage_and_current():

    data = bytes([
        0x88, 0x13,
        0x10, 0x27,
        0x00, 0x00,
        0x00, 0x00
    ])

    result = decode_sensor_data(data)

    assert result["voltage"] == 500.0
    assert result["current"] == 1000.0


def test_invalid_can_message():

    data = bytes([0x88, 0x13])

    try:
        decode_sensor_data(data)
        assert False, "Expected ValueError"
    except ValueError:
        pass
