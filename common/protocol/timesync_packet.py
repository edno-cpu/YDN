from __future__ import annotations

from dataclasses import dataclass
import struct

from common.protocol.packet_types import PACKET_TYPE_TIMESYNC


TIMESYNC_FORMAT = "<BHIBBB"
TIMESYNC_SIZE = struct.calcsize(TIMESYNC_FORMAT)


@dataclass(slots=True)
class TimeSyncPacket:
    frame_id: int
    next_frame_start_unix: int
    source_id: int
    destination_id: int
    hop_count: int
    packet_type: int = PACKET_TYPE_TIMESYNC

    def pack(self) -> bytes:
        return struct.pack(
            TIMESYNC_FORMAT,
            self.packet_type,
            self.frame_id,
            self.next_frame_start_unix,
            self.source_id,
            self.destination_id,
            self.hop_count,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "TimeSyncPacket":
        if len(data) != TIMESYNC_SIZE:
            raise ValueError(f"TimeSyncPacket requires {TIMESYNC_SIZE} bytes, got {len(data)}")

        (
            packet_type,
            frame_id,
            next_frame_start_unix,
            source_id,
            destination_id,
            hop_count,
        ) = struct.unpack(TIMESYNC_FORMAT, data)

        if packet_type != PACKET_TYPE_TIMESYNC:
            raise ValueError(f"Not a TIMESYNC packet: packet_type={packet_type}")

        return cls(
            frame_id=frame_id,
            next_frame_start_unix=next_frame_start_unix,
            source_id=source_id,
            destination_id=destination_id,
            hop_count=hop_count,
        )

    def forwarded(self, new_source_id: int, new_destination_id: int) -> "TimeSyncPacket":
        return TimeSyncPacket(
            frame_id=self.frame_id,
            next_frame_start_unix=self.next_frame_start_unix,
            source_id=new_source_id,
            destination_id=new_destination_id,
            hop_count=self.hop_count + 1,
        )