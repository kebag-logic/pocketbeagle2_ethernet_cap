"""Simplified 3D model of the Bel 1840888-1 MagJack (own work, dimensions from KL_Footprints:BEL_1840888-1).
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

H = 13.5                                  # body height (standard-height version)
X0, X1, Y0, Y1 = -9.335, 9.335, -10.85, 10.8   # footprint fab outline; front (cable) face at footprint +Y


def box(x0, y0, z0, x1, y1, z1):
    """footprint-coordinate box -> model coordinates (y flipped)"""
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, -y1, z0), gp_Pnt(x1, -y0, z1)).Shape()


def cyl(x, y, d, z0, z1):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, -y, z0), gp_Dir(0, 0, 1)), d / 2, z1 - z0).Shape()


body = box(X0, Y0, 0.0, X1, Y1, H)
opening = box(-5.85, Y1 - 12.0, 2.6, 5.85, Y1 + 0.1, 2.6 + 8.2)      # RJ45 plug cavity, tab up
body = BRepAlgoAPI_Cut(body, opening).Shape()
cavity = box(-5.85, Y1 - 12.0, 2.6, 5.85, Y1 - 11.9, 2.6 + 8.2)       # dark back wall of the cavity
contacts = box(-4.2, Y1 - 11.9, 2.6 + 6.6, 4.2, Y1 - 6.0, 2.6 + 8.2)  # contact block at the cavity top
led_l = box(X0 + 0.9, Y1 - 0.05, H - 3.0, X0 + 3.4, Y1 + 0.2, H - 1.3)
led_r = box(X1 - 3.4, Y1 - 0.05, H - 3.0, X1 - 0.9, Y1 + 0.2, H - 1.3)
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
add(led_l, "led_green", (0.10, 0.85, 0.10))
add(led_r, "led_yellow", (0.95, 0.80, 0.10))
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
