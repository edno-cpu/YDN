from pathlib import Path

from common.storage.data_logger import DataLogger, ONE_MINUTE_FIELDS
from common.storage.event_log import EventLog


def main() -> None:
    test_dir = Path("tests/output")
    test_dir.mkdir(parents=True, exist_ok=True)

    data_path = test_dir / "one_minute_data.csv"
    event_path = test_dir / "events.jsonl"

    data_logger = DataLogger(data_path, fieldnames=ONE_MINUTE_FIELDS)
    event_logger = EventLog(event_path)

    data_logger.log_row(
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

    data_logger.log_row(
        {
            "ts_unix": 1763503860,
            "ts_iso": "2025-11-18T12:31:00Z",
            "station_id": 3,
            "frame_id": 1234,
            "minute_in_frame": 5,
            "pms_1": 2.9,
            "pms_25": 5.4,
            "opc_10": 12.1,
            "opc_20": 22.0,
            "opc_40": 40.2,
            "bme_t": 18.8,
            "bme_h": 51.1,
            "bme_p": 1001.5,
            "win_s": 3.8,
            "win_d": 218,
            "batt_v": 4.07,
            "opc_10_max_1min": 15.0,
            "opc_20_max_1min": 27.3,
            "opc_40_max_1min": 45.5,
            "wind_speed_max_1min": 6.3,
            "sample_count": 30,
            "flags": 0,
        }
    )

    event_logger.info(
        "boot",
        "Station boot complete",
        {"station_id": 3},
    )

    event_logger.info(
        "frame_complete",
        "Stored one-minute local data rows",
        {"frame_id": 1234, "rows_written": 2},
    )

    event_logger.warning(
        "sync_offset",
        "Large sync offset observed",
        {"offset_seconds": 4, "station_id": 3},
    )

    print("=== Storage Test Complete ===")
    print(f"CSV written to:   {data_path}")
    print(f"JSONL written to: {event_path}")

    print("\nCSV preview:")
    print(data_path.read_text(encoding='utf-8'))

    print("JSONL preview:")
    print(event_path.read_text(encoding='utf-8'))


if __name__ == "__main__":
    main()

