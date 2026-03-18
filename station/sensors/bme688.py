from __future__ import annotations

from dataclasses import dataclass

import board
import busio
import adafruit_bme680


@dataclass(slots=True)
class BME688Reading:
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "bme_t": self.temperature_c,
            "bme_h": self.humidity_pct,
            "bme_p": self.pressure_hpa,
        }


class BME688Sensor:
    def __init__(self, i2c_address: int = 0x77):
        self.i2c_address = i2c_address
        self.i2c = None
        self.sensor = None

    def initialize(self) -> None:
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bme680.Adafruit_BME680_I2C(self.i2c, address=self.i2c_address)

    def read(self) -> BME688Reading:
        try:
            if self.sensor is None:
                raise RuntimeError("BME688 not initialized")

            return BME688Reading(
                temperature_c=float(self.sensor.temperature),
                humidity_pct=float(self.sensor.relative_humidity),
                pressure_hpa=float(self.sensor.pressure),
                ok=True,
                error=None,
            )
        except Exception as exc:
            return BME688Reading(None, None, None, False, str(exc))