from __future__ import annotations

from common.data.data_record import DataRecord


class TenMinuteRecordBuilder:
    """
    Build one transmitted 10-minute station record from the richer 1-minute local rows.
    """

    def __init__(self, station_id: int, collector):
        self.station_id = station_id
        self.collector = collector

    def build_for_frame(self, frame_id: int):
        rows = self.collector.get_rows_for_frame(frame_id)

        if not rows:
            return DataRecord(
                station_id=self.station_id,
                flags=0,
                pms_1=0.0,
                pms_25=0.0,
                opc_10=0.0,
                opc_20=0.0,
                opc_40=0.0,
                bme_t=0.0,
                bme_h=0.0,
                bme_p=0.0,
                win_s=0.0,
                win_d=0,
                min_batt=0.0,
                max_opc10=0.0,
                max_opc20=0.0,
                max_opc40=0.0,
                max_wind_speed=0.0,
            ).to_station_record()

        def avg(key: str) -> float:
            vals = [float(r[key]) for r in rows if r.get(key) not in ("", None)]
            return sum(vals) / len(vals) if vals else 0.0

        def maxv(key: str) -> float:
            vals = [float(r[key]) for r in rows if r.get(key) not in ("", None)]
            return max(vals) if vals else 0.0

        def minv(key: str) -> float:
            vals = [float(r[key]) for r in rows if r.get(key) not in ("", None)]
            return min(vals) if vals else 0.0

        # Use row-level flags: OR together any nonzero flags seen in the frame
        frame_flags = 0
        for row in rows:
            try:
                frame_flags |= int(row.get("flags", 0))
            except Exception:
                pass

        # Wind direction: keep simple for now as arithmetic mean.
        # Later this can be upgraded to circular mean if needed.
        win_d_avg = int(round(avg("win_d"))) % 360 if rows else 0

        return DataRecord(
            station_id=self.station_id,
            flags=frame_flags,
            pms_1=avg("pms_1"),
            pms_25=avg("pms_25"),
            opc_10=avg("opc_10"),
            opc_20=avg("opc_20"),
            opc_40=avg("opc_40"),
            bme_t=avg("bme_t"),
            bme_h=avg("bme_h"),
            bme_p=avg("bme_p"),
            win_s=avg("win_s"),
            win_d=win_d_avg,
            min_batt=minv("batt_v"),
            max_opc10=maxv("opc_10_max_1min"),
            max_opc20=maxv("opc_20_max_1min"),
            max_opc40=maxv("opc_40_max_1min"),
            max_wind_speed=maxv("wind_speed_max_1min"),
        ).to_station_record()