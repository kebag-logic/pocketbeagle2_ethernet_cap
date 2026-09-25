# Build outputs: PocketBeagle 2 Ethernet cape, rev B

Everything needed to fabricate and assemble the board, generated from the committed schematic and PCB with:

```
python tools/make_build.py            # needs kicad-cli (KiCad 10); drawing needs shapely + matplotlib
python tools/make_build.py --no-step  # skip the 3D STEP export
```

Regenerate after every design change. Don't edit these files by hand.

```
build/
├── fabrication/
│   ├── pocketbeagle2_ethernet_cap_gerber.zip   ← upload this to JLCPCB (PCB order)
│   ├── gerber/                                 Gerber X2 layers + Excellon PTH/NPTH drill + drill maps + job file
│   └── pocketbeagle2_ethernet_cap.ipc          IPC-D-356 netlist (bare-board electrical test)
├── assembly/
│   ├── pocketbeagle2_ethernet_cap_bom_jlcpcb.csv   ← JLCPCB SMT assembly BOM (Comment, Designator, Footprint, LCSC #)
│   ├── pocketbeagle2_ethernet_cap_cpl_jlcpcb.csv   ← JLCPCB pick & place (Designator, Mid X/Y, Layer, Rotation)
│   ├── pocketbeagle2_ethernet_cap_bom_full.csv     every part, with MPN, LCSC, DigiKey, Mouser, assembled yes/no
│   └── pocketbeagle2_ethernet_cap_assembly.pdf     assembly drawing, every reference on its part (vector, zoom in)
└── docs/
    ├── pocketbeagle2_ethernet_cap_schematic.pdf
    ├── pocketbeagle2_ethernet_cap_cape.step        3D of the assembled cape (without the PocketBeagle 2)
    └── pocketbeagle2_ethernet_cap_drc.rpt          DRC report: 0 errors, warnings listed below
```

## PCB order (JLCPCB)

- **4 layers, 1.6 mm, JLC04161H-3313 stackup.**
  - Layers: F / 0.1 mm prepreg / In1 GND / core / In2 GND / 0.1 mm prepreg / B.
  - Board size: 35.3 × 55.3 mm, with rounded corners.
- **Order impedance control**, and let JLC adjust the trace widths to their stackup:
  - RGMII: 50 Ω single-ended, drawn at 0.15 mm. Their 3313 calculator gives about 0.17–0.19 mm.
  - MDI: 100 Ω differential, drawn at 0.13 mm width with a 0.2 mm gap.
- Design limits, all within JLC standard capability:
  - Track 0.1 mm, space 0.15 mm.
  - Vias 0.45 mm with a 0.2 mm drill (0.125 mm ring).
  - Copper to edge ≥ 0.5 mm.
  - Legend text 1.0 mm high with a 0.15 mm stroke.
- J1 (the magjack) overhangs the bottom board edge by design.

## Assembly (JLCPCB, single-sided top)

- **Every SMD part is on the top side.**
- The bottom has only J1 and the test pads TP1/2/4/6/8, which get no part.
- J2/J3 (HC-PZ254-11.5L-2x18PZ, C41376109) are THT on the top. JLC fits them as through-hole assembly.
- **Not in the JLC BOM/CPL** (all are in `bom_full.csv`):
  - U1: the PocketBeagle 2 plugs onto J2/J3.
  - J1: Bel Fuse 1840888-1 magjack, THT on the bottom. It isn't stocked at LCSC/JLC, so hand-solder it (DigiKey 5923-1840888-1-ND).
  - TP1–TP8: test pads only.
- Every LCSC number was in stock when the files were generated. Low stock to watch:
  - U2 DP83867IRPAPR (C477933)
  - C36 (C2167834)
  - U4 TPS7A2025PDBVR (C2869949)
- **Check rotations in JLC's placement preview**, especially Q1–Q3 (SOT-23), U3/U4 (SOT-23-5), U2 (HTQFP-64) and the LEDs D1–D3. JLC's package origins can differ from KiCad's.

## Silkscreen

- 64 of 81 references are printed at 1.0 mm (0.65 mm character width).
- 17 densely packed 0402 parts have no room for a legible reference. Use the assembly drawing for those.

## DRC warnings (expected)

- J2/J3 share the PocketBeagle 2 (U1) holes by design.
- 4 library-mismatch notices.
- U4 legend clipped at J1.1 (an unused pad).
- J1 back-side legend past the edge (the overhang).
- VOUT is not connected on the cape, because the PocketBeagle 2 joins U1.24/U1.49 internally.
