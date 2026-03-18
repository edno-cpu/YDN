from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OPCN3Reading:
    opc_10: float | None
    opc_20: float | None
    opc_40: float | None
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "opc_10": self.opc_10,
            "opc_20": self.opc_20,
            "opc_40": self.opc_40,
        }


class OPCN3Sensor:
    """
    Stub OPC-N3 interface.

    Replace `read()` with real SPI/UART logic later, depending on your setup.
    """

    def __init__(self, port: str | None = None):
        self.port = port

    def initialize(self) -> None:
        pass

    def read(self) -> OPCN3Reading:
        return OPCN3Reading(
            opc_10=0.0,
            opc_20=0.0,
            opc_40=0.0,
            ok=True,
            error=None,
        )
