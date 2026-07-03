---
name: discover-new-trip
description: "Provide one MyRealTrip discovery assistant with three clearly separated uses: finding an unfamiliar international destination from a departure airport using official flight fare data, finding a different accommodation type when the user asks where to sleep, and finding unfamiliar tours or tickets that are actually bookable today or tomorrow. Use when a traveler wants destination inspiration from an airport, non-hotel lodging, or a same-day/next-day activity outside familiar hobbies."
---

# Discover New Trip

Use one conversation and one skill, but keep the three user paths visibly distinct.

## First response: show the guide

On the first skill response in a conversation, show this compact guide before asking questions or searching. Show it only once unless the user asks for help.

```markdown
## 이렇게 사용할 수 있어요

1. ✈️ **공항에서 어디로 갈까**
   출발 공항·여행 기간·익숙한 목적지를 말하면 항공권 데이터에서 새로운 해외 목적지를 찾아요.
   예: `인천공항에서 4일간 갈 새로운 곳을 찾아줘. 일본과 태국은 많이 가봤어.`

2. 🛏️ **어디서 잘까**
   여행지·날짜·익숙한 숙소 유형을 말하면 다른 형태의 숙소를 찾아요.
   예: `내일 도쿄에서 잘 건데 호텔에서만 자봤어.`

3. 🎟️ **오늘·내일 뭐 하지**
   현재 도시와 평소 취미를 말하면 해당 날짜에 예약 가능한 낯선 투어·티켓을 찾아요.
   예: `오늘 도쿄에서 뭐 하지? 나는 야구를 좋아해.`
```

## Route the request

- Airport, flight, destination inspiration, `어디로 갈까`: route to **공항에서 어디로 갈까**.
- Sleep, accommodation, hotel, hostel, ryokan: route to **어디서 잘까**.
- `오늘 뭐 하지`, `내일 뭐 하지`, tour, ticket, activity: route to **오늘·내일 뭐 하지**.

If the request is ambiguous, ask the user to choose with `공항에서 어디로 갈까 / 어디서 잘까 / 오늘·내일 뭐 하지`. Do not expose internal command or skill names.

## Shared rules

1. Read [references/search-and-exclusion-rules.md](references/search-and-exclusion-rules.md) for the selected path.
2. Use `../../scripts/myrealtrip_api.py`, resolved relative to this skill folder, for Partner REST calls.
3. Read `MYREALTRIP_API_KEY` only from the shell environment. Never request or display a real key.
4. Use the official `myrealtrip` MCP for live inventory, type verification, or booking links.
5. Remove only user-declared familiar choices. Never infer personality, hidden preferences, or travel history.
6. Treat `familiar` and `forbidden` differently: familiar choices may be excluded for novelty; forbidden, unsafe, inaccessible, or unwanted choices must never be recommended as a reversal.

## 1. 공항에서 어디로 갈까

Goal: use official MyRealTrip flight fare data to discover an unfamiliar international destination from the stated airport.

Required input:

- Departure airport
- Trip length from 3 to 7 days; use 4 days only when the user accepts the disclosed default
- Familiar destination cities or countries to exclude, if any

Procedure:

1. Resolve the departure airport with `airport-autocomplete` and use `airport.code`, never `city.code`.
2. Call `flight-bulk-lowest --departure AIRPORT_CODE --period DAYS`.
3. Treat this endpoint as international-only. Do not claim that it covers domestic destinations.
4. Preserve only returned facts: `toCity`, `departureDate`, `returnDate`, `totalPrice`, `averagePrice`, `airline`, and `transfer`.
5. Resolve each shortlisted `toCity` with `airport-autocomplete` so the user sees a human-readable city, country, and airport code. Reject unresolved codes.
6. Exclude only the familiar destinations stated by the user. A familiar country excludes its cities; a familiar city does not exclude the whole country.
7. Return up to three candidates with different countries when the returned data permits.
8. Label every candidate price **캘린더 최저가**. It is discovery data, not live inventory or a guaranteed checkout price.
9. After the user chooses one candidate, call `searchInternationalFlights` with the returned dates and exact airport codes. Show the live search price and official booking URL only if returned.

