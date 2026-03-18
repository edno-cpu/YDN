from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WindReading:
    wind_speed: float | None
    wind_dir: float | None
    battery_v: float | None
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "win_s": self.wind_speed,
            "win_d": self.wind_dir,
            "batt_v": self.battery_v,
        }


class WindSensor:
    """
    Stub wind sensor interface.

    This can later wrap:
    - serial wind station
    - pulse/counting hardware
    - external weather board
    """

    def __init__(self, port: str | None = None):
        self.port = port

    def initialize(self) -> None:
        pass

    def read(self) -> WindReading:
        return WindReading(
            wind_speed=0.0,
            wind_dir=0.0,
            battery_v=0.0,
            ok=True,
            error=None,
        )
