from gateway.gateway_controller import (
    GatewayController,
    EXPECTED_FINAL_SENDER_ID,
)
from common.protocol.data_packet import DataPacket
from common.data.record_formats import StationRecord


def make_record(station_id: int) -> StationRecord:
    return StationRecord.from_engineering_values(
        station_id=station_id,
        flags=0,
        pms_1=1.0 * station_id,
        pms_25=2.0 * station_id,
        opc_10=10.0 + station_id,
        opc_20=20.0 + station_id,
        opc_40=40.0 + station_id,
        bme_t=18.0 + station_id,
        bme_h=50.0 + station_id,
        bme_p=1000.0 + station_id,
        win_s=3.0 + station_id,
        win_d=(45 * station_id) % 360,
        min_batt=4.10 - (0.01 * station_id),
        max_opc10=12.0 + station_id,
        max_opc20=22.0 + station_id,
        max_opc40=42.0 + station_id,
        max_wind_speed=5.0 + station_id,
    )


def main() -> None:
    controller = GatewayController("gateway/configs/gateway.yaml")

    complete_packet = DataPacket(
        frame_id=1234,
        sequence=10,
        sender_id=EXPECTED_FINAL_SENDER_ID,
        hop_count=3,
        records=[
            make_record(1),
            make_record(2),
            make_record(3),
            make_record(4),
        ],
    )

    incomplete_packet_missing_n2 = DataPacket(
        frame_id=1234,
        sequence=11,
        sender_id=EXPECTED_FINAL_SENDER_ID,
        hop_count=3,
        records=[
            make_record(1),
            make_record(3),
            make_record(4),
        ],
    )

    incomplete_packet_wrong_sender = DataPacket(
        frame_id=1234,
        sequence=12,
        sender_id=3,
        hop_count=2,
        records=[
            make_record(1),
            make_record(2),
            make_record(3),
            make_record(4),
        ],
    )

    print("=== Gateway Packet Evaluation Test ===")

    for label, packet in [
        ("complete_packet", complete_packet),
        ("incomplete_packet_missing_n2", incomplete_packet_missing_n2),
        ("incomplete_packet_wrong_sender", incomplete_packet_wrong_sender),
    ]:
        frame_complete, missing_station_ids, record_station_ids = controller._evaluate_packet_completeness(packet)

        print(f"\n{label}:")
        print(f"  sender_id: {packet.sender_id}")
        print(f"  record_station_ids: {record_station_ids}")
        print(f"  frame_complete: {frame_complete}")
        print(f"  missing_station_ids: {missing_station_ids}")

    fc1, miss1, _ = controller._evaluate_packet_completeness(complete_packet)
    fc2, miss2, _ = controller._evaluate_packet_completeness(incomplete_packet_missing_n2)
    fc3, miss3, _ = controller._evaluate_packet_completeness(incomplete_packet_wrong_sender)

    assert fc1 is True
    assert miss1 == []

    assert fc2 is False
    assert miss2 == [2]

    assert fc3 is False
    assert miss3 == []

    print("\nPASS")


if __name__ == "__main__":
    main()
