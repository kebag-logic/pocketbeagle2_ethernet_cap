from model import *

W = 0.13
PITCH = 0.33  # 0.13 + 0.2 gap
pads, fps, tr = load()
m = padmap(pads)
P = lambda r, n: m[(r, n)].center


def pair(k, pp, pn, jp, jn, side, bump=0.0, bump_y=(93.9, 94.9)):
    """side=-1: pair heads left (P left of N); +1: heads right."""
    (xp, yp), (xn, yn) = P("U2", pp), P("U2", pn)
    (xjp, yjp), (xjn, yjn) = P("J1", jp), P("J1", jn)
    ystub = 91.6
    # P runs straight down at the J1 P-pin column, N at +PITCH beside it
    xP, xN = xjp, xjp + PITCH
    dp = abs(xP - xp)
    dn = abs(xN - xn)
    p = [(xp, yp), (xp, ystub), (xP, ystub + dp), (xjp, yjp)]
    ysplit = 95.9
    n = [(xn, yn), (xn, ystub), (xN, ystub + dn)]
    if bump:
        y1, y2 = bump_y
        c = 0.2  # 45 deg chamfers, no right angles
        n += [(xN, y1), (xN + c, y1 + c), (xN + bump - c, y1 + c), (xN + bump, y1 + 2 * c),
              (xN + bump, y2 - 2 * c), (xN + bump - c, y2 - c), (xN + c, y2 - c), (xN, y2)]
    n += [(xN, ysplit), (xjn, ysplit + (xjn - xN)), (xjn, yjn)]
    return p, n


PAIRS = [  # (k, U2 P, U2 N, J1 P, J1 N, side)
    (0, "2", "3", "2", "3", -1),
    (1, "5", "6", "4", "5", -1),
    (2, "10", "11", "6", "7", -1),
    (3, "13", "14", "8", "9", +1),
]


def build(bumps):
    plan = Plan()
    routes = {}
    for (k, pp, pn, jp, jn, side), b in zip(PAIRS, bumps):
        p, n = pair(k, pp, pn, jp, jn, side, b)
        netp = m[("U2", pp)].net
        netn = m[("U2", pn)].net
        plan.seg(netp, "F.Cu", p, W, f"MDI{k}_P")
        plan.seg(netn, "F.Cu", n, W, f"MDI{k}_N")
        routes[netp] = p
        routes[netn] = n
        print(f"MDI{k}: P {length(p):.3f}  N {length(n):.3f}  skew {length(p) - length(n):+.3f}")
    return plan, routes


if __name__ == "__main__":
    import sys
    bumps = [float(v) for v in sys.argv[1:]] or [0, 0, 0, 0]
    plan, routes = build(bumps)
    plan.check(pads, tr)
