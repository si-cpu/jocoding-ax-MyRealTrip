# Official Tourism Source Candidates

Generated context: sources found for the T&A Supply Gap Map after removing manual seed anchors from primary analysis.

## Primary rule

Primary supply-gap scoring should use official or public datasets that enumerate tourism places, facilities, cultural assets, events, or certified food/partner locations. Manual/DMO seed lists are kept only as candidate/demo material and must not be mixed into the primary official anchor file.

## Candidate status by city

| City | Source | Status | Use in primary anchors? | Notes |
|---|---|---|---|---|
| Osaka | Osaka City Map Navi open data: culture/tourism, famous/historic sites, parks/sports | Official source page and CSV link IDs confirmed; direct CSV endpoints timed out in this environment | Not yet | Official Osaka page confirms CC-BY Map Navi CSV categories: culture/tourism, famous/historic sites, parks/sports. Need browser/manual download or off-network retry. |
| Tokyo | Tokyo Metropolitan tourist number survey CSV | Downloaded | No | Downloaded file is aggregate visitor-count rows, not place-level attraction list. Keep as demand/context signal only. |
| Kyoto | Kyoto Prefecture tourism facility list via BODIK/CKAN | Downloaded via user-provided official CSV attachment after shell 403 | Yes, Kyoto city rows only | CSV URL identified: `https://data.bodik.jp/dataset/6ad07527-e6ad-4528-b1ad-00e8b5bd1b38/resource/7f63e283-49c4-4737-a838-ccea5cdbc205/download/260002kankoushisetsu.csv`. Primary anchors keep municipality names starting with `京都市`; lodging/restaurant/parking-like rows are excluded from primary tourism-place scoring. |
| Seoul | Seoul-wide official tourist spot/open data | Need source | Not yet | District-only data such as Mapo-gu tourist boundary should be scoped separately, not mixed into Seoul-wide analysis. |
| Busan | Busan film/culture/tourism LOD | Candidate; parser needed | Not yet | TTL/LOD source may contain tourism places, restaurants, lodging, shopping, sports. Needs RDF parsing and place filtering. |
| Yeosu | Yeosu tourism information on data.go.kr | Candidate; portal/API handling needed | Not yet | Public Data Portal record indicates tourism facility/location information. Need download/API handling. |
| Daejeon | Daejeon major tourist spot visitor status | Candidate; portal/API handling needed | Not yet | Good demand-signal candidate; may be annual and old, so separate from facility master unless names can be extracted reliably. |
| Hiroshima | Hiroshima open data: tourism facilities | Downloaded and accepted | Yes | Current clean primary analysis source. |
| Fukuoka | Fukuoka yatai official dataset | Previously available locally; current direct retry got 403 | Partner candidate only | Food/yatai data is retained separately and excluded from first-pass tourism-facility scoring. |

## Immediate next actions

1. Download Osaka Map Navi CSVs through browser/manual download or alternate network.
2. Continue improving Kyoto Japanese-to-Korean alias coverage for official-place matching.
3. Add a Busan TTL parser only after confirming the LOD download path.
4. Keep Seoul/Yeosu/Daejeon out of primary scoring until city-wide official facility datasets are downloaded or API keys are configured.
