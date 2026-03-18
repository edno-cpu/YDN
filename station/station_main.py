from __future__ import annotations

import sys

from station.station_controller import StationController


def main() -> None:
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "station/configs/config.yaml"

    controller = StationController(config_path)
    controller.run_forever()


if __name__ == "__main__":
    main()
