from common.radio.radio_manager import RadioManager
from common.radio.sx1262_driver import SX1262Driver, SX1262Config


class MockSX126x:
    def __init__(self):
        self.queue = []
        self.rssi = -87
        self.snr = 9

    def begin(self):
        pass

    def setFrequency(self, hz):
        self.frequency = hz

    def setSpreadingFactor(self, sf):
        self.sf = sf

    def setBandwidth(self, bw):
        self.bw = bw

    def setCodingRate(self, cr):
        self.cr = cr

    def setTxPower(self, p):
        self.tx_power = p

    def setPreambleLength(self, p):
        self.preamble = p

    def send(self, payload: bytes):
        self.last_sent = payload

    def available(self):
        return len(self.queue) > 0

    def read(self):
        return self.queue.pop(0)

    def getRSSI(self):
        return self.rssi

    def getSNR(self):
        return self.snr


def main():
    mock = MockSX126x()
    driver = SX1262Driver(mock, SX1262Config())
    radio = RadioManager(driver)

    radio.initialize()
    radio.set_mode(sf=9, bw=125000, cr=5, tx_power=14, preamble=8)

    radio.send(b"hello")
    print("Last sent:", mock.last_sent)

    mock.queue.append(b"reply")
    rx = radio.receive(timeout_s=0.1)
    print("Received:", rx)


if __name__ == "__main__":
    main()
