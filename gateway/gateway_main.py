from gateway.gateway_controller import GatewayController


def main() -> None:
    controller = GatewayController("gateway/configs/gateway.yaml")
    controller.run_forever()


if __name__ == "__main__":
    main()