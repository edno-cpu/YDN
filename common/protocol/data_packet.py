from dataclasses import dataclass
import struct
from typing import List

from common.protocol.packet_types import PACKET_TYPE_DATA
from common.data.record_formats import StationRecord, STATION_RECORD_SIZE


# packet_type, frame_id, sequence, source_id, destination_id, hop_count, record_count
DATA_HEADER_FORMAT = "<BHHBBBB"
DATA_HEADER_SIZE = struct.calcsize(DATA_HEADER_FORMAT)


@dataclass
class DataPacket:
    frame_id: int
    sequence: int
    source_id: int
    destination_id: int
    hop_count: int
    records: List[StationRecord]
    packet_type: int = PACKET_TYPE_DATA

    def pack(self) -> bytes:
        record_count = len(self.records)

        header = struct.pack(
            DATA_HEADER_FORMAT,
            self.packet_type,
            self.frame_id,
            self.sequence,
            self.source_id,
            self.destination_id,
            self.hop_count,
            record_count,
        )

        payload = b"".join(r.pack() for r in self.records)
        return header + payload

    @classmethod
    def unpack(cls, data: bytes):
        if len(data) < DATA_HEADER_SIZE:
            raise ValueError("DATA packet too short for header")

        (
            packet_type,
            frame_id,
            sequence,
            source_id,
            destination_id,
            hop_count,
            record_count,
        ) = struct.unpack(DATA_HEADER_FORMAT, data[:DATA_HEADER_SIZE])

        if packet_type != PACKET_TYPE_DATA:
            raise ValueError(f"Not a DATA packet: {packet_type}")

        expected_size = DATA_HEADER_SIZE + record_count * STATION_RECORD_SIZE
        if len(data) < expected_size:
            raise ValueError("DATA packet truncated")

        offset = DATA_HEADER_SIZE
        records = []

        for _ in range(record_count):
            chunk = data[offset:offset + STATION_RECORD_SIZE]
            record = StationRecord.unpack(chunk)
            records.append(record)
            offset += STATION_RECORD_SIZE

        return cls(
            frame_id=frame_id,
            sequence=sequence,
            source_id=source_id,
            destination_id=destination_id,
            hop_count=hop_count,
            records=records,
        )