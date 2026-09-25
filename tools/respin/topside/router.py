"""Small 2-layer (F/B) grid router: 8 directions, turns limited to 45 deg, vias allowed.
Routes one connection from a start pad/point to any same-net copper (or given target geometry).
Obstacles = other-net copper (pads, tracks, vias, planned items) inflated by w/2 + clearance."""
import heapq, math
import numpy as np
import shapely
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from scipy.ndimage import distance_transform_edt
from model import outline

F, B = "F.Cu", "B.Cu"
LAYERS = (F, B)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


class World:
    def __init__(self, pads, tracks):
        self.items = []     # dict(net, layers, geom, drill)
        for p in pads:
            ly = {F, B} if p.drill or p.net == "<NPTH>" else set(p.layers) & {F, B}
            if ly:
                self.items.append(dict(net=p.net, layers=ly, geom=p.poly, drill=p.drill if p.drill else (0.0 if p.net != "<NPTH>" else 1.0), src=p))
        for t in tracks:
            if t['kind'] == 'seg':
                if t['layer'] in LAYERS:
                    self.items.append(dict(net=t['net'], layers={t['layer']}, geom=LineString(t['pts']).buffer(t['w'] / 2, 8), drill=0.0, src=t))
            else:
                self.items.append(dict(net=t['net'], layers={F, B}, geom=Point(t['x'], t['y']).buffer(t['d'] / 2, 16), drill=0.2, src=t))

    def add_plan(self, plan, start=0):
        for it in plan.items[start:]:
            if it['kind'] == 'seg':
                if it['layers'][0] in LAYERS:
                    self.items.append(dict(net=it['net'], layers={it['layers'][0]}, geom=it['geom'], drill=0.0, src=it))
            else:
                self.items.append(dict(net=it['net'], layers={F, B}, geom=it['geom'], drill=it['drill'], src=it))

    def remove(self, pred):
        self.items = [i for i in self.items if not pred(i)]


