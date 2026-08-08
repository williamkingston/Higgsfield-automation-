# Data Sources

Free public sources first, paid tools as a volume/speed shortcut. All NYC Open Data dataset IDs below are Socrata four-by-fours confirmed current as of this writing — they occasionally get renamed on republish, so if `fetch_nyc_violations.py` returns zero rows against a filter that should have hits, run it with `--discover` first to confirm the dataset is still live at that ID before assuming the data itself is empty.

## 1. Pre-foreclosure / Lis Pendens

A lis pendens (notice of pendency) is the first public filing when a lender starts foreclosure — the earliest actionable distress signal, filed while the owner still holds title.

**Queens County Clerk — Block and Lot Clerk**
- Phone: 718-298-0612
- Holds notices of pendency, mechanic's liens, building loan agreements, sidewalk violations, foreclosures
- Online: Queens County Clerk Document & Business Search — index years 1992–present; any case with activity since 2006 is viewable regardless of filing year
- Pre-1992: microfiche, in-person/staff search only
- Search certificate: $10 per 2-year search, $5 each additional 2 years

**NYSCEF** (NY State Courts Electronic Filing) — free search, filter county=Queens, case type=foreclosure. Returns index number, parties, filing date, document list.

**ACRIS** (NYC Dept. of Finance) — recorded lis pendens and foreclosure docs, digitized 1966–present. Indexed by BBL, party name, document type, recording date. Also where you confirm mortgage amount and current ownership.

**Paid shortcuts**: NYLisPendens.com (daily updates, 10 NY counties, since 1993), NYForeclosures.com (auctions/lis pendens/REO), PropertyShark (Queens-specific, strong on permits/violations/FAR/ownership), PropStream/BatchLeads (national, includes skip tracing + list stacking).

**Workflow**: pull new Queens lis pendens filings weekly → filter to zip 11691 and adjacent Far Rockaway/Bayswater zips → cross-reference in ACRIS for mortgage balance and equity position → skip trace owner → contact with HETPA-compliant paperwork ready.

## 2. Probate / Estate Properties

Heirs who inherit a house they don't live in and don't want are among the most motivated sellers — often out of state, often multiple siblings who just want it liquidated and split.

- **Queens County Surrogate's Court** — 88-11 Sutphin Blvd, Jamaica
- NY Unified Court System online Surrogate's Court case search — filings name the decedent, executor/administrator, and estate assets
- Cross-reference the decedent's name in ACRIS to find real property they owned

**Good-lead signals**: no surviving spouse on the deed, executor's mailing address outside NYC, open HPD/DOB violation on the property (nobody's maintaining it), no mortgage recorded or a very old one (high equity, easy close).

**Timing**: reach out 2–4 months after filing — earlier reads as intrusive, later and the estate attorney has already listed it.

## 3. Building & Housing Violations

Open violations signal deferred maintenance and an owner without money or attention — a property that spooks retail buyers and their lenders.

NYC Open Data (Socrata, all downloadable as CSV, all expose OData for live Excel/Sheets refresh):

| Dataset | Socrata ID | Notes |
|---|---|---|
| DOB Violations (older civil penalties, BIS system) | `mkgf-zjhb` | may also appear as `3h2n-5cm9` — verify current ID before a large pull |
| DOB Safety Violations (newer civil penalties, DOB NOW) | `855j-jady` | some overlap with DOB Violations |
| DOB ECB Violations (summonses, adjudicated by OATH/ECB) | `6bgk-3dad` | |
| HPD Housing Violations (Housing Maintenance Code) | `kw57-27ma` | updated daily; classes A (least severe) through C (immediately hazardous: no heat/hot water, lead paint, rodents) |

API pattern (Socrata SODA): `https://data.cityofnewyork.us/resource/{dataset_id}.json?$where=...&$limit=...`. Use `scripts/fetch_nyc_violations.py` rather than hand-rolling requests — it handles the discovery step for field names, which differ slightly per dataset.

**Filter recipe**: borough=Queens, zip=11691 and neighbors, status=OPEN, sorted by violation count per BBL descending. Prioritize Class B/C on the HPD side; structural, illegal-conversion, and work-without-permit on the DOB side.

**Single-property lookup**: DOB BIS Property Profile — open violations, permits, Certificate of Occupancy. Open DOB violations show without an asterisk; dismissed ones show with one (e.g. `V*7052-18P`).

## 4. Tax Delinquency & Lien Sale

NYC Dept. of Finance's annual lien sale list — unpaid property taxes, water charges, or other municipal debts. Owners face a hard deadline, which creates real urgency.

- Dataset: **Tax Lien Sale Lists**, Socrata ID `9rz4-mjek`, ~264K rows, JSON/XML/CSV, OData available.

**HETPA note**: properties on this list are explicitly HETPA-covered (see `hetpa-compliance.md`). Do not approach without compliant paperwork.

## 5. Absentee & Long-Tenure Owners

The quietest list, often the best — no distress signal, just disinterest.

**Filter target**: owner's mailing address ≠ property address (absentee); ownership tenure 20+ years (high equity, low basis); no permits pulled in 15+ years (deferred maintenance); non-owner-occupied 2–4 family (tired landlords).

**Sources**: ACRIS for deeds and mailing addresses (free, but not built for bulk filtering — fine for single-property lookups, painful at volume); NYC DOF property tax records; PropertyShark or PropStream to filter at volume (paid). If the user doesn't have a paid tool with API/export access, this list is realistically a manual, slow build via ACRIS — say so rather than promising a bulk pull that isn't available for free.

## Queens zip codes for reference (Far Rockaway / Bayswater area)

11691 (Far Rockaway core), and adjacent: 11693 (Broad Channel/Rockaway Park), 11692 (Arverne/Edgemere), 11694 (Rockaway Park/Belle Harbor), 11695 (Rockaway Point). Confirm with the user which adjacent zips they actually want in scope before pulling — "Far Rockaway and adjacent" can mean different radii to different people.
