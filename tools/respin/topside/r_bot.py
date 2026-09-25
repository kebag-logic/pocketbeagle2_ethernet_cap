"""All-SMT-on-top, stage 2: TD3 (R11), TX_CLK (R14), RX_CTRL strap R7, CLK_OUT/1V1 test points on the bottom,
U4 and every decoupling cap on the top side (auto-placed nearest their pins, auto-routed with 45 deg corners)."""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts, fpgeo, router
from rg import Design, MODULE
from meander import accordion, serpentine
from shapely.geometry import box, Point
from shapely.ops import unary_union
from crtyd import load_crtyd, placed
from model import outline

F, B = "F.Cu", "B.Cu"
P = 0.6
TARGET = 99.671
GND, V33, V11, V25 = "GND", "/VDD_3V3", "/VDD_1V1", "/VDD_2V5"
# void under the magnetics and the chassis island: no power / GND stubs there
KEEP = unary_union([box(189.3, 95.6, 203.0, 100.7), box(186.0, 100.7, 207.1, 111.0)])


def base():
    pads, kept, removed, crt = ts.state()
    C, NET = ts.lookup(pads)
    return pads, kept, removed, crt, C, NET


def td3(D, C, NET, amp):
    net = NET("U2", "35")
    D.run('TD3', net, F, [C("U2", "35"), (199.31, 76.9)])
    D.via('TD3', net, 199.31, 76.9)
    xr, n = 205.39, 10
    x0 = xr - P * (n - 1)
    acc = accordion(x0, 71.0, 76.4, P, n, start_up=True, direction=1)
    serp, _ = serpentine((xr, 77.0), (xr, 83.0), +1, amp, P, 5, c=0.2)
    v = (xr, 83.35)
    D.run('TD3', net, B, [(199.31, 76.9), (199.31, 76.7), (199.61, 76.4), (x0 - 0.2, 76.4), (x0, 76.2)] + acc[1:-1] + serp + [v])
    D.via('TD3', net, *v)
    r2 = C("R11", "2")
    D.run('TD3', net, F, [v, (r2[0], v[1] + (v[0] - r2[0])), r2])
    r1, u = C("R11", "1"), C("U1", "55")
    cv = (r1[0] + 0.64, r1[1])          # CPU side drops to B: the TD1 lane (F, x 206.9) runs past U1.55
    D.run('TD3', NET("R11", "1"), F, [r1, cv])
    D.via('TD3', NET("R11", "1"), *cv)
    D.run('TD3', NET("R11", "1"), B, [cv, (cv[0] + (cv[1] - u[1]), u[1]), u])


def txclk(D, C, NET):
    p40 = C("U2", "40")
    net = NET("U2", "40")
    D.run('TX_CLK', net, F, [p40, (p40[0], 75.2)])
    D.via('TX_CLK', net, p40[0], 75.2)
    v = (180.65, 100.49)
    D.run('TX_CLK', net, B, [(p40[0], 75.2), (188.75, 75.2), (188.45, 75.5), (188.45, 93.8), (186.35, 95.9),
                             (186.35, 100.19), (186.05, 100.49), v])
    D.via('TX_CLK', net, *v)
    r2, r1 = C("R14", "2"), C("R14", "1")
    D.run('TX_CLK', net, F, [v, (v[0] - (v[1] - r2[1]), r2[1]), r2])
    u = C("U1", "35")
    D.run('TX_CLK', NET("R14", "1"), F, [r1, (r1[0], r1[1] + 0.7), (u[0] - 0.05, r1[1] + 0.7 + (u[0] - 0.05 - r1[0])), u])


def misc(D, C, NET):
    g, s = C("R7", "1"), C("R7", "2")
    D.run('-', GND, F, [g, (g[0], 74.66), (189.0, 74.0)], 0.25)          # existing GND via (189.0, 74.0)
    D.run('-', NET("R7", "2"), F, [s, (190.3, s[1])], 0.15)
    # CLK_OUT: pin 22 inward to a via next to TP2 (bottom, under the PHY)
    p = C("U2", "22")
    v = (200.25, p[1] - 0.175)
    D.run('-', NET("U2", "22"), F, [p, (v[0] + 0.175, p[1]), v], 0.15)
    D.via('-', NET("U2", "22"), *v)
    D.run('-', NET("U2", "22"), B, [v, C("TP2", "1")], 0.2)
    # TP8 (1V1) under the right header edge, via on the U3 output lane
    v = (206.45, 79.6)
    D.via('-', V11, *v)
    D.run('-', V11, B, [v, C("TP8", "1")], 0.25)


def solve_td3(C, NET):
    a, b = 0.7, 2.6
    for _ in range(50):
        m = (a + b) / 2
        D = Design(); td3(D, C, NET, m)
        if MODULE['TD3'] + D.len['TD3'] < TARGET: a = m
        else: b = m
    m = round((a + b) / 2, 4)
    D = Design(); td3(D, C, NET, m)
    return m, MODULE['TD3'] + D.len['TD3']


def fixed(prm):
    pads, kept, removed, crt, C, NET = base()
    D = Design()
    td3(D, C, NET, prm['td3_amp']); txclk(D, C, NET); misc(D, C, NET)
    return D


if __name__ == "__main__":
    pads, kept, removed, crt, C, NET = base()
    amp, t3 = solve_td3(C, NET)
    D = Design(); td3(D, C, NET, amp)
    print("TD3 amp", amp, round(t3, 3), " TX_CLK total", end=" ")
    D2 = Design(); txclk(D2, C, NET); print(round(MODULE['TX_CLK'] + D2.len['TX_CLK'], 3))
    json.dump({'td3_amp': amp}, open('bot_prm.json', 'w'))
    D = fixed({'td3_amp': amp})
    errs = D.plan.check([p for p in pads if p.ref not in ("J2", "J3")], kept, clr=0.1499, verbose=False)
    print("\n".join(errs) or "clean")
    import audit_angles
    print(audit_angles.audit(D.plan.items, pads=pads) or "angles ok")


def load_routes(D, path='cap_routes.json'):
    for it in json.load(open(path)):
        if it['kind'] == 'seg':
            D.plan.seg(it['net'], it['layer'], [tuple(it['a']), tuple(it['b'])], it['w'], 'auto')
        else:
            D.plan.via(it['net'], it['x'], it['y'], tag='auto')


def build(prm):
    D = fixed(prm)
    if os.path.exists('cap_routes.json'):
        load_routes(D)
    return D
