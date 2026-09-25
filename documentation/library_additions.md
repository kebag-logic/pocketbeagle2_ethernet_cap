# Library additions — review checkpoint (M2)

Everything added to `kebag_logic_kicad_library` for the ethernet cap migration, with
sources, license basis and open questions. **Please review before the submodule is
pushed upstream.**

**Sourcing pass (2026-07-27):** every MPN below was checked against a live Digi-Key
product page and against LCSC, and the `Digikey` / `LCSC` fields were filled from those
listings — see [Supplier reference pass](#supplier-reference-pass-2026-07-27) for the
full table and for the three part numbers that turned out not to exist. MPNs previously
marked *(derived)* are now marked **verified** where a distributor listing confirmed
them.

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
| `KL_R`: `R_0R_0.063W_5pct_0402` | CRCW04020000Z0EDC | **verified** (Digi-Key + LCSC) | vishay.com 28773/crcwce3.pdf |
| `KL_R`: `R_22R/200R/2K2/2K49/5K76/11K_0.063W_1pct_0402` | CRCW0402…FKEDC | **verified** — all six exist at Digi-Key and LCSC | same |
| `KL_C`: `C_10n_50V_10pct_X7R_0402` | GRM155R71H103KA88D | **verified** | murata.com productdetail |
| `KL_C`: `C_1u_16V_10pct_X5R_0402` | GRM155R61C105KA12D | **verified** — 0 stock / 17-week lead at Digi-Key, 150 k at LCSC | same |
| `KL_C`: `C_10u_6.3V_20pct_X5R_0402` | GRM155R60J106ME44D | **verified but DISCONTINUED at Digi-Key** (LCSC still stocks 1.1 M) — **6.3 V rating on a 3V3 rail: check derating policy** | same |
| `KL_C`: `C_22p/27p_50V_5pct_C0G_0402` | GRM1555C1H220/270JA01D | **verified** | same |
| `KL_LED`: `LED_Green_2.1V_0.02A_0805` | LTST-C170GKT | **verified** (Lite-On, same family as house 0603s); LCSC field was wrong — see below | liteon.com |
| `KL_LED`: `LED_Orange_2V_0.02A_0805` | LTST-C170KFKT | **verified**; LCSC field was wrong | liteon.com |
| `KL_LED`: `LED_Red_2V_0.02A_0805` | LTST-C170KRKT | **verified**; LCSC field was wrong | liteon.com |
| `KL_TestPoint`: `TestPoint_SMD` | — | clone of house TestPoint, SMD footprint | — |
| `KL_Voltage_Regulators`: `TPS7A2025PDBVR` | TPS7A2025PDBVR | **verified orderable** (2.5 V rail) | ti.com/lit/gpn/tps7a20 |
| `KL_Voltage_Regulators`: `TPS7A2011PDBVR` | TPS7A2011PDBVR | **DOES NOT EXIST — see Q1** (1.1 V rail) | same |
| `KL_Conn_Data`: `RJ45_1840888-1` | 1840888-1 | **verified — manufacturer is Bel Fuse Inc.** (Q2 closed) | LCSC mirror, see Q2 |
| `KL_Conn_Data`: `PMOD_02x06` | TBD (generic 2x6 SMD header) | physical part = any 2x6 SMD header; Digilent PMOD spec linked | digilent.com |
| `KL_Transistor` (new lib): `BSS138LT1G` | BSS138LT1G | **verified** (onsemi, Digi-Key + LCSC C82045) — rev A says only "BSS138"; onsemi variant chosen — see Q3 | onsemi.com |
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

1. **1.1 V LDO — BLOCKING, part does not exist.** rev A used symbol
   `TPS7A20C285PYCKR` (a DSBGA part) for *both* LDOs while the board has SOT-23-5 pads.
   TPS7A20**25**PDBVR (2.5 V) is confirmed orderable. **TPS7A20**11**PDBVR is not a real
   part number**: TI's own `part-details` page 404s for it (it resolves for e.g.
   `TPS7A2018PDBVR`), Digi-Key returns no results, and LCSC has no listing. Digi-Key's
   TPS7A20 SOT-23-5 range skips 1.1 V entirely (…09, 12, 15, 18, 185, 24, 28, 30, 31,
   32, 36, 42, 45, 50, 55). Its supplier fields were therefore left `TBD` — filling
   them would mean inventing an order number for a part nobody sells.
   Options: **(a)** `TLV73311PDBVR` — real TI 1.1 V / 300 mA LDO in the same SOT-23-5
   (DBV) package, LCSC `C2865431`; its pinout differs from TPS7A20 (no separate NR/SS
   pin) so it needs a pin-by-pin check before committing. **(b)** drop U3 and use the
   DP83867's internal core LDO, freeing one regulator. Neither `TPS7A2009PDBVR` (0.9 V)
   nor `TPS7A2012PDBVR` (1.2 V) is within the DP83867 VDD1P1 ±5 % window.
