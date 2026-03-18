from common.protocol.packet_types import (
    PACKET_TYPE_DATA,
    PACKET_TYPE_ACK,
    PACKET_TYPE_TIMESYNC,
)
from common.protocol.ack_packet import AckPacket
from common.protocol.timesync_packet import TimeSyncPacket
from common.protocol.data_packet import DataPacket


def encode_data_packet(packet: DataPacket) -> bytes:
    if packet.packet_type != PACKET_TYPE_DATA:
        raise ValueError("encode_data_packet received non-DATA packet")
    return packet.pack()


def encode_ack_packet(packet: AckPacket) -> bytes:
    if packet.packet_type != PACKET_TYPE_ACK:
        raise ValueError("encode_ack_packet received non-ACK packet")
    return packet.pack()


def encode_timesync_packet(packet: TimeSyncPacket) -> bytes:
    if packet.packet_type != PACKET_TYPE_TIMESYNC:
        raise ValueError("encode_timesync_packet received non-TIMESYNC packet")
    return packet.pack()


def encode_packet(packet) -> bytes:
    if packet.packet_type == PACKET_TYPE_DATA:
        return encode_data_packet(packet)
    if packet.packet_type == PACKET_TYPE_ACK:
        return encode_ack_packet(packet)
    if packet.packet_type == PACKET_TYPE_TIMESYNC:
        return encode_timesync_packet(packet)

    raise ValueError(f"Unknown packet_type: {packet.packet_type}")
