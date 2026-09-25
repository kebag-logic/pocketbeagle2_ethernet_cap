# Review checklist

Everything awaiting user review/decision after the shish-lan-style restructure, the KL
library migration, the expansion (stacking header) rework and the readability pass.
Check items off here; details live in [library_additions.md](library_additions.md) and
[connections.md](connections.md).

## A. Library parts (before pushing the submodule)

- [ ] **1.1 V LDO — BLOCKING.** `TPS7A2011PDBVR` **is not a real part number**: TI's
  `part-details` page 404s for it, Digi-Key returns no results, LCSC has no listing,
  and Digi-Key's TPS7A20 SOT-23-5 range skips 1.1 V entirely. Supplier fields left
  `TBD` on purpose. Decide between `TLV73311PDBVR` (real TI 1.1 V / 300 mA SOT-23-5,
  LCSC C2865431 — **pinout differs from TPS7A20, needs a pin-by-pin check**) and
  dropping U3 for the DP83867's internal core LDO. Detail in
  [library_additions.md Q1](library_additions.md).
- [x] **RJ45 `1840888-1`** — **RESOLVED: manufacturer is Bel Fuse Inc.** Digi-Key
  `5923-1840888-1-ND` (same `5923-` Bel prefix as the house `0826-1X4T-43-F`), LCSC
  `C5876366`. Shielded 10/100/1000 Base-T AutoMDIX MagJack with magnetics, no LEDs.
  `Datasheet` now points at LCSC's mirror of the manufacturer PDF — **swap in a
  belfuse.com URL if you have one**. Availability is poor: 26-week Digi-Key lead,
  0 stock at LCSC.
- [ ] **BSS138** — multi-sourced; onsemi `BSS138LT1G` chosen and now **verified**
  (Digi-Key `BSS138LT1GOSCT-ND`, LCSC `C82045`, 982 k in stock). Confirm, or name a
  preferred source (e.g. Nexperia BSS138P).
- [ ] **Capacitor specs** — all five Murata GRM155 part numbers are now **verified**,
  but the *choice* of X7R/C0G/X5R and 50/16/6.3 V is still derived, not from rev A.
  The 10 µF is only 6.3 V-rated on the 3V3 rail — check the derating policy, or
  provide the rev A BOM. **Sourcing risk:** `GRM155R60J106ME44D` (C15/C22/C26) is
  **discontinued at Digi-Key** (LCSC stocks 1.1 M; Digi-Key suggests
  `GRM155R60J106ME15D`), and `GRM155R61C105KA12D` is on a 17-week Digi-Key lead.
- [x] **Resistors** — all seven Vishay `CRCW0402…EDC` MPNs **verified** against
  Digi-Key product pages and LCSC; order numbers filled.
- [ ] **18x02 stacking header** — `BHR-36-VUA` **is not orderable** (no Digi-Key, no
  LCSC; the Adam Tech BHR series only comes in standard IDC counts …20, 34, 40) and
  its datasheet describes a *shrouded box header*, not the plain 2x18 pin header the
  footprint lays down. Left untouched on request; supplier fields stay `TBD`. Real
  equivalent if wanted: Adam Tech `PH2-36-UA`, Digi-Key `2057-PH2-36-UA-ND`.
- [x] **TBD supplier fields** — Digi-Key and LCSC filled for every part that exists
  (21 MPNs, 205 field writes across the library and all six sheets). Four Mouser
  fields remain `TBD`: mouser.com bot-walls automated lookup and its part numbers are
  not derivable from the MPN. See library_additions.md for the confirmed Mouser
  product-page links.
- [ ] **LED LCSC fields were wrong** (now fixed) — all three 0805 LEDs carried the
  0603 parts' LCSC values, so a JLCPCB order would have fitted the wrong LEDs. The
  pre-existing house 0603 green symbol had the same defect (`LCSC` = the MPN string
  `LTST-C190GKT`) and was corrected to `C125093` — **this one is an upstream fix,
  confirm before pushing the submodule.**
- [ ] **Upstream lib quirks** (found, deliberately not fixed): LED symbols carry the
  placeholder Value `LED_{color}_{U_F}_{I_F}`; the lib README library table names
  don't match the actual files (`KL_Ferrites` vs `KL_Ferrite_Bead`, …). Fix upstream?

## B. Design decisions to approve

- [ ] **R25** (RJ45 VCC feed from `VDD_2V5`) migrated as **0R with the KiCad DNP
  attribute** — confirm the value choice.
