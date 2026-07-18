# MCP Detail Verification Notes

Generated context: manual MCP `getTnaDetail` check for the three currently matched products.

## Conclusion

The current first-pass official-to-MCP matches should be treated as **title/card-level matches**, not fully itinerary-verified matches.

MCP detail checks are useful, but the returned detail payload can be truncated or can expose only inclusion/exclusion/use-guide fields. Therefore, a product should be upgraded to `detail_confirmed` only when the positive itinerary/content area clearly names the official asset.

## Category policy

The matching standard differs by product type:

- The analysis unit is always a place/place-cluster anchor, not the sales format. For example, `포장마차 투어` is interpreted against the place cluster `福岡市 屋台`, not as a separate "tour" anchor.
- Ticket/admission products: the product itself is the right to use the named facility, so a title/product-name match is strong evidence.
- Tour products: a title/card match is only a candidate. The asset should be confirmed through positive itinerary/detail/inclusion text showing where the tour actually goes.
- Exclusion text: never use an asset mentioned only in exclusions as positive visit evidence.

## Checked products

| Product ID | Official asset | Current match basis | Detail check result | Evidence level |
|---|---|---|---|---|
| 3885344 | 후쿠오카 야타이 / 福岡市 屋台 | Product title/card says food-stall tour through `포장마차` | Detail mentions food-stall meal budget in the exclusion section and place is coordinated after booking. This supports the broad yatai/food-stall context, but not individual stall coverage. | `title_plus_context` |
| 4192026 | 広島城 / 히로시마성 | Product title says `히로시마성` | Detail payload exposes `히로시마 성` mainly in the excluded entrance-fee text. Because exclusion text is not positive itinerary evidence, keep as title-level match. | `title_only` |
| 5905368 | 広島平和記念資料館 / 히로시마 평화기념자료관 | Product title says `평화기념관` | Detail payload is partially truncated and visible fields emphasize inclusions/use guide. It does not clearly expose the positive itinerary text for the peace memorial asset. Keep as title-level match. | `title_only` |

## Rule update needed

Future scoring should separate:

- `title_only`: matched from product title/card only
- `title_plus_context`: detail supports the broader context but not exact itinerary coverage
- `detail_confirmed`: positive detail/itinerary/including text directly names the asset
- `exclusion_only`: asset appears only in exclusion text and must not be used as positive confirmation
- `detail_unavailable`: MCP detail failed, was truncated, or did not expose enough text

## Safe interpretation

The three current matches are valid as **candidate productization links**, but only the title/card layer is currently reliable enough for automated scoring.

For a stronger BD-grade report, the next step is to add detail-evidence fields to the matching output and avoid upgrading any match based only on exclusion text.
