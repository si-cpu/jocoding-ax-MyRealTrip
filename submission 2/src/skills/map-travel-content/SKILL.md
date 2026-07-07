---
name: map-travel-content
description: "Turn a destination into balanced MyRealTrip-backed experience shelves, then reveal whether a selected experience is available as an admission ticket, pass, tour, activity, food product, or scenic transport. Use when a traveler asks what to do or eat and needs concrete named reasons to travel without popularity ranking or inferred personalization."
---

# Map Travel Content

Build an experience display shelf, not a personalized recommendation or a product-format list.

## First response

On the first use, briefly explain:

> 여행지를 입력하면 마이리얼트립 상품을 입장권·패스·투어별로 균형 있게 확인한 뒤, 그 안의 장소·작품·팀·공연·음식을 경험 진열대로 펼쳐드려요. 마음이 가는 경험을 고르면 이용 가능한 구매 방식을 보여드립니다.

Then ask only for the destination when it is missing. Date is optional.

## Workflow

1. Read [references/content-indexing-rules.md](references/content-indexing-rules.md).
2. Use the official `myrealtrip` MCP server configured in the plugin's `.mcp.json`. Do not require a Partner REST API key from the traveler.
3. From the available MyRealTrip MCP tools, use the TNA category, product search, product detail, product option, and official product-link capabilities that match the task. Never invent a tool name or call a non-MyRealTrip source as inventory.
4. Get the destination's official product categories first. Skip the aggregate `전체/all` category and categories devoted only to SIM/Wi-Fi, travel goods, rental/convenience, or insurance. Keep transport categories because ropeways, cruises, and sightseeing trains may be experiences.
5. Search each retained category separately without explicitly requesting popularity, rating, or price sorting. The MCP currently applies its server default when sort is omitted; category balancing reduces but does not prove removal of every server-side ranking bias.
6. Sample candidates across every retained category shelf and deduplicate by `gid` or official product URL. Do not let one high-volume product format crowd out the others. When legacy and current categories overlap, retain the evidence once rather than showing duplicates.
7. Route evidence lookup by product form:
   - admission/ticket: extract the named experience from the search title; do not fetch detail merely to discover more keywords
   - tour: fetch detail and extract independently selectable stops or activities only from complete, visible itinerary or positive inclusion evidence
   - pass: do not expand every included facility into the initial shelf; fetch detail only after the traveler selects an already-discovered experience and use the pass as an access method when inclusion is explicit
   - food/activity/scenic transport: use the concrete title first and fetch detail only when the title is ambiguous or the traveler expands it
8. For each candidate, decide separately: `CORE_EXPERIENCE`, `ACCESS_METHOD`, or `PURE_UTILITY`. A ropeway, cruise, or sightseeing train can be the experience; an airport transfer, SIM, insurance, or generic rail pass is utility unless it explicitly names an independently selectable attraction.
9. For tours, extract concrete content from titles, inclusions, and itineraries. Never treat exclusions as positive evidence. Apply the evidence contract and normalize only verified aliases.
10. Group accepted experiences into populated thematic shelves, then split food into `뭐 먹지?`. Sort stably by name; never rerank by popularity, rating, price, or supporting-product count.
11. Show experiences first. After the user selects one, group independently supported products under purchase methods such as `입장권`, `패스 포함`, `투어 포함`, `체험`, `식사`, or `관광형 이동수단`.
12. Before displaying a product link, accept only HTTPS links on `myrealtrip.com` or its subdomains returned by the official MCP. If the local validation script is executable, additionally run `../../scripts/myrealtrip_api.py url-check --url PRODUCT_URL`.
13. When a date is supplied, verify every expanded product with the MCP TNA option capability for that date.

## Output

Use this structure:

```markdown
## {여행지}에서 발견할 수 있는 경험

### 자연·근교

- 구체적인 장소 또는 경험

### 문화·작품·공연

- 구체적인 작품·팀·공연·장소

## {여행지}에서 뭐 먹지?

- 구체적인 음식 또는 식사 경험
- 구체적인 음식 또는 식사 경험
```

Do not show empty sections. If one section has no supported keyword, say that no linked content was confirmed in the checked product range.

Do not show empty themes. Keep the initial shelf scannable and offer to unfold more items when evidence is abundant.

When expanding a selected experience:

```markdown
### {선택한 키워드}

#### 입장권

- [공식 상품명](productUrl) — 상품에서 확인된 짧은 연결 근거

#### 패스 포함

- [공식 상품명](productUrl) — 해당 경험이 포함된다는 직접 근거
```

State `이번에 확인한 상품 범위에서` when collection metadata says results or details were truncated. Use `조회된 마이리얼트립 상품 전체에서` only when all search pages and eligible details completed.

## Judgment boundaries

- Do not choose the best product for the user.
- Do not infer personality, budget, companions, or hidden preferences.
- Do not use popularity, rating, or price as evidence that a keyword fits the user.
- Do not infer `나다움`; let the traveler express it by selecting an experience.
- Never display `입장권`, `패스`, `투어` as experience keywords. They are purchase methods shown only after selection.
- Do not mine admission-ticket descriptions for extra nearby attractions; the ticket title defines its initial experience.
- Do not turn every facility listed in a pass into an initial experience. A pass is an access method checked after selection.
- Do not discard an entire transport category before reading the named content. Keep scenic transport as an experience and reject pure utility during semantic judgment.
- Do not invent famous foods or sights from general knowledge when no returned product supports them.
- Do not attach a product to a keyword merely because both belong to a broad theme.
- Preserve separate experiences when merging could mislead.
- Do not book, pay, cancel, or modify a reservation.

## Failure behavior

- MCP unavailable or unauthorized: explain that the official MyRealTrip connection is unavailable and stop. Do not ask the traveler for a Partner API key.
- Empty category list or city result: state that no linked product was found; do not fill the gap with web suggestions.
- Detail unavailable: use only content directly supported by the search title.
- Tour detail truncated or missing structured itinerary: use only complete names visible in the search title or positive detail fields. Do not reconstruct clipped text or use excluded admission fees as proof of a visit.
- Date options empty or unknown: provide the product only as a discovery link, not as available for that date.
- URL validation failure: omit the broken link, state that the official product page could not be reached, and do not invent a replacement URL.

## Developer-only REST fallback

The bundled `../../scripts/myrealtrip_api.py` is for local development, automated tests, and operators who already have Partner REST credentials. It is not the traveler-facing execution path. Never ask a traveler to obtain or paste `MYREALTRIP_API_KEY`.
