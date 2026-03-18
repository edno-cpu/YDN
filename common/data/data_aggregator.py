from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin
from typing import Iterable

from common.data.data_record import DataRecord
from common.data.record_formats import (
    FLAG_BATT_INVALID,
    FLAG_BME_INVALID,
    FLAG_OPC_INVALID,
    FLAG_PARTIAL_AVG,
    FLAG_PMS_INVALID,
    FLAG_WIND_INVALID,
)


@dataclass(slots=True)
class SensorSample:
    pms_1: float | None = None
    pms_25: float | None = None
    opc_10: float | None = None
    opc_20: float | None = None
    opc_40: float | None = None
    bme_t: float | None = None
    bme_h: float | None = None
    bme_p: float | None = None
    win_s: float | None = None
    win_d: float | None = None
    batt_v: float | None = None


class DataAggregator:
    """
    Builds one 10-minute station record from raw samples collected during that interval.
    """

    def __init__(self, expected_samples: int | None = None):
        self.expected_samples = expected_samples

    def aggregate(self, station_id: int, samples: Iterable[SensorSample]) -> DataRecord:
        samples = list(samples)
        if not samples:
            raise ValueError("Cannot aggregate zero samples")

        flags = 0

        pms_1_vals = _valid(samples, "pms_1")
        pms_25_vals = _valid(samples, "pms_25")

        opc_10_vals = _valid(samples, "opc_10")
        opc_20_vals = _valid(samples, "opc_20")
        opc_40_vals = _valid(samples, "opc_40")

        bme_t_vals = _valid(samples, "bme_t")
        bme_h_vals = _valid(samples, "bme_h")
        bme_p_vals = _valid(samples, "bme_p")

        win_s_vals = _valid(samples, "win_s")
        win_d_vals = _valid(samples, "win_d")

        batt_vals = _valid(samples, "batt_v")

        if not pms_1_vals or not pms_25_vals:
            flags |= FLAG_PMS_INVALID
        if not opc_10_vals or not opc_20_vals or not opc_40_vals:
            flags |= FLAG_OPC_INVALID
        if not bme_t_vals or not bme_h_vals or not bme_p_vals:
            flags |= FLAG_BME_INVALID
        if not win_s_vals or not win_d_vals:
            flags |= FLAG_WIND_INVALID
        if not batt_vals:
            flags |= FLAG_BATT_INVALID

        if self.expected_samples is not None and len(samples) < self.expected_samples:
            flags |= FLAG_PARTIAL_AVG

        return DataRecord(
            station_id=station_id,
            flags=flags,
            pms_1=_mean_or_zero(pms_1_vals),
            pms_25=_mean_or_zero(pms_25_vals),
            opc_10=_mean_or_zero(opc_10_vals),
            opc_20=_mean_or_zero(opc_20_vals),
            opc_40=_mean_or_zero(opc_40_vals),
            bme_t=_mean_or_zero(bme_t_vals),
            bme_h=_mean_or_zero(bme_h_vals),
            bme_p=_mean_or_zero(bme_p_vals),
            win_s=_mean_or_zero(win_s_vals),
            win_d=_circular_mean_deg(win_d_vals),
            min_batt=_min_or_zero(batt_vals),
            max_opc10=_max_or_zero(opc_10_vals),
            max_opc20=_max_or_zero(opc_20_vals),
            max_opc40=_max_or_zero(opc_40_vals),
            max_wind_speed=_max_or_zero(win_s_vals),
        )


def _valid(samples: list[SensorSample], attr: str) -> list[float]:
    out: list[float] = []
    for s in samples:
        value = getattr(s, attr)
        if value is not None:
            out.append(float(value))
    return out


def _mean_or_zero(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _min_or_zero(values: list[float]) -> float:
    return min(values) if values else 0.0


def _max_or_zero(values: list[float]) -> float:
    return max(values) if values else 0.0


def _circular_mean_deg(values: list[float]) -> int:
    if not values:
        return 0

    x = sum(cos(radians(v)) for v in values)
    y = sum(sin(radians(v)) for v in values)

    if x == 0 and y == 0:
        return 0

    angle = degrees(atan2(y, x))
    if angle < 0:
        angle += 360.0
    return int(round(angle)) % 360
