"""Courtyards of placed footprints (from the saved board) + what-if placement checks."""
import math
from sexp import parse, find, walk
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
from model import BOARD

def _rot(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)

def local_crtyd(fp):
    """local courtyard polygon (footprint coords, as stored) and its layer"""
    geoms, layer = [], None
    for n in walk(fp):
        if isinstance(n, list) and n and n[0] in ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle', 'fp_arc'):
            ly = [c for c in n if isinstance(c, list) and c and c[0] == 'layer']
            if not ly or 'CrtYd' not in ly[0][1]:
                continue
            layer = ly[0][1].strip('"')
            pts = [(float(c[1]), float(c[2])) for c in walk(n) if isinstance(c, list) and c and c[0] in ('start', 'end', 'xy', 'mid')]
            geoms.extend(pts)
    if not geoms:
        return None, None
    xs, ys = [p[0] for p in geoms], [p[1] for p in geoms]
    return box(min(xs), min(ys), max(xs), max(ys)), layer

def load_crtyd(path=BOARD):
    t = parse(open(path).read())
    out = {}
    for fp in find(t, 'footprint'):
        ref = [p[2] for p in find(fp, 'property') if p[1] == '"Reference"'][0].strip('"')
        at = find(fp, 'at')[0]
        X, Y = float(at[1]), float(at[2]); R = float(at[3]) if len(at) > 3 else 0.0
        side = find(fp, 'layer')[0][1].strip('"')
        g, layer = local_crtyd(fp)
        if g is None:
            continue
        out[ref] = dict(local=g, x=X, y=Y, rot=R, side=side, lib=fp[1].strip('"'))
    return out

def placed(c, x=None, y=None, rot=None, side=None):
    """global courtyard polygon for crtyd entry c, optionally at a new pose. Board file stores local coords
    already mirrored for B-side footprints, so only rotate+translate."""
    x = c['x'] if x is None else x; y = c['y'] if y is None else y; rot = c['rot'] if rot is None else rot
    g = c['local']
    if side is not None and side != c['side']:
        g = affinity.scale(g, xfact=1, yfact=-1, origin=(0, 0))   # flip (KiCad flips top/bottom about X)
    g = Polygon([_rot(px, py, rot) for px, py in g.exterior.coords])
    return affinity.translate(g, x, y)

def overlaps(cr, poses):
    """poses: {ref: (x, y, rot, side)} overriding; returns list of overlapping pairs (same side, area>1e-4)"""
    geo = {}
    for ref, c in cr.items():
        if ref in poses:
            x, y, r, s = poses[ref]
            geo[ref] = (placed(c, x, y, r, s), s)
        else:
            geo[ref] = (placed(c), c['side'])
    bad = []
    refs = sorted(geo)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if geo[a][1] != geo[b][1]:
                continue
            if a in ('J2', 'J3', 'U1') and b in ('J2', 'J3', 'U1'):
                continue
            ar = geo[a][0].intersection(geo[b][0]).area
            if ar > 1e-4 and (a in poses or b in poses):
                bad.append((a, b, round(ar, 3)))
    return bad

if __name__ == "__main__":
    cr = load_crtyd()
    for r in ('J1', 'U4', 'C1', 'TP1', 'R29', 'C36', 'J3', 'U2', 'U1'):
        print(r, cr[r]['side'], cr[r]['rot'], [round(v, 2) for v in placed(cr[r]).bounds])
    print(overlaps(cr, {}))
