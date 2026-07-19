# Supply Gap Match Report

- Generated at: 2026-07-19T19:58:05+09:00
- Official anchors: 541
- Primary tourism-asset anchors: 401
- Partner-candidate anchors excluded from primary scoring: 108
- MCP products: 283
- Auto alias anchors used: 37
- Auto aliases used: 53
- Direct matches: 63
- Matched anchors: 22
- Classification counts: {'MCP 추가 수집 필요': 379, '검증된 대표 경험': 6, '부분 상품화 자산': 8, '연결 후보(투어 상세 확인 필요)': 8}

## By city

| City | Classification counts |
|---|---|
| jp-fukuoka | {'MCP 추가 수집 필요': 71, '검증된 대표 경험': 5, '부분 상품화 자산': 5} |
| jp-hiroshima | {'부분 상품화 자산': 3, 'MCP 추가 수집 필요': 24, '검증된 대표 경험': 1} |
| jp-kyoto | {'연결 후보(투어 상세 확인 필요)': 8, 'MCP 추가 수집 필요': 284} |

## City-level coverage

| City | Official scope | Official assets | MCP products | Confirmed | Detail pending | Confirmed match rate | Observed link rate | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 후쿠오카 | 후쿠오카시 공식 한국어 관광가이드(비관광·시외 필터 후) | 81 | 180 | 10 | 0 | 12.3% | 12.3% | 잠정치(MCP 일부 오류) |
| 히로시마 | 공식 관광시설(비관광 시설 필터 후) | 28 | 20 | 4 | 0 | 14.3% | 14.3% | 잠정치(MCP 일부 오류) |
| 교토 | 공식 관광시설(비관광 시설 필터 후) | 292 | 49 | 0 | 8 | 0.0% | 2.7% | 잠정치(MCP 일부 오류) |

- Confirmed match rate uses only ticket/product-card evidence or positive tour-detail evidence.
- Observed link rate additionally includes tour-title matches still waiting for itinerary/inclusion confirmation.
- Rates marked provisional must not be presented as final coverage until city collection errors are cleared.

## Important interpretation

- Every Kyoto primary asset is matched with a Korean translated name generated from its official kana reading; curated standard translations are marked separately from automatic transliterations.
- `매칭 보류(한국어 번역 부족)` is not a supply gap. Japanese-to-Korean translation must be completed first.
- `연결 후보(투어 상세 확인 필요)` is title-level evidence only; itinerary/inclusion detail must confirm an actual visit.
- `수집 표본 내 미연결 후보` means a Korean translated name had no direct match after a complete MCP collection. It is still not proof of zero market demand.
- `MCP 추가 수집 필요` means the Korean translated name is ready, but category/page errors prevent a supply-gap conclusion.
- Multi-city manual/DMO seed candidates are excluded from this primary scoring file to avoid contaminating official-data analysis.
- MCP collection was rate-limited for several non-tour categories, so the current match is a first-pass sample.
- Generic Fukuoka yatai aliases such as `야타이` and `포장마차` apply only to the aggregate `후쿠오카 야타이` anchor.
- Individual yatai stalls are kept as partner candidates and excluded from primary tourism-asset gap scoring to avoid restaurant-level overcounting.
