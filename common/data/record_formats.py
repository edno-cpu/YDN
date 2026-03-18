from __future__ import annotations

from dataclasses import dataclass
import struct

# -----------------------------------------------------------------------------
# Station Record V2
# -----------------------------------------------------------------------------
# Field order (little-endian):
#   station_id        uint8
#   flags             uint8
#   pms_1             uint16   scaled x10
#   pms_25            uint16   scaled x10
#   opc_10            uint16   scaled x10
#   opc_20            uint16   scaled x10
#   opc_40            uint16   scaled x10
#   bme_t             int16    scaled x100 (deg C)
#   bme_h             uint16   scaled x100 (%RH)
#   bme_p             uint16   scaled x10 after subtracting 800 hPa
#   win_s             uint16   scaled x10
#   win_d             uint16   degrees 0-359
#   min_batt          uint16   scaled x1000 (V -> mV)
#   max_opc10         uint16   scaled x10
#   max_opc20         uint16   scaled x10
#   max_opc40         uint16   scaled x10
#   max_wind_speed    uint16   scaled x10
#
# Total size: 32 bytes
# -----------------------------------------------------------------------------

STATION_RECORD_FORMAT = "<BBHHHHHhHHHHHHHHH"
STATION_RECORD_SIZE = struct.calcsize(STATION_RECORD_FORMAT)  # 32 bytes

FLAG_PMS_INVALID = 1 << 0
FLAG_OPC_INVALID = 1 << 1
FLAG_BME_INVALID = 1 << 2
FLAG_WIND_INVALID = 1 << 3
FLAG_BATT_INVALID = 1 << 4
FLAG_PARTIAL_AVG = 1 << 5


@dataclass(slots=True)
class StationRecord:
    station_id: int
    flags: int
    pms_1: int
    pms_25: int
    opc_10: int
    opc_20: int
    opc_40: int
    bme_t: int
    bme_h: int
    bme_p: int
    win_s: int
    win_d: int
    min_batt: int
    max_opc10: int
    max_opc20: int
    max_opc40: int
    max_wind_speed: int

    def pack(self) -> bytes:
        self.validate()
        return struct.pack(
            STATION_RECORD_FORMAT,
            self.station_id,
            self.flags,
            self.pms_1,
            self.pms_25,
            self.opc_10,
            self.opc_20,
            self.opc_40,
            self.bme_t,
            self.bme_h,
            self.bme_p,
            self.win_s,
            self.win_d,
            self.min_batt,
            self.max_opc10,
            self.max_opc20,
            self.max_opc40,
            self.max_wind_speed,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "StationRecord":
        if len(data) != STATION_RECORD_SIZE:
            raise ValueError(
                f"StationRecord requires {STATION_RECORD_SIZE} bytes, got {len(data)}"
            )
        values = struct.unpack(STATION_RECORD_FORMAT, data)
        return cls(*values)

    def validate(self) -> None:
        _check_uint8("station_id", self.station_id)
        _check_uint8("flags", self.flags)

        for name, value in [
            ("pms_1", self.pms_1),
            ("pms_25", self.pms_25),
            ("opc_10", self.opc_10),
            ("opc_20", self.opc_20),
            ("opc_40", self.opc_40),
            ("bme_h", self.bme_h),
            ("bme_p", self.bme_p),
            ("win_s", self.win_s),
            ("win_d", self.win_d),
            ("min_batt", self.min_batt),
            ("max_opc10", self.max_opc10),
            ("max_opc20", self.max_opc20),
            ("max_opc40", self.max_opc40),
            ("max_wind_speed", self.max_wind_speed),
        ]:
            _check_uint16(name, value)

        _check_int16("bme_t", self.bme_t)

    def to_dict(self) -> dict[str, float | int]:
        return {
            "station_id": self.station_id,
            "flags": self.flags,
            "pms_1": self.pms_1 / 10.0,
            "pms_25": self.pms_25 / 10.0,
            "opc_10": self.opc_10 / 10.0,
            "opc_20": self.opc_20 / 10.0,
            "opc_40": self.opc_40 / 10.0,
            "bme_t": self.bme_t / 100.0,
            "bme_h": self.bme_h / 100.0,
            "bme_p": 800.0 + (self.bme_p / 10.0),
            "win_s": self.win_s / 10.0,
            "win_d": self.win_d,
            "min_batt": self.min_batt / 1000.0,
            "max_opc10": self.max_opc10 / 10.0,
            "max_opc20": self.max_opc20 / 10.0,
            "max_opc40": self.max_opc40 / 10.0,
            "max_wind_speed": self.max_wind_speed / 10.0,
        }

    @classmethod
    def from_engineering_values(
        cls,
        *,
        station_id: int,
        flags: int = 0,
        pms_1: float,
        pms_25: float,
        opc_10: float,
        opc_20: float,
        opc_40: float,
        bme_t: float,
        bme_h: float,
        bme_p: float,
        win_s: float,
        win_d: int,
        min_batt: float,
        max_opc10: float,
        max_opc20: float,
        max_opc40: float,
        max_wind_speed: float,
    ) -> "StationRecord":
        return cls(
            station_id=station_id,
            flags=flags,
            pms_1=int(round(pms_1 * 10)),
            pms_25=int(round(pms_25 * 10)),
            opc_10=int(round(opc_10 * 10)),
            opc_20=int(round(opc_20 * 10)),
            opc_40=int(round(opc_40 * 10)),
            bme_t=int(round(bme_t * 100)),
            bme_h=int(round(bme_h * 100)),
            bme_p=int(round((bme_p - 800.0) * 10)),
            win_s=int(round(win_s * 10)),
            win_d=int(win_d),
            min_batt=int(round(min_batt * 1000)),
            max_opc10=int(round(max_opc10 * 10)),
            max_opc20=int(round(max_opc20 * 10)),
            max_opc40=int(round(max_opc40 * 10)),
            max_wind_speed=int(round(max_wind_speed * 10)),
        )


def _check_uint8(name: str, value: int) -> None:
    if not (0 <= value <= 0xFF):
        raise ValueError(f"{name} out of range for uint8: {value}")


def _check_uint16(name: str, value: int) -> None:
    if not (0 <= value <= 0xFFFF):
        raise ValueError(f"{name} out of range for uint16: {value}")


def _check_int16(name: str, value: int) -> None:
    if not (-32768 <= value <= 32767):
        raise ValueError(f"{name} out of range for int16: {value}")