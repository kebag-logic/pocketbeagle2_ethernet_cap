# Handover — Rev B schematic review and PCB re-spin

Date: 2026-09-25. Project: PocketBeagle 2 Ethernet cape (DP83867, KiCad 10.0.6).

**State (end of 2026-09-25):** the re-spin is **routed, DRC-clean on copper and committed** on branch
`revb-respin`, with **every SMD part on the top side**. JLCPCB Gerbers, BOM and CPL are in `production/`.
Sections 2.1–2.2 are the schematic/library history; 2.3 onward is the current board.

---

## 1. What was asked

- Review the schematics, then re-spin the PCB.
- Match the RGMII lanes as they must be, **including the PocketBeagle 2 (PB2) module-side
  lengths**, with the right impedance. EMC must be good.
- Add F.Silkscreen labels for the P1/P2 headers.
- Add missing 3D models to the `kebag_logic_kicad_library` submodule and commit them.
  Commit as `hackerman-kl <alexandremalki89@gmail.com>`, at most 10 words, no co-author.
- Pour the signal-layer (F/B) GND planes **last**, after everything else is routed.
- Avoid 90° corners. Follow every IC's layout guidelines.

PB2 module-side RGMII2 lengths given by the user (mils → mm):

| Signal  | Ball | mils    | mm    |
|---------|------|---------|-------|
| RD0     | AE23 | 1808.5  | 45.94 |
| RD1     | AB20 | 1520.17 | 38.61 |
| RD2     | AC21 | 1511.44 | 38.39 |
| RD3     | AE22 | 1459.68 | 37.08 |
| RX_CLK  | AD23 | 2204.81 | 56.00 |
| RX_CTRL | AD22 | 1350.87 | 34.31 |
| TD0     | Y18  | 1182.32 | 30.03 |
| TD1     | AA18 | 1991.72 | 50.59 |
| TD2     | AD21 | 785.48  | 19.95 |
| TD3     | AC20 | 328.86  | 8.35  |
| TX_CLK  | AE21 | 2442.23 | 62.03 |
| TX_CTRL | AA19 | 2925.95 | 74.32 |

TD2 and TD3 each have "2 possibilities" (two SoC balls). The table uses the listed ball.

---

## 2. Done

### 2.1 Schematic fixes (ERC: 0 errors; committed)

| Fix | Where | Why |
|-----|-------|-----|
| J2.2/4/19/21/23/25/27/34/35 and J3.10/19 were tied to GND. They now carry their U1 RGMII net. | `io.kicad_sch` | J2/J3 are co-located on the U1 holes, so they are the same plated hole. As drawn, the GND tie shorted RGMII to GND. It came from commit `c8bef36`. |
| AIN_VREF_N label moved from U1.51 to U1.17. U1.51 is GND again. | `io.kicad_sch` | The label was on the wrong pin. |
| Removed a dangling 2.54 mm wire under `#PWR0100`. | `io.kicad_sch` | ERC warning. |
| **R30 5k76 added**, STRAP_RX_CTRL_PHY to VDD_3V3. With R7 2k49 this gives **mode 3**. | `phy.kicad_sch` | RX_CTRL in mode 1 is forbidden (SNLS484J Table 7-6 note 1): the PHY can enter a test mode. |
| RX_D7 strap changed to **mode 4**: R5 5k76 → 2k49, R6 removed. | `phy.kicad_sch` | Speed-opt stays on and CLK_OUT is disabled, so the unused 25 MHz to TP2 no longer radiates. Table 7-5/7-6. |
| C28 (22p on RBIAS) removed. | `phy.kicad_sch` | Not in the datasheet or TI reference designs. Konnect can't set DNP, so the part was deleted. |
| C18 27p → **22p**. | `oscillator.kicad_sch` | XI amplitude goes from 1.51 Vpp (marginal) to about 1.65 Vpp, against the 1.5–1.9 Vpp spec. |
| **R25 removed**, J1.1 (centre-tap common) marked no-connect, and the `VDD_2V5` sheet pin on the magjack sheet deleted. | `rj45_connector_port0.kicad_sch`, `network.kicad_sch` | Fitting R25 would put 2.5 V DC on the magjack centre taps. Fig 9-2: CTs go to GND through caps only. |
| **Chassis isolation.** J1.S1/S2 go to a `CHASSIS` net, then R29 **1M 1206** ∥ C36 **4n7 2 kV 1210** to GND. This replaces the two 0R links. | `rj45_connector_port0.kicad_sch` | TI §9.2.2 chassis isolation, for ESD and EMC. |

Review findings that are **not** schematic changes. They go to firmware and device tree (DT):

- **Shared pins:** PB2 RGMII/MDIO header pins are shared with other SoC balls (E18, D20, A13, B20, B18) and with MSPM0 PA16/PA21–26. The PB2 pinmux must keep the second balls as inputs with no pull, and the MSPM0 must keep those pins Hi-Z/analog. Check the RX eye at 1000 Mb/s.
- **PHY address:** it depends on RX_D0/RX_D2 floating at strap latch time. Put `reg = <0>` in the DT.
- **RGMII delays:** AM62x normally uses `phy-mode = "rgmii-rxid"`, and the DT needs `ti,rx-internal-delay`. Set the final values after routing, from the measured lengths (section 4.4).
- **Voltage:** RGMII2 on the PB2 is 3.3 V (VDDSHV2), so VDDIO = 3.3 V is correct. The "1.8V" pin labels were wrong; see 2.2.

