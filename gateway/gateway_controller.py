from __future__ import annotations

import datetime
import time
from pathlib import Path

from common.config.config_loader import load_config, GatewayConfig
from common.frame.slot_scheduler import SlotScheduler
from common.protocol.ack_packet import AckPacket, ACK_FLAG_ACCEPTED
from common.protocol.data_packet import DataPacket
from common.protocol.packet_decoder import decode_packet
from common.protocol.packet_encoder import encode_packet
from common.protocol.timesync_packet import TimeSyncPacket
from common.radio.radio_manager import RadioManager
from common.radio.sx1262_driver import SX1262Driver, SX1262Config
from common.storage.data_logger import DataLogger
from common.storage.event_log import EventLog
from common.time.clock_manager import ClockManager


# ---------------------------------------------------------------------
# Network topology for current 4-station deployment
# ---------------------------------------------------------------------
STATION_NAMES = {
    0: "Hub",
    1: "N1",
    2: "N2",
    3: "N3",
    4: "N4",
}

EXPECTED_FINAL_SOURCE_ID = 4
EXPECTED_STATION_IDS = {1, 2, 3, 4}
EXPECTED_RECORD_COUNT = 4


GATEWAY_DATA_FIELDS = [
    "gateway_rx_unix",
    "gateway_rx_iso",
    "frame_id",
    "frame_start_unix",
    "frame_start_iso",
    "sequence",
    "source_id",
    "source_name",
    "destination_id",
    "destination_name",
    "hop_count",
    "record_count",
    "station_id",
    "station_name",
    "flags",
    "pms_1_ugm3",
    "pms_25_ugm3",
    "opc_10_ugm3",
    "opc_20_ugm3",
    "opc_40_ugm3",
    "bme_t_c",
    "bme_h_pct",
    "bme_p_hpa",
    "win_s",
    "win_d_deg",
    "min_batt_v",
    "max_opc10_ugm3",
    "max_opc20_ugm3",
    "max_opc40_ugm3",
    "max_wind_speed",
    "frame_complete",
    "missing_station_ids",
]


