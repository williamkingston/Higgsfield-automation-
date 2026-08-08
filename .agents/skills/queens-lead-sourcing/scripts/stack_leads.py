#!/usr/bin/env python3
"""Stack multiple lead-source CSVs into one BBL-keyed spreadsheet, scored by how
many source lists each property (BBL) appears on.

Each input CSV must have a "bbl" column (case-insensitive). If a source only has
block/lot, build the bbl column first: bbl = "4" + block.zfill(5) + lot.zfill(4)
for Queens (borough code 4).

The source name used in the output (one boolean column per source) is the CSV's
filename stem unless overridden with --name.

Example:
    python stack_leads.py \\
        --source lis_pendens_q1.csv \\
        --source probate_filings.csv --name probate \\
        --source hpd_violations_11691.csv --name hpd_violations \\
        --source tax_lien_11691.csv --name tax_lien \\
        --out stacked_leads.csv
"""
import argparse
import csv
import sys
from collections import defaultdict


def find_bbl_key(fieldnames: list[str]) -> str:
    for f in fieldnames:
        if f.strip().lower() == "bbl":
            return f
    raise ValueError(f"No 'bbl' column found among: {fieldnames}")


def normalize_bbl(raw: str) -> str:
    return "".join(ch for ch in raw.strip() if ch.isdigit())


def load_source(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", action="append", required=True, dest="sources",
                     help="Path to a source CSV with a 'bbl' column. Repeat for each source.")
    ap.add_argument("--name", action="append", dest="names", default=[],
                     help="Display name for the preceding --source (in order). Optional — defaults to filename stem.")
    ap.add_argument("--out", required=True, help="Output CSV path")
    args = ap.parse_args()

    names = list(args.names)
    while len(names) < len(args.sources):
        import os
        idx = len(names)
        names.append(os.path.splitext(os.path.basename(args.sources[idx]))[0])
    if len(names) != len(args.sources):
        ap.error("--name count must not exceed --source count")

    # bbl -> {"hits": {source_name: True}, "score": int, extra columns merged in}
    merged: dict[str, dict] = defaultdict(lambda: {"hits": {}, "extra": {}})

    for path, name in zip(args.sources, names):
        rows = load_source(path)
        if not rows:
            print(f"Warning: {path} has no rows, skipping", file=sys.stderr)
            continue
        bbl_key = find_bbl_key(rows[0].keys())
        for row in rows:
            raw_bbl = row.get(bbl_key, "")
            bbl = normalize_bbl(raw_bbl)
            if not bbl:
                continue
            entry = merged[bbl]
            entry["hits"][name] = True
            for col, val in row.items():
                if col == bbl_key or not val:
                    continue
                # Don't clobber a value already captured from an earlier source
                entry["extra"].setdefault(col, val)

    if not merged:
        print("No rows with a usable bbl column across any source — nothing to write.", file=sys.stderr)
        sys.exit(1)

    all_extra_cols = sorted({col for entry in merged.values() for col in entry["extra"].keys()})
    fieldnames = ["bbl", "score"] + names + all_extra_cols

    ranked = sorted(merged.items(), key=lambda kv: len(kv[1]["hits"]), reverse=True)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for bbl, entry in ranked:
            row = {"bbl": bbl, "score": len(entry["hits"])}
            for name in names:
                row[name] = "Y" if name in entry["hits"] else ""
            row.update(entry["extra"])
            writer.writerow(row)

    three_plus = sum(1 for _, e in ranked if len(e["hits"]) >= 3)
    print(f"Wrote {len(ranked)} unique BBLs to {args.out} ({three_plus} with 3+ source hits — work these first)")


if __name__ == "__main__":
    main()
