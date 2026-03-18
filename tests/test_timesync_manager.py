from common.protocol.timesync_packet import TimeSyncPacket
from common.time.clock_manager import ClockManager
from common.time.timesync import TimeSyncManager
from common.frame.slot_scheduler import SlotScheduler


def main() -> None:
    scheduler = SlotScheduler(
        frame_length_s=600,
        slot_length_s=30,
        phase_b_start_offset_s=480,
        station_count=8,
    )

    clock_manager = ClockManager()

    manager = TimeSyncManager(
        station_id=7,
        clock_manager=clock_manager,
        scheduler=scheduler,
    )

    packet = TimeSyncPacket(
        frame_id=1234,
        next_frame_start_unix=1763503800,
        sender_id=0,   # hub
        hop_count=0,
    )

    result, forwarded_packet = manager.handle_packet(packet)

    print("=== TimeSyncManager Test ===")
    print("Result:")
    print(f"  frame_id: {result.frame_id}")
    print(f"  next_frame_start_unix: {result.next_frame_start_unix}")
    print(f"  local_time_unix: {result.local_time_unix}")
    print(f"  offset_seconds: {result.offset_seconds}")
    print(f"  action: {result.action}")

    print("\nScheduler state:")
    print(f"  synced_frame_id: {scheduler.synced_frame_id}")
    print(f"  synced_next_frame_start_unix: {scheduler.synced_next_frame_start_unix}")

    print("\nForwarded packet:")
    print(f"  frame_id: {forwarded_packet.frame_id}")
    print(f"  next_frame_start_unix: {forwarded_packet.next_frame_start_unix}")
    print(f"  sender_id: {forwarded_packet.sender_id}")
    print(f"  hop_count: {forwarded_packet.hop_count}")

    packed = forwarded_packet.pack()
    print(f"\nForwarded packed bytes ({len(packed)} bytes): {packed.hex(' ')}")


if __name__ == "__main__":
    main()
