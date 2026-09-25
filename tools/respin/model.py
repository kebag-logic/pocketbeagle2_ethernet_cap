"""Read-only board model for route planning: pads from the saved .kicad_pcb,
planned copper checked with shapely. Never writes the board."""
import math, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from sexp import parse, find, walk
from shapely.geometry import Point, LineString, Polygon, box
from shapely import affinity
from shapely.ops import unary_union

BOARD = "/home/alex/prjs/ames/switch/pocketbeagle2_ethernet_cap/pocketbeagle2_ethernet_cap.kicad_pcb"
CU = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]


def rot(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)


class Pad:
    def __init__(s, ref, num, net, layers, poly, center, drill):
        s.ref, s.num, s.net, s.layers, s.poly, s.center, s.drill = ref, num, net, layers, poly, center, drill

    def __repr__(s):
        return f"{s.ref}.{s.num}[{s.net}]@({s.center[0]:.3f},{s.center[1]:.3f})"


def load(path=BOARD):
    t = parse(open(path).read())
    pads, fps, tracks = [], {}, []
    for fp in find(t, "footprint"):
        at = find(fp, "at")[0]
        X, Y = float(at[1]), float(at[2])
        R = float(at[3]) if len(at) > 3 else 0.0
        side = find(fp, "layer")[0][1].strip('"')
        ref = [p[2] for p in find(fp, "property") if p[1] == '"Reference"'][0].strip('"')
        fps[ref] = (X, Y, R, side)
        for p in find(fp, "pad"):
            num = p[1].strip('"')
            kind, shape = p[2], p[3]
            pa = find(p, "at")[0]
            px, py = float(pa[1]), float(pa[2])
            pr = float(pa[3]) if len(pa) > 3 else 0.0
            sz = find(p, "size")[0]
            w, h = float(sz[1]), float(sz[2])
            ly = [l.strip('"') for l in find(p, "layers")[0][1:]]
            if "*.Cu" in ly:
                ly = CU[:]
            ly = [l for l in ly if l in CU]
            nt = find(p, "net")
            net = nt[0][-1].strip('"') if nt else ""
            dx, dy = rot(px, py, R)
            cx, cy = X + dx, Y + dy
            if shape == "circle":
                poly = Point(cx, cy).buffer(w / 2, 32)
            elif shape == "oval":
                r = min(w, h) / 2
                L = max(w, h) - 2 * r
                seg = LineString([(-L / 2, 0), (L / 2, 0)]) if w >= h else LineString([(0, -L / 2), (0, L / 2)])
                poly = seg.buffer(r, 32)
                poly = affinity.rotate(poly, -pr, origin=(0, 0))
                poly = affinity.translate(poly, cx, cy)
            else:
                poly = box(-w / 2, -h / 2, w / 2, h / 2)
                poly = affinity.rotate(poly, -pr, origin=(0, 0))
                poly = affinity.translate(poly, cx, cy)
            dr = find(p, "drill")
            drill = float(dr[0][1]) if dr and len(dr[0]) > 1 and dr[0][1] not in ("oval",) else 0.0
            if kind == "np_thru_hole":
                net = "<NPTH>"
                ly = CU[:]
            pads.append(Pad(ref, num, net, ly, poly, (cx, cy), drill))
    for s in find(t, "segment"):
        st, en = find(s, "start")[0], find(s, "end")[0]
        tracks.append(dict(kind="seg", layer=find(s, "layer")[0][1].strip('"'), net=find(s, "net")[0][-1].strip('"'),
                           w=float(find(s, "width")[0][1]),
                           pts=[(float(st[1]), float(st[2])), (float(en[1]), float(en[2]))]))
    for v in find(t, "via"):
        a = find(v, "at")[0]
        tracks.append(dict(kind="via", net=find(v, "net")[0][-1].strip('"'), x=float(a[1]), y=float(a[2]),
                           d=float(find(v, "size")[0][1])))
    return pads, fps, tracks


def outline():
    # rounded rectangle drawn with add_board_outline
    x1, y1, x2, y2, r = 178.9576, 55.0, 214.25, 110.2725, 10.25
    return box(x1 + r, y1 + r, x2 - r, y2 - r).buffer(r, 64)


class Plan:
    def __init__(s):
        s.items = []  # dict(kind, net, layer(s), geom, desc)

    def seg(s, net, layer, pts, w, tag=""):
        for a, b in zip(pts, pts[1:]):
            s.items.append(dict(kind="seg", net=net, layers=[layer], w=w, a=a, b=b,
                                geom=LineString([a, b]).buffer(w / 2, 16), tag=tag))

    def via(s, net, x, y, d=0.45, drill=0.2, tag=""):
        s.items.append(dict(kind="via", net=net, layers=CU[:], d=d, drill=drill, x=x, y=y,
                            geom=Point(x, y).buffer(d / 2, 32), tag=tag))

    def check(s, pads, tracks=(), clr=0.15, edge=0.5, verbose=True, clr_fn=None):
        edge_poly = outline()
        errs = []
        existing = []
        for t in tracks:
            if t["kind"] == "seg":
                existing.append(dict(net=t["net"], layers=[t["layer"]], geom=LineString(t["pts"]).buffer(t["w"] / 2, 16), tag="existing"))
            else:
                existing.append(dict(net=t["net"], layers=CU[:], geom=Point(t["x"], t["y"]).buffer(t["d"] / 2, 32), tag="existing via"))
        for i, it in enumerate(s.items):
            c = clr_fn(it) if clr_fn else clr
            # edge
            d_edge = edge_poly.exterior.distance(it["geom"])
            if not edge_poly.contains(it["geom"]) or d_edge < edge:
                errs.append(f"EDGE {d_edge:.3f} {it['net']} {it['tag']}")
            for p in pads:
                if p.net == it["net"]:
                    continue
                if not set(p.layers) & set(it["layers"]):
                    continue
                d = p.poly.distance(it["geom"])
                if d < c - 1e-4:
                    errs.append(f"PAD {d:.3f} {it['net']} {it['tag']} vs {p}")
            for j, o in enumerate(s.items + existing):
                if j <= i and j < len(s.items):
                    continue
                if o["net"] == it["net"]:
                    continue
                if not set(o["layers"]) & set(it["layers"]):
                    continue
                d = o["geom"].distance(it["geom"])
                if d < c - 1e-4:
                    errs.append(f"CU {d:.3f} {it['net']} {it['tag']} vs {o['net']} {o['tag']}")
        if verbose:
            for e in errs:
                print(e)
            print(f"{len(errs)} issues / {len(s.items)} items")
        return errs


def padmap(pads):
    m = {}
    for p in pads:
        m[(p.ref, p.num)] = p
    return m


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
