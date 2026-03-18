from station.sensors.sensor_manager import SensorManager


def main() -> None:
    manager = SensorManager()
    manager.initialize()

    snapshot = manager.read_all()

    print("=== Sensor Manager Test ===")
    print("Values:")
    for k, v in snapshot.values.items():
        print(f"  {k}: {v}")

    print("\nFlags:", snapshot.flags)
    print("Sensor OK:", snapshot.sensor_ok)
    print("Errors:", snapshot.errors)


if __name__ == "__main__":
    main()
