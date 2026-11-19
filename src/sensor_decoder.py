
def decode_sensor_data(data: bytes) -> dict:
    """
    Decode CAN sensor data.

    Bytes 0-1: Stack voltage
    Bytes 2-3: Stack current

    Intel byte order (little-endian).
    Scaling factor: 0.1
    """

    if len(data) < 4:
        raise ValueError("CAN data must contain at least 4 bytes")

    raw_voltage = int.from_bytes(data[0:2], byteorder="little")
    raw_current = int.from_bytes(data[2:4], byteorder="little")

    voltage = raw_voltage * 0.01
    current = raw_current * 0.1

    return {
        "voltage": voltage,
        "current": current
    }

