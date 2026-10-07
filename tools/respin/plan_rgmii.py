# REFERENCE ONLY: rev B "shortest path" RGMII plan, superseded by the length-matched re-spin.
from model import *
import plan_mdi

pads, fps, tr = load()
m = padmap(pads)
C = lambda r, n: m[(r, n)].center
NET = lambda r, n: m[(r, n)].net
WR = 0.15   # RGMII 50 ohm microstrip
WS = 0.2    # slow signals
F, B = "F.Cu", "B.Cu"

plan, mdi_routes = plan_mdi.build([1.2745, 1.2745, 1.2745, 1.3455])
R = {}  # name -> list of (layer, pts)


def route(name, net, layer, pts, w=WR):
    plan.seg(net, layer, pts, w, name)
    R.setdefault(name, []).append(pts)


def via(name, net, x, y):
    plan.via(net, x, y, tag=name + " via")


# ---------------- RX group: PHY -> series R (at PHY) -> PB2 left header, all F.Cu
rx = [  # name, U2 pin, R, U1 pad, level y, gap y, lane x
    ("RD3", "47", "R19", "21", None, 80.17, 180.95),
    ("RD2", "46", "R18", "23", 73.60, 77.63, 180.60),
    ("RD1", "45", "R17", "25", 73.10, 75.09, 180.25),
    ("RD0", "44", "R16", "27", 72.55, 72.55, 179.90),
]


def fan(pin, r):
    """0.5 mm pin pitch -> 1.0 mm resistor pitch with parallel 45 deg escapes."""
    xp, yp = C("U2", pin)
    r2 = C(r, "2")
    s_ = xp - r2[0]
    return [(xp, yp), (xp, 77.9), (r2[0], 77.9 - s_), r2]


for name, pin, r, u1, lvl, gap, lane in rx:
    route(name + "_phy", NET("U2", pin), F, fan(pin, r))
    r1 = C(r, "1")
    ux, uy = C("U1", u1)
    if lvl is None:
        pts = [r1, (r1[0] - 0.5, r1[1])]
    elif abs(lvl - gap) < 1e-6:
        pts = [r1, (r1[0], lvl + 0.3), (r1[0] - 0.3, lvl)]
    else:
        pts = [r1, (r1[0], lvl + 0.3), (r1[0] - 0.3, lvl), (186.22 + abs(lvl - gap), lvl)]
    pts += [(186.22, gap), (lane + 0.3, gap), (lane, gap + 0.3), (lane, uy - 0.92), (lane + 0.92, uy), (ux, uy)]
    route(name, NET(r, "1"), F, pts)

# RX_CLK: to inner pad U1.34 via the outer strip and the 100.49 row gap
route("RXCLK_phy", NET("U2", "43"), F, fan("43", "R15"))
r1 = C("R15", "1")
ux, uy = C("U1", "34")
route("RXCLK", NET("R15", "1"), F, [r1, (r1[0], 72.4), (r1[0] - 0.3, 72.1), (188.31, 72.1), (186.22, 70.01),
                                     (179.85, 70.01), (179.55, 70.31), (179.55, 100.19), (179.85, 100.49),
                                     (183.86, 100.49), (ux, uy)])

# RX_CTRL: pin 53 -> R12 (at PHY) -> U1.19 through the 85.25 row gap
route("RXCTL_phy", NET("U2", "53"), F, [C("U2", "53"), (189.8, 82.975), C("R12", "2")])
route("RXCTL_strap", NET("U2", "53"), F, [C("R7", "2"), C("R12", "2")])
r1 = C("R12", "1")
ux, uy = C("U1", "19")
route("RXCTL", NET("R12", "1"), F, [r1, (186.14, 85.25), (183.86, 85.25), (ux, uy)])

# ---------------- TX group
# TD0: F.Cu only, pin 38 -> R8 (at PB2) -> U1.4
xp, yp = C("U2", "38")
route("TD0_phy", NET("U2", "38"), F, [(xp, yp), (xp, 72.8), C("R8", "2")])
route("TD0", NET("R8", "1"), F, [C("R8", "1"), C("U1", "4")])

# TD3: F.Cu from pin 35 around the top-right, via down to R11 (B) next to U1.55
xp, yp = C("U2", "35")
route("TD3_phy", NET("U2", "35"), F, [(xp, yp), (xp, 77.8), (xp + 0.3, 77.5), (204.0, 77.5), (204.5, 78.0), (204.5, 83.3)])
via("TD3_phy", NET("U2", "35"), 204.5, 83.3)
route("TD3_phy_b", NET("U2", "35"), B, [(204.5, 83.3), C("R11", "2")])
route("TD3", NET("R11", "1"), B, [C("R11", "1"), C("U1", "55")])

# TD2: via at the pin, B.Cu diagonal to R10 (B), then through the inner row gap to U1.46
xp, yp = C("U2", "36")
route("TD2_phy", NET("U2", "36"), F, [(xp, yp), (xp, 77.6)])
via("TD2_phy", NET("U2", "36"), xp, 77.6)
r2 = C("R10", "2")
route("TD2_phy_b", NET("U2", "36"), B, [(xp, 77.6), (r2[0] - 1.03, r2[1]), r2])
ux, uy = C("U1", "46")
route("TD2", NET("R10", "1"), B, [C("R10", "1"), (209.26, 72.55), (ux, uy)])

