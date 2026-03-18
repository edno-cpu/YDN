from __future__ import annotations

from dataclasses import dataclass

from common.data.record_formats import (
    StationRecord,
    FLAG_BATT_INVALID,
    FLAG_BME_INVALID,
    FLAG_OPC_INVALID,
    FLAG_PARTIAL_AVG,
    FLAG_PMS_INVALID,
    FLAG_WIND_INVALID,
)


@dataclass(slots=True)
class DataRecord:
    station_id: int
    flags: int = 0
    pms_1: float = 0.0
    pms_25: float = 0.0
    opc_10: float = 0.0
    opc_20: float = 0.0
    opc_40: float = 0.0
    bme_t: float = 0.0
    bme_h: float = 0.0
    bme_p: float = 0.0
    win_s: float = 0.0
    win_d: int = 0
    min_batt: float = 0.0
    max_opc10: float = 0.0
    max_opc20: float = 0.0
    max_opc40: float = 0.0
    max_wind_speed: float = 0.0

    def to_station_record(self) -> StationRecord:
        return StationRecord.from_engineering_values(
            station_id=self.station_id,
            flags=self.flags,
            pms_1=self.pms_1,
            pms_25=self.pms_25,
            opc_10=self.opc_10,
            opc_20=self.opc_20,
            opc_40=self.opc_40,
            bme_t=self.bme_t,
            bme_h=self.bme_h,
            bme_p=self.bme_p,
            win_s=self.win_s,
            win_d=self.win_d,
            min_batt=self.min_batt,
            max_opc10=self.max_opc10,
            max_opc20=self.max_opc20,
            max_opc40=self.max_opc40,
            max_wind_speed=self.max_wind_speed,
        )

    @classmethod
    def from_station_record(cls, record: StationRecord) -> "DataRecord":
        d = record.to_dict()
        return cls(
            station_id=int(d["station_id"]),
            flags=int(d["flags"]),
            pms_1=float(d["pms_1"]),
            pms_25=float(d["pms_25"]),
            opc_10=float(d["opc_10"]),
            opc_20=float(d["opc_20"]),
            opc_40=float(d["opc_40"]),
            bme_t=float(d["bme_t"]),
            bme_h=float(d["bme_h"]),
            bme_p=float(d["bme_p"]),
            win_s=float(d["win_s"]),
            win_d=int(d["win_d"]),
            min_batt=float(d["min_batt"]),
            max_opc10=float(d["max_opc10"]),
            max_opc20=float(d["max_opc20"]),
            max_opc40=float(d["max_opc40"]),
            max_wind_speed=float(d["max_wind_speed"]),
        )


__all__ = [
    "DataRecord",
    "StationRecord",
    "FLAG_PMS_INVALID",
    "FLAG_OPC_INVALID",
    "FLAG_BME_INVALID",
    "FLAG_WIND_INVALID",
    "FLAG_BATT_INVALID",
    "FLAG_PARTIAL_AVG",
]
