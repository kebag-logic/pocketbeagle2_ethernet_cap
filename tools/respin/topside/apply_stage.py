"""Apply a stage: check live pad positions vs the model, remove pruned copper (exact endpoints), push the plan."""
import sys, json, math, importlib
from kipy import KiCad
from push import push, NM
import ts

def main(modname, prmfile, dry=False):
    mod = importlib.import_module(modname)
    D = mod.build(json.load(open(prmfile)))
    k = KiCad(socket_path="ipc:///tmp/kicad/api.sock"); b = k.get_board()
    # 1. live pads of placed parts vs model
    want = {(p.ref, p.num): p.center for p in mod.pads if p.ref in ts.PLACE}
    bad = 0
    for fp in b.get_footprints():
        ref = fp.reference_field.text.value
        if ref not in ts.PLACE: continue
        for pad in fp.definition.pads:
            c = want.get((ref, pad.number))
            x, y = pad.position.x / 1e6, pad.position.y / 1e6
            if c is None or math.dist(c, (x, y)) > 0.002:
                print("PAD MISMATCH", ref, pad.number, (x, y), c); bad += 1
    assert not bad
    # 2. removals
    rem = mod.removed
    segs = {}
    for t in rem:
        if t['kind'] == 'seg':
            a, e = t['pts']
            segs[frozenset({(NM(a[0]), NM(a[1])), (NM(e[0]), NM(e[1]))}), t['layer']] = t
    vias = {(NM(t['x']), NM(t['y'])) for t in rem if t['kind'] == 'via'}
    LN = {3: 'F.Cu', 34: 'B.Cu'}
    rm_t = []
    for t in b.get_tracks():
        key = (frozenset({(t.start.x, t.start.y), (t.end.x, t.end.y)}), 'F.Cu' if t.layer == 3 else 'B.Cu')
        if key in segs:
            rm_t.append(t)
    rm_v = [v for v in b.get_vias() if (v.position.x, v.position.y) in vias]
    print("remove", len(rm_t), "of", len(segs), "segs;", len(rm_v), "of", len(vias), "vias")
    assert len(rm_t) == len(segs) and len(rm_v) == len(vias)
    if dry:
        return
    c = b.begin_commit(); b.remove_items(rm_t + rm_v); b.push_commit(c, f"{modname}: remove copper of re-placed parts")
    push(D.plan, f"{modname}: top-side rework copper")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], dry="--dry" in sys.argv)
