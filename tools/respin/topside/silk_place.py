"""Place reference designators (0.8 mm) and the P1/P2 pin labels so no silkscreen overlaps pads, other silk or
the board edge. Nearest free spot around each courtyard; hide a reference only if nothing fits. --apply writes."""
import sys, math
from kipy import KiCad
from kipy.geometry import Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer as L
from shapely.geometry import box, Point, LineString, Polygon
from shapely.ops import unary_union
from shapely import affinity
from sexp import parse, find, walk
from model import load, outline, BOARD
from crtyd import load_crtyd, placed

H, TH = float(__import__('os').environ.get('SILK_H', '1.0')), 0.15          # JLCPCB legend: text >= 1.0 mm, line >= 0.15 mm
WC = float(__import__('os').environ.get('SILK_W', '0.65'))   # narrow characters (width) so more references fit
GAP = 0.15                      # JLCPCB pad-to-silkscreen 0.15 mm (also used silk-silk)
EDGE = outline().buffer(-0.3)

def text_box(s, x, y, angle):
    w, h = WC * 0.905 * len(s) + 0.37 * H, H + TH + 0.1     # refs/labels: caps + digits only
    if round(angle) % 180 == 90:
        w, h = h, w
    return box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)

def rot(x, y, deg):
    t = math.radians(deg)
    return x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t)

def silk_graphics():
    """static silk geometry per layer from the saved board (footprint graphics + board-level non-text graphics)"""
    t = parse(open(BOARD).read())
    out = {"F.SilkS": [], "B.SilkS": []}
    def add(layer, g):
        if layer in out: out[layer].append(g)
    for fp in find(t, 'footprint'):
        at = find(fp, 'at')[0]; X, Y = float(at[1]), float(at[2]); R = float(at[3]) if len(at) > 3 else 0.0
        T = lambda px, py: (lambda d: (X + d[0], Y + d[1]))(rot(px, py, R))
        for n in fp:
            if not (isinstance(n, list) and n and n[0] in ('fp_line', 'fp_arc', 'fp_circle', 'fp_rect', 'fp_poly')):
                continue
            ly = [c for c in n if isinstance(c, list) and c and c[0] == 'layer']
            if not ly: continue
            layer = ly[0][1].strip('"')
            if layer not in out: continue
            st = [c for c in walk(n) if isinstance(c, list) and c and c[0] == 'width']
            w = float(st[0][1]) if st else 0.12
            pts = {c[0]: (float(c[1]), float(c[2])) for c in walk(n) if isinstance(c, list) and c and c[0] in ('start', 'end', 'mid', 'center')}
            xy = [(float(c[1]), float(c[2])) for c in walk(n) if isinstance(c, list) and c and c[0] == 'xy']
            if n[0] == 'fp_line': g = LineString([T(*pts['start']), T(*pts['end'])])
            elif n[0] == 'fp_arc': g = LineString([T(*pts['start']), T(*pts['mid']), T(*pts['end'])])
            elif n[0] == 'fp_circle':
                c, e = T(*pts['center']), T(*pts['end']); g = Point(c).buffer(math.dist(c, e)).exterior
            elif n[0] == 'fp_rect':
                (x1, y1), (x2, y2) = pts['start'], pts['end']
                g = LineString([T(x1, y1), T(x2, y1), T(x2, y2), T(x1, y2), T(x1, y1)])
            else:
                g = Polygon([T(*p) for p in xy]).exterior
            add(layer, g.buffer(w / 2))
    for n in t:
        if isinstance(n, list) and n and n[0] in ('gr_line', 'gr_arc', 'gr_rect', 'gr_poly', 'gr_circle'):
            ly = [c for c in n if isinstance(c, list) and c and c[0] == 'layer']
            if ly and ly[0][1].strip('"') in out:
                pts = [(float(c[1]), float(c[2])) for c in walk(n) if isinstance(c, list) and c and c[0] in ('start', 'end', 'mid', 'xy')]
                add(ly[0][1].strip('"'), LineString(pts).buffer(0.08))
    return out