# TD1: U1.67 -> R9 (B) -> via -> F.Cu lane up the right edge -> across the top -> pin 37
xp, yp = C("U2", "37")
route("TD1", NET("R9", "1"), B, [C("U1", "67"), C("R9", "1")])
r2 = C("R9", "2")
route("TD1_phy_b", NET("R9", "2"), B, [r2, (r2[0], 96.7)])
via("TD1_phy", NET("R9", "2"), r2[0], 96.7)
route("TD1_phy", NET("R9", "2"), F, [(r2[0], 96.7), (206.75, 96.55), (206.75, 77.3), (206.25, 76.8), (xp + 0.3, 76.8), (xp, 77.1), (xp, yp)])

# TX_CTRL: pin 52 -> via -> B.Cu lane up the left corridor -> R13 (B) -> U1.2
route("TXCTL_phy", NET("U2", "52"), F, [C("U2", "52"), (187.6, 82.475)])
via("TXCTL_phy", NET("U2", "52"), 187.6, 82.475)
r2 = C("R13", "2")
route("TXCTL_phy_b", NET("U2", "52"), B, [(187.6, 82.475), (187.25, 82.125), (187.25, 63.6), r2])
route("TXCTL", NET("R13", "1"), B, [C("R13", "1"), C("U1", "2")])

# GTX_CLK: pin 40 -> via -> B.Cu left above U2, down the left corridor -> R14 (B) -> U1.35
xp, yp = C("U2", "40")
route("TXCLK_phy", NET("U2", "40"), F, [(xp, yp), (xp, 76.9)])
via("TXCLK_phy", NET("U2", "40"), xp, 76.9)
r2 = C("R14", "2")
route("TXCLK_phy_b", NET("U2", "40"), B, [(xp, 76.9), (188.8, 76.9), (188.3, 77.4), (188.3, 98.9),
                                           (r2[0], 98.9 + (188.3 - r2[0])), r2])
ux, uy = C("U1", "35")
r1 = C("R14", "1")
route("TXCLK", NET("R14", "1"), B, [r1, (186.03, 103.03), (183.86, 103.03), (ux, uy)])

# ---------------- management / control (slow, 0.2 mm)
# RESET_N / INT: F stubs to vias in the corridor, B.Cu lanes up to U1.8 / U1.6
route("RESET", NET("U2", "59"), F, [C("U2", "59"), (186.6, 85.975), (186.4, 86.2)], 0.15)
via("RESET", NET("U2", "59"), 186.4, 86.2)
ux, uy = C("U1", "8")
route("RESET_b", NET("U2", "59"), B, [(186.4, 86.2), (186.4, 69.3), (ux, uy)], 0.15)
route("INT", NET("U2", "60"), F, [C("U2", "60"), (187.5, 86.475), (187.05, 86.9)], 0.15)
via("INT", NET("U2", "60"), 187.05, 86.9)
ux, uy = C("U1", "6")
route("INT_b", NET("U2", "60"), B, [(187.05, 86.9), (186.85, 86.7), (186.85, 66.9), (ux, uy)], 0.15)
route("INT_pu", NET("U2", "60"), F, [C("R24", "2"), C("U1", "6")], WS)

# MDIO / MDC: inner-ring vias, B.Cu lanes under U2 and up to U1.39 / U1.37
route("MDIO", NET("U2", "21"), F, [C("U2", "21"), (200.6, 86.475)], WS)
via("MDIO", NET("U2", "21"), 200.6, 86.475)
ux, uy = C("U1", "39")
route("MDIO_b", NET("U2", "21"), B, [(200.6, 86.475), (199.95, 85.825), (199.95, 80.5), (198.15, 78.7),
                                      (198.15, uy + 0.3), (198.45, uy), (ux, uy)], WS)
route("MDC", NET("U2", "20"), F, [C("U2", "20"), (201.2, 86.975), (200.15, 87.45)], WS)
via("MDC", NET("U2", "20"), 200.15, 87.45)
ux, uy = C("U1", "37")
route("MDC_b", NET("U2", "20"), B, [(200.15, 87.45), (199.35, 86.65), (199.35, 80.5), (197.75, 78.9),
                                     (197.75, uy + 0.3), (198.05, uy), (ux, uy)], WS)

# XI: 25 MHz clock, pin 19 -> C18 (shunt) / C14 (series) -> Y1 OUT
route("XI", NET("U2", "19"), F, [C("U2", "19"), (203.3, 87.475), C("C18", "2")], WS)
route("XI2", NET("U2", "19"), F, [(203.3, 87.475), C("C14", "2")], WS)
route("YOUT", NET("C14", "1"), F, [C("C14", "1"), C("Y1", "3")], WS)
# CLK_OUT -> TP2
route("CLKOUT", NET("U2", "22"), F, [C("U2", "22"), (203.3, 85.975), C("TP2", "1")], WS)
# RBIAS: pin 15 -> R22 / C28
route("RBIAS", NET("U2", "15"), F, [C("U2", "15"), (199.81, 91.3), C("R22", "1")], WS)
# C28 removed in rev B schematic review (RBIAS is a bare 11k)

if __name__ == "__main__":
    errs = plan.check([p for p in pads if p.ref not in ("J2", "J3")], tr)
    L = {k: sum(length(p) for p in v) for k, v in R.items()}
    def tot(a, *bs): return L.get(a, 0) + sum(L.get(b, 0) for b in bs)
    print("\nRX cape-side lengths (PHY pin -> PB2 pad, mm):")
    for n in ["RD0", "RD1", "RD2", "RD3", "RXCLK", "RXCTL"]:
        print(f"  {n:6s} {tot(n, n + '_phy'):6.2f}")
    print("TX cape-side lengths:")
    for n in ["TD0", "TD1", "TD2", "TD3", "TXCLK", "TXCTL"]:
        print(f"  {n:6s} {tot(n, n + '_phy', n + '_phy_b'):6.2f}")
