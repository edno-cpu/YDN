from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Any

import yaml

from common.config.radio_modes import RADIO_MODES, RadioMode


RoleType = Literal["station", "gateway"]


@dataclass(slots=True)
class BaseConfig:
    role: RoleType
    node_id: int
    frequency_hz: int
    default_radio_mode: RadioMode
    frame_length_s: int
    slot_length_s: int
    phase_b_start_offset_s: int


@dataclass(slots=True)
class StationConfig(BaseConfig):
    station_index: int
    station_count: int
    primary_downstream: int | None
    secondary_downstream: int | None
    primary_upstream: int | None
    secondary_upstream: int | None


@dataclass(slots=True)
class GatewayConfig(BaseConfig):
    station_count: int


def load_config(path: str | Path) -> BaseConfig:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a top-level mapping")

    role = raw.get("role")
    if role not in ("station", "gateway"):
        raise ValueError("Config field 'role' must be 'station' or 'gateway'")

    if role == "station":
        return _build_station_config(raw)

    return _build_gateway_config(raw)


def _build_station_config(raw: dict[str, Any]) -> StationConfig:
    _require_fields(
        raw,
        [
            "role",
            "node_id",
            "frequency_hz",
            "default_radio_mode",
            "frame_length_s",
            "slot_length_s",
            "phase_b_start_offset_s",
            "station_count",
        ],
    )

    node_id = _as_int(raw["node_id"], "node_id")
    station_count = _as_int(raw["station_count"], "station_count")

    if node_id < 1 or node_id > station_count:
        raise ValueError(
            f"Station node_id must be between 1 and station_count ({station_count}), got {node_id}"
        )

    topology = _derive_station_topology(node_id=node_id, station_count=station_count)

    return StationConfig(
        role="station",
        node_id=node_id,
        frequency_hz=_as_int(raw["frequency_hz"], "frequency_hz"),
        default_radio_mode=_lookup_radio_mode(raw["default_radio_mode"]),
        frame_length_s=_as_int(raw["frame_length_s"], "frame_length_s"),
        slot_length_s=_as_int(raw["slot_length_s"], "slot_length_s"),
        phase_b_start_offset_s=_as_int(raw["phase_b_start_offset_s"], "phase_b_start_offset_s"),
        station_index=topology["station_index"],
        station_count=station_count,
        primary_downstream=topology["primary_downstream"],
        secondary_downstream=topology["secondary_downstream"],
        primary_upstream=topology["primary_upstream"],
        secondary_upstream=topology["secondary_upstream"],
    )


def _build_gateway_config(raw: dict[str, Any]) -> GatewayConfig:
    _require_fields(
        raw,
        [
            "role",
            "node_id",
            "frequency_hz",
            "default_radio_mode",
            "frame_length_s",
            "slot_length_s",
            "phase_b_start_offset_s",
            "station_count",
        ],
    )

    node_id = _as_int(raw["node_id"], "node_id")
    if node_id != 0:
        raise ValueError("Gateway node_id must be 0")

    return GatewayConfig(
        role="gateway",
        node_id=node_id,
        frequency_hz=_as_int(raw["frequency_hz"], "frequency_hz"),
        default_radio_mode=_lookup_radio_mode(raw["default_radio_mode"]),
        frame_length_s=_as_int(raw["frame_length_s"], "frame_length_s"),
        slot_length_s=_as_int(raw["slot_length_s"], "slot_length_s"),
        phase_b_start_offset_s=_as_int(raw["phase_b_start_offset_s"], "phase_b_start_offset_s"),
        station_count=_as_int(raw["station_count"], "station_count"),
    )


def _derive_station_topology(node_id: int, station_count: int) -> dict[str, int | None]:
    station_index = node_id - 1

    # Downstream
    if node_id < station_count:
        primary_downstream = node_id + 1
    else:
        primary_downstream = 0  # hub

    if node_id + 2 <= station_count:
        secondary_downstream = node_id + 2
    elif node_id + 1 == station_count:
        secondary_downstream = 0  # skip directly to hub
    else:
        secondary_downstream = None

    # Upstream
    if node_id > 1:
        primary_upstream = node_id - 1
    else:
        primary_upstream = None

    if node_id - 2 >= 1:
        secondary_upstream = node_id - 2
    else:
        secondary_upstream = None

    return {
        "station_index": station_index,
        "primary_downstream": primary_downstream,
        "secondary_downstream": secondary_downstream,
        "primary_upstream": primary_upstream,
        "secondary_upstream": secondary_upstream,
    }


def _lookup_radio_mode(name: Any) -> RadioMode:
    if not isinstance(name, str):
        raise ValueError("default_radio_mode must be a string")

    if name not in RADIO_MODES:
        valid = ", ".join(RADIO_MODES.keys())
        raise ValueError(f"Unknown radio mode '{name}'. Valid modes: {valid}")

    return RADIO_MODES[name]


def _require_fields(raw: dict[str, Any], field_names: list[str]) -> None:
    missing = [name for name in field_names if name not in raw]
    if missing:
        raise ValueError(f"Missing required config field(s): {', '.join(missing)}")


def _as_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"Config field '{field_name}' must be an integer")
    return value