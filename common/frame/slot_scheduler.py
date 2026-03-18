from dataclasses import dataclass


@dataclass
class SlotScheduler:
    frame_length_s: int = 600
    slot_length_s: int = 30
    phase_b_start_offset_s: int = 480
    station_count: int = 8
    synced_frame_id: int | None = None
    synced_next_frame_start_unix: int | None = None

    def frame_start(self, unix_time: int) -> int:
        return unix_time - (unix_time % self.frame_length_s)

    def frame_id(self, unix_time: int) -> int:
        return unix_time // self.frame_length_s

    def next_frame_start(self, unix_time: int) -> int:
        if self.synced_next_frame_start_unix is not None:
            return self.synced_next_frame_start_unix
        return self.frame_start(unix_time) + self.frame_length_s

    def set_synced_next_frame(self, frame_id: int, next_frame_start_unix: int) -> None:
        self.synced_frame_id = frame_id
        self.synced_next_frame_start_unix = next_frame_start_unix

    def station_slot_start(self, frame_start_unix: int, station_index_zero_based: int) -> int:
        return frame_start_unix + (station_index_zero_based * self.slot_length_s)

    def station_slot_end(self, frame_start_unix: int, station_index_zero_based: int) -> int:
        return self.station_slot_start(frame_start_unix, station_index_zero_based) + self.slot_length_s

    def is_in_station_slot(self, unix_time: int, station_index_zero_based: int) -> bool:
        fs = self.frame_start(unix_time)
        start = self.station_slot_start(fs, station_index_zero_based)
        end = self.station_slot_end(fs, station_index_zero_based)
        return start <= unix_time < end

    def phase_a_window(self, frame_start_unix: int) -> tuple[int, int]:
        return frame_start_unix, frame_start_unix + self.phase_b_start_offset_s

    def phase_b_window(self, frame_start_unix: int) -> tuple[int, int]:
        return frame_start_unix + self.phase_b_start_offset_s, frame_start_unix + self.frame_length_s

    def is_phase_a(self, unix_time: int) -> bool:
        fs = self.frame_start(unix_time)
        start, end = self.phase_a_window(fs)
        return start <= unix_time < end

    def is_phase_b(self, unix_time: int) -> bool:
        fs = self.frame_start(unix_time)
        start, end = self.phase_b_window(fs)
        return start <= unix_time < end