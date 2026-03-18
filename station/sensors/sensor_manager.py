from __future__ import annotations

from dataclasses import dataclass

from station.sensors.pms5003 import PMS5003Sensor
from station.sensors.opc_n3 import OPCN3Sensor
from station.sensors.bme688 import BME688Sensor
from station.sensors.wind import WindSensor


@dataclass(slots=True)
class SensorSnapshot:
    values: dict[str, float | int | None]
    flags: int
    sensor_ok: dict[str, bool]
    errors: dict[str, str | None]

    def to_dict(self) -> dict:
        return {
            **self.values,
            "flags": self.flags,
            "sensor_ok": self.sensor_ok,
            "errors": self.errors,
        }


class SensorManager:
    """
    Collects readings from all station sensors and returns one merged snapshot.

    Flags byte mapping used here:
      bit 0 = PMS invalid
      bit 1 = OPC invalid
      bit 2 = BME invalid
      bit 3 = WIND invalid
      bit 4 = BATT invalid
    """

    FLAG_PMS_INVALID = 1 << 0
    FLAG_OPC_INVALID = 1 << 1
    FLAG_BME_INVALID = 1 << 2
    FLAG_WIND_INVALID = 1 << 3
    FLAG_BATT_INVALID = 1 << 4

    def __init__(
        self,
        pms: PMS5003Sensor | None = None,
        opc: OPCN3Sensor | None = None,
        bme: BME688Sensor | None = None,
        wind: WindSensor | None = None,
    ):
        self.pms = pms or PMS5003Sensor()
        self.opc = opc or OPCN3Sensor()
        self.bme = bme or BME688Sensor()
        self.wind = wind or WindSensor()

    def initialize(self) -> None:
        self.pms.initialize()
        self.opc.initialize()
        self.bme.initialize()
        self.wind.initialize()

    def read_all(self) -> SensorSnapshot:
        flags = 0

        pms_read = self.pms.read()
        opc_read = self.opc.read()
        bme_read = self.bme.read()
        wind_read = self.wind.read()

        if not pms_read.ok:
            flags |= self.FLAG_PMS_INVALID
        if not opc_read.ok:
            flags |= self.FLAG_OPC_INVALID
        if not bme_read.ok:
            flags |= self.FLAG_BME_INVALID
        if not wind_read.ok:
            flags |= self.FLAG_WIND_INVALID

        if wind_read.battery_v is None:
            flags |= self.FLAG_BATT_INVALID

        values = {
            **pms_read.to_dict(),
            **opc_read.to_dict(),
            **bme_read.to_dict(),
            **wind_read.to_dict(),
        }

        sensor_ok = {
            "pms": pms_read.ok,
            "opc": opc_read.ok,
            "bme": bme_read.ok,
            "wind": wind_read.ok,
        }

        errors = {
            "pms": pms_read.error,
            "opc": opc_read.error,
            "bme": bme_read.error,
            "wind": wind_read.error,
        }

        return SensorSnapshot(
            values=values,
            flags=flags,
            sensor_ok=sensor_ok,
            errors=errors,
        )
