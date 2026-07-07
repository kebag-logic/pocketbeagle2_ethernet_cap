# Library additions — review checkpoint (M2)

Everything added to `kebag_logic_kicad_library` for the ethernet cap migration, with
sources, license basis and open questions. **Please review before the submodule is
pushed upstream.** Supplier fields marked `TBD` need order numbers; MPNs marked
*(derived)* follow the manufacturer's part-numbering scheme but were not individually
verified against a distributor listing.

## Footprints (`KL_Footprints.pretty`)

| Footprint | Used by | Source | License basis | Notes |
|---|---|---|---|---|
| `SOT-23` | Q1-Q3 BSS138 | KiCad official lib, verbatim + KL 3D path | CC-BY-SA-4.0 w/ exception (house precedent: `C_0402`, `TQFP-128`) | 3D model included |
| `SOT-23-5` | U3/U4 LDOs | KiCad official lib | same | 3D model included. **PCB rev A uses SOT-23-5**, not the DSBGA of the old vendor import |
| `LED_0805` | D1-D3 | KiCad official `LED_0805_2012Metric` | same | 3D model included |
| `06x02_2.54mm_SMD_Header` | P1/P2 PMOD | KiCad official `PinHeader_2x06_P2.54mm_Vertical_SMD` | same | name follows `10x02_2.54mm_Header` house pattern; 3D model included |
| `TestPoint_SMD_1.0x1.0mm` | TP1-TP8 | KiCad official | same | existing KL `TestPoint` is through-hole — not interchangeable |
| `ECS-2520MV` | Y1 | KiCad official `Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm` (the exact footprint on the routed rev A board) | same | no 3D model in KiCad lib; ECS provides a STEP on ecsxtal.com (SnapEDA copy not redistributable) |
| `BeagleBoard_PocketBeagle` | U1 | KiCad official Module lib | same | no 3D model available upstream |
| `HTQFP-64_10x10mm_P0.5mm` | U2 DP83867 | **redrawn**: pad geometry (incl. thermal-via array) identical to rev A board (TI PAP0064 land pattern); all graphics regenerated per FOOTPRINTS.md | land-pattern dimensions are datasheet facts; no SnapEDA file content copied (their license §1a forbids library redistribution) | via-in-pad array kept exactly as routed |
| `BEL_1840888-1` | J1 RJ45 | **redrawn**: pad geometry identical to rev A board; graphics regenerated | same reasoning | TH pin 1 is rectangular = pin-1 marking per FOOTPRINTS.md |

## Symbols

| Symbol (lib) | MPN | Status | Datasheet |
|---|---|---|---|
| `KL_R`: `R_0R_0.063W_5pct_0402` | CRCW04020000Z0EDC | *(derived)* Vishay CRCW0402, house family | vishay.com 28773/crcwce3.pdf |
| `KL_R`: `R_22R/200R/2K2/2K49/5K76/11K_0.063W_1pct_0402` | CRCW0402…FKEDC | *(derived)* | same |
| `KL_C`: `C_10n_50V_10pct_X7R_0402` | GRM155R71H103KA88D | *(derived)* Murata GRM155 | murata.com productdetail |
| `KL_C`: `C_1u_16V_10pct_X5R_0402` | GRM155R61C105KA12D | *(derived)* | same |
| `KL_C`: `C_10u_6.3V_20pct_X5R_0402` | GRM155R60J106ME44D | *(derived)* — **6.3 V rating on a 3V3 rail: check derating policy** | same |
| `KL_C`: `C_22p/27p_50V_5pct_C0G_0402` | GRM1555C1H220/270JA01D | *(derived)* | same |
| `KL_LED`: `LED_Green_2.1V_0.02A_0805` | LTST-C170GKT | **verified** (Lite-On, same family as house 0603s) | liteon.com |
| `KL_LED`: `LED_Orange_2V_0.02A_0805` | LTST-C170KFKT | **verified** | liteon.com |
| `KL_LED`: `LED_Red_2V_0.02A_0805` | LTST-C170KRKT | **verified** | liteon.com |
| `KL_TestPoint`: `TestPoint_SMD` | — | clone of house TestPoint, SMD footprint | — |
| `KL_Voltage_Regulators`: `TPS7A2025PDBVR` | TPS7A2025PDBVR | **verified orderable** (2.5 V rail) | ti.com/lit/gpn/tps7a20 |
| `KL_Voltage_Regulators`: `TPS7A2011PDBVR` | TPS7A2011PDBVR | **UNVERIFIED — see Q1** (1.1 V rail) | same |
| `KL_Conn_Data`: `RJ45_1840888-1` | 1840888-1 | **manufacturer unconfirmed — see Q2** | TBD |
| `KL_Conn_Data`: `PMOD_02x06` | TBD (generic 2x6 SMD header) | physical part = any 2x6 SMD header; Digilent PMOD spec linked | digilent.com |
| `KL_Transistor` (new lib): `BSS138LT1G` | BSS138LT1G | *(derived)* — rev A says only "BSS138"; onsemi variant chosen — see Q3 | onsemi.com |
| `KL_Oscillator` (new lib): `Oscillator_25M_25ppm_HCMOS_2.5x2.0` | ECS-2520MV-250-CN-TR | **verified** (LCSC C405464); matches `footporint_manual/ECS_2520MV_250_CN_TR/` | ecsxtal.com/store/pdf/ECS-2520MV.pdf |
| `KL_PHY` (new lib): `DP83867IRPAPR` | DP83867IRPAPR | **verified** | ti.com/lit/gpn/dp83867ir |
| `KL_Module` (new lib): `PocketBeagle2` | PocketBeagle 2 | board, not a component | docs.beagleboard.org/boards/pocketbeagle-2/ |

