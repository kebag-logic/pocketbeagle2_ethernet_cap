"""Simplified 3D model of the Bel/TRP 1840888-1 MagJack (own work; envelope from the manufacturer drawing).
Origin = footprint origin, +Z up from the mounting face, model Y = -footprint Y (KiCad convention)."""
import sys
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDataStd import TDataStd_Name
from OCP.IFSelect import IFSelect_RetDone

# TRP/Bel 1840888-1 drawing (LCSC C5876366): 16.13 max wide, 21.65 max deep, 13.75 high; no LEDs; latch tab down.
# The footprint fab outline (18.67 wide) includes the 1.27 mm EMI spring fingers on each side.
H = 13.75
X0, X1, Y0, Y1 = -8.065, 8.065, -10.85, 10.8   # front (cable) face at footprint +Y


def box(x0, y0, z0, x1, y1, z1):
    """footprint-coordinate box -> model coordinates (y flipped)"""
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, -y1, z0), gp_Pnt(x1, -y0, z1)).Shape()


def cyl(x, y, d, z0, z1):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, -y, z0), gp_Dir(0, 0, 1)), d / 2, z1 - z0).Shape()


body = box(X0, Y0, 0.0, X1, Y1, H)
ZC0, ZC1 = 3.2, 3.2 + 8.3                                              # RJ45 plug cavity (11.7 x 8.3)
opening = box(-5.85, Y1 - 12.0, ZC0, 5.85, Y1 + 0.1, ZC1)
latch = box(-1.7, Y1 - 12.0, ZC0 - 1.6, 1.7, Y1 + 0.1, ZC0 + 0.1)       # latch notch, tab down (towards the PCB)
body = BRepAlgoAPI_Cut(BRepAlgoAPI_Cut(body, opening).Shape(), latch).Shape()
cavity = box(-5.85, Y1 - 12.0, ZC0, 5.85, Y1 - 11.9, ZC1)               # dark back wall of the cavity
contacts = box(-4.2, Y1 - 11.9, ZC1 - 1.6, 4.2, Y1 - 6.0, ZC1)          # contact block at the cavity top
fingers = [box(x0, Y1 - 5.0, 3.0, x1, Y1 - 1.5, 9.5) for x0, x1 in ((X0 - 1.27, X0), (X1, X1 + 1.27))]  # EMI springs
pins = [cyl(x, y, 0.9, -3.3, 0.5) for x, y in (
    (-5.715, -8.89), (-4.445, -6.35), (-3.175, -8.89), (-1.905, -6.35), (-0.635, -8.89),
    (0.635, -6.35), (1.905, -8.89), (3.175, -6.35), (4.445, -8.89), (5.715, -6.35))]
shield = [cyl(x, -3.04, 1.5, -3.3, 0.5) for x in (-7.745, 7.745)]
pegs = [cyl(x, 0.0, 3.2, -3.0, 0.5) for x in (-5.715, 5.715)]

doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())


def add(shape, name, rgb):
    lab = st.AddShape(shape, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)


add(body, "shield", (0.78, 0.78, 0.80))
add(cavity, "cavity", (0.05, 0.05, 0.05))
add(contacts, "contacts", (0.83, 0.69, 0.22))
for i, f_ in enumerate(fingers):
    add(f_, f"emi_finger{i + 1}", (0.78, 0.78, 0.80))
for i, p in enumerate(pins):
    add(p, f"pin{i + 1}", (0.83, 0.69, 0.22))
for i, p in enumerate(shield):
    add(p, f"shield_pin{i + 1}", (0.78, 0.78, 0.80))
for i, p in enumerate(pegs):
    add(p, f"peg{i + 1}", (0.10, 0.10, 0.10))

w = STEPCAFControl_Writer()
w.SetColorMode(True); w.SetNameMode(True)
w.Transfer(doc, STEPControl_AsIs)
out = sys.argv[1]
assert w.Write(out) == IFSelect_RetDone
print("wrote", out)
