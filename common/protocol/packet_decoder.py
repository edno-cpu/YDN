from common.protocol.packet_types import (
    PACKET_TYPE_DATA,
    PACKET_TYPE_ACK,
    PACKET_TYPE_TIMESYNC,
)
from common.protocol.ack_packet import AckPacket
from common.protocol.timesync_packet import TimeSyncPacket
from common.protocol.data_packet import DataPacket


def get_packet_type(packet_bytes: bytes) -> int:
    if not packet_bytes:
        raise ValueError("Empty packet")
    return packet_bytes[0]


def decode_packet(packet_bytes: bytes):
    packet_type = get_packet_type(packet_bytes)

    if packet_type == PACKET_TYPE_DATA:
        return DataPacket.unpack(packet_bytes)

    if packet_type == PACKET_TYPE_ACK:
        return AckPacket.unpack(packet_bytes)

    if packet_type == PACKET_TYPE_TIMESYNC:
        return TimeSyncPacket.unpack(packet_bytes)

    raise ValueError(f"Unknown packet type: {packet_type}")
