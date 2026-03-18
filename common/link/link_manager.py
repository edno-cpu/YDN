from dataclasses import dataclass, field

from common.protocol.ack_packet import AckPacket, ACK_FLAG_ACCEPTED
from common.protocol.data_packet import DataPacket
from common.protocol.packet_encoder import encode_packet
from common.protocol.packet_decoder import decode_packet
from common.protocol.sequence_cache import SequenceCache
from common.protocol.timesync_packet import TimeSyncPacket


@dataclass
class LinkStats:
    attempts: int = 0
    successes: int = 0
    retries: int = 0
    skips: int = 0
    duplicates: int = 0
    last_rssi: int | None = None
    last_snr: int | None = None

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts


@dataclass
class LinkManager:
    node_id: int
    radio_manager: object
    sequence_cache: SequenceCache
    max_attempts: int = 3
    ack_timeout_s: float = 1.5
    stats: LinkStats = field(default_factory=LinkStats)

    def build_ack(
        self,
        frame_id: int,
        ack_seq: int,
        source_id: int,
        destination_id: int,
        rssi_raw: int,
        snr_raw: int,
    ) -> AckPacket:
        return AckPacket(
            frame_id=frame_id,
            ack_seq=ack_seq,
            source_id=source_id,
            destination_id=destination_id,
            rssi_raw=rssi_raw,
            snr_raw=snr_raw,
            ack_flags=ACK_FLAG_ACCEPTED,
        )

    def receive_data_and_build_ack(self, packet_bytes: bytes, rssi_raw: int, snr_raw: int):
        packet = decode_packet(packet_bytes)

        if not isinstance(packet, DataPacket):
            return False, "not_data_packet", None, None

        if packet.destination_id != self.node_id:
            return False, "wrong_destination", packet, None

        if self.sequence_cache.contains(packet.frame_id, packet.sequence, packet.source_id):
            self.stats.duplicates += 1
            return False, "duplicate", packet, None

        self.sequence_cache.add(packet.frame_id, packet.sequence, packet.source_id)

        ack = self.build_ack(
            frame_id=packet.frame_id,
            ack_seq=packet.sequence,
            source_id=self.node_id,
            destination_id=packet.source_id,
            rssi_raw=rssi_raw,
            snr_raw=snr_raw,
        )

        ack_bytes = encode_packet(ack)
        return True, "accepted", packet, ack_bytes

    def send_data_with_ack(
        self,
        packet: DataPacket,
        max_attempts: int | None = None,
        ack_timeout_s: float | None = None,
    ) -> tuple[bool, str, object | None]:
        payload = encode_packet(packet)
        attempts = max_attempts if max_attempts is not None else self.max_attempts
        timeout_s = ack_timeout_s if ack_timeout_s is not None else self.ack_timeout_s

        for attempt_index in range(attempts):
            self.stats.attempts += 1
            if attempt_index > 0:
                self.stats.retries += 1

            self.radio_manager.send(payload)

            rx = self.radio_manager.receive(timeout_s=timeout_s)
            if rx is None:
                continue

            try:
                reply = decode_packet(rx.payload)
            except Exception:
                continue

            if not isinstance(reply, AckPacket):
                continue

            if reply.frame_id != packet.frame_id:
                continue
            if reply.ack_seq != packet.sequence:
                continue
            if reply.destination_id != packet.source_id:
                continue
            if reply.source_id != packet.destination_id:
                continue

            self.stats.successes += 1
            self.stats.last_rssi = reply.rssi_raw
            self.stats.last_snr = reply.snr_raw

            return True, "ack_received", reply

        return False, "ack_timeout", None

    def forward_with_optional_skip(
        self,
        packet: DataPacket,
        try_primary,
        try_secondary=None,
    ) -> tuple[bool, str, object | None]:
        success, reason, ack = try_primary(packet)
        if success:
            return True, "primary_success", ack

        if try_secondary is not None:
            self.stats.skips += 1
            success, reason, ack = try_secondary(packet)
            if success:
                return True, "secondary_success", ack
            return False, "secondary_failed", ack

        return False, "primary_failed", None