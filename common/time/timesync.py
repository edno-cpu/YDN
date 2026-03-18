from __future__ import annotations

from dataclasses import dataclass

from common.protocol.timesync_packet import TimeSyncPacket
from common.time.clock_manager import ClockManager, ClockStatus


@dataclass(slots=True)
class TimeSyncResult:
    frame_id: int
    next_frame_start_unix: int
    local_time_unix: int
    offset_seconds: int
    action: str


class TimeSyncManager:
    """
    Handles incoming TIMESYNC packets.

    Responsibilities:
    - decode packet meaning
    - compare to local clock
    - update scheduler
    - prepare forwarded packet
    """

    def __init__(self, station_id: int, clock_manager: ClockManager, scheduler):
        self.station_id = station_id
        self.clock_manager = clock_manager
        self.scheduler = scheduler

    def handle_packet(self, packet: TimeSyncPacket) -> tuple[TimeSyncResult, TimeSyncPacket]:
        """
        Process a received TIMESYNC packet and prepare the forwarded copy.
        """
        clock_status: ClockStatus = self.clock_manager.apply_frame_sync(
            next_frame_start_unix=packet.next_frame_start_unix
        )

        # Update local scheduler to follow the hub's real next frame start
        if hasattr(self.scheduler, "set_synced_next_frame"):
            self.scheduler.set_synced_next_frame(
                frame_id=packet.frame_id,
                next_frame_start_unix=packet.next_frame_start_unix,
            )

        forwarded_packet = packet.forwarded(new_sender_id=self.station_id)

        result = TimeSyncResult(
            frame_id=packet.frame_id,
            next_frame_start_unix=packet.next_frame_start_unix,
            local_time_unix=clock_status.local_time_unix,
            offset_seconds=clock_status.offset_seconds,
            action=clock_status.action,
        )

        return result, forwarded_packet
