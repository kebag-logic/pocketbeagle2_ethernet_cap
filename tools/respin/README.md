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