def route(world, net, start, layer, w, window, clr=0.17, via_d=0.45, via_cost=1.2, turn_cost=0.08, res=0.05,
          target=None, start_geom=None, allow_via=True, layers=LAYERS, keepout=None, max_expand=3_000_000,
          via_goal=False):
    """start: (x, y); target: shapely geometry per layer {layer: geom} or None = same-net copper (minus start_geom).
    Returns (list of (layer, [pts])), [via points]) or None."""
    x0, y0, x1, y1 = window
    xs = np.arange(x0, x1 + 1e-9, res); ys = np.arange(y0, y1 + 1e-9, res)
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys)
    win = box(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    inside = outline().buffer(-(0.5 + w / 2))
    vinside = outline().buffer(-(0.5 + via_d / 2))
    near = [i for i in world.items if i['geom'].intersects(win)]
    blocked, tmask = {}, {}
    for L in layers:
        obs = [i['geom'] for i in near if L in i['layers'] and i['net'] != net]
        if keepout is not None and L in keepout:
            obs.append(keepout[L])
        og = unary_union(obs).buffer(w / 2 + clr) if obs else Point(-1e3, -1e3)
        blocked[L] = shapely.contains_xy(og, X, Y) | ~shapely.contains_xy(inside, X, Y)
        if target is not None:
            tg = target.get(L)
        else:
            same = [i['geom'] for i in near if L in i['layers'] and i['net'] == net]
            tg = unary_union(same) if same else None
            if tg is not None and start_geom is not None:
                tg = tg.difference(start_geom.buffer(0.02))
        tmask[L] = shapely.contains_xy(tg.buffer(-0.03), X, Y) if tg is not None and not tg.is_empty else np.zeros_like(X, bool)
        tmask[L] &= ~blocked[L] | shapely.contains_xy(tg, X, Y) if tg is not None and not tg.is_empty else tmask[L]
    if allow_via:
        vobs = [i['geom'] for i in near if i['net'] != net]
        holes = [i['geom'].centroid.buffer(max(i['drill'], 0.2) / 2) for i in near if i['drill'] > 0]
        vo = unary_union(vobs).buffer(via_d / 2 + clr) if vobs else Point(-1e3, -1e3)
        ho = unary_union(holes).buffer(0.1 + 0.3) if holes else Point(-1e3, -1e3)    # drill 0.2 + 0.3 hole gap
        smd = [i['geom'] for i in near if i['drill'] == 0 and i['net'] == net and type(i['src']).__name__ == 'Pad']
        so = unary_union(smd).buffer(via_d / 2 + 0.05) if smd else Point(-1e3, -1e3)   # no via-in-pad
        via_ok = ~shapely.contains_xy(vo, X, Y) & ~shapely.contains_xy(ho, X, Y) & ~shapely.contains_xy(so, X, Y) \
            & shapely.contains_xy(vinside, X, Y)
        if keepout is not None and 'via' in keepout:
            via_ok &= ~shapely.contains_xy(keepout['via'], X, Y)
    else:
        via_ok = np.zeros_like(X, bool)
    if via_goal:                      # GND: dropping a via into the inner planes ends the route
        for L in layers:
            tmask[L] = tmask[L] | via_ok
    if not any(tmask[L].any() for L in layers):
        raise ValueError(f"no target cells for {net}")
    # heuristic: distance to target per layer (+ via for the other layer)
    H = {}
    for L in layers:
        H[L] = distance_transform_edt(~tmask[L]) * res
    Hmin = {L: np.minimum(H[L], min((H[M] + via_cost for M in layers if M != L), default=np.inf)) if allow_via else H[L] for L in layers}
    li = {L: k for k, L in enumerate(layers)}
    INF = 1e18
    g = np.full((len(layers), ny, nx, 9), INF)
    parent = {}
    heap = []
    sx, sy = start
    # start cells: inside start_geom (if given) else nearest cell
    if start_geom is not None:
        sc = np.argwhere(shapely.contains_xy(start_geom.buffer(-0.02), X, Y) & ~blocked[layer])
    else:
        sc = [(int(round((sy - y0) / res)), int(round((sx - x0) / res)))]
    for (i, j) in sc:
        c0 = math.hypot(xs[j] - sx, ys[i] - sy) * 0.3
        k = li[layer]
        if c0 < g[k, i, j, 8]:
            g[k, i, j, 8] = c0
            heapq.heappush(heap, (c0 + Hmin[layer][i, j], c0, k, i, j, 8))
            parent[(k, i, j, 8)] = None
    goal = None
    n = 0
    while heap:
        f, gc, k, i, j, d = heapq.heappop(heap)
        if gc > g[k, i, j, d]:
            continue
        L = layers[k]
        if tmask[L][i, j]:
            goal = (k, i, j, d); break
        n += 1
        if n > max_expand:
            break
        cand = range(8) if d == 8 else ((d - 1) % 8, d, (d + 1) % 8)
        for nd in cand:
            di, dj = DIRS[nd][1], DIRS[nd][0]
            ii, jj = i + di, j + dj
            if not (0 <= ii < ny and 0 <= jj < nx) or blocked[L][ii, jj]:
                continue
            step = res * (1.4142 if nd % 2 else 1.0) + (turn_cost if (d != 8 and nd != d) else 0.0)
            ng = gc + step
            if ng < g[k, ii, jj, nd]:
                g[k, ii, jj, nd] = ng; parent[(k, ii, jj, nd)] = (k, i, j, d)
                heapq.heappush(heap, (ng + Hmin[L][ii, jj], ng, k, ii, jj, nd))
        if allow_via and via_ok[i, j] and d != 8:
            for M in layers:
                if M == L or blocked[M][i, j]:
                    continue
                kk = li[M]; ng = gc + via_cost
                if ng < g[kk, i, j, 8]:
                    g[kk, i, j, 8] = ng; parent[(kk, i, j, 8)] = (k, i, j, d)
                    heapq.heappush(heap, (ng + Hmin[M][i, j], ng, kk, i, j, 8))
    if goal is None:
        return None
    states = []
    s = goal
    while s is not None:
        states.append(s); s = parent[s]
    states.reverse()
    runs, vias = [], []
    cur_layer, pts = None, []
    for (k, i, j, d) in states:
        p = (round(float(xs[j]), 4), round(float(ys[i]), 4))
        L = layers[k]
        if cur_layer is None:
            cur_layer, pts = L, [p]
        elif L != cur_layer:
            if len(pts) > 1:
                runs.append((cur_layer, pts))
            vias.append(p); cur_layer, pts = L, [p]
        else:
            pts.append(p)
    if len(pts) > 1:
        runs.append((cur_layer, pts))
    k, i, j, d = goal
    if via_goal and via_ok[i, j]:
        L = layers[k]
        same = [it['geom'] for it in near if L in it['layers'] and it['net'] == net]
        if not same or not unary_union(same).contains(Point(xs[j], ys[i])):
            vias.append((round(float(xs[j]), 4), round(float(ys[i]), 4)))
    return [(L, simplify(p)) for L, p in runs], vias


def simplify(pts):
    out = [pts[0]]
    for a, b in zip(pts[1:], pts[2:] + [None]):
        if b is None:
            out.append(a); break
        d1 = (round(a[0] - out[-1][0], 4), round(a[1] - out[-1][1], 4))
        d2 = (round(b[0] - a[0], 4), round(b[1] - a[1], 4))
        n1, n2 = math.hypot(*d1), math.hypot(*d2)
        if n1 > 0 and n2 > 0 and abs(d1[0] / n1 - d2[0] / n2) < 1e-6 and abs(d1[1] / n1 - d2[1] / n2) < 1e-6:
            continue
        out.append(a)
    return out
