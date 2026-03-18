from station.tasks.build_10min_record import TenMinuteRecordBuilder
from common.data.data_record import DataRecord


class MockCollector:
    def __init__(self, rows):
        self._rows = rows

    def get_rows_for_frame(self, frame_id: int):
        return [row for row in self._rows if row["frame_id"] == frame_id]


def main() -> None:
    rows = [
        {
            "ts_unix": 1763503800,
            "ts_iso": "2025-11-18T12:30:00Z",
            "station_id": 3,
            "frame_id": 1234,
            "minute_in_frame": 0,
            "pms_1": 2.0,
            "pms_25": 4.0,
            "opc_10": 10.0,
            "opc_20": 20.0,
            "opc_40": 40.0,
            "bme_t": 18.0,
            "bme_h": 50.0,
            "bme_p": 1000.0,
            "win_s": 3.0,
            "win_d": 200.0,
            "batt_v": 4.10,
            "opc_10_max_1min": 12.0,
            "opc_20_max_1min": 22.0,
            "opc_40_max_1min": 42.0,
            "wind_speed_max_1min": 5.0,
            "sample_count": 30,
            "flags": 0,
        },
        {
            "ts_unix": 1763503860,
            "ts_iso": "2025-11-18T12:31:00Z",
            "station_id": 3,
            "frame_id": 1234,
            "minute_in_frame": 1,
            "pms_1": 4.0,
            "pms_25": 6.0,
            "opc_10": 14.0,
            "opc_20": 24.0,
            "opc_40": 44.0,
            "bme_t": 20.0,
            "bme_h": 52.0,
            "bme_p": 1002.0,
            "win_s": 5.0,
            "win_d": 220.0,
            "batt_v": 4.05,
            "opc_10_max_1min": 16.0,
            "opc_20_max_1min": 26.0,
            "opc_40_max_1min": 46.0,
            "wind_speed_max_1min": 7.0,
            "sample_count": 30,
            "flags": 2,
        },
        {
            "ts_unix": 1763503920,
            "ts_iso": "2025-11-18T12:32:00Z",
            "station_id": 3,
            "frame_id": 1234,
            "minute_in_frame": 2,
            "pms_1": 6.0,
            "pms_25": 8.0,
            "opc_10": 18.0,
            "opc_20": 28.0,
            "opc_40": 48.0,
            "bme_t": 22.0,
            "bme_h": 54.0,
            "bme_p": 1004.0,
            "win_s": 7.0,
            "win_d": 240.0,
            "batt_v": 4.00,
            "opc_10_max_1min": 20.0,
            "opc_20_max_1min": 30.0,
            "opc_40_max_1min": 50.0,
            "wind_speed_max_1min": 9.0,
            "sample_count": 30,
            "flags": 4,
        },
    ]

    collector = MockCollector(rows)
    builder = TenMinuteRecordBuilder(station_id=3, collector=collector)

    station_record = builder.build_for_frame(1234)
    decoded = station_record.to_dict()

    print("=== 10-Minute Record Builder Test ===")
    print("Decoded station record:")
    for k, v in decoded.items():
        print(f"  {k}: {v}")

    print("\nExpected checks:")
    print("  pms_1 avg          = 4.0")
    print("  pms_25 avg         = 6.0")
    print("  opc_10 avg         = 14.0")
    print("  opc_20 avg         = 24.0")
    print("  opc_40 avg         = 44.0")
    print("  bme_t avg          = 20.0")
    print("  bme_h avg          = 52.0")
    print("  bme_p avg          = 1002.0")
    print("  win_s avg          = 5.0")
    print("  win_d avg          = 220")
    print("  min_batt           = 4.0")
    print("  max_opc10          = 20.0")
    print("  max_opc20          = 30.0")
    print("  max_opc40          = 50.0")
    print("  max_wind_speed     = 9.0")
    print("  flags OR           = 6")

    assert decoded["station_id"] == 3
    assert abs(decoded["pms_1"] - 4.0) < 1e-6
    assert abs(decoded["pms_25"] - 6.0) < 1e-6
    assert abs(decoded["opc_10"] - 14.0) < 1e-6
    assert abs(decoded["opc_20"] - 24.0) < 1e-6
    assert abs(decoded["opc_40"] - 44.0) < 1e-6
    assert abs(decoded["bme_t"] - 20.0) < 1e-6
    assert abs(decoded["bme_h"] - 52.0) < 1e-6
    assert abs(decoded["bme_p"] - 1002.0) < 1e-6
    assert abs(decoded["win_s"] - 5.0) < 1e-6
    assert decoded["win_d"] == 220
    assert abs(decoded["min_batt"] - 4.0) < 1e-6
    assert abs(decoded["max_opc10"] - 20.0) < 1e-6
    assert abs(decoded["max_opc20"] - 30.0) < 1e-6
    assert abs(decoded["max_opc40"] - 50.0) < 1e-6
    assert abs(decoded["max_wind_speed"] - 9.0) < 1e-6
    assert decoded["flags"] == 6

    print("\nPASS")


if __name__ == "__main__":
    main()
