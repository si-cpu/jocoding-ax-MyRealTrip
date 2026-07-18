# Official Experience Anchor Build Report

- Generated at: 2026-07-18T14:40:46+09:00
- Anchor count: 172
- By city: {'jp-fukuoka': 108, 'jp-hiroshima': 64}
- By type: {'place_cluster': 1, 'food_place': 107, 'place': 32, 'event': 32}
- By source: {'official_yatai_cluster': 1, 'official_yatai': 107, 'tourism_facility': 32, 'official_event': 32}

## Outputs

- `data/official_tourism_sources/anchors/official_experience_anchors.csv`
- `data/official_tourism_sources/anchors/official_experience_anchors.jsonl`

## Notes

- Fukuoka yatai anchors are deduplicated by `屋台ID`.
- Hiroshima tourism facilities are filtered to Hiroshima city code `341002`.
- Hiroshima event anchors are time-sensitive and should be discounted or excluded when expired.
