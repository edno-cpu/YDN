from dataclasses import dataclass


@dataclass(frozen=True)
class RadioMode:
    name: str
    sf: int
    bw: int
    cr: int
    tx_power: int
    preamble: int


MODE_A_FAST = RadioMode(
    name="A_FAST",
    sf=7,
    bw=125000,
    cr=5,
    tx_power=10,
    preamble=8,
)

MODE_B_OKAY = RadioMode(
    name="B_OKAY",
    sf=8,
    bw=125000,
    cr=5,
    tx_power=14,
    preamble=8,
)

MODE_C_POOR = RadioMode(
    name="C_POOR",
    sf=9,
    bw=125000,
    cr=5,
    tx_power=17,
    preamble=10,
)

MODE_D_VERY_POOR = RadioMode(
    name="D_VERY_POOR",
    sf=10,
    bw=125000,
    cr=5,
    tx_power=20,
    preamble=12,
)

RADIO_MODES = {
    MODE_A_FAST.name: MODE_A_FAST,
    MODE_B_OKAY.name: MODE_B_OKAY,
    MODE_C_POOR.name: MODE_C_POOR,
    MODE_D_VERY_POOR.name: MODE_D_VERY_POOR,
}
