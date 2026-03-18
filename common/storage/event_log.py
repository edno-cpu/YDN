from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(slots=True)
class EventEntry:
    ts_utc: str
    level: str
    event_type: str
    message: str
    details: dict


class EventLog:
    """
    Writes operational events as JSON Lines (.jsonl).

    Good for:
    - retries
    - skipped nodes
    - sync updates
    - packet errors
    - boot events
    - radio mode changes
    """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        level: str,
        event_type: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        entry = EventEntry(
            ts_utc=datetime.now(timezone.utc).isoformat(),
            level=level.upper(),
            event_type=event_type,
            message=message,
            details=details or {},
        )

        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")

    def info(self, event_type: str, message: str, details: dict | None = None) -> None:
        self.log("INFO", event_type, message, details)

    def warning(self, event_type: str, message: str, details: dict | None = None) -> None:
        self.log("WARNING", event_type, message, details)

    def error(self, event_type: str, message: str, details: dict | None = None) -> None:
        self.log("ERROR", event_type, message, details)
