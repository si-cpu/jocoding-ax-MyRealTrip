# BD Decision Brief — T&A Supply Gap Map

## One-line answer

Yes. When this project is complete, a business-development user should be able to see which official tourism assets are heavily productized, lightly productized, or under-connected on MyRealTrip.

The current first-pass result already demonstrates that logic, but it should be treated as a sample because MCP collection was rate-limited.

## What the user can understand

| Question | What the tool shows | Current first-pass example |
|---|---|---|
| 어떤 관광 자산이 상품화되어 있나? | official anchor matched to MCP products | `후쿠오카 야타이`, `広島城`, `広島平和記念資料館` |
| 어떤 자산이 덜 조명됐나? | official anchor exists, but direct MCP product match is missing | individual Fukuoka yatai stalls, many Hiroshima official places/events |
| 어디에 상품 공급이 집중됐나? | product count per official anchor/category/city | current sample has three confirmed partial matches |
| 어디를 더 봐야 하나? | high official strength + low MCP supply strength | official yatai inventory, Hiroshima facilities/events with no direct match |
| 신규 상품/파트너 후보는? | supply-gap candidates requiring manual validation | individual stalls, facilities, and events with no direct match |

## Current interpretation

The first-pass result should be read as:

> “일부 공식 관광 자산은 마이리얼트립 상품과 연결되며, 많은 공식 자산은 현재 수집된 상품 샘플에서 직접 연결이 약하거나 없다.”

It should **not** be read as:

> “관광객이 적다” or “수요가 없다”.

This distinction matters because the tool is designed for T&A business development, not public tourism demand forecasting.

## Current strongest signal

Fukuoka has an official yatai inventory with 107 individual stalls.

The collected MCP sample contains a product that clearly sells the broader food-stall/yatai experience:

- `후쿠오카 여행의 필수 코스!! 포장마차 맛집 투어`

Therefore:

- `후쿠오카 야타이` as a city-level experience is partially productized.
- Individual yatai stalls are not automatically counted as productized.
- This creates a useful BD question: should MyRealTrip expose yatai as a broader city experience, a curated stall route, or partner-specific products?

## Hiroshima signal

Hiroshima official anchors were built from tourism facilities and events.

After rerunning Hiroshima tour collection, two official facilities matched MCP products:

- `広島城` matched to a Hiroshima day-tour product mentioning `히로시마성`
- `広島平和記念資料館` matched to a Hiroshima/Miyajima product mentioning `평화기념관`

This shows that the matching layer works when official local names and Korean product wording are normalized.

The correct follow-up is:

1. rerun MCP collection after cooldown,
2. collect fewer categories per run,
3. check tour detail text for itinerary-level mentions,
4. then recalculate the supply gap.

## Portfolio positioning

This project is stronger as a business-development analysis tool than as a traveler recommendation app.

It demonstrates the work pattern expected in T&A business development:

- collect fragmented market/product data,
- normalize it into comparable units,
- avoid overclaiming from incomplete data,
- find supply gaps,
- and turn the result into partner/content/promotion hypotheses.
