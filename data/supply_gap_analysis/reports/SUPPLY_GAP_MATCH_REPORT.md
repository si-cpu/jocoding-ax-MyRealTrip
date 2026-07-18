# Supply Gap Match Report

- Generated at: 2026-07-18T15:37:45+09:00
- Official anchors: 228
- Primary tourism-asset anchors: 88
- Partner-candidate anchors excluded from primary scoring: 108
- MCP products: 103
- Auto alias anchors used: 88
- Auto aliases used: 105
- Direct matches: 9
- Matched anchors: 8
- Classification counts: {'상품화 부족 자산': 32, '부분 상품화 자산': 8, 'MCP 미수집 자산': 48}

## By city

| City | Classification counts |
|---|---|
| jp-hiroshima | {'상품화 부족 자산': 30, '부분 상품화 자산': 2} |
| jp-kyoto | {'MCP 미수집 자산': 8} |
| jp-osaka | {'부분 상품화 자산': 6, '상품화 부족 자산': 2} |
| jp-tokyo | {'MCP 미수집 자산': 8} |
| kr-busan | {'MCP 미수집 자산': 8} |
| kr-daejeon | {'MCP 미수집 자산': 8} |
| kr-seoul | {'MCP 미수집 자산': 8} |
| kr-yeosu | {'MCP 미수집 자산': 8} |

## Important interpretation

- `상품화 부족 자산` means no direct MCP product match in the collected sample, not proof of zero market demand.
- `MCP 미수집 자산` means official/seed anchors exist but the city has no collected MCP products yet, often due to collection rate limits.
- MCP collection was rate-limited for several non-tour categories, so the current match is a first-pass sample.
- Generic Fukuoka yatai aliases such as `야타이` and `포장마차` apply only to the aggregate `후쿠오카 야타이` anchor.
- Individual yatai stalls are kept as partner candidates and excluded from primary tourism-asset gap scoring to avoid restaurant-level overcounting.