class GatewayController:
    def __init__(self, config_path: str | Path):
        self.config: GatewayConfig = load_config(config_path)  # type: ignore

        self.scheduler = SlotScheduler(
            frame_length_s=self.config.frame_length_s,
            slot_length_s=self.config.slot_length_s,
            phase_b_start_offset_s=self.config.phase_b_start_offset_s,
            station_count=self.config.station_count,
        )

        self.clock_manager = ClockManager()

        driver_config = SX1262Config(
            frequency_hz=self.config.frequency_hz,
            sf=self.config.default_radio_mode.sf,
            bw=self.config.default_radio_mode.bw,
            cr=self.config.default_radio_mode.cr,
            tx_power=self.config.default_radio_mode.tx_power,
            preamble=self.config.default_radio_mode.preamble,
        )

        self.radio_manager = RadioManager(SX1262Driver(driver_config))

        # Daily files on gateway only
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

        data_file = Path(f"gateway/logs/data/received_frames_{today}.csv")
        event_file = Path(f"gateway/logs/events/events_{today}.jsonl")

        data_file.parent.mkdir(parents=True, exist_ok=True)
        event_file.parent.mkdir(parents=True, exist_ok=True)

        self.data_logger = DataLogger(
            data_file,
            fieldnames=GATEWAY_DATA_FIELDS,
        )

        self.event_log = EventLog(event_file)

        self._last_frame_processed: int | None = None
        self._last_timesync_sent_for_frame: int | None = None

    def initialize(self) -> None:
        self.radio_manager.initialize()
        self.radio_manager.apply_mode(self.config.default_radio_mode)

        self.event_log.info(
            "gateway_init",
            "Gateway initialized",
            {
                "node_id": self.config.node_id,
                "node_name": STATION_NAMES.get(self.config.node_id, f"Node{self.config.node_id}"),
                "frequency_hz": self.config.frequency_hz,
                "radio_mode": self.config.default_radio_mode.name,
                "station_count": self.config.station_count,
                "slot_length_s": self.config.slot_length_s,
                "phase_b_start_offset_s": self.config.phase_b_start_offset_s,
            },
        )

    def run_forever(self) -> None:
        self.initialize()

        while True:
            now = self.clock_manager.now_unix()
            frame_id = self.scheduler.frame_id(now)

            if self.scheduler.is_phase_a(now):
                self._run_phase_a(frame_id)

            elif self.scheduler.is_phase_b(now):
                self._run_phase_b(frame_id)

            time.sleep(0.2)

    def _run_phase_a(self, frame_id: int) -> None:
        if self._last_frame_processed == frame_id:
            return

        rx = self.radio_manager.receive(timeout_s=1.0)
        if rx is None:
            return

        try:
            packet = decode_packet(rx.payload)
        except Exception as exc:
            self.event_log.warning(
                "gateway_decode_error",
                "Failed to decode incoming packet during Phase A",
                {"error": str(exc)},
            )
            return

        if not isinstance(packet, DataPacket):
            return

        # Ignore DATA not addressed to the hub
        if packet.destination_id != self.config.node_id:
            self.event_log.info(
                "gateway_wrong_destination",
                "Ignoring DATA packet not addressed to this gateway",
                {
                    "frame_id": packet.frame_id,
                    "sequence": packet.sequence,
                    "source_id": packet.source_id,
                    "destination_id": packet.destination_id,
                },
            )
            return

        # ACK any valid DATA packet immediately back to packet source
        ack = AckPacket(
            frame_id=packet.frame_id,
            ack_seq=packet.sequence,
            source_id=self.config.node_id,
            destination_id=packet.source_id,
            rssi_raw=rx.rssi,
            snr_raw=rx.snr,
            ack_flags=ACK_FLAG_ACCEPTED,
        )

        try:
            self.radio_manager.send(encode_packet(ack))
            self.event_log.info(
                "gateway_ack_sent",
                "Sent ACK for received DATA packet",
                {
                    "frame_id": packet.frame_id,
                    "sequence": packet.sequence,
                    "ack_source_id": ack.source_id,
                    "ack_destination_id": ack.destination_id,
                    "rssi": rx.rssi,
                    "snr": rx.snr,
                },
            )
        except Exception as exc:
            self.event_log.warning(
                "gateway_ack_failed",
                "Failed to send ACK for received DATA packet",
                {
                    "frame_id": packet.frame_id,
                    "sequence": packet.sequence,
                    "ack_source_id": ack.source_id,
                    "ack_destination_id": ack.destination_id,
                    "error": str(exc),
                },
            )

        frame_complete, missing_station_ids, record_station_ids = self._evaluate_packet_completeness(packet)

        self.event_log.info(
            "gateway_data_received",
            "Gateway received DATA packet",
            {
                "frame_id": packet.frame_id,
                "sequence": packet.sequence,
                "source_id": packet.source_id,
                "source_name": STATION_NAMES.get(packet.source_id, f"Node{packet.source_id}"),
                "destination_id": packet.destination_id,
                "destination_name": STATION_NAMES.get(packet.destination_id, f"Node{packet.destination_id}"),
                "hop_count": packet.hop_count,
                "record_count": len(packet.records),
                "record_station_ids": record_station_ids,
                "frame_complete": frame_complete,
                "missing_station_ids": missing_station_ids,
                "rssi": rx.rssi,
                "snr": rx.snr,
                "packet_size_bytes": len(rx.payload),
            },
        )

        self._save_data_packet(packet, frame_complete, missing_station_ids)

        # For now, process only the first valid DATA packet seen in the frame.
        # Later, this could keep listening for a more complete packet.
        self._last_frame_processed = frame_id

    def _run_phase_b(self, frame_id: int) -> None:
        if self._last_timesync_sent_for_frame == frame_id:
            return

        next_frame_start_unix = self.scheduler.next_frame_start(self.clock_manager.now_unix())

        # Hub sends TIMESYNC to N4 first in current 4-station chain
        pkt = TimeSyncPacket(
            frame_id=frame_id,
            next_frame_start_unix=next_frame_start_unix,
            source_id=self.config.node_id,
            destination_id=EXPECTED_FINAL_SOURCE_ID,
            hop_count=0,
        )

        try:
            self.radio_manager.send(encode_packet(pkt))
            self.event_log.info(
                "gateway_timesync_sent",
                "Gateway sent TIMESYNC",
                {
                    "frame_id": frame_id,
                    "next_frame_start_unix": next_frame_start_unix,
                    "source_id": pkt.source_id,
                    "destination_id": pkt.destination_id,
                    "packet_size_bytes": len(pkt.pack()),
                },
            )
            self._last_timesync_sent_for_frame = frame_id
        except Exception as exc:
            self.event_log.warning(
                "gateway_timesync_failed",
                "Failed to send TIMESYNC",
                {
                    "frame_id": frame_id,
                    "source_id": pkt.source_id,
                    "destination_id": pkt.destination_id,
                    "error": str(exc),
                },
            )

    def _evaluate_packet_completeness(self, packet: DataPacket) -> tuple[bool, list[int], list[int]]:
        record_station_ids = [record.station_id for record in packet.records]
        record_station_id_set = set(record_station_ids)

        missing_station_ids = sorted(EXPECTED_STATION_IDS - record_station_id_set)

        source_ok = packet.source_id == EXPECTED_FINAL_SOURCE_ID
        count_ok = len(packet.records) == EXPECTED_RECORD_COUNT
        stations_ok = record_station_id_set == EXPECTED_STATION_IDS

        frame_complete = source_ok and count_ok and stations_ok

        return frame_complete, missing_station_ids, record_station_ids

    def _save_data_packet(self, packet: DataPacket, frame_complete: bool, missing_station_ids: list[int]) -> None:
        gateway_rx_unix = self.clock_manager.now_unix()
        gateway_rx_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(gateway_rx_unix))

        frame_start_unix = packet.frame_id * self.config.frame_length_s
        frame_start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(frame_start_unix))

        missing_station_ids_str = ",".join(str(x) for x in missing_station_ids)

        for record in packet.records:
            row = record.to_dict()

            enriched_row = {
                "gateway_rx_unix": gateway_rx_unix,
                "gateway_rx_iso": gateway_rx_iso,
                "frame_id": packet.frame_id,
                "frame_start_unix": frame_start_unix,
                "frame_start_iso": frame_start_iso,
                "sequence": packet.sequence,
                "source_id": packet.source_id,
                "source_name": STATION_NAMES.get(packet.source_id, f"Node{packet.source_id}"),
                "destination_id": packet.destination_id,
                "destination_name": STATION_NAMES.get(packet.destination_id, f"Node{packet.destination_id}"),
                "hop_count": packet.hop_count,
                "record_count": len(packet.records),
                "station_id": row["station_id"],
                "station_name": STATION_NAMES.get(int(row["station_id"]), f"Node{row['station_id']}"),
                "flags": row["flags"],
                "pms_1_ugm3": row["pms_1"],
                "pms_25_ugm3": row["pms_25"],
                "opc_10_ugm3": row["opc_10"],
                "opc_20_ugm3": row["opc_20"],
                "opc_40_ugm3": row["opc_40"],
                "bme_t_c": row["bme_t"],
                "bme_h_pct": row["bme_h"],
                "bme_p_hpa": row["bme_p"],
                "win_s": row["win_s"],
                "win_d_deg": row["win_d"],
                "min_batt_v": row["min_batt"],
                "max_opc10_ugm3": row["max_opc10"],
                "max_opc20_ugm3": row["max_opc20"],
                "max_opc40_ugm3": row["max_opc40"],
                "max_wind_speed": row["max_wind_speed"],
                "frame_complete": frame_complete,
                "missing_station_ids": missing_station_ids_str,
            }

            self.data_logger.log_row(enriched_row)