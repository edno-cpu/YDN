from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


# Recommended richer local 1-minute station log format.
# You can use this directly when creating the logger:
#
# logger = DataLogger("station/logs/one_minute_data.csv", fieldnames=ONE_MINUTE_FIELDS)
#
ONE_MINUTE_FIELDS = [
    "ts_unix",
    "ts_iso",
    "station_id",
    "frame_id",
    "minute_in_frame",
    "pms_1",
    "pms_25",
    "opc_10",
    "opc_20",
    "opc_40",
    "bme_t",
    "bme_h",
    "bme_p",
    "win_s",
    "win_d",
    "batt_v",
    "opc_10_max_1min",
    "opc_20_max_1min",
    "opc_40_max_1min",
    "wind_speed_max_1min",
    "sample_count",
    "flags",
]


class DataLogger:
    """
    Generic CSV logger for local station data or gateway-decoded data.

    Main intended use:
    - save 1-minute averaged local station data with richer columns
    - optionally save other CSV rows later

    Behavior:
    - creates parent directory if needed
    - writes header once when file is first created
    - appends one row at a time
    - can enforce a fixed column order if provided
    """

    def __init__(self, filepath: str | Path, fieldnames: Iterable[str] | None = None):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.fieldnames = list(fieldnames) if fieldnames is not None else None

    def log_row(self, row: dict[str, Any]) -> None:
        """
        Append one dictionary row to the CSV file.

        If fieldnames were provided when the logger was created, missing fields
        are filled with empty strings and extra fields are ignored.
        If fieldnames were not provided, the row's keys define the CSV columns.
        """
        if not isinstance(row, dict):
            raise TypeError("row must be a dictionary")

        if self.fieldnames is None:
            fieldnames = list(row.keys())
        else:
            fieldnames = self.fieldnames

        write_header = not self.filepath.exists()

        with self.filepath.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            if write_header:
                writer.writeheader()

            full_row = {key: row.get(key, "") for key in fieldnames}
            writer.writerow(full_row)

    def log_rows(self, rows: list[dict[str, Any]]) -> None:
        """
        Append multiple dictionary rows.
        """
        for row in rows:
            self.log_row(row)


if __name__ == "__main__":
    logger = DataLogger("station/logs/one_minute_data.csv", fieldnames=ONE_MINUTE_FIELDS)

    logger.log_row(
        {
            "ts_unix": 1763503800,
            "ts_iso": "2025-11-18T12:30:00Z",
            "station_id": 3,
            "frame_id": 1234,
            "minute_in_frame": 4,
            "pms_1": 2.7,
            "pms_25": 5.1,
            "opc_10": 11.4,
            "opc_20": 21.8,
            "opc_40": 39.6,
            "bme_t": 18.7,
            "bme_h": 51.3,
            "bme_p": 1001.6,
            "win_s": 3.4,
            "win_d": 212,
            "batt_v": 4.08,
            "opc_10_max_1min": 14.2,
            "opc_20_max_1min": 26.0,
            "opc_40_max_1min": 44.8,
            "wind_speed_max_1min": 5.9,
            "sample_count": 30,
            "flags": 0,
        }
    )

    print(f"Wrote example row to {logger.filepath}")
