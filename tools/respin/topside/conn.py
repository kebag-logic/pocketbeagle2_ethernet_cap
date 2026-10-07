"""Per-net connectivity of pads + tracks + vias (+ planned items). GND vias / THT GND pads join the inner planes.
Zones on F/B are ignored on purpose (every pad must reach copper explicitly)."""
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree


def islands(pads, tracks, plan=None, nets=None):
    items = []
    for p in pads:
        if p.net and not p.net.startswith('unconnected') and p.net != '<NPTH>':
            items.append((p.net, set(p.layers), p.poly, f"{p.ref}.{p.num}", bool(p.drill)))
    for t in tracks:
        if t['kind'] == 'seg':
            items.append((t['net'], {t['layer']}, LineString(t['pts']).buffer(t['w'] / 2), 'seg', False))
        else:
            items.append((t['net'], {'F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'}, Point(t['x'], t['y']).buffer(t['d'] / 2), 'via', True))
    for it in (plan.items if plan else []):
        if it['kind'] == 'seg':
            items.append((it['net'], set(it['layers']), it['geom'], 'seg', False))
        else:
            items.append((it['net'], {'F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'}, it['geom'], 'via', True))
    bynet = {}
    for i, it in enumerate(items):
        if nets is None or it[0] in nets:
            bynet.setdefault(it[0], []).append(it)
    out = {}
    for net, its in bynet.items():
        n = len(its)
        par = list(range(n + 1))          # n = plane node

        def f(a):
            while par[a] != a:
                par[a] = par[par[a]]; a = par[a]
            return a

        def u(a, b):
            par[f(a)] = f(b)
        geoms = [it[2].buffer(1e-3) for it in its]
        tree = STRtree(geoms)
        for i, it in enumerate(its):
            for j in tree.query(geoms[i]):
                j = int(j)
                if j > i and (it[1] & its[j][1]) and geoms[i].intersects(geoms[j]):
                    u(i, j)
            if net == 'GND' and it[4]:
                u(i, n)
        comps = {}
        for i, it in enumerate(its):
            if it[3] not in ('seg', 'via'):
                comps.setdefault(f(i), []).append(it[3])
        pad_comps = [v for v in comps.values()]
        if len(pad_comps) > 1:
            out[net] = pad_comps
    return out
