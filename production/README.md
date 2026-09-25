# JLCPCB production files

Generated with `tools/make_production.py` from the committed board and schematic. Regenerate after any change.

| File | Use |
|------|-----|
| `pocketbeagle2_ethernet_cap_gerber.zip` | PCB order. Contains the Gerbers for F/In1/In2/B copper, mask, paste, silk and edge, plus PTH/NPTH Excellon drill files. |
| `pocketbeagle2_ethernet_cap_bom_jlcpcb.csv` | Assembly BOM: Comment, Designator, Footprint, LCSC Part #. |
| `pocketbeagle2_ethernet_cap_cpl_jlcpcb.csv` | Pick and place: Designator, Mid X/Y, Layer, Rotation. |
| `pocketbeagle2_ethernet_cap_assembly.pdf` | Assembly drawing, vector (zoom in). Every reference sits on its part: top page and bottom page. |

## PCB order settings

- **4 layers, 1.6 mm, JLC04161H-3313 stackup** (F / 0.1 mm prepreg / In1 / core / In2 / 0.1 mm prepreg / B).
- In1 and In2 are both solid GND.
- **Order impedance control.** Controlled nets:
  - RGMII: 50 Ω single-ended on F.Cu/B.Cu over GND, drawn at 0.15 mm.
  - MDI: 100 Ω differential, drawn at 0.13 mm width with a 0.2 mm gap.
  - Ask JLC to adjust the widths to their stackup. Their 3313 calculator gives about 0.17–0.19 mm for 50 Ω.
- Minimum track and space are 0.1/0.15 mm. Vias are 0.45 mm with a 0.2 mm drill. Copper to edge is at least 0.5 mm. All are within JLC standard capability.

## Assembly (single-sided, top)

- Every SMD part is on the top side. The bottom has only J1 and the test pads TP1/2/4/6/8, which get no part.
- **Not in the JLC BOM/CPL:**
  - U1: the PocketBeagle 2 plugs onto J2/J3.
  - J1: Bel 1840888-1 magjack, a THT part on the bottom. It isn't stocked at LCSC/JLC, so hand-solder it or send it as consigned stock (DigiKey 5923-1840888-1-ND).
  - TP1–TP8: test pads only.
- J2/J3 (HC-PZ254-11.5L-2x18PZ, C41376109) are THT on the top. JLC fits them as through-hole assembly.
- Every LCSC number in the BOM was in stock when generated. Low stock to watch: U2 DP83867IRPAPR C477933 (18 pcs), C36 C2167834 (67 pcs), U4 TPS7A2025PDBVR C2869949 (162 pcs).
- Check rotations in JLC's placement preview, especially SOT-23 (Q1–Q3), SOT-23-5 (U3, U4), HTQFP-64 (U2), and polarised parts D1–D3. JLC's package origins can differ from KiCad's.

## Silkscreen

- Legend text is at the JLC minimum: 1.0 mm character height, 0.15 mm stroke, with narrowed 0.65 mm character width.
- 64 of 81 references fit without touching pads or other text.
- 17 crowded 0402 parts have no room for a legible reference: the right-edge cap column, the bottom-left cap bank and around U4. Their references are hidden on the silkscreen. They appear in the assembly drawing and on F.Fab.
