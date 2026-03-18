from dataclasses import dataclass
import time


@dataclass
class FrameConfig:
    frame_length_s: int = 600
    slot_length_s: int = 30
    phase_b_reserved_s: int = 60


@dataclass
class FrameState:
    frame_id: int
    frame_start_unix: int
    frame_end_unix: int


class FrameManager:
    def __init__(self, config: FrameConfig):
        self.config = config

    def compute_frame_start(self, unix_time: int | None = None) -> int:
        if unix_time is None:
            unix_time = int(time.time())
        return unix_time - (unix_time % self.config.frame_length_s)

    def compute_next_frame_start(self, unix_time: int | None = None) -> int:
        return self.compute_frame_start(unix_time) + self.config.frame_length_s

    def frame_id_from_time(self, unix_time: int | None = None) -> int:
        if unix_time is None:
            unix_time = int(time.time())
        return unix_time // self.config.frame_length_s

    def current_frame_state(self, unix_time: int | None = None) -> FrameState:
        if unix_time is None:
            unix_time = int(time.time())

        frame_start = self.compute_frame_start(unix_time)
        frame_id = self.frame_id_from_time(unix_time)

        return FrameState(
            frame_id=frame_id,
            frame_start_unix=frame_start,
            frame_end_unix=frame_start + self.config.frame_length_s,
        )

    def slot_start_for_station(self, frame_start_unix: int, station_index_zero_based: int) -> int:
        return frame_start_unix + (station_index_zero_based * self.config.slot_length_s)

    def slot_end_for_station(self, frame_start_unix: int, station_index_zero_based: int) -> int:
        return self.slot_start_for_station(frame_start_unix, station_index_zero_based) + self.config.slot_length_s

    def next_frame_start_from_sync(self, sync_packet) -> int:
        return sync_packet.next_frame_start_unix
