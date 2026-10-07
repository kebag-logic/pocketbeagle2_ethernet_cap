"""All-SMT-on-top rework: new placements (F.Cu; test points to B.Cu), pruned copper, lookup helpers."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Point
from shapely import affinity
from model import load, Pad, outline
from crtyd import load_crtyd, placed
from prune import prune
import fpgeo

F, B = "F.Cu", "B.Cu"
LIB = {'C': 'C_0402', 'R': 'R_0402', 'R29': 'R_1206', 'C36': 'C_1210', 'Q': 'SOT-23', 'U4': 'SOT-23-5', 'TP': 'TestPoint_SMD_1.0x1.0mm'}

# ref: (x, y, rot, side)
PLACE = {
    # stage 3: chassis bridge parts off the J1 shield-pin holes (their chassis pads covered ~45 % of S1/S2)
    'R29': (188.5, 99.8, 270, F), 'C36': (204.6, 99.85, 270, F),
    'C33': (205.25, 97.075, 0, F),     # LDO output cap in the gap between U4 and C36
}
CAPS = ['C24', 'C40', 'C12', 'C35', 'C5', 'C32']      # in the way of the moved R29 / C36, re-fitted
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cap_place.json')):
    import json as _j
    for k, v in _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cap_place.json'))).items():
        PLACE[k] = tuple(v)
MOVE_B = ['C1', 'C10', 'C11', 'C12', 'C13', 'C15', 'C16', 'C17', 'C18', 'C19', 'C2', 'C20', 'C21', 'C22', 'C23', 'C24',
          'C25', 'C3', 'C33', 'C37', 'C38', 'C39', 'C40', 'C5', 'C6', 'C7', 'C8', 'C9',
          'Q1', 'Q2', 'Q3', 'R10', 'R11', 'R14', 'R20', 'R21', 'R24', 'R31', 'R32', 'R7', 'R8', 'U4']
TP_TO_B = ['TP1', 'TP2', 'TP8']
EXTRA_GONE = set(CAPS)     # re-placed later in this stage (auto placer / by hand)
# our GND stitching / old Q-source vias in the way of the new top-side copper
REMOVE_VIAS = {(188.5, 98.2), (204.6, 98.1), (206.0, 97.75), (205.0, 96.57), (204.43, 96.55)}
GONE = set(PLACE) | EXTRA_GONE   # parts re-placed in this stage (their old pads / dangling copper go)

board_pads, fps, board_tracks = load()
NETS = {}
for p in board_pads:
    NETS.setdefault(p.ref, {})[p.num] = p.net


def libname(ref):
    if ref in ('U4', 'R29', 'C36'): return LIB[ref]
    if ref.startswith('TP'): return LIB['TP']
    return LIB[ref[0]]


def new_pads(place=None):
    place = PLACE if place is None else place
    out, crt = [], {}
    for ref, (x, y, r, side) in place.items():
        pads, c = fpgeo.place(ref, libname(ref), x, y, r, NETS[ref])
        if side == B:
            for p in pads:
                p.layers = [B]
        out += pads; crt[ref] = (c, side)
    return out, crt


def state(place=None):
    """pads (board minus moved + placed), kept tracks, removed tracks, new courtyards"""
    kept, rem = prune(board_pads, board_tracks, GONE)
    rv = [t for t in kept if t['kind'] == 'via' and (t['x'], t['y']) in REMOVE_VIAS]
    missing = REMOVE_VIAS - {(t['x'], t['y']) for t in rv} - {(t['x'], t['y']) for t in rem if t['kind'] == 'via'}
    assert not missing, missing
    kept = [t for t in kept if t not in rv]; rem = rem + rv
    kept, rem2 = prune(board_pads, kept, GONE)       # chains left dangling by the removed vias
    rem = rem + rem2
    np_, crt = new_pads(place)
    pads = [p for p in board_pads if p.ref not in GONE] + np_
    return pads, kept, rem, crt


def lookup(pads):
    m = {(p.ref, p.num): p for p in pads}
    return (lambda r, n: m[(r, n)].center), (lambda r, n: m[(r, n)].net)


def check_place(pads, tracks, crt, place=None):
    place = PLACE if place is None else place
    cr = load_crtyd()
    out = []
    geo = {r: (placed(c), c['side']) for r, c in cr.items() if r not in GONE}
    geo.update(crt)
    refs = sorted(geo)
    for r in place:
        g, s = geo[r]
        for o in refs:
            if o == r or geo[o][1] != s or o in ('U1',):
                continue
            a = g.intersection(geo[o][0]).area
            if a > 1e-4 and not (o in place and o < r):
                out.append(f"CRTYD {r} x {o} {a:.3f}")
    edge = outline()
    newp = [p for p in pads if p.ref in place]
    for p in newp:
        if edge.exterior.distance(p.poly) < 0.5 or not edge.contains(p.poly):
            out.append(f"EDGE {p}")
        for q in pads:
            if q.ref == p.ref or q.net == p.net or not set(q.layers) & set(p.layers):
                continue
            d = q.poly.distance(p.poly)
            if d < 0.15:
                out.append(f"PAD {p} x {q} {d:.3f}")
        for t in tracks:
            if t['net'] == p.net:
                continue
            if t['kind'] == 'seg':
                if t['layer'] not in p.layers:
                    continue
                from shapely.geometry import LineString
                d = LineString(t['pts']).distance(p.poly) - t['w'] / 2
            else:
                d = Point(t['x'], t['y']).distance(p.poly) - t['d'] / 2
            if d < 0.15:
                out.append(f"CU {p} x {t['net']} {t.get('layer', 'via')} {t.get('pts', (t.get('x'), t.get('y')))} {d:.3f}")
    return out


if __name__ == "__main__":
    pads, kept, rem, crt = state()
    for e in check_place(pads, kept, crt):
        print(e)
    if len(sys.argv) > 1:
        from netview import view
        b = tuple(map(float, sys.argv[2:6]))
        view(sys.argv[1], b, sys.argv[6], pads, kept)
