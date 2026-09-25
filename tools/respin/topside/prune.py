"""Which of our tracks/vias dangle once the given footprints' pads are gone (iterative prune)."""
import math
from shapely.geometry import Point, LineString


def prune(pads, tracks, gone_refs, nets=None, keep_via=lambda v: False):
    """pads: remaining board pads (model.Pad) incl. the gone ones (they are ignored); returns (kept, removed)."""
    live_pads = [p for p in pads if p.ref not in gone_refs]
    gone_nets = {p.net for p in pads if p.ref in gone_refs} if nets is None else set(nets)
    segs = [t for t in tracks if t['kind'] == 'seg']
    vias = [t for t in tracks if t['kind'] == 'via']
    removed = set()

    def touches_pad(net, layer, pt):
        P = Point(pt)
        return any(p.net == net and layer in p.layers and p.poly.buffer(1e-3).contains(P) for p in live_pads)

    changed = True
    while changed:
        changed = False
        alive = [t for t in segs if id(t) not in removed]
        alive_v = [v for v in vias if id(v) not in removed]
        for t in alive:
            if t['net'] not in gone_nets:
                continue
            for end in t['pts']:
                P = Point(end)
                ok = touches_pad(t['net'], t['layer'], end)
                ok = ok or any(v['net'] == t['net'] and math.dist((v['x'], v['y']), end) <= v['d'] / 2 + 1e-3 for v in alive_v)
                ok = ok or any(o is not t and o['net'] == t['net'] and o['layer'] == t['layer'] and
                               LineString(o['pts']).buffer(o['w'] / 2 + 1e-3).contains(P) for o in alive)
                if not ok:
                    removed.add(id(t)); changed = True; break
        for v in alive_v:
            if v['net'] not in gone_nets or v['net'] == 'GND' or keep_via(v):
                continue
            c = (v['x'], v['y'])
            layers = {t['layer'] for t in alive if id(t) not in removed and t['net'] == v['net'] and
                      LineString(t['pts']).distance(Point(c)) <= v['d'] / 2 + 1e-3}
            padl = {l for l in ('F.Cu', 'B.Cu') if touches_pad(v['net'], l, c)}
            if len(layers | padl) <= 1:
                removed.add(id(v)); changed = True
    kept = [t for t in tracks if id(t) not in removed]
    rem = [t for t in tracks if id(t) in removed]
    return kept, rem