def main(apply):
    k = KiCad(socket_path="ipc:///tmp/kicad/api.sock"); b = k.get_board()
    pads, fps, _ = load()
    cr = load_crtyd()
    gfx = silk_graphics()
    padg = {"F.SilkS": unary_union([p.poly for p in pads if 'F.Cu' in p.layers]).buffer(GAP),
            "B.SilkS": unary_union([p.poly for p in pads if 'B.Cu' in p.layers]).buffer(GAP)}
    static = {l: unary_union(gfx[l]).buffer(GAP) for l in gfx}
    placed_txt = {"F.SilkS": [], "B.SilkS": []}

    def free(layer, g):
        if not EDGE.contains(g): return False
        if g.intersects(padg[layer]) or g.intersects(static[layer]): return False
        return all(not g.intersects(o) for o in placed_txt[layer])

    # P1/P2 pin labels (board texts): nearest free spot around the original
    labels, to_fab = [], []
    for t in b.get_text():
        if not hasattr(t, 'value') or t.layer != L.BL_F_SilkS: continue
        x0, y0 = t.position.x / 1e6, t.position.y / 1e6
        best = None
        for r in (0.0, 0.3, 0.6, 0.9, 1.2, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0):
            for a in range(0, 360, 20):
                for ang in (0, 90):
                    x, y = x0 + r * math.cos(math.radians(a)), y0 + r * math.sin(math.radians(a))
                    g = text_box(t.value, x, y, ang)
                    if free("F.SilkS", g):
                        best = (x, y, g, ang); break
                if best: break
            if best: break
        if best:
            placed_txt["F.SilkS"].append(best[2].buffer(GAP)); labels.append((t, best[0], best[1], best[3]))
        else:
            print("label without room -> F.Fab:", t.value, x0, y0); to_fab.append(t)
    footprints = list(b.get_footprints())
    for f in footprints:        # references left where they are (headers, module) are obstacles
        t = f.reference_field.text
        if t.value in ('U1', 'J2', 'J3') and f.reference_field.visible:
            fh = t.attributes.size.y / 1e6
            w_ = t.attributes.size.x / 1e6 * 0.905 * len(t.value) + 0.37 * fh
            if round(t.attributes.angle) % 180 == 90:
                w_, fh = fh, w_
            x, y = t.position.x / 1e6, t.position.y / 1e6
            layer = "B.SilkS" if t.layer == L.BL_B_SilkS else "F.SilkS"
            placed_txt[layer].append(box(x - w_ / 2, y - fh, x + w_ / 2, y + fh).buffer(GAP))
    lname = lambda f: "B.SilkS" if f.reference_field.text.layer == L.BL_B_SilkS else "F.SilkS"
    # crowded parts first
    def crowd(f):
        p = f.position; return -sum(1 for q in pads if math.dist(q.center, (p.x / 1e6, p.y / 1e6)) < 3)
    footprints.sort(key=crowd)
    result, hidden = {}, []
    for f in footprints:
        ref = f.reference_field.text.value
        if ref in ('U1', 'J2', 'J3') or ref not in cr:
            continue
        layer = lname(f)
        c = placed(cr[ref]); x0, y0, x1, y1 = c.bounds
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for ring in (0.05, 0.3, 0.6, 0.9, 1.3, 1.9, 2.5, 3.0, 3.5):
            for ang in (0, 90):
                s = text_box(ref, 0, 0, ang); w, h = s.bounds[2] - s.bounds[0], s.bounds[3] - s.bounds[1]
                cands = [(cx, cy)]
                for i in range(9):
                    fx = x0 + (x1 - x0) * i / 8; fy = y0 + (y1 - y0) * i / 8
                    cands += [(fx, y0 - h / 2 - ring), (fx, y1 + h / 2 + ring), (x0 - w / 2 - ring, fy), (x1 + w / 2 + ring, fy)]
                for (x, y) in cands:
                    g = text_box(ref, x, y, ang)
                    if free(layer, g):
                        d = math.dist((x, y), (cx, cy)) + (0 if ang == 0 else 0.3)
                        if best is None or d < best[0]:
                            best = (d, x, y, ang, g)
            if best: break
        if best:
            _, x, y, ang, g = best
            placed_txt[layer].append(g.buffer(GAP)); result[ref] = (x, y, ang)
        else:
            hidden.append(ref)
    print(f"placed {len(result)} references, hidden {len(hidden)}: {hidden}; labels moved {len(labels)}")
    if not apply:
        return
    upd = []
    for f in footprints:
        ref = f.reference_field.text.value
        if ref in result:
            x, y, ang = result[ref]
            tx = f.reference_field.text
            tx.position = Vector2.from_xy(int(round(x * 1e6)), int(round(y * 1e6)))
            tx.attributes.size = Vector2.from_xy(int(WC * 1e6), int(H * 1e6))
            tx.attributes.stroke_width = int(TH * 1e6)
            f.reference_field.visible = True
            tx.attributes.angle = ang
            upd.append(f)
        elif ref in hidden:
            f.reference_field.visible = False; upd.append(f)
    for t, x, y, ang in labels:
        t.position = Vector2.from_xy(int(round(x * 1e6)), int(round(y * 1e6)))
        t.attributes.angle = ang; upd.append(t)
    for t in to_fab:
        t.layer = L.BL_F_Fab; upd.append(t)
    c = b.begin_commit(); b.update_items(upd); b.push_commit(c, "Silkscreen: place references and labels without overlaps")
    print("updated", len(upd))

if __name__ == "__main__":
    main("--apply" in sys.argv)
