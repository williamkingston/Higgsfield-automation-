#!/usr/bin/env python3
"""Pull a NYC Open Data (Socrata) dataset — DOB/HPD violations, tax lien sale list,
etc. — filtered by zip code, and save it as CSV.

Socrata dataset IDs occasionally get renamed on republish, and exact field names
differ per dataset (e.g. "zip" vs "zip_code" vs "postcode"). Run with --discover
first against a new dataset ID to see real column names before building a filter.

Examples:
    # See what columns a dataset actually has
    python fetch_nyc_violations.py --dataset kw57-27ma --discover

    # Pull HPD violations for Far Rockaway zips, status OPEN
    python fetch_nyc_violations.py --dataset kw57-27ma \\
        --zip-field zip --zips 11691,11692,11693 \\
        --status-field violationstatus --status Open \\
        --out hpd_violations_11691.csv

    # Pull the tax lien sale list for the same zips (no status filter)
    python fetch_nyc_violations.py --dataset 9rz4-mjek \\
        --zip-field zip_code --zips 11691,11692,11693 \\
        --out tax_lien_11691.csv
"""
import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request

SOCRATA_BASE = "https://data.cityofnewyork.us/resource/{dataset}.json"


def fetch(dataset: str, params: dict) -> list[dict]:
    url = SOCRATA_BASE.format(dataset=dataset) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, help="Socrata dataset ID (four-by-four), e.g. kw57-27ma")
    ap.add_argument("--discover", action="store_true", help="Fetch a small sample and print column names, then exit")
    ap.add_argument("--zip-field", help="Column name for zip code (varies per dataset — use --discover to find it)")
    ap.add_argument("--zips", help="Comma-separated zip codes to filter to, e.g. 11691,11692,11693")
    ap.add_argument("--status-field", help="Column name for status, if filtering by it")
    ap.add_argument("--status", help="Status value to filter to, e.g. Open")
    ap.add_argument("--limit", type=int, default=50000, help="Max rows to fetch (default 50000)")
    ap.add_argument("--out", help="Output CSV path (required unless --discover)")
    args = ap.parse_args()

    if args.discover:
        rows = fetch(args.dataset, {"$limit": 5})
        if not rows:
            print(f"Dataset {args.dataset} returned no rows at all — check the ID is still current at "
                  f"https://data.cityofnewyork.us/resource/{args.dataset}.json", file=sys.stderr)
            sys.exit(1)
        print(f"Columns in dataset {args.dataset}:")
        for col in sorted(rows[0].keys()):
            print(f"  {col}")
        print("\nSample row:")
        print(json.dumps(rows[0], indent=2))
        return

    if not args.out:
        ap.error("--out is required unless using --discover")

    where_clauses = []
    if args.zips:
        if not args.zip_field:
            ap.error("--zip-field is required when --zips is given (run --discover to find the right column name)")
        zip_list = [z.strip() for z in args.zips.split(",")]
        quoted = ",".join(f"'{z}'" for z in zip_list)
        where_clauses.append(f"{args.zip_field} in ({quoted})")
    if args.status:
        if not args.status_field:
            ap.error("--status-field is required when --status is given")
        where_clauses.append(f"upper({args.status_field})=upper('{args.status}')")

    params = {"$limit": args.limit}
    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    rows = fetch(args.dataset, params)
    if not rows:
        print("Query returned 0 rows. If you expected results, re-run with --discover to confirm the "
              "dataset ID and field names are correct before assuming the data source is empty.", file=sys.stderr)

    fieldnames = sorted({k for row in rows for k in row.keys()}) if rows else []
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
