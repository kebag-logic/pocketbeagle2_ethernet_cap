"""Assembly drawing (vector PDF): board outline, pads, courtyards and every reference on its part body."""
import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MP
from model import load, outline
from crtyd import load_crtyd, placed

pads, fps, tracks = load()
cr = load_crtyd()
out = sys.argv[1]
with PdfPages(out) as pdf:
    for side, title in (("F.Cu", "TOP (all assembled SMD parts, J2/J3)"), ("B.Cu", "BOTTOM (J1 magjack, test pads)")):
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        o = outline(); xs, ys = o.exterior.xy
        ax.plot(xs, ys, color="k", lw=0.8)
        for p in pads:
            if side in p.layers and len(p.layers) == 1 or (p.drill and p.ref not in ("U1",)):
                for g in getattr(p.poly, "geoms", [p.poly]):
                    ax.add_patch(MP(list(g.exterior.coords), fc="#d9b44a" if side in p.layers else "#dddddd", ec="none", alpha=0.6, lw=0))
        for ref, c in sorted(cr.items()):
            if c["side"] != side or ref == "U1":
                continue
            g = placed(c)
            x0, y0, x1, y1 = g.bounds
            ax.add_patch(MP(list(g.exterior.coords), fc="none", ec="#3050c0", lw=0.3))
            w, h = x1 - x0, y1 - y0
            vertical = h > w * 1.2
            L = max(w, h); S = min(w, h)
            fs = max(1.6, min(7.0, L / (0.62 * len(ref)) * 2.83, S * 2.83 * 0.8))   # points: 1 mm ~ 2.83 pt
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, ref, fontsize=fs, ha="center", va="center",
                    rotation=90 if vertical else 0, color="#b00000", family="DejaVu Sans")
        ax.set_aspect("equal"); ax.invert_yaxis()
        if side == "B.Cu":
            ax.invert_xaxis()      # viewed from the bottom
        ax.set_xlim(178, 215) if side == "F.Cu" else ax.set_xlim(215, 178)
        ax.set_ylim(118, 54)
        ax.axis("off")
        ax.set_title(f"pocketbeagle2_ethernet_cap rev B - assembly {title}", fontsize=9)
        pdf.savefig(fig); plt.close(fig)
print("wrote", out)
