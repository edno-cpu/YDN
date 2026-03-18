from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from station.sensors.sensor_manager import SensorManager


@dataclass(slots=True)
class OneMinuteCollector:
    station_id: int
    clock_manager: object
    data_logger: object
    sensor_manager: SensorManager

    def __post_init__(self) -> None:
        self._last_logged_minute_unix: int | None = None
        self._minute_rows: list[dict] = []

    def maybe_collect_minute(self, frame_id: int) -> None:
        now = self.clock_manager.now_unix()
        minute_start = now - (now % 60)

        if self._last_logged_minute_unix == minute_start:
            return

        row = self._build_minute_row(minute_start, frame_id)
        self.data_logger.log_row(row)
        self._minute_rows.append(row)
        self._last_logged_minute_unix = minute_start

    def get_rows_for_frame(self, frame_id: int) -> list[dict]:
        return [row for row in self._minute_rows if row["frame_id"] == frame_id]

    def clear_rows_before_frame(self, frame_id: int) -> None:
        """
        Optional cleanup helper so memory does not grow forever.
        Keeps only rows from the current frame and newer.
        """
        self._minute_rows = [row for row in self._minute_rows if row["frame_id"] >= frame_id]

    def _build_minute_row(self, minute_start_unix: int, frame_id: int) -> dict:
        ts_iso = datetime.fromtimestamp(minute_start_unix, tz=timezone.utc).isoformat()
        minute_in_frame = int((minute_start_unix % 600) // 60)

        snapshot = self.sensor_manager.read_all()
        values = snapshot.values

        opc_10 = _as_float(values.get("opc_10"))
        opc_20 = _as_float(values.get("opc_20"))
        opc_40 = _as_float(values.get("opc_40"))
        win_s = _as_float(values.get("win_s"))

        row = {
            "ts_unix": minute_start_unix,
            "ts_iso": ts_iso,
            "station_id": self.station_id,
            "frame_id": frame_id,
            "minute_in_frame": minute_in_frame,
            "pms_1": _as_float(values.get("pms_1")),
            "pms_25": _as_float(values.get("pms_25")),
            "opc_10": opc_10,
            "opc_20": opc_20,
            "opc_40": opc_40,
            "bme_t": _as_float(values.get("bme_t")),
            "bme_h": _as_float(values.get("bme_h")),
            "bme_p": _as_float(values.get("bme_p")),
            "win_s": win_s,
            "win_d": _as_float(values.get("win_d")),
            "batt_v": _as_float(values.get("batt_v")),
            "opc_10_max_1min": opc_10,
            "opc_20_max_1min": opc_20,
            "opc_40_max_1min": opc_40,
            "wind_speed_max_1min": win_s,
            "sample_count": 1,
            "flags": snapshot.flags,
        }

        return row


def _as_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)