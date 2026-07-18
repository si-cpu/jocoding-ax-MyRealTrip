# T&A Supply Gap Map — First-pass insights

Generated basis: official tourism/public datasets + collected MyRealTrip MCP T&A product sample.

## What this tool can tell

This project does **not** claim real traveler popularity or total market demand.

It shows the gap between:

1. tourism assets that are officially listed by a city or tourism-related public source, and
2. assets that are visibly productized in the collected MyRealTrip T&A product sample.

In business-development terms, the output helps answer:

- Which official tourism assets already have visible MyRealTrip product supply?
- Which assets are repeatedly productized and can be treated as stable representative experiences?
- Which official assets have little or no direct product connection in the current sample?
- Which cities/categories need more source collection, partner discovery, or manual validation?

## First-pass data status

| Area | Current status |
|---|---|
| Official anchors | 172 official experience anchors |
| Fukuoka official anchors | 108 anchors: 1 aggregate yatai category + 107 individual yatai stalls |
| Hiroshima official anchors | 64 anchors: 32 tourism facilities + 32 event anchors |
| MCP product sample | 63 collected products |
| MCP collection limitation | Several categories were rate-limited, so this is still a first-pass sample |
| Direct official-to-MCP matches | 3 matched anchors |

## Current observed match

The current direct matches are:

- `후쿠오카 야타이` matched to `후쿠오카 여행의 필수 코스!! 포장마차 맛집 투어`
- `広島城` matched to `히로시마 일일관광 - 미야지마, 평화공원, 원폭돔, 히로시마성`
- `広島平和記念資料館` matched to `[히로시마] 평화기념관 + 미야지마 이쓰쿠시마 신사 :: 유네스코 등재지 1일 투어`

These are classified as `부분 상품화 자산`, because each has at least one collected MCP product clearly connected to the official asset.

## Important matching rule

Fukuoka yatai data has two levels:

1. `후쿠오카 야타이` as an aggregate city experience category
2. individual stall names from the official yatai inventory

Generic words such as `야타이`, `yatai`, and `포장마차` are allowed to match only the aggregate category.

Individual stalls require a direct stall-name match. This prevents a single generic food-stall tour from being incorrectly counted as covering all 107 official stalls.

## How to interpret the current gap

`상품화 부족 자산` means:

> no direct MyRealTrip product match was found in the collected sample.

It does **not** mean:

- the asset has no visitors,
- the asset has no commercial value,
- MyRealTrip has no related product at all,
- or the asset should automatically become a new product.

It means the asset is a candidate for one of the following BD follow-up actions:

- collect more MCP categories after rate-limit cooldown,
- inspect similar Korean/English/Japanese aliases,
- manually validate whether the asset appears inside tour itineraries,
- check whether a partner already covers it under a different wording,
- or consider it as a new product/partner/promotion discovery candidate.

## Current improvement discovered

The first Hiroshima rerun showed that direct matching needs official-name aliases.

For example:

- official `広島城` should match Korean product wording `히로시마성`
- official `広島平和記念資料館` should match Korean product wording `평화기념관`

This alias layer is not arbitrary recommendation logic. It is a normalization layer that connects official local names to Korean product wording.

## Portfolio message

The project turns fragmented product listings and public tourism data into a supply-gap map for T&A business development.

Instead of recommending a few products to travelers, it helps a business-development manager see where product supply is concentrated, where official tourism assets are under-connected, and where new partner or content opportunities may exist.
