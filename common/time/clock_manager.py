from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class ClockStatus:
    local_time_unix: int
    offset_seconds: int
    action: str


class ClockManager:
    """
    Version 1 clock manager.

    For now this uses system time as the active clock source.
    Later it can be extended to:
    - read from an RTC module
    - write corrected time back to RTC
    - distinguish between RTC time and system time
    """

    def now_unix(self) -> int:
        return int(time.time())

    def set_time_unix(self, unix_time: int) -> None:
        """
        Placeholder for future system/RTC time setting.
        In Version 1 we do not directly step system time here.
        """
        # Later:
        # - update RTC
        # - optionally update system clock
        pass

    def apply_frame_sync(
        self,
        next_frame_start_unix: int,
        small_step_threshold_s: int = 2,
    ) -> ClockStatus:
        """
        Compare local time to network timing and decide what kind of correction
        would be appropriate.

        Version 1 behavior:
        - does not actually change system time
        - reports what should happen
        """
        local_now = self.now_unix()
        offset = next_frame_start_unix - local_now

        if abs(offset) <= small_step_threshold_s:
            action = "aligned_or_small_correction"
        else:
            action = "large_correction"

        return ClockStatus(
            local_time_unix=local_now,
            offset_seconds=offset,
            action=action,
        )
