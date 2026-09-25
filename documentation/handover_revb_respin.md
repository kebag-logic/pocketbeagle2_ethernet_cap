# Handover — Rev B schematic review and PCB re-spin

Date: 2026-09-25. Project: PocketBeagle 2 Ethernet cape (DP83867, KiCad 10.0.6).

This is the state at the checkpoint where the PCB copper was cleared for the re-spin.
The schematic and library work is **done**. The PCB layout re-spin is **not started beyond the
clear and the schematic sync**.

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

### 2.1 Schematic fixes (ERC: 0 violations, down from 8; not committed)

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

3D model notes:

- **KiCad model rotation:** +Z is **clockwise** viewed from the top. This was verified with KiCad 10's STEP exporter.
- **PB2 Z offset:** it assumes the PB2 SoC-side face is 10.1 mm below the cape top (1.6 mm cape plus 8.5 mm female header). With a 2.54 mm stack, the PB2 USB-C would hit the cape. **The real mechanical stack is an open question for the user.**
- **Bel 1840888-1 (J1):** no model was committed. The file found had been downloaded by going around Bel's form and reCAPTCHA. Download it yourself from belfuse.com; it is licensed CC BY-ND, so commit it unchanged.

### 2.3 PCB

- **Silkscreen:** `P1` and `P2` below each header, with pin numbers 1/2 and 35/36 at each header's corners.
- **Board state:** a backup was taken, then all tracks, vias and zones were cleared (582 items, via kicad-python, approved). The board was then synced from the schematic.
- **Placement:** 79 footprints. Positions are unchanged from the previous layout **except the three new parts, which are off-board and must be placed**:
  - R29 (1206) at (7.3, 16.5) and C36 (1210) at (7.3, 8.7). Put them next to the J1 shield tabs, on a chassis island.
  - R30 (0402) at (5.9, 1.1). Put it next to R7/R12 (about (188.9, 84.3)) on STRAP_RX_CTRL, close to U2 pin 53.
- **Backup of the previous full routing:** `tools/respin/reference/board_before_respin.kicad_pcb`. It has the MDI, power, slow nets and LED routes, for reference.

---

## 3. Decisions and approvals from the user (keep them)

1. **Stackup:** F.Cu / 0.1 mm prepreg / **In1 GND** / 1.24 mm core / **In2 GND** / 0.1 mm prepreg / B.Cu.
   - Both inner planes are solid GND, so every outer-layer signal references GND.
   - 3V3, 1V1 and 2V5 go on **outer-layer pours and wide traces**.
   - Every signal via that changes layer gets a **GND stitching via within about 1 mm**.
2. **Tools:** kicad-python (kipy 0.8.0, socket `ipc:///tmp/kicad/api.sock`) is allowed for **bulk adding** planned tracks and vias in undoable batches, and it was used for the bulk clear. Everything else goes through **Konnect MCP**. Never hand-edit `.kicad_pcb`/`.kicad_sch`/`.kicad_pro`.
   - The one exception already used: approved direct `.kicad_sym` edits in the library.
3. **Commits:** small and incremental, one-line messages of at most 10 words, author and committer `hackerman-kl <alexandremalki89@gmail.com>`, **no co-author trailer**.
   - Use `git -c user.name=hackerman-kl -c user.email=alexandremalki89@gmail.com commit -m "..."`.
   - The main repo is on `main`. **Nothing in the main repo is committed yet.**
4. **Pours:** F/B GND pours go on last.
5. **Corners:** 45° routing only, never 90° corners.

---

## 4. Next steps (in order)

### 4.1 Placement touch-ups

- Place R30, R29 and C36 (see 2.3).
- R29 and C36 bridge the J1 `CHASSIS` pads (S1/S2) to GND. Keep a 2 mm or more gap between the chassis copper and the GND pours.

### 4.2 Planes and power

- Add In1 GND and In2 GND full-board zones (Konnect `add_zone`).
- Void all planes under the magjack's cable-side and MDI area per TI §9.4 ("no metal under the transformer"). In rev A, In2 was voided under J1. The GND plane under the PHY side stays.
- Power on outer layers:
  - **3V3:** U2 VDDIO pins 23/41/57, U3/U4 inputs, pull-ups, oscillator. Use a B.Cu 3V3 pour region plus 0.3 mm or wider traces.
  - **1V1:** U3 output to U2 VDD1P1 pins 8/29/42/58.
  - **2V5:** U4 output to U2 VDDA2P5 pins 4/12. It was a B.Cu pour before.
  - Each decoupling cap gets its own GND via.

### 4.3 MDI and LEDs (ready to push)

- `tools/respin/plan_mdi.py 1.2745 1.2745 1.2745 1.3455` gives 0 issues. P/N are matched to 0.001 mm with 0.13 mm traces and a 0.2 mm gap (≈100 Ω diff); confirm with the fab's calculator.
- `tools/respin/plan_led.py` gives 0 issues. The LED0–2 gates run on B.Cu up the left strip and around the top-left arc, necked to 0.10 mm (board minimum).
  - **Check:** it assumes B.Cu at the left strip is free.
- Both scripts build a `Plan` object. Push it with a kipy batch (see 4.7).

### 4.4 RGMII re-route with length matching (main work)

- **Impedance:** 0.15 mm traces over GND at 0.1 mm prepreg ≈ 51 Ω on both F.Cu and B.Cu (Hammerstad estimate; confirm with the fab calculator).
- **Series resistors:** RX resistors (R15–R19, R12) stay at the PHY. TX resistors (R8–R11, R13, R14) stay at the PB2 pins.
- **Target:** total length (module + cape) matched within each group to **±2.5 mm** (≈ ±17 ps). The clock is matched too, so the standard 2 ns RGMII-ID delays work.
- **Meanders:** ≥ 3W spacing (0.45 mm gap) and 45° corners. Keep them 3W or more from other nets. No meanders under U2 or near J1.
- **Layer changes:** keep them to one per net, each with an adjacent GND stitching via.

