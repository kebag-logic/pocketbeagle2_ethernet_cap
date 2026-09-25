# Rev B re-spin helper scripts

These are read-only planning tools plus one kipy script, which clears copper. See `documentation/handover_revb_respin.md`.

Requirements: Python 3 with `shapely` and `kipy==0.8.0`. KiCad 10 must be running with IPC enabled for the kipy scripts.

| Script | What it does |
|--------|--------------|
| `sexp.py` | Minimal s-expression parser. |
| `model.py` | Loads pads and tracks from the saved `.kicad_pcb`. `Plan.seg/via/check` does clearance and edge checks for planned copper with shapely. |
| `plan_mdi.py [bumps…]` | MDI pair routes with the P/N skew bumps. Run with `1.2745 1.2745 1.2745 1.3455` to get 0 issues. |
| `plan_led.py` | LED0–2 gate routes: F stubs, vias, then B.Cu lanes around the top-left arc, necked to 0.10 mm. |
| `plan_rgmii.py` | **Reference only.** The old shortest-path RGMII plan, superseded by the length-matched re-spin. |
| `rgmii_len.py` | Measures the cape-side RGMII lengths per line (PHY pin → R → PB2 pad) and prints the PB2 module lengths. |
| `schio.py <sheet.kicad_sch>` | Read-only schematic geometry helper: pin positions and wire clusters. |
| `ses_parse.py` | Reads Freerouting `.ses` wiring into segment and via lists. |
| `clear_copper.py` | **Destructive.** Removes every track, via and zone from the live board in one KiCad undo step. |

`reference/board_before_respin.kicad_pcb` is the board just before the copper was cleared on 2026-09-25. It has the MDI, power, slow-net and LED routing.

## `topside/`: all SMD parts moved to F.Cu (2026-09-25)

These are archived as run. They also import the working-copy planners (`rg.py`, `d_*.py`, `meander.py`, `audit_angles.py`), which are not archived, so treat them as a record, not a ready-to-run tool.

| Script | What it does |
|--------|--------------|
| `fpgeo.py` | Library footprint pads and courtyards for what-if placements. |
| `prune.py` | Finds the copper that dangles once a set of footprints leaves; used to clear their old bottom-side routing. |
| `ts.py` | The stage placement table (x, y, rot, side) plus courtyard and pad-clearance checks. |
| `r_top.py` | Stage 1. LED drivers Q1–Q3, D-K lanes, rebuilt LED gate lanes, MDIO/INT pull-ups, and the TD0/TD2 series resistors with their re-matched accordions. |
| `r_bot.py` | Stage 2. TD3 (R11) re-matched, TX_CLK (R14), R7 strap, CLK_OUT/1V1 test points moved to B.Cu. |
| `router.py` | 2-layer grid router. It uses 8 directions with turns of 45° or less, places vias, and stays clear of other-net copper and keepouts. |
| `capfit.py` | Greedy placement of U4 and the 30 caps nearest their pins. Each part is routed rail to copper and GND to a plane via. Results go to `cap_place.json` and `cap_routes.json`. |
| `conn.py` | Per-net island check: pads, tracks and vias, with GND vias joining the planes. |
| `apply_stage.py` | Checks live pads against the model, removes the pruned copper (exact endpoints), then pushes the plan. |
| `silk_place.py` | Places reference designators and P1/P2 labels at 1.0/0.15 mm with no overlaps. |

`../make_production.py` writes `production/`: the Gerber and drill zip, the JLCPCB BOM (LCSC part numbers) and the CPL.