### 2.2 Library submodule (`kebag_logic_kicad_library`, branch `pocketbeagle-2`)

There are 3 local commits. They are **not pushed**, and the main repo's submodule pointer has not been bumped.

- `3800219` Add 3D models for PHY, oscillator and PocketBeagle 2:
  - HTQFP-64: KiCad model `TQFP-64-1EP_10x10mm_P0.5mm_EP5.305x5.305mm.step`.
  - ECS-2520MV: KiCad `SG210` 2.5×2.0 model as a **stand-in** (see `3dmodels/Oscillator.3dshapes/README.md`).
  - PocketBeagle 2: `3dmodels/Module.3dshapes/PocketBeagle2.stpZ`. The source is the openbeagle.org pocketbeagle-2 repo (EVT STEP), licensed CC BY-SA 4.0. Attribution is in `README.md`.
- `d30326e` Add 1M 1206 resistor and 4n7 2kV 1210 capacitor:
  - `R_1M_0.25W_1pct_1206`: CRCW12061M00FKEA, LCSC C844869.
  - `C_4n7_2kV_10pct_X7R_1210`: KEMET C1210C472KGRACTU. **The Mouser, Digikey and LCSC fields are blank because they weren't verified.**
  - New footprints `R_1206` and `C_1210`, with KiCad 3D models.
- `561d560` Match PocketBeagle2 symbol GND pins, AIN0-4 are 3.3V:
  - The library symbol now matches the schematic layout.
  - GND pin 15 is `power_out`; the other GND pins are `passive`.

Later schematic changes (user-approved, committed):

- 1 µF added on PHY pins 4, 12, 41, 42 (C37–C40), per TI.
- **DP83867 RJ45 mirror mode** (§7.4.6.6), so J1 can sit on B.Cu:
  - J1 MDI pins are remapped: A↔D and B↔C, with polarity swapped.
  - A LED_0 mode-3 strap enables it: R31 5k76 to 3V3, R32 2k49 to GND. LED0 stays active-high.
- BOM swapped to in-stock LCSC parts. U3 is now **TLV73311PDBVR** (C2865431), same DBV pinout.

3D models (submodule `kebag_logic_kicad_library`): `PocketBeagle2.stpz` (lower-case extension, which KiCad 10 needs)
sits 11 mm above the cape top: 2.5 mm male-header plastic plus the 8.5 mm PB2 female header, which is on the PB2's
bottom face, so the PB2 is component-side up. The J1 Bel STEP is **not** committed; see section 5.

### 2.3 PCB (current)

**Stackup:** F / 0.1 mm prepreg / **In1 GND** / 1.24 mm core / **In2 GND** / 0.1 mm prepreg / B, close to JLC04161H-3313.

