# Content indexing rules

Use these rules after collecting MyRealTrip TNA search and detail responses.

## 1. Evidence contract

Every displayed keyword must retain:

- normalized keyword
- `DO` or `EAT`
- relation: `DIRECT` or `ALIAS`
- product `gid`
- exact source field
- short source excerpt
- official `productUrl`
- purchase form, kept separate from the experience label

Reject `UNSUPPORTED` relations.

## 2. Source priority

Use evidence in this order:

1. `title` or search `itemName`
2. `itineraries[].title`
3. `included`
4. detail `description`
5. `itineraries[].description`

Treat search `description` such as `오사카 ∙ 투어` as location/category metadata, not content evidence.

## 3. Separate content from purchase form

Classify two independent axes:

- experience: the named thing the traveler may want to do, see, or eat
- purchase form: admission, pass, tour, activity, food product, scenic transport, transport, or other

`고베 누노비키 허브원` is an experience. `입장권`, `로프웨이 결합권`, `패스 포함`, and `투어 포함` are ways to access it. Never merge the second axis into the first.

Use these semantic roles:

- `CORE_EXPERIENCE`: independently selectable content
- `ACCESS_METHOD`: a product that directly grants or includes access to that content
- `PURE_UTILITY`: logistics without independently selectable experience evidence

Do not globally reject transport. A ropeway, cruise, sightseeing train, sky capsule, or beach train can be `CORE_EXPERIENCE`; airport transfer, SIM, insurance, rental car, and generic point-to-point transport are normally `PURE_UTILITY`.

## 4. DO keywords

Prefer concrete nouns or noun-action pairs that can become a reason to travel:

- franchise, work, or character: `해리포터`, `슈퍼 닌텐도 월드`
- team or named performance: `아스널`, `위키드`
- named place or facility: `스톤헨지`, `감천문화마을`
- specific activity with a visible scene: `광안대교 야경 요트`, `한복 스냅 촬영`

Keep a broader place only when it is independently selectable. For a product containing `도톤보리 오코노미야키 식사`, index `도톤보리` as DO and `오코노미야키` as EAT.

## 5. EAT keywords

Prefer concrete food, drink, restaurant experience, or food-making activity:

- dish: `오코노미야키`, `충칭 훠궈`
- drink: `사케 시음`, `삿포로 맥주`
- named food venue when it is the experience: `쿠로몬시장 해산물`
- making or tasting: `스시 만들기`, `와이너리 시음`

Prioritize products where food is purchased, reserved, included, tasted, or made. If food appears only as optional nearby advice, do not link it as a bookable food experience.

## 6. Reject low-information terms

Reject:

- generic concepts: 관광, 체험, 여행, 명소, 음식, 액티비티
- sales language: 추천, 인기, 특가, 필수, 프리미엄, 베스트
- product format: 일일투어, 단독투어, 입장권, 패키지, 자유시간
- logistics: 픽업, 샌딩, 이동, 와이파이, 유심, 보험
- unsupported inference: an anime-related product does not prove `나루토`

## 7. Normalize without over-merging

Normalize punctuation, repeated whitespace, and verified aliases.

Safe alias examples:

- `USJ` → `유니버설 스튜디오 재팬`
- `슈퍼마리오 월드` only when source clearly means `슈퍼 닌텐도 월드`
- `아스날` → `아스널`

Do not merge neighboring but distinct experiences:

- `해운대 해변열차` and `스카이캡슐`
- `오코노미야키` and `모던야키`
- `아스널 경기 관람` and `아스널 스타디움 투어`

When uncertain, keep separate labels or reject the alias.

## 8. Thematic shelves and grouping

Group products under a keyword only when every product independently supports it. Do not transfer evidence from one product to another.

Group experiences under populated themes such as `테마파크·작품`, `스포츠·공연`, `문화·역사`, `자연·근교`, `만들기·체험`, and `먹거리`. Themes organize discovery; they are not user preference predictions.

Use a stable display order such as Korean alphabetical order. Do not order by sales, popularity, rating, price, or number of supporting products. Category-balanced collection is a coverage method, not a ranking signal.

Do not label the first item as best or recommended.

## 9. Geographic rules

- Require exact city evidence from structured search metadata.
- A city product may include a named nearby destination; keep that keyword when the itinerary explicitly includes it.
- Expand a region to cities only after disclosing the mapping, such as `연해주 → 블라디보스토크·우수리스크`.
- Reject products whose primary city conflicts with the requested city.

## 10. Availability language

- With no date: say the product is listed by MyRealTrip and require page confirmation.
- With a date and non-empty options: say options were returned for that date.
- Empty or failed option lookup: do not call it bookable for that date.
- Never turn a search starting price into a date-specific checkout price.

## 11. Product URL safety

- Accept HTTPS URLs only.
- Accept `myrealtrip.com` and its subdomains only.
- Reject credentials, custom ports, missing product paths, and non-MyRealTrip redirects.
- Check only links about to be displayed, not every collected URL.
- Treat HTTP 2xx and 3xx ending on an official MyRealTrip domain as reachable.
- Omit a failed link and report the failure; never synthesize a replacement URL.

## 12. Coverage language

- Every returned category and all its pages/details completed: `조회된 마이리얼트립 상품 전체에서`
- Any category page or detail limit reached: `이번에 카테고리별로 확인한 상품 범위에서`
- API unavailable: stop; do not replace official inventory with general web knowledge.
