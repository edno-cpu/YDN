from common.protocol.data_packet import DataPacket, DATA_HEADER_SIZE
from common.data.record_formats import StationRecord, STATION_RECORD_SIZE


def make_record(station_id: int) -> StationRecord:
    return StationRecord.from_engineering_values(
        station_id=station_id,
        flags=0,
        pms_1=1.1 * station_id,
        pms_25=2.2 * station_id,
        opc_10=10.0 + station_id,
        opc_20=20.0 + station_id,
        opc_40=40.0 + station_id,
        bme_t=18.5 + station_id,
        bme_h=45.0 + station_id,
        bme_p=1000.0 + station_id,
        win_s=3.0 + station_id,
        win_d=(45 * station_id) % 360,
        min_batt=4.05 - (0.01 * station_id),
        max_opc10=12.0 + station_id,
        max_opc20=24.0 + station_id,
        max_opc40=48.0 + station_id,
        max_wind_speed=5.0 + station_id,
    )


def test_packet(record_count: int) -> None:
    records = [make_record(i) for i in range(1, record_count + 1)]

    packet = DataPacket(
        frame_id=123,
        sequence=7,
        sender_id=1,
        hop_count=2,
        records=records,
    )

    packed = packet.pack()
    unpacked = DataPacket.unpack(packed)

    expected_size = DATA_HEADER_SIZE + (record_count * STATION_RECORD_SIZE)

    print(f"\n=== DATA packet test: {record_count} record(s) ===")
    print(f"Header size: {DATA_HEADER_SIZE} bytes")
    print(f"Record size: {STATION_RECORD_SIZE} bytes")
    print(f"Expected packet size: {expected_size} bytes")
    print(f"Actual packet size:   {len(packed)} bytes")
    print(f"Packet hex: {packed.hex(' ')}")

    assert len(packed) == expected_size
    assert unpacked.frame_id == packet.frame_id
    assert unpacked.sequence == packet.sequence
    assert unpacked.sender_id == packet.sender_id
    assert unpacked.hop_count == packet.hop_count
    assert len(unpacked.records) == len(packet.records)

    for i, (original, decoded) in enumerate(zip(packet.records, unpacked.records), start=1):
        assert original == decoded, f"Mismatch in record {i}"

    print("Round-trip pack/unpack: PASS")


def main() -> None:
    for count in [1, 4, 8]:
        test_packet(count)


if __name__ == "__main__":
    main()
