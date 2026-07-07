# Schematic Connections — PocketBeagle 2 ↔ DP83867 Ethernet Cap

## Scope

Detailed information about the connections between the PocketBeagle 2 (AM62x, "CPU"),
the DP83867IRPAPR gigabit PHY ("PHY") and the RJ45 magjack. Net names follow
[naming_convention.md](naming_convention.md).

## RGMII (CPU ↔ PHY)

- 12 signals: `RGMII_TD0..3_CPU_to_PHY`, `RGMII_TX_CLK_CPU_to_PHY`,
  `RGMII_TX_CTRL_CPU_to_PHY`, `RGMII_RD0..3_PHY_to_CPU`, `RGMII_RX_CLK_PHY_to_CPU`,
  `RGMII_RX_CTRL_PHY_to_CPU` — routed on the PocketBeagle 2 RGMII2 header pins.
- Every RGMII line has a **22R series resistor** (R8–R19) placed near the driver end.
- Skew/length matching is enforced by the custom DRC rules
  (`pocketbeagle2_ethernet_cap.kicad_dru`) via the net classes **RGMII_TX** and
  **RGMII_RX** (3 mm window). The classes are defined in the project settings; the rev A
  board carried the internal PHY RGMII delay (flight-time matching still open, see
  rev A commit history).

## MDI (PHY ↔ RJ45)

- `MDI0..3_PHY_RJ45_P/_N` — four differential pairs, connected **directly** from the
  PHY to the 1840888-1 jack: the magnetics are integrated in the jack, no external
  Bob-Smith termination on the pairs in rev A.
- Jack center tap / VCC (`Net-(J1-VCC)`) can be fed from `VDD_2V5` through **R25 (0R,
  DNP)** — unpopulated by default.
- Both shield tabs go to GND through 0R resistors (R26, R29).

## MDIO (CPU ↔ PHY)

- `MDIO_MDC_CPU_PHY`, `MDIO_DIO_CPU_PHY` — shared management bus, participants listed
  per convention (no direction encoded). Pull-ups: R20/R21/R24 (2.2K to `VDD_3V3`).

## Clocking

- `CLK_25M_OSC_to_PHY`: ECS-2520MV-250-CN-TR 25 MHz HCMOS oscillator (Y1, own
  `oscillator` sheet) → series C14 (22 pF) → PHY XI (pin 19). C18 (27 pF) shunts the
  XI node to GND; TP4 probes the clock. Y1 runs from `VDD_3V3` (C4 100n decoupling).
- PHY `CLK_OUT` (pin 22) is only brought to test point TP2.

## Reset / Interrupt / Straps

- `RESET_N_CPU_to_PHY`: CPU GPIO → PHY RESET_N (pin 59).
- `INT_PWDN_N_CPU_PHY`: dual-function open-drain INT/PWDN — bidirectional by protocol,
  so participants are listed without direction.
- Strap nets `STRAP_RX_CTRL_PHY` / `STRAP_RX_D7_PHY` carry the RX_CTRL / RX_D7 strap
  dividers (R5 5K76, R6/R7 2K49). `RBIAS` (pin 15) has R22 = 11K 1% to GND.
- PHY status LEDs: `LED0_PHY_to_Q1` … `LED2_PHY_to_Q3` drive BSS138 gates (Q1–Q3);
  the FETs sink D1–D3 (0805 green/orange/red) from `VDD_3V3` via 200R (R23/R27/R28).

## Audio (PMOD)

- Two PMOD 2x6 connectors (P1, P2) share the I2S bus: `I2S_BCLK_CPU_PMOD`,
  `I2S_LRCLK_CPU_PMOD` (bus naming — master role is protocol/configuration defined),
  and per-module data `I2S_SDIN_CPU_to_PMOD1/2`, `I2S_SDOUT_PMOD1/2_to_CPU`.
- `MCLK_PMOD` is the module master clock rail; 0R links R1–R4 select its CPU source:
  `MCLK_TOUT` (timer out), `MCLK_TIN` (timer in), `MCLK_MCASP` (MCASP AHCLK). These
  CPU-side option nets keep functional names per convention rule 4.

## Power tree

```
PocketBeagle 2 VDD_3V3 (P1.14/P2.23 rails)
├── PHY VDDIO (3x), oscillator, pull-ups, LED anodes
├── ldo_2v5: U4 TPS7A2025PDBVR -> VDD_2V5 -> PHY VDDA2P5, (R25/DNP -> J1 VCC)
└── ldo_1v1: U3 TPS7A2011PDBVR -> VDD_1V1 -> PHY VDD1P1 (core)
```
Each LDO sheet: 1u in + 1u out + 100n input decoupling, EN tied to input rail,
test points on input and output rails.

## Net rename map (rev A → current)

| rev A | current |
|---|---|
| RGMII_TD0..3 | RGMII_TD0..3_CPU_to_PHY |
| RGMII_TX_CLK / TX_CTRL | RGMII_TX_*_CPU_to_PHY |
| RGMII_RD0..3 / RX_CLK / RX_CTRL | RGMII_*_PHY_to_CPU |
| MDIO0_MDC / MDIO_MDC | MDIO_MDC_CPU_PHY |
| MDIO0_DIO / MDIO_DIO | MDIO_DIO_CPU_PHY |
| RESET_N / RST_N | RESET_N_CPU_to_PHY |
| INT_N/PWRDN_N / INT_PWDN_N | INT_PWDN_N_CPU_PHY |
| X_IN | CLK_25M_OSC_to_PHY |
| MD0..3_P/N | MDI0..3_PHY_RJ45_P/N |
| LED0/1/2 | LED0..2_PHY_to_Q1..3 |
| RX_CTRL / RX_D7 (straps) | STRAP_RX_CTRL_PHY / STRAP_RX_D7_PHY |
| 1V1 / 2V5 / 3V3 (hier) | VDD_1V1 / VDD_2V5 / VDD_3V3 |
| BCLK / LRCK / LRCLK | I2S_BCLK_CPU_PMOD / I2S_LRCLK_CPU_PMOD |
| PMOD1/2_SDIN/SDOUT (+ `.` typos) | I2S_SDIN_CPU_to_PMODx / I2S_SDOUT_PMODx_to_CPU |
| MCLK | MCLK_PMOD |

Known accepted ERC warnings: local rail labels intentionally share the global
`VDD_*` names inside child sheets (`same_local_global_label`, 3x) — connectivity is
via hierarchical pins and was netlist-verified against rev A.
