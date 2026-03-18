from __future__ import annotations

from dataclasses import dataclass

from SX126x import SX126x


@dataclass(slots=True)
class SX1262Config:
    frequency_hz: int = 915_000_000
    sf: int = 9
    bw: int = 125_000
    cr: int = 5
    tx_power: int = 14
    preamble: int = 8
    sync_word: int = SX126x.LORA_SYNC_WORD_PRIVATE
    crc_on: bool = True

    spi_bus: int = SX126x.DEFAULT_SPI_BUS
    spi_device: int = SX126x.DEFAULT_SPI_DEVICE
    reset_pin: int = SX126x.DEFAULT_RESET_PIN
    busy_pin: int = SX126x.DEFAULT_BUSY_PIN
    irq_pin: int = SX126x.DEFAULT_IRQ_PIN
    txen_pin: int = SX126x.DEFAULT_TXEN_PIN


class SX1262Driver:
    """
    Adapter around the existing SX126x class.

    This exposes a stable API to the rest of the project:
      - begin()
      - set_spreading_factor()
      - set_bandwidth()
      - set_coding_rate()
      - set_tx_power()
      - set_preamble_length()
      - send()
      - packet_available()
      - recv()
      - get_rssi()
      - get_snr()
    """

    def __init__(self, config: SX1262Config | None = None):
        self.config = config or SX1262Config()
        self.radio = SX126x()

    def begin(self) -> None:
        ok = self.radio.begin(
            spibus=self.config.spi_bus,
            spidev=self.config.spi_device,
            reset_pin=self.config.reset_pin,
            busy_pin=self.config.busy_pin,
            irq_pin=self.config.irq_pin,
            txen_pin=self.config.txen_pin,
        )

        if ok is False:
            raise RuntimeError("SX126x.begin() failed")

        self.radio.setFrequency(self.config.frequency_hz)
        self.radio.setSpreadingFactor(self.config.sf)
        self.radio.setBandwidth(self.config.bw)
        self.radio.setCodeRate(self.config.cr)
        self.radio.setTxPower(self.config.tx_power)
        self.radio.setPreambleLength(self.config.preamble)
        self.radio.setSyncWord(self.config.sync_word)
        self.radio.setCrcEnable(self.config.crc_on)

    def set_spreading_factor(self, sf: int) -> None:
        self.config.sf = sf
        self.radio.setSpreadingFactor(sf)

    def set_bandwidth(self, bw: int) -> None:
        self.config.bw = bw
        self.radio.setBandwidth(bw)

    def set_coding_rate(self, cr: int) -> None:
        self.config.cr = cr
        self.radio.setCodeRate(cr)

    def set_tx_power(self, tx_power: int) -> None:
        self.config.tx_power = tx_power
        self.radio.setTxPower(tx_power)

    def set_preamble_length(self, preamble: int) -> None:
        self.config.preamble = preamble
        self.radio.setPreambleLength(preamble)

    def set_frequency(self, frequency_hz: int) -> None:
        self.config.frequency_hz = frequency_hz
        self.radio.setFrequency(frequency_hz)

    def set_sync_word(self, sync_word: int) -> None:
        self.config.sync_word = sync_word
        self.radio.setSyncWord(sync_word)

    def set_crc(self, enabled: bool) -> None:
        self.config.crc_on = enabled
        self.radio.setCrcEnable(enabled)

    def send(self, payload: bytes) -> None:
        self.radio.send_packet(payload)

    def packet_sent(self) -> bool:
        return self.radio.packet_sent()

    def listen(self) -> None:
        self.radio.listen()

    def packet_available(self) -> bool:
        return self.radio.packet_available()

    def recv(self) -> bytes:
        return self.radio.read_packet()

    def get_rssi(self) -> int:
        return int(round(self.radio.packetRssi()))

    def get_snr(self) -> int:
        return int(round(self.radio.packetSnr()))

    def standby(self) -> None:
        self.radio.standby()

    def get_errors(self) -> dict:
        return getattr(self.radio, "errors", {})