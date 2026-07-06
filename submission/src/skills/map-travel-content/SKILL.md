---
name: map-travel-content
description: "Turn a destination into a MyRealTrip-backed content map with two sections: what to do and what to eat. Use when a traveler asks what to do, see, experience, or eat in a city or region and needs concrete named experiences—places, franchises, characters, teams, performances, dishes, and food activities—linked to official MyRealTrip products without personalized ranking."
---

# Map Travel Content

Build a discovery index, not a personalized recommendation.

## First response

On the first use, briefly explain:

> 여행지를 입력하면 마이리얼트립 상품에서 확인되는 `뭐 하지?`와 `뭐 먹지?`를 구체적인 키워드로 보여드려요. 키워드를 고르면 관련 공식 상품으로 연결합니다.

Then ask only for the destination when it is missing. Date is optional.

## Workflow

1. Read [references/content-indexing-rules.md](references/content-indexing-rules.md).
2. Run `../../scripts/myrealtrip_api.py tna-collect --city CITY --with-details` relative to this skill folder.
3. Read `MYREALTRIP_API_KEY` only from the environment. Never ask the user to paste a key.
4. If Partner REST is unavailable, use the configured official MyRealTrip MCP TNA search and detail tools when available.
5. Reject city mismatches and non-experience utility categories.
6. Extract concrete content candidates from returned titles, descriptions, inclusions, and itineraries.
7. Apply the evidence contract and normalize only verified aliases.
8. Separate accepted keywords into `뭐 하지?` and `뭐 먹지?`.
9. Show keywords first. Expand related products after the user selects a keyword, unless the user explicitly asks for links immediately.
10. Before displaying an expanded product link, run `../../scripts/myrealtrip_api.py url-check --url PRODUCT_URL`. Keep only links with `reachable: true` and a final official MyRealTrip domain.
11. When a date is supplied, verify every expanded product with TNA options for that date.

## Output

Use this structure:

```markdown
## {여행지}에서 뭐 하지?

- 구체적인 키워드
- 구체적인 키워드

## {여행지}에서 뭐 먹지?

- 구체적인 음식 또는 식사 경험
- 구체적인 음식 또는 식사 경험
```

Do not show empty sections. If one section has no supported keyword, say that no linked content was confirmed in the checked product range.

When expanding a keyword:

```markdown
### {선택한 키워드}

- [공식 상품명](productUrl) — 상품에서 확인된 짧은 연결 근거
```

State `이번에 확인한 상품 범위에서` when collection metadata says results or details were truncated. Use `조회된 마이리얼트립 상품 전체에서` only when all search pages and eligible details completed.

## Judgment boundaries

- Do not choose the best product for the user.
- Do not infer personality, budget, companions, or hidden preferences.
- Do not use popularity, rating, or price as evidence that a keyword fits the user.
- Do not invent famous foods or sights from general knowledge when no returned product supports them.
- Do not attach a product to a keyword merely because both belong to a broad theme.
- Preserve separate experiences when merging could mislead.
- Do not book, pay, cancel, or modify a reservation.

## Failure behavior

- Missing API key and no MCP: explain that official inventory cannot be checked and stop.
- Empty city result: state that no linked product was found; do not fill the gap with web suggestions.
- Detail unavailable: use only content directly supported by the search title.
- Date options empty or unknown: provide the product only as a discovery link, not as available for that date.
- URL validation failure: omit the broken link, state that the official product page could not be reached, and do not invent a replacement URL.
