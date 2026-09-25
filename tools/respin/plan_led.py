import math, sys, json
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from model import *
pads, fps, tr = load()
m = padmap(pads)
C = lambda r, n: m[(r, n)].center
F, B = "F.Cu", "B.Cu"
CX, CY = 178.9576 + 10.25, 65.25   # top-left outline arc centre (R 10.25)
L0, L1, L2 = [m[("U2", p)].net for p in ("63", "62", "61")]
plan = Plan()
OUT = []
def seg(net, layer, pts, w):
    plan.seg(net, layer, pts, w, net.split('/')[-1])
    for a, b in zip(pts, pts[1:]):
        OUT.append(("seg", net, layer, w, a, b))
def via(net, x, y):
    plan.via(net, x, y, tag=net.split('/')[-1] + " via")
    OUT.append(("via", net, x, y))

def arc(r, ya, yb, n):
    """points on circle r (left-upper quadrant) from y=ya up to y=yb"""
    a0 = math.atan2(ya - CY, -math.sqrt(r * r - (ya - CY) ** 2))
    a1 = math.atan2(yb - CY, -math.sqrt(r * r - (yb - CY) ** 2))
    a0 %= 2 * math.pi
    a1 %= 2 * math.pi
    return [(CX + r * math.cos(a0 + (a1 - a0) * i / n), CY + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

def lane(net, v, ydrop, yrow, xs, r, h, q, yj):
    # B.Cu: via -> (drop) -> row gap -> strip at xs (0.15) -> 45 deg jog at yj to x=CX-r (0.10)
    #       -> tangent into arc r -> leave arc at y=h -> 45 deg rise into Q gate
    pts = [v]
    if ydrop:
        pts += [(v[0], yrow - 0.53), (v[0] - 0.53, yrow)]
    pts += [(xs + 0.3, yrow), (xs, yrow - 0.3), (xs, yj)]
    seg(net, B, pts, 0.15)
    xt = CX - r
    top = [(xs, yj), (xt, yj - (xs - xt)), (xt, CY)] + arc(r, CY, h, 16)[1:] + [(q[0] - (h - q[1]), h), q]
    seg(net, B, top, 0.10)

V2, V1, V0 = (186.6, 87.79), (187.15, 88.9), (187.7, 90.0)
p61, p62, p63 = C("U2", "61"), C("U2", "62"), C("U2", "63")
def stub(net, p, xd, v):
    seg(net, F, [p, (xd, p[1]), (xd - (v[1] - p[1]), v[1]), v], 0.15)
stub(L2, p61, 189.2, V2)
stub(L1, p62, 189.6, V1)
stub(L0, p63, 189.95, V0)
for n, v in ((L2, V2), (L1, V1), (L0, V0)):
    via(n, *v)

q1, q2, q3 = C("Q1", "1"), C("Q2", "1"), C("Q3", "1")
lane(L2, V2, False, 87.79, 181.49, 9.181, 59.985, q3, 71.2)
lane(L1, V1, True, 90.33, 181.17, 9.438, 59.73, q2, 71.6)
lane(L0, V0, True, 92.87, 180.85, 9.695, 59.475, q1, 72.0)

if __name__ == "__main__":
    errs = plan.check([p for p in pads if p.ref not in ("J2", "J3")], tr, clr=0.1499)
    json.dump(OUT, open("led_calls.json", "w"))
    tot = {}
    for o in OUT:
        if o[0] == "seg":
            tot[o[1]] = tot.get(o[1], 0) + math.dist(o[4], o[5])
    print({k.split('/')[-1]: round(v, 2) for k, v in tot.items()}, len(OUT), "items")
    # angle audit
    for o1, o2 in zip(OUT, OUT[1:]):
        if o1[0] == o2[0] == "seg" and o1[1] == o2[1] and o1[5] == o2[4]:
            a = math.atan2(o1[5][1]-o1[4][1], o1[5][0]-o1[4][0]); b = math.atan2(o2[5][1]-o2[4][1], o2[5][0]-o2[4][0])
            d = abs((math.degrees(b - a) + 180) % 360 - 180)
            if d > 46: print("TURN", round(d, 1), o1[1][-6:], o1[5])
