# Current consumption (estimate)

| Rail | Consumer | Estimate | Source |
|---|---|---|---|
| VDD_3V3 (from PocketBeagle 2) | DP83867 VDDIO + oscillator + LEDs + pull-ups | TBD | — |
| VDD_2V5 (TPS7A2025PDBVR, 300 mA max) | DP83867 VDDA2P5 | TBD | DP83867 total: ~490 mW (PAP pkg, ti.com datasheet) |
| VDD_1V1 (TPS7A2011PDBVR, 300 mA max) | DP83867 VDD1P1 core | TBD | — |
| Oscillator | ECS-2520MV | < 6 mA typ. | ECS-2520MV datasheet |

TODO: fill per-rail figures from the DP83867 datasheet power tables for RGMII/1000Base-T
operation and verify the LDO thermal budget (SOT-23-5).
