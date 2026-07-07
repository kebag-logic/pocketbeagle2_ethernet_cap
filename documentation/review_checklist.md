# Review checklist

Everything awaiting user review/decision after the shish-lan-style restructure, the KL
library migration, the expansion (stacking header) rework and the readability pass.
Check items off here; details live in [library_additions.md](library_additions.md) and
[connections.md](connections.md).

## A. Library parts (before pushing the submodule)

- [ ] **1.1 V LDO** — `TPS7A2011PDBVR` follows TI's numbering but no distributor
  listing was found. Confirm the part, or decide to use the DP83867's internal core
  LDO instead (frees one LDO). *(rev A used a DSBGA part number on SOT-23-5 pads for
  both rails.)*
- [ ] **RJ45 `1840888-1`** — manufacturer/datasheet unknown (SnapEDA import said
  "BEL", the number format says TE Connectivity). Provide the datasheet used for
  rev A; needed for the `Datasheet` field and MDI pin documentation.
- [ ] **BSS138** — multi-sourced; onsemi `BSS138LT1G` was chosen. Confirm or name a
  preferred source (e.g. Nexperia BSS138P).
- [ ] **Capacitor specs** — derived choices: Murata GRM155, X7R/C0G/X5R, 50/16/6.3 V.
  The 10 µF is only 6.3 V-rated on the 3V3 rail — check the derating policy, or
  provide the rev A BOM to match exactly.
- [ ] **Resistors** — Vishay CRCW0402 MPNs derived from the house family
  (`CRCW0402…FKEDC`); spot-check one or two against a distributor.
- [ ] **18x02 stacking header** — MPN `BHR-36-VUA` derived from the house
  BHR-20-VUA (Adam Tech); confirm it is orderable.
- [ ] **TBD supplier fields** — remaining Digikey/LCSC/some Mouser order numbers:
  fill manually, or request a lookup pass.
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
- [ ] **Waived ERC warnings** — 3× `same_local_global_label` on the `VDD_*` rails
  (local labels inside child sheets intentionally share the global names;
  connectivity netlist-verified against rev A).
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
  (fonts, print scale, personal preference). ERC should report 0 errors /
  3 waived warnings.

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
| ERC | 0 errors, 3 waived warnings (baseline was 35 violations) |
| Netlist vs rev A | identical node-sets (incl. power flags); only net *names* re-scoped (pass-through nets now `/io/*`) |
| IO pass-through | all 72 U1 pins match J2/J3 1:1 (scripted check) |
| Connectivity | fully hierarchical: 0 global labels, GND via power symbols, inter-sheet via ports |
| Libraries | 100 % `KL_*` + `power:` symbols, 100 % `KL_Footprints` footprints |
| BOM export | grouped, with MPN/Mouser/Digikey/LCSC columns |
| PCB file | byte-identical to tag `revA-routed` (rename only) |