Suggested targets. `rgmii_len.py` measures the cape side: PHY pin → series R → PB2 pad, both nets summed.

| Group | Line    | Module mm | Target total | Cape target mm | Old cape (rev B) |
|-------|---------|-----------|--------------|----------------|------------------|
| RX    | RX_CLK  | 56.00     | ≈91          | ≈35 (shortest possible) | 58.6 |
| RX    | RD0     | 45.94     | 91           | 45.1           | 43.4 |
| RX    | RD1     | 38.61     | 91           | 52.4           | 37.1 |
| RX    | RD2     | 38.39     | 91           | 52.6           | 30.9 |
| RX    | RD3     | 37.08     | 91           | 53.9           | 25.0 |
| RX    | RX_CTRL | 34.31     | 91           | 56.7           | 9.7  |
| TX    | TX_CTRL | 74.32     | 100          | 25.7 (≈ shortest) | 25.0 |
| TX    | TX_CLK  | 62.03     | 100          | 38.0           | 40.3 |
| TX    | TD0     | 30.03     | 100          | 70.0           | 21.6 |
| TX    | TD1     | 50.59     | 100          | 49.4           | 32.5 |
| TX    | TD2     | 19.95     | 100          | 80.0           | 14.7 |
| TX    | TD3     | 8.35      | 100          | 91.6           | 14.7 |

- **Meander length:** about 115 mm extra on RX and 210 mm on TX.
- **Space:** B.Cu above U2 (about x 187.5–204, y 62–76) is the largest free region. The F.Cu left strip carries the RX lanes. RX_CLK should get a shorter route than the old detour around the header.
- **Velocity caveat:** the matching above is by physical length. If the PB2 routes are stripline (≈6.9 ps/mm) and the cape is microstrip (≈6.0 ps/mm), a residual ≤ 50 ps offset between groups is possible. It's within the delay-trim range.
- **After routing:**
  - Report the per-line totals and skew in ps.
  - Recommend the DT and DP83867 settings: RGMIICTL 0x32 and RGMIIDCTL 0x86, 0.25 ns steps; `ti,rx-internal-delay` / `ti,tx-internal-delay`.

### 4.5 Slow nets

Use Freerouting 2.1.0 (headless, `-de X.dsn -do X.ses --router.max_passes=150 --gui.enabled=false`):

- Export the DSN with `pcbnew.ExportSpecctraDSN` from a **copy** of the board with J2/J3 removed (they are co-located with U1 pads).
- Change `(type route)` to `(type protect)` to lock the copper already placed.
- Restrict routing to F/B only; with In1 and In2 both GND, mark the inner layers unusable.
- Parse the SES with `tools/respin/ses_parse.py`, filter it, then push with kipy.

### 4.6 EMC finish

- GND via fence along the board edge, ≤ 2.5 mm pitch, 0.5 mm from the edge.
- Stitching vias next to every signal layer change and around the PHY.
- Then F/B GND pours with no floating islands, refill, and final DRC.
- Angle audit: no 90° corners.

### 4.7 Pushing geometry with kipy

This follows the pattern in `clear_copper.py`:

- `KiCad(socket_path=...)`, then `board.begin_commit()`.
- Create `Track` / `Via` items with nets from `board.get_nets()` and positions in nm.
- `board.create_items([...])`, then `board.push_commit(c, "message")`.
- Save with Konnect `save_project`.

Before pushing, always run `Plan.check()` (`tools/respin/model.py`, shapely) against the saved board.

---

## 5. Actions only the user can do

1. **3D path variable:** KiCad → Preferences → Configure Paths → add `KL_LIB` = `<project>/kebag_logic_kicad_library`. Without it, no KL 3D model resolves.
2. **Footprint refresh:** KiCad → Tools → **Update Footprints from Library** (all, include 3D models). Konnect can't do it losslessly, because of the `unlocked` clauses on U1, U2, Y1, J1 and the TPs.
3. **Annular ring:** Board Setup → min via annular width 0.2 → **0.1 mm**. The vias are 0.45/0.2 mm, which gives a 0.125 mm ring. JLC 4-layer allows 0.075 mm, and Konnect can't set this.
4. **Impedance:** confirm 50 Ω SE and 100 Ω diff trace sizes with the fab's stackup calculator.
5. **Mechanical stack:** decide the PB2 to cape height (PB2 USB-C clearance) and adjust the U1 model Z offset.
6. **J1 model:** download the Bel 1840888-1 STEP from Bel's site.
7. **C36 fields:** fill in the distributor numbers.
8. **Pushes:** push the library commits and bump the submodule pointer.

---

## 6. Tooling and gotchas

- **Scripts** are in `tools/respin/` (see its README). They need Python with `shapely` and `kipy==0.8.0`.
- **Konnect cannot:**
  - delete vias or zones;
  - set DNP;
  - create `extends`-derived symbols;
  - import SES on 4-layer or rounded-outline boards.
- **Konnect symbol edits:**
  - `replace_component` keeps the **old** instance fields, so re-set Value, MPN and so on afterwards.
  - `add_schematic_component` doesn't copy custom fields; add them with `edit_schematic_component`.
- **kicad-cli ERC JSON:** coordinates and lengths are scaled by 100.
- **Earlier notes:** see `documentation/library_additions.md` and `documentation/review_checklist.md`.
