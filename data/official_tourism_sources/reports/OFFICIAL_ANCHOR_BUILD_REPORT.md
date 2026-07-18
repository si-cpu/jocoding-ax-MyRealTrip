# Official Experience Anchor Build Report

- Generated at: 2026-07-18T16:17:08+09:00
- Anchor count: 742
- By city: {'jp-fukuoka': 108, 'jp-kyoto': 570, 'jp-hiroshima': 64}
- By type: {'place_cluster': 1, 'food_place': 107, 'place': 602, 'event': 32}
- By source: {'official_yatai_cluster': 1, 'official_yatai': 107, 'tourism_facility': 602, 'official_event': 32}

## Outputs

- `data/official_tourism_sources/anchors/official_experience_anchors.csv`
- `data/official_tourism_sources/anchors/official_experience_anchors.jsonl`
- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.csv`
- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.jsonl`

## Notes

- Fukuoka yatai anchors are deduplicated by `屋台ID`.
- Hiroshima tourism facilities are filtered to Hiroshima city code `341002`.
- Kyoto tourism facilities are filtered to municipality names starting with `京都市`; lodging/restaurant-like records are excluded from primary place anchors by name terms.
- Hiroshima event anchors are time-sensitive and should be discounted or excluded when expired.
- Multi-city seed anchors are exported separately as candidate/demo anchors and are excluded from the primary official anchor file to avoid analysis contamination.
