"""Greedy top-side placement + routing of U4 and the decoupling caps (stage 2).
Each cap: candidate poses nearest its anchor (free courtyard, pads clear of copper), then route the rail pad to
same-net copper and the GND pad to a new plane via; first pose where both route wins. Writes cap_place.json and
cap_routes.json (consumed by r_bot.build)."""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shapely
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union
import r_bot, router, fpgeo, ts
from crtyd import load_crtyd, placed
from model import outline, Plan

F, B = "F.Cu", "B.Cu"
GND, V33, V11, V25 = r_bot.GND, r_bot.V33, r_bot.V11, r_bot.V25
VOID = unary_union([box(189.3, 95.6, 203.0, 100.7), box(186.0, 100.7, 207.1, 111.0)])
KEEP_T = unary_union([box(189.3, 96.3, 202.0, 100.7), box(186.0, 100.7, 207.1, 111.0)])
KEEPOUT = {F: KEEP_T, B: KEEP_T, 'via': VOID}

ORDER = [  # ref, anchor
    ('C7', (196.1, 92.1)), ('C1', (194.0, 92.2)), ('C5', (198.55, 92.75)), ('C9', (204.2, 85.475)),
    ('C13', (203.8, 82.5)), ('C3', (189.5, 85.5)), ('C2', (189.5, 85.0)), ('C10', (195.8, 77.5)),
    ('C6', (196.3, 77.5)), ('C33', (202.7, 95.9)), ('C35', (205.0, 96.2)), ('C32', (205.0, 96.2)),
    ('C39', (194.3, 91.8)), ('C40', (198.3, 91.8)), ('C17', (196.3, 91.8)), ('C38', (195.8, 77.8)),
    ('C37', (196.3, 77.8)), ('C21', (203.5, 82.5)), ('C25', (190.0, 85.5)), ('C12', (190.0, 85.0)),
    ('C16', (203.5, 85.5)), ('C20', (203.5, 85.5)), ('C24', (190.0, 85.0)), ('C23', (201.0, 88.0)),
    ('C11', (202.7, 95.9)), ('C8', (202.7, 95.9)), ('C19', (202.7, 95.9)), ('C15', (202.7, 95.9)),
    ('C22', (204.0, 88.0)),
]
LEFT = {'C3': (188.4, 93.4), 'C25': (188.4, 94.5), 'C2': (188.4, 95.6), 'C12': (188.4, 96.7), 'C24': (189.5, 97.6),
        'C22': (188.6, 97.6)}


class Ctx:
    def __init__(s):
        s.pads, s.kept, s.removed, s.crt, s.C, s.NET = r_bot.base()
        s.prm = json.load(open('bot_prm.json'))
        s.D = r_bot.fixed(s.prm)
        s.world = router.World([p for p in s.pads], s.kept)
        s.world.add_plan(s.D.plan)
        cr = load_crtyd()
        s.court = [placed(c) for r, c in cr.items() if c['side'] == F and r not in ts.GONE and r != 'U1']
        s.court += [c for r, (c, side) in s.crt.items() if side == F]
        s.edge = outline()
        s.placed = {}
        s.routes = []      # plan items (dicts) added by the fitter

    def fcopper(s):
        return [i for i in s.world.items if F in i['layers']]


def add_route(ctx, net, res, w):
    runs, vias = res
    P = Plan()
    for L, pts in runs:
        P.seg(net, L, pts, w, tag='auto')
    for v in vias:
        P.via(net, v[0], v[1], tag='auto')
    ctx.world.add_plan(P)
    ctx.routes += [dict(kind=i['kind'], net=i['net'], layer=i['layers'][0] if i['kind'] == 'seg' else None,
                        a=i.get('a'), b=i.get('b'), w=i.get('w'), x=i.get('x'), y=i.get('y')) for i in P.items]
    return P


def try_route(ctx, pad, net, target_pt, gnd, widths=(0.3, 0.2), span=(3.0, 7.0)):
    for m in span:
        x0 = min(pad.center[0], target_pt[0]) - m; x1 = max(pad.center[0], target_pt[0]) + m
        y0 = min(pad.center[1], target_pt[1]) - m; y1 = max(pad.center[1], target_pt[1]) + m
        if gnd:
            x0, y0, x1, y1 = pad.center[0] - m / 2 - 0.5, pad.center[1] - m / 2 - 0.5, pad.center[0] + m / 2 + 0.5, pad.center[1] + m / 2 + 0.5
        for w in widths:
            try:
                res = router.route(ctx.world, net, pad.center, F, w, (x0, y0, x1, y1), start_geom=pad.poly,
                                   keepout=KEEPOUT, via_goal=gnd, max_expand=400_000)
            except ValueError:
                res = None
            if res:
                return res, w
    return None, None


