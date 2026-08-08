# List Stacking & Scoring

## Why stacking matters more than any single list

Any one distress list is mostly noise — most lis pendens filings cure, most violations get fixed, most absentee owners are perfectly content. What separates a live deal from noise is **overlap**: a property showing up on two or more independent lists is dramatically more likely to have a genuinely motivated seller behind it, because each additional list is an independent signal pointing the same direction.

## The join key: BBL

Every source list needs to resolve to a **BBL** (Borough-Block-Lot) before it can be stacked. Queens is borough code `4`. If a source only gives block/lot, construct it as:

```
bbl = "4" + block.zfill(5) + lot.zfill(4)
```

(10-digit BBL: 1-digit borough + 5-digit block + 4-digit lot.)

If a source gives an address instead of BBL/block/lot, it needs to be geocoded against NYC's PLUTO/GeoSearch data before it can join — flag this to the user rather than silently dropping rows or guessing.

## Scoring model

`scripts/stack_leads.py` implements the simplest version of this: **score = number of distinct source files a BBL appears in.** That's a reasonable default and matches the source playbook's own recommendation to "work the 3+ hits first."

If the user wants a weighted score instead (e.g. lis pendens hit worth more than an absentee-owner hit because it's more time-sensitive), that's a legitimate refinement — but start with the simple count. It's transparent, it's easy for the user to audit by eye, and weighting schemes are easy to over-fit to a handful of past deals without enough data to justify the weights.

## High-value combinations to call out specifically

| Combination | What it signals |
|---|---|
| Probate + open violations | Heirs, nobody maintaining it, want out |
| Absentee + tax delinquent | Owner disengaged and now under a deadline |
| Lis pendens + high equity (low mortgage balance relative to ACRIS-confirmed value) | Motivated *and* room to negotiate |
| Long tenure + no permits + absentee | Tired landlord, low basis, likely to take a discount |

When presenting a stacked/scored spreadsheet back to the user, call out any rows matching these combinations explicitly rather than just handing over a sorted-by-score table — the combination itself is often more informative than the raw count, especially at a 2-hit score where the *which two* matters as much as *how many*.

## Output spreadsheet shape

Minimum columns for the stacked output: `bbl`, `score`, one column per source (boolean or hit-count), plus any owner/address/mailing-address columns that survived the merge (useful for skip tracing without a second lookup pass). Sort descending by score, then flag rows matching the high-value combinations above.
