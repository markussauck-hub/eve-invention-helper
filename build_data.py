#!/usr/bin/env python3
"""
Baut invention.json fuer die Website aus dem Fuzzwork-SDE-Dump.

    python build_data.py                         # laedt von Fuzzwork, schreibt ./invention.json
    python build_data.py --out site/invention.json
    python build_data.py --local ./sde_csv       # nutzt lokal liegende CSVs (offline)

Nur Standardbibliothek.
"""

import argparse
import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://www.fuzzwork.co.uk/dump/latest/csv/"
USER_AGENT = "EVE-Invention-Helper/1.0 (GitHub Pages build)"
ACT_MANUFACTURING = 1
ACT_INVENTION = 8
SALVAGE_GROUP = 754      # invGroups: "Salvaged Materials"
PI_CATEGORY = 43         # invCategories: "Planetary Commodities"

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def rows(name, local_dir=None):
    if local_dir:
        text = (Path(local_dir) / f"{name}.csv").read_text(encoding="utf-8-sig")
    else:
        url = f"{BASE_URL}{name}.csv"
        print(f"Lade {url}", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=300) as resp:
            text = resp.read().decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    header = [h.strip().lower() for h in next(reader)]
    for row in reader:
        yield dict(zip(header, row))


def to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build(local_dir=None):
    names, published, group_of = {}, set(), {}
    for r in rows("invTypes", local_dir):
        tid = to_int(r.get("typeid"))
        if tid is None:
            continue
        names[tid] = r.get("typename", "")
        gid = to_int(r.get("groupid"))
        if gid is not None:
            group_of[tid] = gid
        if str(r.get("published", "")).strip().lower() in ("1", "true"):
            published.add(tid)

    category_of = {}
    for r in rows("invGroups", local_dir):
        gid, cid = to_int(r.get("groupid")), to_int(r.get("categoryid"))
        if None not in (gid, cid):
            category_of[gid] = cid

    times = {}
    for r in rows("industryActivity", local_dir):
        bp, act, t = to_int(r.get("typeid")), to_int(r.get("activityid")), to_int(r.get("time"))
        if None not in (bp, act, t):
            times[(bp, act)] = t

    def collect(name, key_col, val_col):
        out = {}
        for r in rows(name, local_dir):
            bp, act = to_int(r.get("typeid")), to_int(r.get("activityid"))
            k, v = to_int(r.get(key_col)), to_int(r.get(val_col))
            if None not in (bp, act, k, v):
                out.setdefault((bp, act), []).append([k, v])
        return out

    materials = collect("industryActivityMaterials", "materialtypeid", "quantity")
    skills = collect("industryActivitySkills", "skillid", "level")
    products = collect("industryActivityProducts", "producttypeid", "quantity")

    probs = {}
    for r in rows("industryActivityProbabilities", local_dir):
        bp, act = to_int(r.get("typeid")), to_int(r.get("activityid"))
        prod, p = to_int(r.get("producttypeid")), to_float(r.get("probability"))
        if act == ACT_INVENTION and None not in (bp, prod, p):
            probs[(bp, prod)] = p

    def first_product(bp, act):
        lst = products.get((bp, act))
        return lst[0][0] if lst else None

    bps, used = [], set()
    for (bp, act), prods in products.items():
        if act != ACT_INVENTION:
            continue
        for t2_bp, runs in prods:
            t2_prod = first_product(t2_bp, ACT_MANUFACTURING)
            check = t2_prod if t2_prod is not None else t2_bp
            if published and check not in published:
                continue
            entry = {
                "t1": bp,
                "t1p": first_product(bp, ACT_MANUFACTURING),
                "t2": t2_bp,
                "p": t2_prod,
                "r": runs,
                "c": probs.get((bp, t2_bp)),
                "t": times.get((bp, ACT_INVENTION)),
                "m": sorted(materials.get((bp, ACT_INVENTION), [])),
                "s": sorted(skills.get((bp, ACT_INVENTION), [])),
                "b": sorted(skills.get((t2_bp, ACT_MANUFACTURING), [])),
                "bm": sorted(materials.get((t2_bp, ACT_MANUFACTURING), [])),
            }
            bps.append(entry)
            used.update([bp, t2_bp])
            if entry["t1p"]:
                used.add(entry["t1p"])
            if t2_prod:
                used.add(t2_prod)
            for key in ("m", "s", "b", "bm"):
                used.update(i for i, _ in entry[key])

    bps.sort(key=lambda e: (names.get(e["p"]) or names.get(e["t2"], "")).lower())

    # Wer baut welches Bauteil? (veröffentlichte Blueprints bevorzugt)
    made_by = {}
    for (bp, act), prods in products.items():
        if act != ACT_MANUFACTURING:
            continue
        for prod, qty in prods:
            known = made_by.get(prod)
            if known is None or (known[0] not in published and bp in published):
                made_by[prod] = (bp, qty)

    # Nur Bauteile, die in irgendeinem T2-Rezept vorkommen – eine Ebene tief
    mb = {}
    for e in bps:
        for comp, _ in e["bm"]:
            if comp in mb or comp not in made_by:
                continue
            cbp, out = made_by[comp]
            mats = sorted(materials.get((cbp, ACT_MANUFACTURING), []))
            mb[str(comp)] = [out, mats]
            used.update(i for i, _ in mats)

    tags = {}
    for i in used:
        gid = group_of.get(i)
        if gid == SALVAGE_GROUP:
            tags[str(i)] = "S"
        elif gid is not None and category_of.get(gid) == PI_CATEGORY:
            tags[str(i)] = "P"

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Fuzzwork SDE dump (fuzzwork.co.uk/dump/latest/csv/)",
        "names": {str(i): names.get(i, f"#{i}") for i in sorted(used)},
        "tags": tags,
        "mb": mb,
        "bps": bps,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="invention.json")
    ap.add_argument("--local", help="Ordner mit lokalen SDE-CSVs statt Download")
    args = ap.parse_args()

    data = build(args.local)
    if not data["bps"]:
        sys.exit("Keine inventierbaren Blueprints gefunden – Datenquelle prüfen.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(data['bps'])} Blueprints, {len(data['names'])} Namen -> {out} "
          f"({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