All IC/connector/module symbols replicate the **pin positions of the rev A schematic
symbols exactly**, so the migration drops them onto the existing wires without rewiring.
Only numeric pin data was carried over; symbol bodies, properties and fields are fresh
(KL conventions). Electrical pin types were corrected where the vendor import was wrong
(e.g. LDO `GND` was `power_out`, `NC` now `no_connect`).

## New convention documents

- `TRANSISTOR.md`, `OSCILLATOR.md`, `PHY.md`, `MODULE.md` — modeled on `VOLTAGE_REGULATOR.md`.
- `README.md` — four new libraries registered. *(Note: the pre-existing README table
  names several libraries that don't match the actual files, e.g. `KL_Ferrites` vs
  `KL_Ferrite_Bead` — left untouched, upstream issue.)*

## Open questions

1. **1.1 V LDO**: rev A schematic used symbol `TPS7A20C285PYCKR` (a DSBGA part) for
   *both* LDOs while the board has SOT-23-5 pads. TPS7A20**25**PDBVR (2.5 V) is
   confirmed orderable; TPS7A20**11**PDBVR follows TI's numbering but I could not
   confirm a distributor listing. Please confirm the intended 1.1 V part (or whether
   the DP83867's internal core LDO should be used instead, freeing one LDO).
2. **RJ45 1840888-1**: SnapEDA import was labeled `BEL_…` but the part-number format
   looks like TE Connectivity; general web search finds no listing. Please point me at
   the datasheet you used (needed for `Datasheet` field + MDI/LED pin documentation).
3. **BSS138 vendor**: plain "BSS138" is multi-sourced. I picked onsemi `BSS138LT1G`.
   OK, or do you have a preferred source (Nexperia BSS138P …)?
4. **Capacitor specs**: rev A schematic has bare values (no voltage/dielectric).
   Derived choices above (X7R/C0G/X5R, 50/16/6.3 V). If a rev A BOM exists, I'll match it.
5. **DNP resistor R25**: value literally "DNP" in rev A. It will be migrated as the
   footprint-compatible resistor of its strap group with the KiCad DNP attribute set —
   which value should it document (11K like R22?)
6. **Supplier numbers**: all `TBD` Digikey/LCSC/Mouser fields — want me to fill them
   in from distributor searches where available, or do you maintain these manually?

## Post-migration symbol fixes (M6, also in the submodule)

- `KL_Module:PocketBeagle2`: pin 15 (GND) `power_in` → `power_out` (the host board
  sources ground — makes GND ERC-driven); pin 59 (second 3.3V) `power_out` → `passive`
  (avoids output-vs-output conflict with pin 14; KiCad idiom for duplicated rail pins).
- `KL_PHY:DP83867IRPAPR`: RBIAS (15) `unspecified` → `passive`, XI (19) `unspecified`
  → `input`.

## Submodule state

19 commits on `kebag_logic_kicad_library` main (local only, **not pushed**), identity
`hackerman-kl`. The superproject records the new submodule SHA; push both after review.
