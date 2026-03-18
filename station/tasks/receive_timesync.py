from __future__ import annotations

import time
from dataclasses import dataclass

from common.protocol.timesync_packet import TimeSyncPacket


@dataclass(slots=True)
class SyncResult:
    received_frame_id: int
    next_frame_start_unix: int
    local_time_unix: int
    offset_seconds: int
    action: str


class StationScheduler:
    """
    Minimal scheduler placeholder.

    Later this can manage:
    - current frame ID
    - next frame start time
    - slot timing
    - phase timing
    """

    def __init__(self) -> None:
        self.next_frame_start_unix: int | None = None
        self.current_frame_id: int | None = None

    def update_from_timesync(self, frame_id: int, next_frame_start_unix: int) -> None:
        self.current_frame_id = frame_id
        self.next_frame_start_unix = next_frame_start_unix


class TimeSource:
    """
    Wrapper around current time.

    Later this can be replaced with:
    - RTC read
    - RTC + system time comparison
    - slewing/step correction logic
    """

    def now_unix(self) -> int:
        return int(time.time())


class TimeSyncHandler:
    def __init__(
        self,
        station_id: int,
        scheduler: StationScheduler,
        time_source: TimeSource,
        small_step_threshold_s: int = 2,
    ) -> None:
        self.station_id = station_id
        self.scheduler = scheduler
        self.time_source = time_source
        self.small_step_threshold_s = small_step_threshold_s

    def handle_timesync(self, packet_bytes: bytes) -> tuple[SyncResult, bytes]:
        """
        Decode a TIMESYNC packet, update local scheduler, and prepare a forwarded copy.
        Returns:
            (sync_result, forwarded_packet_bytes)
        """
        pkt = TimeSyncPacket.unpack(packet_bytes)

        local_now = self.time_source.now_unix()
        offset = pkt.next_frame_start_unix - local_now

        # Version 1:
        # Keep it simple and just adopt the hub's next frame start.
        # Later this can become:
        # - small offset -> slew
        # - large offset -> hard step
        self.scheduler.update_from_timesync(
            frame_id=pkt.frame_id,
            next_frame_start_unix=pkt.next_frame_start_unix,
        )

        if abs(offset) <= self.small_step_threshold_s:
            action = "aligned_or_small_correction"
        else:
            action = "large_correction"

        forwarded_pkt = pkt.forwarded(new_sender_id=self.station_id)
        forwarded_bytes = forwarded_pkt.pack()

        result = SyncResult(
            received_frame_id=pkt.frame_id,
            next_frame_start_unix=pkt.next_frame_start_unix,
            local_time_unix=local_now,
            offset_seconds=offset,
            action=action,
        )

        return result, forwarded_bytes
