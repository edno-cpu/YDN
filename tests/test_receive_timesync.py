# YDN/tests/test_receive_timesync.py

from station.tasks.receive_timesync import (
    StationScheduler,
    TimeSource,
    TimeSyncHandler,
)
from common.protocol.timesync_packet import TimeSyncPacket


def main() -> None:
    scheduler = StationScheduler()
    time_source = TimeSource()
    handler = TimeSyncHandler(
        station_id=7,
        scheduler=scheduler,
        time_source=time_source,
    )

    incoming = TimeSyncPacket(
        frame_id=101,
        next_frame_start_unix=1763503800,
        sender_id=0,   # hub
        hop_count=0,
    ).pack()

    result, forwarded = handler.handle_timesync(incoming)

    print("Result:", result)
    print("Scheduler frame_id:", scheduler.current_frame_id)
    print("Scheduler next_frame_start_unix:", scheduler.next_frame_start_unix)
    print("Forwarded bytes:", forwarded.hex(" "))


if __name__ == "__main__":
    main()