- [ ] **C30/C32 pin swap** — pins 1/2 swapped vs rev A (non-polarized input caps,
  electrically identical; artifact of the redrawn LDO sheets).
- [ ] **PocketBeagle2 symbol pin types** — one GND pin is `power_out` (the host board
  sources ground), the duplicate 3.3V and VOUT pins are `passive` (KiCad idiom to
  avoid output-vs-output ERC conflicts).
- [ ] **Pass-through semantics** — cap-used signals (RGMII, MDIO, RESET/INT on the
  SPI0 pins) are exposed 1:1 on J2/J3; stacked modules must not drive them
  (documented in connections.md). OK?
- [ ] **PWR_FLAG rails** — rails a stacked module may legally drive: `VIN`,
  `USB1_VIN`, `BAT_VIN`, `AIN_VREF_P`, `AIN_VREF_N`. Confirm this matches the
  intended stacking topology.
- [ ] **Audio removal consequences** — the MCLK 0R selection matrix (R1–R4) is gone;
  MCASP/TIMER/EXT_REFCLK pins are plain pass-through now. The PMOD symbol
  (`KL_Conn_Data:PMOD_02x06`) and `06x02_2.54mm_SMD_Header` footprint remain in the
  KL library as stock — keep or drop?
- [ ] **Sheet naming deviation** — the clock sheet is `oscillator.kicad_sch` (plan
  said `crystal.kicad_sch`; the part is an oscillator, not a crystal).

## C. Housekeeping / publishing

- [ ] Delete the duplicate untracked `Requirements` file (`requirements.md` is
  committed and is a superset).
- [ ] **Submodule**: 25 commits on branch `pocketbeagle-2`, **not pushed** — push /
  open a PR (upstream uses branch-per-issue) once section A is approved.
- [ ] Decide whether local submodule `main` should be reset to `origin/main` (it
  still shows "ahead 20" from before the branch existed).
- [ ] Push the superproject `main` when ready.
- [ ] Open the project in KiCad once — headless rendering can't judge everything
  (fonts, print scale, personal preference). ERC should report 0 errors / 0 warnings.

## D. Known leftovers (low priority)

- [ ] Stray floating GND symbol in `phy.kicad_sch` at (43.18, 91.44) — pre-existing
  rev A cruft, harmless; delete on request.
- [ ] `current_consumption.md` has TBD figures awaiting the DP83867 power-table
  numbers per operating mode.
- [ ] Root title block still says "Gigabit EthernetCap, Rev V0.1, 2025-08-19" —
  bump revision/date if this rework warrants it.
- [ ] Flight-time matching on the RGMII (open since rev A) — becomes relevant again
  when routing resumes; the RGMII_TX/RGMII_RX netclasses and skew DRC rules are
  repaired and active.

## Verification status (for reference)

| Check | Result |
|---|---|
| ERC (last commit) | 0 errors, 58 warnings — the warnings are `lib_symbol_mismatch`, expected while the submodule is ahead of the committed sheets |
| ERC (working tree, 2026-07-27) | **6 errors, 3 warnings** — see the note below |
| Netlist vs rev A | identical node-sets (incl. power flags); only net *names* re-scoped (pass-through nets now `/io/*`) |
| IO pass-through | all 72 U1 pins match J2/J3 1:1 (scripted check) |
| Connectivity | fully hierarchical: 0 global labels, GND via power symbols, inter-sheet via ports |
| Libraries | 100 % `KL_*` + `power:` symbols, 100 % `KL_Footprints` footprints |
| BOM export | grouped, with MPN/Mouser/Digikey/LCSC columns |
| PCB file | byte-identical to tag `revA-routed` (rename only) |

> **ERC regression in the uncommitted working tree.** `kicad-cli sch erc` on the current
> tree reports 6 errors / 3 warnings, against 0 errors at `HEAD`. They are **not** from
> the supplier-field pass — re-running ERC with every one of those 205 field writes
> reverted gives the same 6 errors. They come from the uncommitted sheet edits that were
> already in the tree: 4 × `pin_to_pin` "Power output connected to Power output",
> 1 × `power_pin_not_driven`, 1 × `ground_pin_not_ground` (U1 pin 51 GND), plus
> `unconnected_wire_endpoint`, `pin_not_connected` and a `lib_symbol_mismatch` on
> `KL_Module:PocketBeagle2`. That last one is a one-character issue: the cached symbol
> in `io.kicad_sch` now has `Reference` = `U1` where the library says `U` (`HEAD` still
> says `U`). Worth resolving before the next commit.
