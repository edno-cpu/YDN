from __future__ import annotations

from dataclasses import dataclass
import serial


@dataclass(slots=True)
class PMS5003Reading:
    pm1_0: float | None
    pm2_5: float | None
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "pms_1": self.pm1_0,
            "pms_25": self.pm2_5,
        }


class PMS5003Sensor:
    def __init__(self, port: str = "/dev/ttyS0", baudrate: int = 9600, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: serial.Serial | None = None

    def initialize(self) -> None:
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)

    def read(self) -> PMS5003Reading:
        try:
            if self.ser is None:
                raise RuntimeError("PMS5003 serial port not initialized")

            frame = self._read_frame()
            if frame is None:
                return PMS5003Reading(None, None, False, "no_frame")

            # PMS5003 standard frame positions
            pm1_atm = (frame[10] << 8) | frame[11]
            pm25_atm = (frame[12] << 8) | frame[13]

            return PMS5003Reading(
                pm1_0=float(pm1_atm),
                pm2_5=float(pm25_atm),
                ok=True,
                error=None,
            )
        except Exception as exc:
            return PMS5003Reading(None, None, False, str(exc))

    def _read_frame(self) -> bytes | None:
        assert self.ser is not None

        while True:
            b1 = self.ser.read(1)
            if not b1:
                return None
            if b1[0] != 0x42:
                continue

            b2 = self.ser.read(1)
            if not b2:
                return None
            if b2[0] != 0x4D:
                continue

            rest = self.ser.read(30)
            if len(rest) != 30:
                return None

            frame = bytes([0x42, 0x4D]) + rest

            # checksum
            received_checksum = (frame[30] << 8) | frame[31]
            calculated_checksum = sum(frame[:30]) & 0xFFFF

            if received_checksum != calculated_checksum:
                return None

            return frame