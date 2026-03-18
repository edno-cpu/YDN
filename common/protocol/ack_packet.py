from dataclasses import dataclass
import struct

from common.protocol.packet_types import PACKET_TYPE_ACK


ACK_FORMAT = "<BHHBBbbB"
ACK_SIZE = struct.calcsize(ACK_FORMAT)

ACK_FLAG_ACCEPTED = 1 << 0
ACK_FLAG_DUPLICATE = 1 << 1
ACK_FLAG_CRC_ERROR = 1 << 2
ACK_FLAG_BUSY = 1 << 3


@dataclass
class AckPacket:
    frame_id: int
    ack_seq: int
    source_id: int
    destination_id: int
    rssi_raw: int
    snr_raw: int
    ack_flags: int
    packet_type: int = PACKET_TYPE_ACK

    def pack(self) -> bytes:
        return struct.pack(
            ACK_FORMAT,
            self.packet_type,
            self.frame_id,
            self.ack_seq,
            self.source_id,
            self.destination_id,
            self.rssi_raw,
            self.snr_raw,
            self.ack_flags,
        )

    @classmethod
    def unpack(cls, data: bytes) -> "AckPacket":
        if len(data) != ACK_SIZE:
            raise ValueError(f"AckPacket requires {ACK_SIZE} bytes, got {len(data)}")

        (
            packet_type,
            frame_id,
            ack_seq,
            source_id,
            destination_id,
            rssi_raw,
            snr_raw,
            ack_flags,
        ) = struct.unpack(ACK_FORMAT, data)

        if packet_type != PACKET_TYPE_ACK:
            raise ValueError(f"Not an ACK packet: packet_type={packet_type}")

        return cls(
            frame_id=frame_id,
            ack_seq=ack_seq,
            source_id=source_id,
            destination_id=destination_id,
            rssi_raw=rssi_raw,
            snr_raw=snr_raw,
            ack_flags=ack_flags,
        )