**Placement:**
- **All SMD parts are on F.Cu.**
- B.Cu holds only J1 (THT Bel 1840888-1, rotated 180° after the flip) and the unassembled test pads TP1/2/4/6/8.
- The PB2 (U1) plugs onto J2/J3 (2×18 male headers on U1's holes).
- LED drivers Q1–Q3 are under the 3V3 top bus.
- The TX series resistors R8/R10/R11/R14 sit next to their header pins.
- U4 (2V5 LDO) is at the bottom right.

**Routing:** everything uses 45° corners, audited by script.
- **RGMII:** 0.15 mm (≈50 Ω, estimate). Lengths are matched including the PB2 module side (module + cape, physical length, vias counted as 1.6 mm):

  | Group | Lines | Total (mm) |
  |-------|-------|------------|
  | RX | RD0–3 | 84.76 |
  | RX | RX_CLK | 98.86 (+14.1) |
  | TX | TX_CTRL, TD0–3 | 99.671 |
  | TX | TX_CLK | 115.07 (+15.4) |

  - The clock offsets (≈ +95 ps RX, ≈ +103 ps TX) come from the routes and are absorbed by the delay settings. Use AM62x `phy-mode = "rgmii-rxid"` or `rgmii-id`, and tune with DP83867 RGMIIDCTL (0.25 ns steps) or `ti,rx/tx-internal-delay`.
  - Measure with `tools/respin/rgmii_len.py`. It sums stubs as well, so strapped nets such as RX_CTRL read long.
- **MDI:** 0.13 mm width, 0.2 mm gap, on F.Cu with no vias, P/N skew-matched.
- **Chassis:** a CHASSIS island under J1 on F and B, with a 1 mm moat to GND. R29 (1M) and C36 (4n7 2 kV) bridge it.
- **Stitching:** GND stitching fence plus interior grid. F/B GND pours are refilled.
- **Decoupling:** placed and routed by `tools/respin/topside/capfit.py`, nearest free top-side spot to each pin.
  - C7 sits on pin 8 in the MDI gap, and C9 on pin 23.
  - Because of the single-sided constraint (user decision: "Everything on top anyway"), several caps are several mm from their pins. They connect over short B.Cu rail links.
  - The 2V5/3V3 bulk caps C11/C8/C19/C15/C16/C20 sit on the right edge strip beyond J3. C22 sits on the left strip.

**DRC (kicad-cli, `--refill-zones`):** 0 clearance, short, width, courtyard or silk-overlap errors. What remains:
- `annular_width` and `starved_thermal`: Board Setup values the user has to change (section 5).
- `holes_co_located`: J2/J3 on U1, by design.
- 4 `lib_footprint_mismatch`.
- U4 silk clipped by the J1.1 NC pad.
- J1 B.Silk past the edge: J1 overhangs the edge by design.
- VOUT U1.24 ↔ U1.49 unconnected: the PB2 joins them internally.
- Schematic parity field mismatches.

**Silkscreen:**
- 1.0 mm text, 0.15 mm stroke, with no overlaps.
- P1/P2 labels and pin numbers are kept.
- 19 crowded references are hidden on silk; they're still on F.Fab.

**Production:** `production/` holds the Gerber and drill zip, `*_bom_jlcpcb.csv` (LCSC #) and `*_cpl_jlcpcb.csv`. See `production/README.md`. Regenerate with `python tools/make_production.py`.

---

## 3. Decisions and approvals from the user (keep them)

1. **Stackup:** In1 and In2 are both GND. Power runs on outer-layer traces.
2. **Tools:**
   - Konnect MCP is used for part moves, flips, saves, refills and footprint updates.
   - kicad-python (kipy 0.8.0, `ipc:///tmp/kicad/api.sock`) is approved for:
     - bulk clear or add of planned tracks and vias in undoable batches;
     - zone outline and spoke edits;
     - silkscreen text placement;
     - one-off 3D model entries.
   - Never hand-edit `.kicad_pcb`, `.kicad_sch` or `.kicad_pro`.
3. **Commits:**
   - One line, at most 10 words.
   - Author and committer `hackerman-kl <alexandremalki89@gmail.com>`, with **no co-author trailer**.
   - Branch `revb-respin`.
   - Never commit the untracked `.gitprep-hackerman-kl`, `Requirements`, `konnect/` or the PDF.
4. **Layout:**
   - F/B GND pours go on last.
   - 45° corners only.
   - Every SMD part on the top side, **"Everything on top anyway"**: decoupling can sit farther from the pins.
   - J1 is the only part on the bottom.
5. **Schematic changes need explicit approval.**

---

## 4. Open items

- **J1 sourcing:** C5876366 isn't stocked at LCSC or in the JLC catalogue, so J1 is left out of the JLC BOM/CPL. Either hand-solder it (DigiKey 5923-1840888-1-ND), or switch to HanRun HR911130A (C54408), which needs a new footprint and placement.
- **Low stock:** U2 C477933 has 18 pcs; order early.
- **Firmware / DT:**
  - Set the PHY address with `reg = <0>`.
  - RGMII delays per 2.3.
  - Mirror mode is strap-enabled; nothing to do in software.
  - PB2 shared pins: keep the second SoC balls and the MSPM0 pins Hi-Z.

---

## 5. Actions only the user can do

1. **Close and reopen the project in KiCad.** Its in-memory project settings are stale (pre-rev-B netclasses) and rewrite `pocketbeagle2_ethernet_cap.kicad_pro` on save. Every script run so far restores the file with `git checkout -- pocketbeagle2_ethernet_cap.kicad_pro`.
2. **3D path:** Preferences → Configure Paths → add `KL_LIB` = `<project>/kebag_logic_kicad_library`. Without it, KiCad shows only pads.
3. **Board Setup:**
   - Minimum via annular width 0.2 → **0.1 mm**. The vias are 0.45/0.2 mm; JLC allows it.
   - Zone minimum thermal spoke count → **1**.
4. **Impedance:** order JLC impedance control and let them adjust the widths. On their 3313 stackup, 50 Ω may need about 0.17–0.19 mm.
5. **J1 model:** download the Bel 1840888-1 STEP from belfuse.com (CC BY-ND, commit it unchanged).
6. **Library:** push the `kebag_logic_kicad_library` commits and bump the submodule pointer.
7. **JLC order:** check part rotations in the placement preview (SOT-23, SOT-23-5, HTQFP, LEDs).

---

## 6. Tooling and gotchas

- Scripts live in `tools/respin/` (see its README), including `topside/`: the router, the cap fitter and the stage plans.
- `kicad-cli pcb render` / `export` need `-D KL_LIB=<repo>/kebag_logic_kicad_library`.
- KiCad re-nets a dangling via or stub when a footprint it touched is flipped. Check for orphan vias and duplicate tracks after pushes.
- **Konnect cannot:** delete vias or zones, set DNP, or import SES on 4-layer or rounded boards.
- `kicad-cli` ERC JSON coordinates are scaled by 100.