2. ~~**RJ45 1840888-1**~~ — **RESOLVED. The manufacturer is Bel Fuse Inc.**, so the
   SnapEDA `BEL_…` label was right and the TE-looking number format was a red herring.
   Digi-Key `5923-1840888-1-ND` (the same `5923-` Bel Fuse prefix as the house part
   `0826-1X4T-43-F`), LCSC `C5876366`. It is a shielded 10/100/1000 Base-T AutoMDIX
   MagJack with integrated magnetics, gold-plated phosphor bronze contacts, no LEDs.
   The `Datasheet` field now points at LCSC's mirror of the manufacturer PDF:
   `https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2312031643_TRP-Connector-1840888-1_C5876366.pdf`
   — **replace this with a belfuse.com URL if you have one**; Bel's own site does not
   expose a per-part page for this number. Note availability is poor: 26-week lead at
   Digi-Key, 0 stock at LCSC.
3. **BSS138 vendor**: plain "BSS138" is multi-sourced. I picked onsemi `BSS138LT1G`.
   OK, or do you have a preferred source (Nexperia BSS138P …)?
4. **Capacitor specs**: rev A schematic has bare values (no voltage/dielectric).
   Derived choices above (X7R/C0G/X5R, 50/16/6.3 V) — all five part numbers are now
   confirmed real, but the *choice* of rating is still mine, not rev A's. If a rev A
   BOM exists, I'll match it. Two availability notes: the 10 µF `GRM155R60J106ME44D`
   is **discontinued at Digi-Key** (LCSC still stocks it heavily; Digi-Key suggests
   `GRM155R60J106ME15D`), and the 1 µF `GRM155R61C105KA12D` is on a 17-week Digi-Key
   lead.
5. **DNP resistor R25**: value literally "DNP" in rev A. It will be migrated as the
   footprint-compatible resistor of its strap group with the KiCad DNP attribute set —
   which value should it document (11K like R22?)
6. ~~**Supplier numbers**~~ — **DONE for Digi-Key and LCSC**, see the section below.
   **Mouser could not be automated**: mouser.com serves an "Access to this page has
   been denied" bot wall to every request, and Mouser part numbers are not derivable
   from the MPN (the house entries show Mouser mangles them — MPN `GRM187R61A226ME15D`
   is Mouser `81-GRM187R61A226ME5D`, a character short). Four Mouser fields are still
   `TBD`; the confirmed Mouser product pages are listed below so you can copy the
   numbers in one click.

## Expansion header addition

| Symbol (lib) | MPN | Source | Notes |
|---|---|---|---|
| `KL_Header`: `Header_18x02_2.54mm_2.54mm_Straight` | BHR-36-VUA *(derived from house BHR-20-VUA)* | Adam Tech BHR series | footprint `18x02_2.54mm_Header` ported from KiCad official 2x18 vertical + 3D model |

**Sourcing check (left as-is on request, recorded for the record):** `BHR-36-VUA` is not
orderable anywhere — not Digi-Key, not LCSC. The Adam Tech BHR series only comes in the
standard IDC position counts (…20, 34, 40; BHR-20/34/40-VUA all resolve, 36 does not).
Its datasheet also titles it *"BOX HEADER, VERTICAL PCB MOUT, 2 ROW .100 PITCH"* — a
shrouded/keyed connector, which is not what the plain `18x02_2.54mm_Header` footprint
lays down. (The same mismatch already exists upstream on the house `BHR-20-VUA` /
`10x02_2.54mm_Header` pair, so this is inherited, not introduced here.) A real
equivalent, if wanted later: **Adam Tech `PH2-36-UA`** — 36 positions, 2 rows, 2.54 mm,
through-hole, unshrouded, Digi-Key `2057-PH2-36-UA-ND` (same `2057-` Adam Tech prefix as
the house BHR-20-VUA entry); not carried by LCSC. `Digikey`/`LCSC` on this symbol were
left `TBD`.

## Supplier reference pass (2026-07-27)

Method: each MPN was resolved against its live Digi-Key product page (for the Digi-Key
part number, and to confirm the MPN exists at all) and against LCSC via the JLCPCB parts
API, accepting only exact MPN matches. Nothing here is derived from a naming scheme.

