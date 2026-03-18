from common.protocol.timesync_packet import TimeSyncPacket, TIMESYNC_SIZE

def main() -> None:
    pkt = TimeSyncPacket(
        frame_id=1452,
        next_frame_start_unix=1763503800,
        sender_id=0,   # hub
        hop_count=0,
    )

    packed = pkt.pack()
    print(f"TIMESYNC_SIZE: {TIMESYNC_SIZE} bytes")
    print(f"Packed length: {len(packed)} bytes")
    print(f"Packed hex: {packed.hex(' ')}")

    decoded = TimeSyncPacket.unpack(packed)
    print("Decoded:", decoded.to_dict())

    forwarded = decoded.forwarded(new_sender_id=8)
    print("Forwarded:", forwarded.to_dict())

if __name__ == "__main__":
    main()
