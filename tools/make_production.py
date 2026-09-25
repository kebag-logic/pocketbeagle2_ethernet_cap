"""JLCPCB production files: Gerbers + drill (zip), LCSC BOM and CPL (pick & place) from the saved project."""
import csv, os, subprocess, zipfile, collections, re, shutil, sys
PRJ = "/home/alex/prjs/ames/switch/pocketbeagle2_ethernet_cap"
OUT = os.environ.get("PROD_OUT", os.path.join(PRJ, "production"))
PCB = os.path.join(PRJ, "pocketbeagle2_ethernet_cap.kicad_pcb")
SCH = os.path.join(PRJ, "pocketbeagle2_ethernet_cap.kicad_sch")
KL = ["-D", f"KL_LIB={PRJ}/kebag_logic_kicad_library"]
NOT_ASSEMBLED = {"U1", "J1"}   # PB2 module plugs onto J2/J3; J1 magjack is not stocked at LCSC: hand-solder
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(f"failed: {a}")
    return r.stdout


def gerbers():
    g = os.path.join(OUT, "gerber")
    shutil.rmtree(g, ignore_errors=True); os.makedirs(g)
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--check-zones",
        "--no-netlist", *KL, "-o", g + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th", "--generate-map",
        "--map-format", "gerberx2", "-u", "mm", "-o", g + "/", PCB)
    z = os.path.join(OUT, "pocketbeagle2_ethernet_cap_gerber.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in sorted(os.listdir(g)):
            f.write(os.path.join(g, n), n)
    print("gerber zip:", z, len(os.listdir(g)), "files")


def bom():
    raw = os.path.join(OUT, "bom_raw.csv")
    run("kicad-cli", "sch", "export", "bom", "--fields", "Reference,Value,Footprint,MPN,Manufacturer,LCSC,${DNP},${EXCLUDE_FROM_BOM}",
        "--labels", "Ref,Value,Footprint,MPN,Manufacturer,LCSC,DNP,EXCL", "--group-by", "", "--ref-range-delimiter", "",
        "-o", raw, SCH)
    rows = list(csv.DictReader(open(raw)))
    os.remove(raw)
    groups = collections.OrderedDict()
    skipped = []
    for r in rows:
        ref = r["Ref"]
        if r["DNP"] or r["EXCL"] or ref in NOT_ASSEMBLED or ref.startswith("TP"):
            skipped.append(ref); continue
        fp = r["Footprint"].split(":")[-1]
        key = (r["Value"], r["MPN"], fp, r["LCSC"])
        groups.setdefault(key, []).append(ref)
    nat = lambda s: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]
    path = os.path.join(OUT, "pocketbeagle2_ethernet_cap_bom_jlcpcb.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Manufacturer Part", "Quantity"])
        for (val, mpn, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: nat(kv[1][0])):
            refs.sort(key=nat)
            w.writerow([val, ",".join(refs), fp, lcsc, mpn, len(refs)])
    print("BOM:", path, len(groups), "lines; not assembled:", sorted(skipped, key=nat))
    return {r for g in groups.values() for r in g}


def cpl(refs):
    raw = os.path.join(OUT, "pos_raw.csv")
    run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "-o", raw, PCB)
    rows = list(csv.DictReader(open(raw)))
    os.remove(raw)
    path = os.path.join(OUT, "pocketbeagle2_ethernet_cap_cpl_jlcpcb.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        n = 0
        for r in rows:
            if r["Ref"] not in refs:
                continue
            w.writerow([r["Ref"], f'{float(r["PosX"]):.4f}mm', f'{float(r["PosY"]):.4f}mm',
                        "Top" if r["Side"] == "top" else "Bottom", f'{float(r["Rot"]):.1f}'])
            n += 1
    print("CPL:", path, n, "placements")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    refs = bom()
    cpl(refs)
    if "--no-gerber" not in sys.argv:
        gerbers()
