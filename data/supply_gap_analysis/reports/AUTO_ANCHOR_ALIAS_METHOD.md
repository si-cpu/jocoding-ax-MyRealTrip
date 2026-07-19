# Auto Anchor Alias Method

## Goal

Replace manually maintained aliases such as:

- `広島城 -> 히로시마성`
- `広島平和記念資料館 -> 히로시마평화기념관`

with a repeatable automatic candidate pipeline.

## Principle

The analysis unit remains a tourism place/spot anchor.

Aliases are not new anchors. They are matching aids that connect official Japanese place names to Korean product wording.

## Current pipeline

1. Read official tourism anchors from `official_experience_anchors.csv`.
2. Exclude food/yatai assets from the first-pass tourism-spot analysis.
3. Generate Korean alias candidates using conservative term rules.
4. Check whether each alias candidate appears in collected MCP product titles.
5. Use only candidates that:
   - match at least one MCP product title, and
   - have confidence `>= 0.75`.
6. Keep unmatched/low-confidence candidates in the candidate file for review, but do not use them for scoring.

## Current outputs

- `data/supply_gap_analysis/auto_anchor_alias_candidates.csv`
- `data/supply_gap_analysis/reports/auto_anchor_alias_candidate_summary.json`

## Current result

| Official name | Auto alias | Matched product signal |
|---|---|---|
| `広島城` | `히로시마성` | matched one MCP product title |
| `広島平和記念資料館` | `히로시마평화기념관` | matched one MCP product title |

## Why this is safer than direct manual aliases

Manual aliases can silently bias the analysis.

The automatic pipeline makes each alias candidate visible, scored, and reviewable. It also prevents weak candidates from affecting the main supply-gap score unless they are actually observed in MCP product wording.

## Known limitations

This is not a full Japanese-to-Korean translation system.

Some generated candidates still contain mixed Japanese/Korean text, especially long event titles. Those candidates are preserved for review but ignored in scoring unless they are observed in MCP product titles and pass confidence thresholds.

## Next improvements

- Add a curated reusable place-term dictionary by country/city.
- Add romaji/English route when official English names are available.
- Add tourism-event filters before alias generation.
- Use detail-level MCP itinerary text for tour products.
- Separate evidence levels:
  - `ticket_product_confirmed`
  - `tour_title_needs_detail`
  - `detail_confirmed`
  - `exclusion_only`
  - `detail_unavailable`
