import sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
from model import load, outline
NC = {"/VDD_3V3": "#e03030", "/VDD_1V1": "#2080ff", "/VDD_2V5": "#20b040", "GND": "#000000"}
def view(layer, box, out, pads=None, tracks=None, plan=None):
    if pads is None: pads, _, tracks = load()
    fig, ax = plt.subplots(figsize=(12, 12 * (box[3] - box[1]) / (box[2] - box[0])))
    for p in pads:
        if layer not in p.layers: continue
        c = NC.get(p.net, "#bbbbbb")
        for g in getattr(p.poly, "geoms", [p.poly]):
            ax.add_patch(MP(list(g.exterior.coords), fc=c, alpha=0.35, ec='none'))
        if box[0] < p.center[0] < box[2] and box[1] < p.center[1] < box[3]:
            ax.text(*p.center, f"{p.ref}.{p.num}", fontsize=4, ha='center', va='center')
    items = list(tracks)
    if plan: items += [dict(kind=i['kind'], layer=i['layers'][0], net=i['net'], w=i.get('w'), pts=[i['a'], i['b']]) if i['kind']=='seg' else dict(kind='via', net=i['net'], x=i['x'], y=i['y'], d=i['d']) for i in plan.items]
    for t in items:
        if t['kind'] == 'seg' and t['layer'] == layer:
            (a, b) = t['pts']; ax.plot([a[0], b[0]], [a[1], b[1]], color=NC.get(t['net'], "#999999"), lw=max(0.5, t['w'] * 30), alpha=0.8, solid_capstyle='round')
        elif t['kind'] == 'via':
            ax.add_patch(Circle((t['x'], t['y']), t['d'] / 2, fc=NC.get(t['net'], "#777777"), ec='k', lw=0.3, alpha=0.9))
    ax.set_xlim(box[0], box[2]); ax.set_ylim(box[3], box[1]); ax.set_aspect('equal')
    import numpy as np
    ax.set_xticks(np.arange(int(box[0]), box[2], 1)); ax.set_yticks(np.arange(int(box[1]), box[3], 1)); ax.grid(lw=0.2); ax.tick_params(labelsize=6)
    ax.set_title(layer); fig.savefig(out, dpi=160, bbox_inches='tight'); plt.close(fig)
if __name__ == "__main__":
    b = tuple(map(float, sys.argv[2:6])); view(sys.argv[1], b, sys.argv[6])