| MPN | Digi-Key | LCSC | Refs |
|---|---|---|---|
| CRCW04020000Z0EDC | 541-4062-1-ND | C844710 | R25, R26, R29 |
| CRCW040222R0FKEDC | 541-3973-1-ND | C2076943 | R8–R19 |
| CRCW0402200RFKEDC | 541-3995-1-ND | C843896 | R23, R27, R28 |
| CRCW04022K20FKEDC | 541-3971-1-ND | C2076947 | R20, R21, R24 |
| CRCW04022K49FKEDC | 541-4867-1-ND | C1730862 | R6, R7 |
| CRCW04025K76FKEDC | 541-5031-1-ND | C4180495 | R5 |
| CRCW040211K0FKEDC | 541-4691-1-ND | C1730800 | R22 |
| GRM155R71H103KA88D | 490-4516-1-ND | C77019 | C19, C24, C27 |
| GRM155R61C105KA12D | 490-10694-1-ND | C77006 | C8, C11, C12, C16, C17, C20, C21, C23, C25, C30–C33 |
| GRM155R60J106ME44D | 490-13811-2-ND | C76991 | C15, C22, C26 |
| GRM1555C1H220JA01D | 490-5868-1-ND | C76960 | C28 |
| GRM1555C1H270JA01D | 490-5869-1-ND | C76961 | C14, C18 |
| LTST-C170GKT | 160-1179-1-ND | C125090 | D1 |
| LTST-C170KFKT | 160-1413-1-ND | C284931 | D2 |
| LTST-C170KRKT | 160-1415-1-ND | C94868 | D3 |
| TPS7A2025PDBVR | 296-TPS7A2025PDBVRCT-ND | C2869949 | U4 |
| DP83867IRPAPR | 296-46083-1-ND | C477933 | U2 |
| BSS138LT1G | BSS138LT1GOSCT-ND | C82045 | Q1–Q3 |
| ECS-2520MV-250-CN-TR | XC2752TR-ND | C405464 | Y1 |
| 1840888-1 (Bel Fuse) | 5923-1840888-1-ND | C5876366 | J1 |
| PocketBeagle 2 (BeagleBoard MPN `102110780`) | 2820-102110780-ND | NA | U1 |

### Corrections made to existing data

- **All three 0805 LED `LCSC` fields were wrong** — they held the *0603* parts' values,
  copy-pasted: green had the literal string `LTST-C190GKT` (an MPN, not a C-number),
  orange had `C7297440` (the 0603 orange) and red had `C913101` (the 0603 red
  `LTST-C194KRKT`). All three would have ordered the wrong LED. Now C125090 / C284931 /
  C94868.
- **Upstream bug fixed in passing**: the pre-existing house 0603 symbol
  `LED_Green_2.1V_0.03A_0603` also had its `LCSC` field set to the MPN string
  `LTST-C190GKT` instead of a part number — corrected to `C125093`. This is the source
  the 0805 green was copied from.

### Still `TBD`, and why

| Field | Reason |
|---|---|
| `TPS7A2011PDBVR` → Digikey, LCSC | part does not exist — see Q1 |
| `Header_18x02…` (BHR-36-VUA) → Digikey, LCSC | part does not exist — see above |
| `PMOD_02x06` → MPN + all suppliers | no physical part chosen; symbol is lib stock and is not placed in this design |
| Mouser on Y1, J1, U1 | mouser.com bot-walls automated lookup and its numbers are not derivable. Confirmed product pages: oscillator `mouser.com/ProductDetail/ECS/ECS-2520MV-250-CN-TR`, PocketBeagle 2 `mouser.com/new/beagleboardorg/beagleboard-pocketbeagle-2/`. Mouser stocks Bel Fuse but no page for `1840888-1` was found. |

## Post-migration symbol fixes (M6, also in the submodule)

- `KL_Module:PocketBeagle2`: pin 15 (GND) `power_in` → `power_out` (the host board
  sources ground — makes GND ERC-driven); pin 59 (second 3.3V) `power_out` → `passive`
  (avoids output-vs-output conflict with pin 14; KiCad idiom for duplicated rail pins); pin 49 (second VOUT) `power_out` → `passive` for the same reason once the expansion headers connected both VOUT pins.
- `KL_PHY:DP83867IRPAPR`: RBIAS (15) `unspecified` → `passive`, XI (19) `unspecified`
  → `input`.

## Submodule state

19 commits on `kebag_logic_kicad_library` main (local only, **not pushed**), identity
`hackerman-kl`. The superproject records the new submodule SHA; push both after review.
