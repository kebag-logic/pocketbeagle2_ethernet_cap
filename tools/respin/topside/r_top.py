"""All-SMT-on-top, step 1: LED drivers (Q1-Q3), D-K lanes, rebuilt LED gate lanes, MDIO pull-ups, INT pull-up,
TD0/TD2/TD3 re-routed to top-side series resistors (one via each) and re-matched to TX_CTRL."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts
from rg import Design, MODULE, VIA_LEN
from meander import accordion, serpentine
from d_misc import CX, CY, _arc, LED

F, B = "F.Cu", "B.Cu"
pads, kept, removed, crt = ts.state()
C, NET = ts.lookup(pads)
TARGET = 99.671                       # TX_CTRL total (module + cape), unchanged
GND, V33 = "GND", "/VDD_3V3"
P = 0.6
GATE_Y = {'Q3': 61.75, 'Q2': 61.5, 'Q1': 61.25}      # B gate lanes (lowest = westmost Q)
VIA_Y = 62.1                                         # gate / source via row (between lanes and TD0 run)
TD0_Y = 62.8                                         # TD0 B run to the R8 via
DK_VIA = {'D1': (188.4, 58.5), 'D2': (192.1, 58.5), 'D3': (195.8, 58.5)}


def drivers(D):
    for q, d, lane_y in (('Q3', 'D3', 57.0), ('Q2', 'D2', 57.7), ('Q1', 'D1', 57.0)):
        dx, dy = C(q, "3")
        dn = NET(q, "3")
        v = (dx + 0.6, 60.75)
        D.run('-', dn, F, [(dx, dy), (dx + 0.6, dy - 0.6), v], 0.25)
        D.via('-', dn, *v)
        kx, ky = DK_VIA[d]
        if q == 'Q3':
            D.run('-', dn, B, [v, (kx, ky)], 0.2)
        elif q == 'Q2':
            D.run('-', dn, B, [v, (v[0], lane_y + 0.5), (v[0] - 0.5, lane_y), (kx + 0.4, lane_y), (kx, lane_y + 0.4), (kx, ky)], 0.2)
        else:
            D.run('-', dn, B, [v, (v[0], 57.6), (v[0] - 0.6, 57.0), (kx + 0.5, 57.0), (kx, 57.5), (kx, ky)], 0.2)
        D.via('-', dn, kx, ky)
        k = C(d, "1")
        D.run('-', dn, F, [(kx, ky), (kx - 0.5, ky - 0.5), k], 0.25)
        # gate and source vias in the row between the gate lanes and the TD0 run
        g, s = C(q, "1"), C(q, "2")
        D.run('-', NET(q, "1"), F, [(g[0], VIA_Y), g], 0.2)
        D.via('-', NET(q, "1"), g[0], VIA_Y)
        D.run('-', GND, F, [(s[0], VIA_Y), s], 0.3)
        D.via('-', GND, s[0], VIA_Y)


def gate_lanes(D):
    """U2 LED pins -> F west through the header gaps -> left strip -> via -> B arc -> top level (as rev B) ->
    45 deg down to the gate lane level -> east -> 45 deg into the gate via."""
    xk = {'LED2': 186.1, 'LED1': 186.4, 'LED0': 186.9}   # descent columns under the J2 body (parts can't go there)
    turn = {'LED2': 190.3, 'LED1': 190.42, 'LED0': 190.54}
    for name, pin, g, xs, xv, vy, r, h, q in LED:
        net = NET("U2", pin)
        p = C("U2", pin)
        x = xk[name]
        j = 87.79 - C("U2", "61")[1]   # all three step down right after the pins, keeping the 0.5 mm pitch
        yj = p[1] + j
        if name == 'LED2':      # into the 87.79 header gap
            pts = [p, (189.9, p[1]), (189.9 - j, yj), (xs + 0.3, g)]
        else:
            pts = [p, (189.9, p[1]), (189.9 - j, yj), (x + 0.3, yj), (x, yj + 0.3), (x, g - 0.3), (x - 0.3, g), (xs + 0.3, g)]
        pts += [(xs, g - 0.3), (xs, 77.0 + (xs - xv)), (xv, 77.0), (xv, vy)]
        D.run('-', net, F, pts, 0.15)
        D.via('-', net, xv, vy)
        xt = CX - r
        dl = 10.5
        ya = CY + r * math.sin(math.radians(225 - dl))
        k = CX + CY - math.sqrt(2) * r * math.cos(math.radians(dl))
        gx = C(q, "1")[0]
        L = GATE_Y[q]
        t0 = turn[name]
        top = [(xv, vy), (xt, vy - (xv - xt)), (xt, CY)] + _arc(r, CY, ya, 14)[1:] + [(k - h, h), (t0, h),
               (t0 + (L - h), L), (gx - (VIA_Y - L), L), (gx, VIA_Y)]
        D.run('-', net, B, top, 0.10)


def pullups(D):
    # MDIO/MDC pull-ups: 3V3 from the top bus down x = R20.2, signal pads straight into U1.37 / U1.39
    a, b = C("R20", "2"), C("R21", "2")
    D.run('-', V33, F, [(a[0], 60.0), a, b], 0.3)
    D.run('-', NET("R20", "1"), F, [C("R20", "1"), C("U1", "37")], 0.2)
    D.run('-', NET("R21", "1"), F, [C("R21", "1"), C("U1", "39")], 0.2)
    # INT pull-up R24: INT pad -> via -> B -> U1.6; 3V3 pad -> F riser x 190.6 to the top bus
    i = C("R24", "2")
    iv = (188.05, i[1])
    D.run('-', NET("R24", "2"), F, [i, iv], 0.2)
    D.via('-', NET("R24", "2"), *iv)
    u6 = C("U1", "6")
    D.run('-', NET("R24", "2"), B, [iv, (u6[0] + (u6[1] - iv[1]), iv[1]), u6], 0.2)
    v = C("R24", "1")
    D.run('-', V33, F, [v, (191.4, v[1]), (191.7, v[1] - 0.3), (191.7, 60.0)], 0.3)


def strap(D):
    lane_x = 186.9
    for ref, net2, via in (("R32", GND, (189.75, 90.0)), ("R31", V33, (189.75, 91.3))):
        a, b = C(ref, "1"), C(ref, "2")
        D.run('-', NET(ref, "1"), F, [a, (lane_x, a[1])], 0.2)
        D.run('-', net2, F, [b, (via[0] - abs(via[1] - b[1]), b[1]), via], 0.3)
        D.via('-', net2, *via)
    D.run('-', V33, B, [(189.75, 91.3), (191.3, 91.3)], 0.3)


def td0(D, bot):
    net = NET("U2", "38")
    p38 = C("U2", "38")
    D.run('TD0', net, F, [p38, (197.81, 77.6)])
    D.via('TD0', net, 197.81, 77.6)
    acc = accordion(197.81, 63.4, bot, P, 5, start_up=True, direction=-1)
    xl = acc[-1][0]
    r2 = C("R8", "2")
    pv = (191.05, TD0_Y)
    D.run('TD0', net, B, [(197.81, 77.6)] + acc + [(xl, TD0_Y + 0.3), (xl - 0.3, TD0_Y), pv])
    D.via('TD0', net, *pv)
    D.run('TD0', net, F, [pv, (pv[0], r2[1] - (pv[0] - r2[0])), r2])
    r1 = C("R8", "1")
    cv = (189.1, 63.6)
    D.run('TD0', NET("R8", "1"), F, [r1, (r1[0] - 0.3, cv[1]), cv])
    D.via('TD0', NET("R8", "1"), *cv)
    D.run('TD0', NET("R8", "1"), B, [cv, C("U1", "4")])


def td2(D, top):
    net = NET("U2", "36")
    D.run('TD2', net, F, [C("U2", "36"), (198.81, 77.6)])
    D.via('TD2', net, 198.81, 77.6)
    acc = accordion(198.81, top, 69.6, P, 10, start_up=True, direction=1)
    acc[0] = (198.81, 77.6)
    xl = acc[-1][0]
    r2 = C("R10", "2")
    v = (xl - 0.36, r2[1] + 0.29)
    D.run('TD2', net, B, acc + [(xl, v[1] - 0.36), v])
    D.via('TD2', net, *v)
    D.run('TD2', net, F, [v, (v[0] + 0.29, r2[1]), r2])
    r1, u = C("R10", "1"), C("U1", "46")
    D.run('TD2', NET("R10", "1"), F, [r1, (u[0] - 1.27, r1[1]), u])


def td3(D, amp):
    net = NET("U2", "35")
    D.run('TD3', net, F, [C("U2", "35"), (199.31, 76.9)])
    D.via('TD3', net, 199.31, 76.9)
    xr = 205.39
    n = 10
    x0 = xr - P * (n - 1)
    acc = accordion(x0, 71.0, 76.4, P, n, start_up=True, direction=1)
    serp, _ = serpentine((xr, 77.0), (xr, 83.0), +1, amp, P, 5, c=0.2)
    v = (xr, 83.35)
    D.run('TD3', net, B, [(199.31, 76.9), (199.31, 76.7), (199.61, 76.4), (x0 - 0.2, 76.4), (x0, 76.2)] + acc[1:-1] + serp + [v])
    D.via('TD3', net, *v)
    r2 = C("R11", "2")
    D.run('TD3', net, F, [v, (r2[0], v[1] + (v[0] - r2[0])), r2])
    r1, u = C("R11", "1"), C("U1", "55")
    D.run('TD3', NET("R11", "1"), F, [r1, (r1[0] + (r1[1] - u[1]), u[1]), u])


def total(D, ln):
    return MODULE[ln] + D.len[ln]


def solve(fn, lo, hi, sign, ln):
    """sign +1: larger knob -> longer"""
    a, b = lo, hi
    for _ in range(50):
        m = (a + b) / 2
        D = Design(); fn(D, m)
        if (total(D, ln) < TARGET) == (sign > 0): a = m
        else: b = m
    m = round((a + b) / 2, 4)
    D = Design(); fn(D, m)
    return m, total(D, ln)


def build(prm):
    D = Design()
    drivers(D); gate_lanes(D); pullups(D); strap(D)
    td0(D, prm['td0_bot']); td2(D, prm['td2_top'])
    if 'R11' in ts.PLACE:
        td3(D, prm['td3_amp'])
    return D


if __name__ == "__main__":
    prm = {}
    prm['td0_bot'], t0 = solve(td0, 64.5, 76.0, +1, 'TD0')
    prm['td2_top'], t2 = solve(td2, 63.3, 69.0, -1, 'TD2')
    print("TD0", prm['td0_bot'], round(t0, 3), " TD2", prm['td2_top'], round(t2, 3))
    if 'R11' in ts.PLACE:
        prm['td3_amp'], t3 = solve(td3, 0.7, 2.6, +1, 'TD3')
        print("TD3", prm['td3_amp'], round(t3, 3))
    json.dump(prm, open('top_prm.json', 'w'))
    D = build(prm)
    errs = D.plan.check([p for p in pads if p.ref not in ("J2", "J3")], kept, clr=0.1499, verbose=False)
    print("\n".join(errs) or "clean")
    import audit_angles
    print(audit_angles.audit(D.plan.items, pads=pads) or "angles ok")
    from netview import view
    view(F, (178.9, 55, 208, 95), "rt_F.png", pads, kept, D.plan)
    view(B, (178.9, 55, 208, 95), "rt_B.png", pads, kept, D.plan)
