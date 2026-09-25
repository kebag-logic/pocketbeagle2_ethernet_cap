"""Build every manufacturing output into build/ from the committed schematic and board.

  build/fabrication  Gerbers + Excellon drill (and the zip to upload to JLCPCB), IPC-D-356 netlist
  build/assembly     JLCPCB BOM (LCSC #), CPL (pick & place), full BOM with all distributors, assembly drawing
  build/docs         schematic PDF, 3D STEP of the assembled cape, DRC report

Needs kicad-cli (KiCad 10); the assembly drawing also needs Python with shapely + matplotlib.
Usage: python tools/make_build.py [--no-step]"""
import csv, os, re, shutil, subprocess, sys, zipfile, collections

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "pocketbeagle2_ethernet_cap"
PCB = os.path.join(PRJ, f"{NAME}.kicad_pcb")
SCH = os.path.join(PRJ, f"{NAME}.kicad_sch")
OUT = os.environ.get("BUILD_OUT", os.path.join(PRJ, "build"))
FAB, ASM, DOC = (os.path.join(OUT, d) for d in ("fabrication", "assembly", "docs"))
KL = ["-D", f"KL_LIB={PRJ}/kebag_logic_kicad_library"]
NOT_ASSEMBLED = {"U1", "J1"}   # PB2 module plugs onto J2/J3; J1 magjack is not stocked at LCSC: hand-solder
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
nat = lambda s: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(f"failed: {' '.join(a)}")
    return r.stdout


def restore_pro():
    """kicad-cli must not leave the project file modified"""
    r = subprocess.run(["git", "-C", PRJ, "status", "--short", f"{NAME}.kicad_pro"], capture_output=True, text=True)
    if r.stdout.strip():
        subprocess.run(["git", "-C", PRJ, "checkout", "--", f"{NAME}.kicad_pro"])


def fabrication():
    g = os.path.join(FAB, "gerber")
    shutil.rmtree(g, ignore_errors=True); os.makedirs(g)
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--check-zones",
        "--no-netlist", *KL, "-o", g + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
        "--map-format", "gerberx2", "-u", "mm", "-o", g + "/", PCB)
    z = os.path.join(FAB, f"{NAME}_gerber.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in sorted(os.listdir(g)):
            f.write(os.path.join(g, n), n)
    run("kicad-cli", "pcb", "export", "ipcd356", "-o", os.path.join(FAB, f"{NAME}.ipc"), PCB)
    print("fabrication:", len(os.listdir(g)), "gerber/drill files, zip, IPC-D-356")


def boms():
    raw = os.path.join(ASM, "bom_raw.csv")
    run("kicad-cli", "sch", "export", "bom", "--fields",
        "Reference,Value,Footprint,MPN,MANUFACTURER,Manufacturer,LCSC,Digikey,Mouser,${DNP},${EXCLUDE_FROM_BOM}",
        "--labels", "Ref,Value,Footprint,MPN,MFR1,MFR2,LCSC,Digikey,Mouser,DNP,EXCL", "--group-by", "",
        "--ref-range-delimiter", "", "-o", raw, SCH)
    rows = list(csv.DictReader(open(raw)))
    os.remove(raw)
    jlc, full, skipped = collections.OrderedDict(), collections.OrderedDict(), []
    for r in rows:
        ref, fp = r["Ref"], r["Footprint"].split(":")[-1]
        if r["DNP"] or r["EXCL"]:
            continue
        mfr = r["MFR1"] or r["MFR2"]
        full.setdefault((r["Value"], mfr, r["MPN"], fp, r["LCSC"], r["Digikey"], r["Mouser"]), []).append(ref)
        if ref in NOT_ASSEMBLED or ref.startswith("TP"):
            skipped.append(ref); continue
        jlc.setdefault((r["Value"], r["MPN"], fp, r["LCSC"]), []).append(ref)
    path = os.path.join(ASM, f"{NAME}_bom_jlcpcb.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part", "Quantity"])
        for (val, mpn, fp, lcsc), refs in sorted(jlc.items(), key=lambda kv: nat(kv[1][0])):
            refs.sort(key=nat); w.writerow([val, ",".join(refs), fp, lcsc, mpn, len(refs)])
    path2 = os.path.join(ASM, f"{NAME}_bom_full.csv")
    with open(path2, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Quantity", "Value", "Manufacturer", "MPN", "Footprint", "LCSC", "Digikey", "Mouser",
                    "Assembled by JLCPCB"])
        for (val, mfr, mpn, fp, lcsc, dk, mo), refs in sorted(full.items(), key=lambda kv: nat(kv[1][0])):
            refs.sort(key=nat)
            asm = "no" if all(r in NOT_ASSEMBLED or r.startswith("TP") for r in refs) else "yes"
            w.writerow([",".join(refs), len(refs), val, mfr, mpn, fp, lcsc, dk, mo, asm])
    print("assembly: JLC BOM", len(jlc), "lines, full BOM", len(full), "lines; not assembled:", sorted(set(skipped), key=nat))
    return {r for g in jlc.values() for r in g}


def cpl(refs):
    raw = os.path.join(ASM, "pos_raw.csv")
    run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", raw, PCB)
    rows = list(csv.DictReader(open(raw)))
    os.remove(raw)
    path = os.path.join(ASM, f"{NAME}_cpl_jlcpcb.csv")
    n = 0
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in sorted(rows, key=lambda r: nat(r["Ref"])):
            if r["Ref"] in refs:
                w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm',
                            "Top" if r["Side"] == "top" else "Bottom", f'{float(r["Rot"]):.1f}']); n += 1
    print("assembly: CPL", n, "placements")


def drawing():
    sys.path[:0] = [os.path.join(PRJ, "tools", "respin"), os.path.join(PRJ, "tools", "respin", "topside")]
    try:
        out = os.path.join(ASM, f"{NAME}_assembly.pdf")
        subprocess.run([sys.executable, os.path.join(PRJ, "tools", "respin", "topside", "asm_drawing.py"), out],
                       check=True, env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path[:2])})
    except Exception as e:
        print("assembly drawing skipped:", e)


def docs(step=True):
    os.makedirs(DOC, exist_ok=True)
    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(DOC, f"{NAME}_schematic.pdf"), SCH)
    run("kicad-cli", "pcb", "drc", "--format", "report", "--severity-all", "--refill-zones", "--schematic-parity",
        "-o", os.path.join(DOC, f"{NAME}_drc.rpt"), PCB)
    if step:
        # the assembled cape without the PocketBeagle 2 module (U1) on top
        run("kicad-cli", "pcb", "export", "step", "--force", "--subst-models", *KL,
            "--component-filter", "C*,R*,D*,Q*,U2,U3,U4,Y1,J*",
            "-o", os.path.join(DOC, f"{NAME}_cape.step"), PCB)
    print("docs: schematic PDF, DRC report" + (", STEP" if step else ""))


if __name__ == "__main__":
    for d in (FAB, ASM, DOC):
        os.makedirs(d, exist_ok=True)
    try:
        fabrication()
        cpl(boms())
        drawing()
        docs(step="--no-step" not in sys.argv)
    finally:
        restore_pro()
