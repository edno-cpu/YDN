from station.station_controller import StationController


def main() -> None:
    controller = StationController("station/configs/station_N3.yaml")
    controller.run_forever()


if __name__ == "__main__":
    main()