If `MYREALTRIP_API_KEY` is unavailable, explain that all-destination discovery cannot run. Do not invent a destination list or replace it with popularity-based suggestions. The MCP flight tools may verify a chosen route, but they do not replace the all-destination discovery call.

## 2. 어디서 잘까

Goal: answer where to sleep by excluding accommodation types the user already knows.

Required input:

- Destination
- Check-in and check-out; `tomorrow` without checkout means one night
- Familiar accommodation types to exclude
- Adult count only when not inferable; otherwise use one and disclose it

Procedure:

1. Resolve one exact `CITY` with `stay-regions --exact-city` and use its `regionId`.
2. Reject stations, airports, attractions, and similarly named regions.
3. Call REST `stay-search` for the exact region and dates.
4. Call MCP `searchStays` with the same conditions and allowed non-familiar `stayTypes`.
5. Verify actual accommodation type and location from MCP structured data. REST accommodation search does not expose type; a property name or star rating is not type evidence.
6. Prefer candidates whose MCP `gid` matches a REST `itemId`.
7. Reject candidates whose type matches an excluded familiar type.
8. Return up to three different verified types with date-specific price, tax status, rating, and official URL when returned.

Never claim a room is secured until the product page confirms room inventory and final checkout price.

## 3. 오늘·내일 뭐 하지

Goal: recommend an unfamiliar tour, activity, or admission ticket that is actually bookable on today or tomorrow.

Required input:

- Current city
- Selected date: today or tomorrow
- Usual hobbies or familiar activities to exclude

Procedure:

1. Resolve relative dates to an explicit `YYYY-MM-DD` date.
2. Call REST `tna-categories` and use returned values only.
3. Call `tna-search --keyword CITY --city CITY --page 1 --size 100`.
4. Reject missing/mismatched city evidence and titles explicitly naming another city.
5. Keep tours, participatory activities, and admission tickets. Remove transport-only products, SIMs, travel goods, and generic utilities.
6. Label each candidate:
   - `OVERLAP`: the hobby appears directly or the central experience is a direct instance of it.
   - `NON_OVERLAP`: the central experience clearly differs.
   - `UNCLEAR`: evidence is insufficient; do not remove it as overlap.
7. Remove only `OVERLAP` candidates.
8. Call `tna-detail` for promising `gid` values.
9. Call `tna-options --gid GID --date YYYY-MM-DD` or MCP `getTnaOptions` for every final candidate.
10. Keep only candidates with an affirmative option result for the selected date. An empty option list, restricted automatic lookup, unknown result, or starting price alone is not proof of bookability.
11. Return up to three different experience types with the selected date, available option, verified price, and official product URL.

Examples of direct overlap: baseball → baseball game or stadium tour; DJ/clubbing → nightclub crawl; hiking → mountain hiking tour. Do not broaden these into lifestyle stereotypes.

If the Partner key is unavailable, use `getCategoryList`, `searchTnas`, `getTnaDetail`, and `getTnaOptions` through MCP. Reject visible city conflicts and still require affirmative date availability.

## Output

Use exactly one heading matching the routed path:

- `## 공항에서 어디로 갈까`
- `## 어디서 잘까`
- `## 오늘·내일 뭐 하지`

Before recommendations, show:

- Verified origin or destination
- Explicit date or trip duration
- Familiar choice being excluded

For each result show only returned facts, the exclusion contrast, and the official link. Clearly distinguish calendar estimates, starting prices, and date-specific bookable prices.

## Failure and safety

- Never invent products, tickets, prices, ratings, times, airport codes, regions, availability, or URLs.
- If the official interface cannot prove the user's condition, state the missing capability and stop.
- Do not silently relax trip duration, date availability, region match, or familiarity exclusion.
- Do not book, pay, cancel, or modify reservations.
- Require product-page confirmation for final price, inventory, room, eligibility, and accessibility.