def candidates(ctx, ref, anchor, R=6.0, step=0.1):
    lib = ts.libname(ref)
    courts = unary_union(ctx.court)
    fcu = [(i['net'], i['geom']) for i in ctx.fcopper()]
    tree = shapely.STRtree([g for _, g in fcu])
    out = []
    xs = np.arange(anchor[0] - R, anchor[0] + R + 1e-9, step)
    ys = np.arange(anchor[1] - R, anchor[1] + R + 1e-9, step)
    for rot in (0, 90, 180, 270):
        pads0, c0 = fpgeo.place(ref, lib, 0, 0, rot, ts.NETS[ref])
        for x in xs:
            for y in ys:
                d = math.hypot(x - anchor[0], y - anchor[1])
                if d > R:
                    continue
                out.append((d + (0.05 if rot in (90, 270) else 0), round(float(x), 3), round(float(y), 3), rot))
    out.sort()
    good = []
    edge_in = ctx.edge.buffer(-0.5)
    for d, x, y, rot in out:
        pads, c = fpgeo.place(ref, lib, x, y, rot, ts.NETS[ref])
        if c.intersection(courts).area > 1e-4:
            continue
        ok = True
        for p in pads:
            if not edge_in.contains(p.poly) or p.poly.intersects(KEEP_T):
                ok = False; break
            for j in tree.query(p.poly.buffer(0.17)):
                n, g = fcu[int(j)]
                if n != p.net and g.distance(p.poly) < 0.17:
                    ok = False; break
            if not ok:
                break
        if ok:
            good.append((d, x, y, rot, pads, c))
            if len(good) >= 600:
                break
    # thin out near-duplicates
    thin = []
    for g in good:
        if all(math.hypot(g[1] - h[1], g[2] - h[2]) > 0.25 or g[3] != h[3] for h in thin):
            thin.append(g)
    return thin


def fit_part(ctx, ref, anchor, tries=10):
    for R in (6.0, 12.0):
        cands = candidates(ctx, ref, anchor, R=R, step=0.1 if R < 7 else 0.2)
        rest = cands[6:]
        pick = cands[:6] + rest[::max(1, len(rest) // 10)][:10]
        for d, x, y, rot, pads, c in pick:
            # tentatively add pads as obstacles
            items0 = len(ctx.world.items)
            for p in pads:
                ctx.world.items.append(dict(net=p.net, layers={F}, geom=p.poly, drill=0.0, src=p))
            ok, routed = True, []
            nroutes = len(ctx.routes)
            for p in sorted(pads, key=lambda p: p.net == GND):
                if not p.net or p.net.startswith('unconnected'):
                    continue
                gnd = p.net == GND
                res, w = try_route(ctx, p, p.net, anchor, gnd)
                if res is None:
                    ok = False; break
                add_route(ctx, p.net, res, w)
            if ok:
                ctx.placed[ref] = (x, y, rot, F)
                ctx.court.append(c)
                print(f"{ref}: ({x}, {y}) rot {rot}  d={d:.2f}", flush=True)
                return True
            ctx.world.items = ctx.world.items[:items0]
            ctx.routes = ctx.routes[:nroutes]
    print(f"{ref}: FAILED", flush=True)
    return False


def route_u4(ctx, pins=("5", "1", "3", "2")):
    T = {"5": (198.31, 89.35), "1": (206.8, 94.0), "3": (206.8, 94.0), "2": None}
    for num, target in ((n, T[n]) for n in pins):
        p = [q for q in ctx.pads if q.ref == 'U4' and q.num == num][0]
        res, w = try_route(ctx, p, p.net, target or p.center, p.net == GND, widths=(0.4, 0.3), span=(4.0, 9.0))
        print("U4", num, p.net, "ok" if res else "FAILED", w, flush=True)
        if res:
            add_route(ctx, p.net, res, w)


def resume(ctx, place_file, routes_file):
    """re-load a previous pass: its parts (pads + courtyards) and routes become fixed"""
    for ref, (x, y, rot, side) in json.load(open(place_file)).items():
        pads, c = fpgeo.place(ref, ts.libname(ref), x, y, rot, ts.NETS[ref])
        for p in pads:
            ctx.world.items.append(dict(net=p.net, layers={F}, geom=p.poly, drill=0.0, src=p))
        ctx.court.append(c)
        ctx.placed[ref] = (x, y, rot, side)
    P = Plan()
    for it in json.load(open(routes_file)):
        if it['kind'] == 'seg':
            P.seg(it['net'], it['layer'], [tuple(it['a']), tuple(it['b'])], it['w'], 'auto')
        else:
            P.via(it['net'], it['x'], it['y'], tag='auto')
    ctx.world.add_plan(P)
    ctx.routes = json.load(open(routes_file))


if __name__ == "__main__":
    t0 = time.time()
    ctx = Ctx()
    extra = {}
    if '--resume' in sys.argv:
        resume(ctx, 'pass1_place.json', 'pass1_routes.json')
        extra = json.load(open('pass2_anchors.json'))
    else:
        route_u4(ctx, ("1", "3", "2"))
        fit_part(ctx, 'C18', (201.2, 93.5))       # XI shunt cap before the LDO output claims the pocket
        route_u4(ctx, ("5",))
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    only = only[0].split(',') if only else None
    for ref, anchor in ORDER:
        if only and ref not in only or ref in ctx.placed:
            continue
        fit_part(ctx, ref, tuple(extra.get(ref, LEFT.get(ref, anchor))))
    json.dump({k: list(v) for k, v in ctx.placed.items()}, open('cap_place.json', 'w'), indent=0)
    json.dump(ctx.routes, open('cap_routes.json', 'w'))
    print(f"done in {time.time() - t0:.0f}s; placed {len(ctx.placed)}/{len(ORDER)}")
