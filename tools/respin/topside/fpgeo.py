"""Library footprint geometry (pads + courtyard) for what-if F.Cu placements."""
import math, functools
from sexp import parse, find, walk
from shapely.geometry import box, Point
from shapely import affinity
from model import rot, Pad
LIB = "/home/alex/prjs/ames/switch/pocketbeagle2_ethernet_cap/kebag_logic_kicad_library/footprints/KL_Footprints.pretty"

@functools.lru_cache(None)
def lib(name):
    t = parse(open(f"{LIB}/{name}.kicad_mod").read())
    pads = []
    for p in find(t, "pad"):
        a = find(p, "at")[0]; s = find(p, "size")[0]
        pads.append((p[1].strip('"'), float(a[1]), float(a[2]), float(s[1]), float(s[2]), p[3]))
    pts = []
    for n in walk(t):
        if isinstance(n, list) and n and n[0] in ('fp_line', 'fp_rect', 'fp_poly'):
            ly = [c for c in n if isinstance(c, list) and c and c[0] == 'layer']
            if ly and 'CrtYd' in ly[0][1]:
                pts += [(float(c[1]), float(c[2])) for c in walk(n) if isinstance(c, list) and c and c[0] in ('start', 'end', 'xy')]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return pads, (min(xs), min(ys), max(xs), max(ys))

def place(ref, name, x, y, r, nets):
    """global F.Cu pads (model.Pad) and courtyard polygon; nets: {padnum: net}"""
    pads, cb = lib(name)
    out = []
    for num, px, py, w, h, shape in pads:
        g = box(-w / 2, -h / 2, w / 2, h / 2)
        g = affinity.rotate(g, -r, origin=(0, 0))
        dx, dy = rot(px, py, r)
        g = affinity.translate(g, x + dx, y + dy)
        out.append(Pad(ref, num, nets.get(num, ""), ["F.Cu"], g, (x + dx, y + dy), 0.0))
    c = affinity.translate(affinity.rotate(box(*cb), -r, origin=(0, 0)), x, y)
    return out, c
