"""Stage 3: R29 / C36 chassis-bridge pads off the J1 shield-pin holes; re-fit the caps in the way; re-route U4 IN."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts, router, capfit, conn
from rg import Design
from crtyd import load_crtyd, placed

F, B = "F.Cu", "B.Cu"
CH = "/network/rj45_connector_port0/CHASSIS"


class Ctx(capfit.Ctx):
    def __init__(s):
        s.pads, s.kept, s.removed, s.crt = ts.state()
        s.C, s.NET = ts.lookup(s.pads)
        s.D = Design()
        # chassis pads straight down into the shield-pin rings (same net, the pads touch the ring edge)
        for ref, pin in (("R29", "S2"), ("C36", "S1")):
            c = s.C(ref, "2")
            s.D.run('-', CH, F, [c, (c[0], 102.2)], 0.5)
        s.world = router.World(list(s.pads), s.kept)
        s.world.add_plan(s.D.plan)
        cr = load_crtyd()
        s.court = [placed(c) for r, c in cr.items() if c['side'] == F and r not in ts.GONE and r != 'U1']
        s.court += [c for r, (c, side) in s.crt.items() if side == F]
        from model import outline
        s.edge = outline()
        s.placed = {}
        s.routes = []


def build(prm=None):
    ctx_routes = json.load(open('fix_routes.json'))
    D = Design()
    pads, kept, removed, crt = ts.state()
    C, NET = ts.lookup(pads)
    for ref in ("R29", "C36"):
        c = C(ref, "2")
        D.run('-', CH, F, [c, (c[0], 102.2)], 0.5)
    for it in ctx_routes:
        if it['kind'] == 'seg':
            D.plan.seg(it['net'], it['layer'], [tuple(it['a']), tuple(it['b'])], it['w'], 'auto')
        else:
            D.plan.via(it['net'], it['x'], it['y'], tag='auto')
    return D


if __name__ == "__main__":
    ctx = Ctx()
    # GND sides of the bridge parts and any U4 pin that lost its feed
    for ref in ("R29", "C36"):
        p = [q for q in ctx.pads if q.ref == ref and q.num == "1"][0]
        res, w = capfit.try_route(ctx, p, p.net, p.center, True, widths=(0.5, 0.3))
        print(ref, "GND", "ok" if res else "FAILED"); capfit.add_route(ctx, p.net, res, w)
    isl = conn.islands(ctx.pads, ctx.kept, None)
    lonely = [q.num for q in ctx.pads if q.ref == 'U4' and q.net in isl and any(c == [f'U4.{q.num}'] for c in isl[q.net])]
    print("U4 pins left without copper:", lonely)
    if lonely:
        capfit.route_u4(ctx, lonely)
    # C33 is placed by hand: route its 2V5 pad to the LDO output net and its GND pad to C36.1 / a plane via
    for num in ("1", "2"):
        p = [q for q in ctx.pads if q.ref == 'C33' and q.num == num][0]
        res, w = capfit.try_route(ctx, p, p.net, (203.9, 95.6), p.net == 'GND', widths=(0.3, 0.25))
        print("C33", num, p.net, "ok" if res else "FAILED"); capfit.add_route(ctx, p.net, res, w)
    anchors = {'C24': (188.6, 96.2), 'C40': (191.5, 94.5), 'C12': (187.6, 95.9), 'C35': (205.9, 93.9), 'C5': (198.5, 92.8),
               'C32': (206.0, 96.0)}
    for ref in ('C35', 'C32', 'C5', 'C24', 'C12', 'C40'):
        capfit.fit_part(ctx, ref, anchors[ref])
    json.dump({k: list(v) for k, v in ctx.placed.items()}, open('cap_place.json', 'w'))
    json.dump(ctx.routes, open('fix_routes.json', 'w'))
