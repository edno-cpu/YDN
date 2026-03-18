from common.data.record_formats import STATION_RECORD_SIZE

DATA_HEADER_SIZE = 8
CRC_SIZE = 2

for n in [1, 2, 4, 8]:
    total = DATA_HEADER_SIZE + (n * STATION_RECORD_SIZE) + CRC_SIZE
    print(f"{n} stations: {total} bytes")
