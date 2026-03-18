from __future__ import annotations

import time
from pathlib import Path

from common.config.config_loader import load_config, StationConfig
from common.config.radio_modes import (
    MODE_A_FAST,
    MODE_B_OKAY,
    MODE_C_POOR,
    MODE_D_VERY_POOR,
)
from common.frame.slot_scheduler import SlotScheduler
from common.link.link_manager import LinkManager
from common.protocol.data_packet import DataPacket
from common.protocol.packet_decoder import decode_packet
from common.protocol.sequence_cache import SequenceCache
from common.protocol.timesync_packet import TimeSyncPacket
from common.radio.radio_manager import RadioManager
from common.radio.sx1262_driver import SX1262Driver, SX1262Config
from common.storage.data_logger import (
    DataLogger,
    ONE_MINUTE_FIELDS,
    TEN_MINUTE_TX_FIELDS,
)
from common.storage.event_log import EventLog
from common.time.clock_manager import ClockManager
from common.time.timesync import TimeSyncManager

from station.sensors.sensor_manager import SensorManager
from station.tasks.build_10min_record import TenMinuteRecordBuilder
from station.tasks.collect_1min import OneMinuteCollector


class StationController:
    DATA_ATTEMPTS_PRIMARY = 3
    DATA_ATTEMPTS_SECONDARY = 3
    DATA_ACK_TIMEOUT_S = 1.5

    def __init__(self, config_path: str | Path):
        self.config: StationConfig = load_config(config_path)  # type: ignore

        self.scheduler = SlotScheduler(
            frame_length_s=self.config.frame_length_s,
            slot_length_s=self.config.slot_length_s,
            phase_b_start_offset_s=self.config.phase_b_start_offset_s,
            station_count=self.config.station_count,
        )

        self.clock_manager = ClockManager()

        self.timesync_manager = TimeSyncManager(
            station_id=self.config.node_id,
            clock_manager=self.clock_manager,
            scheduler=self.scheduler,
        )

        driver_config = SX1262Config(
            frequency_hz=self.config.frequency_hz,
            sf=self.config.default_radio_mode.sf,
            bw=self.config.default_radio_mode.bw,
            cr=self.config.default_radio_mode.cr,
            tx_power=self.config.default_radio_mode.tx_power,
            preamble=self.config.default_radio_mode.preamble,
        )

        self.radio_manager = RadioManager(SX1262Driver(driver_config))
        self.sequence_cache = SequenceCache(max_size=100)

        self.link_manager = LinkManager(
            node_id=self.config.node_id,
            radio_manager=self.radio_manager,
            sequence_cache=self.sequence_cache,
            max_attempts=self.DATA_ATTEMPTS_PRIMARY,
            ack_timeout_s=self.DATA_ACK_TIMEOUT_S,
        )

        self.data_logger = DataLogger(
            "station/logs/one_minute_data.csv",
            fieldnames=ONE_MINUTE_FIELDS,
        )

        self.tx_summary_logger = DataLogger(
            "station/logs/tx_summary.csv",
            fieldnames=TEN_MINUTE_TX_FIELDS,
        )

        self.event_log = EventLog("station/logs/events.jsonl")

        self.sensor_manager = SensorManager()

        self.collector = OneMinuteCollector(
            station_id=self.config.node_id,
            clock_manager=self.clock_manager,
            data_logger=self.data_logger,
            sensor_manager=self.sensor_manager,
        )

        self.record_builder = TenMinuteRecordBuilder(
            station_id=self.config.node_id,
            collector=self.collector,
        )

        self._last_phase_a_frame_sent: int | None = None
        self._last_phase_b_frame_seen: int | None = None
        self._sequence_counter: int = 0

        # Per-neighbor current radio mode
        self.neighbor_modes: dict[int, object] = {}
        for neighbor in [
            self.config.primary_downstream,
            self.config.secondary_downstream,
            self.config.primary_upstream,
            self.config.secondary_upstream,
        ]:
            if neighbor is not None:
                self.neighbor_modes[neighbor] = self.config.default_radio_mode

    def initialize(self) -> None:
        self.sensor_manager.initialize()
        self.radio_manager.initialize()
        self.radio_manager.apply_mode(self.config.default_radio_mode)

        self.event_log.info(
            "station_init",
            "Station initialized",
            {
                "node_id": self.config.node_id,
                "station_index": self.config.station_index,
                "primary_downstream": self.config.primary_downstream,
                "secondary_downstream": self.config.secondary_downstream,
                "primary_upstream": self.config.primary_upstream,
                "secondary_upstream": self.config.secondary_upstream,
                "frequency_hz": self.config.frequency_hz,
                "radio_mode": self.config.default_radio_mode.name,
                "slot_length_s": self.config.slot_length_s,
                "phase_b_start_offset_s": self.config.phase_b_start_offset_s,
                "data_attempts_primary": self.DATA_ATTEMPTS_PRIMARY,
                "data_attempts_secondary": self.DATA_ATTEMPTS_SECONDARY,
                "data_ack_timeout_s": self.DATA_ACK_TIMEOUT_S,
            },
        )

    def run_forever(self) -> None:
        self.initialize()

        while True:
            now = self.clock_manager.now_unix()
            frame_id = self.scheduler.frame_id(now)

            self.collector.maybe_collect_minute(frame_id=frame_id)

            if self.scheduler.is_phase_a(now):
                self._run_phase_a(now, frame_id)
            elif self.scheduler.is_phase_b(now):
                self._run_phase_b(now, frame_id)

            time.sleep(0.2)

    def _run_phase_a(self, now: int, frame_id: int) -> None:
        if self._last_phase_a_frame_sent == frame_id:
            return

        if not self.scheduler.is_in_station_slot(now, self.config.station_index):
            return

        local_record = self.record_builder.build_for_frame(frame_id)
        upstream_packet = self._listen_for_upstream_data(listen_timeout_s=2.0)

        outgoing_packet = self._build_outgoing_data_packet(
            frame_id=frame_id,
            local_record=local_record,
            upstream_packet=upstream_packet,
        )

        success, reason, ack = self.link_manager.forward_with_optional_skip(
            packet=outgoing_packet,
            try_primary=self._try_primary_downstream,
            try_secondary=self._try_secondary_downstream if self.config.secondary_downstream is not None else None,
        )

        tx_route_used = "failed"
        if reason == "primary_success":
            tx_route_used = "primary"
        elif reason == "secondary_success":
            tx_route_used = "secondary"

        self._log_tx_summary(
            frame_id=frame_id,
            sequence=outgoing_packet.sequence,
            station_record=local_record,
            tx_attempted=True,
            tx_success=success,
            tx_route_used=tx_route_used,
        )

        if success:
            if ack is not None:
                self._update_neighbor_mode_from_ack(ack.source_id, ack.rssi_raw, ack.snr_raw)

            self.event_log.info(
                "phase_a_send_success",
                "DATA packet forwarded successfully",
                {
                    "frame_id": frame_id,
                    "sequence": outgoing_packet.sequence,
                    "reason": reason,
                    "ack_source_id": getattr(ack, "source_id", None),
                    "ack_rssi": getattr(ack, "rssi_raw", None),
                    "ack_snr": getattr(ack, "snr_raw", None),
                },
            )
            self._last_phase_a_frame_sent = frame_id
            self.collector.clear_rows_before_frame(frame_id)
        else:
            self.event_log.warning(
                "phase_a_send_failed",
                "DATA packet forwarding failed",
                {
                    "frame_id": frame_id,
                    "sequence": outgoing_packet.sequence,
                    "reason": reason,
                },
            )

    def _run_phase_b(self, now: int, frame_id: int) -> None:
        if self._last_phase_b_frame_seen == frame_id:
            return

        rx = self.radio_manager.receive(timeout_s=1.0)
        if rx is None:
            return

        try:
            pkt = decode_packet(rx.payload)
        except Exception as exc:
            self.event_log.warning(
                "phase_b_decode_error",
                "Failed to decode Phase B packet",
                {"error": str(exc)},
            )
            return

        if not isinstance(pkt, TimeSyncPacket):
            return

        if pkt.destination_id != self.config.node_id:
            return

        result, _ = self.timesync_manager.handle_packet(pkt)

        success, reason = self._forward_timesync_upstream(pkt)

        if success:
            self.event_log.info(
                "timesync_forwarded",
                "Forwarded TIMESYNC upstream",
                {
                    "frame_id": result.frame_id,
                    "reason": reason,
                    "offset_seconds": result.offset_seconds,
                },
            )
        else:
            self.event_log.warning(
                "timesync_forward_failed",
                "Failed to forward TIMESYNC upstream",
                {
                    "frame_id": result.frame_id,
                    "reason": reason,
                },
            )

        self._last_phase_b_frame_seen = frame_id

    def _listen_for_upstream_data(self, listen_timeout_s: float) -> DataPacket | None:
        rx = self.radio_manager.receive(timeout_s=listen_timeout_s)
        if rx is None:
            return None

        accepted, reason, packet, ack_bytes = self.link_manager.receive_data_and_build_ack(
            packet_bytes=rx.payload,
            rssi_raw=rx.rssi,
            snr_raw=rx.snr,
        )

        if not accepted:
            return None

        if ack_bytes is not None:
            self.radio_manager.send(ack_bytes)

        return packet

    def _build_outgoing_data_packet(self, frame_id: int, local_record, upstream_packet: DataPacket | None) -> DataPacket:
        self._sequence_counter = (self._sequence_counter + 1) % 65536

        if upstream_packet is None:
            destination_id = self.config.primary_downstream if self.config.primary_downstream is not None else 0
            return DataPacket(
                frame_id=frame_id,
                sequence=self._sequence_counter,
                source_id=self.config.node_id,
                destination_id=destination_id,
                hop_count=0,
                records=[local_record],
            )

        return DataPacket(
            frame_id=frame_id,
            sequence=self._sequence_counter,
            source_id=self.config.node_id,
            destination_id=self.config.primary_downstream if self.config.primary_downstream is not None else 0,
            hop_count=upstream_packet.hop_count + 1,
            records=[*upstream_packet.records, local_record],
        )

    def _try_primary_downstream(self, packet: DataPacket):
        if self.config.primary_downstream is None:
            return False, "no_primary_downstream", None

        packet.destination_id = self.config.primary_downstream
        self._apply_neighbor_mode(self.config.primary_downstream)

        return self.link_manager.send_data_with_ack(
            packet,
            max_attempts=self.DATA_ATTEMPTS_PRIMARY,
            ack_timeout_s=self.DATA_ACK_TIMEOUT_S,
        )

    def _try_secondary_downstream(self, packet: DataPacket):
        if self.config.secondary_downstream is None:
            return False, "no_secondary_downstream", None

        packet.destination_id = self.config.secondary_downstream
        self._apply_neighbor_mode(self.config.secondary_downstream)

        return self.link_manager.send_data_with_ack(
            packet,
            max_attempts=self.DATA_ATTEMPTS_SECONDARY,
            ack_timeout_s=self.DATA_ACK_TIMEOUT_S,
        )

    def _forward_timesync_upstream(self, incoming_packet: TimeSyncPacket) -> tuple[bool, str]:
        if self.config.primary_upstream is None:
            return True, "no_upstream_needed"

        primary_packet = incoming_packet.forwarded(
            new_source_id=self.config.node_id,
            new_destination_id=self.config.primary_upstream,
        )

        try:
            self._apply_neighbor_mode(self.config.primary_upstream)
            self.radio_manager.send(primary_packet.pack())
            return True, "primary_upstream_success"
        except Exception:
            pass

        if self.config.secondary_upstream is not None:
            secondary_packet = incoming_packet.forwarded(
                new_source_id=self.config.node_id,
                new_destination_id=self.config.secondary_upstream,
            )
            try:
                self._apply_neighbor_mode(self.config.secondary_upstream)
                self.radio_manager.send(secondary_packet.pack())
                return True, "secondary_upstream_success"
            except Exception:
                return False, "secondary_upstream_failed"

        return False, "primary_upstream_failed"

    def _apply_neighbor_mode(self, neighbor_id: int) -> None:
        mode = self.neighbor_modes.get(neighbor_id, self.config.default_radio_mode)
        self.radio_manager.apply_mode(mode)

    def _update_neighbor_mode_from_ack(self, neighbor_id: int, rssi_raw: int, snr_raw: int) -> None:
        if rssi_raw >= -85 and snr_raw >= 10:
            mode = MODE_A_FAST
        elif rssi_raw >= -95 and snr_raw >= 5:
            mode = MODE_B_OKAY
        elif rssi_raw >= -105 and snr_raw >= 0:
            mode = MODE_C_POOR
        else:
            mode = MODE_D_VERY_POOR

        self.neighbor_modes[neighbor_id] = mode

    def _log_tx_summary(
        self,
        frame_id: int,
        sequence: int,
        station_record,
        tx_attempted: bool,
        tx_success: bool,
        tx_route_used: str,
    ) -> None:
        row = station_record.to_dict()

        frame_start_unix = frame_id * self.config.frame_length_s
        frame_start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(frame_start_unix))

        self.tx_summary_logger.log_row(
            {
                "frame_id": frame_id,
                "frame_start_unix": frame_start_unix,
                "frame_start_iso": frame_start_iso,
                "station_id": row["station_id"],
                "flags": row["flags"],
                "pms_1": row["pms_1"],
                "pms_25": row["pms_25"],
                "opc_10": row["opc_10"],
                "opc_20": row["opc_20"],
                "opc_40": row["opc_40"],
                "bme_t": row["bme_t"],
                "bme_h": row["bme_h"],
                "bme_p": row["bme_p"],
                "win_s": row["win_s"],
                "win_d": row["win_d"],
                "min_batt": row["min_batt"],
                "max_opc10": row["max_opc10"],
                "max_opc20": row["max_opc20"],
                "max_opc40": row["max_opc40"],
                "max_wind_speed": row["max_wind_speed"],
                "tx_attempted": int(tx_attempted),
                "tx_success": int(tx_success),
                "tx_route_used": tx_route_used,
                "sequence": sequence,
            }
        )