from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class RadioMode:
    sf: int
    bw: int
    cr: int
    tx_power: int
    preamble: int


@dataclass(slots=True)
class RadioRxResult:
    payload: bytes
    rssi: int
    snr: int
    received_at_unix: float


class RadioManager:
    def __init__(self, driver):
        self.driver = driver
        self.current_mode: RadioMode | None = None
        self.initialized = False

    def initialize(self) -> None:
        self.driver.begin()
        self.initialized = True

    def set_mode(self, *, sf: int, bw: int, cr: int, tx_power: int, preamble: int) -> None:
        self.driver.set_spreading_factor(sf)
        self.driver.set_bandwidth(bw)
        self.driver.set_coding_rate(cr)
        self.driver.set_tx_power(tx_power)
        self.driver.set_preamble_length(preamble)

        self.current_mode = RadioMode(
            sf=sf,
            bw=bw,
            cr=cr,
            tx_power=tx_power,
            preamble=preamble,
        )

    def apply_mode(self, mode: RadioMode) -> None:
        self.set_mode(
            sf=mode.sf,
            bw=mode.bw,
            cr=mode.cr,
            tx_power=mode.tx_power,
            preamble=mode.preamble,
        )

    def send(self, payload: bytes, wait_for_completion: bool = True, tx_timeout_s: float = 5.0) -> None:
        if not self.initialized:
            raise RuntimeError("RadioManager.send() called before initialize()")

        self.driver.send(payload)

        if not wait_for_completion:
            return

        end_time = time.time() + tx_timeout_s
        while time.time() < end_time:
            if self.driver.packet_sent():
                return
            time.sleep(0.01)

        raise TimeoutError("Radio transmission did not complete before timeout")

    def receive(self, timeout_s: float) -> RadioRxResult | None:
        if not self.initialized:
            raise RuntimeError("RadioManager.receive() called before initialize()")

        self.driver.listen()

        end_time = time.time() + timeout_s
        while time.time() < end_time:
            if self.driver.packet_available():
                payload = self.driver.recv()
                rssi = self.driver.get_rssi()
                snr = self.driver.get_snr()

                return RadioRxResult(
                    payload=payload,
                    rssi=rssi,
                    snr=snr,
                    received_at_unix=time.time(),
                )

            time.sleep(0.01)

        return None

    def standby(self) -> None:
        if not self.initialized:
            raise RuntimeError("RadioManager.standby() called before initialize()")
        self.driver.standby()