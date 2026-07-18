# Official Tourism Source Candidates

Generated context: sources found for the T&A Supply Gap Map after removing manual seed anchors from primary analysis.

## Primary rule

Primary supply-gap scoring should use official or public datasets that enumerate tourism places, facilities, cultural assets, events, or certified food/partner locations. Manual/DMO seed lists are kept only as candidate/demo material and must not be mixed into the primary official anchor file.

## Candidate status by city

| City | Source | Status | Use in primary anchors? | Notes |
|---|---|---|---|---|
| Osaka | Osaka City Map Navi open data: culture/tourism, famous/historic sites, parks/sports | Candidate; direct CSV endpoints timed out in this environment | Not yet | Official Osaka page confirms CC-BY Map Navi CSV categories. Need slower retry/manual download. |
| Tokyo | Tokyo Metropolitan tourist number survey CSV | Downloaded | No | Downloaded file is aggregate visitor-count rows, not place-level attraction list. Keep as demand/context signal only. |
| Kyoto | Kyoto Prefecture tourism facility list via BODIK/CKAN | Candidate; CKAN API returned 403 in this environment | Not yet | Source page describes official Kyoto tourism facility CSV/XLSX/RDF. Need manual resource URL or browser download. |
| Seoul | Seoul-wide official tourist spot/open data | Need source | Not yet | District-only data such as Mapo-gu tourist boundary should be scoped separately, not mixed into Seoul-wide analysis. |
| Busan | Busan film/culture/tourism LOD | Candidate; parser needed | Not yet | TTL/LOD source may contain tourism places, restaurants, lodging, shopping, sports. Needs RDF parsing and place filtering. |
| Yeosu | Yeosu tourism information on data.go.kr | Candidate; portal/API handling needed | Not yet | Public Data Portal record indicates tourism facility/location information. Need download/API handling. |
| Daejeon | Daejeon major tourist spot visitor status | Candidate; portal/API handling needed | Not yet | Good demand-signal candidate; may be annual and old, so separate from facility master unless names can be extracted reliably. |
| Hiroshima | Hiroshima open data: tourism facilities | Downloaded and accepted | Yes | Current clean primary analysis source. |
| Fukuoka | Fukuoka yatai official dataset | Previously available locally; current direct retry got 403 | Partner candidate only | Food/yatai data is retained separately and excluded from first-pass tourism-facility scoring. |

## Immediate next actions

1. Retry Osaka Map Navi with longer timeout or browser/manual download.
2. Resolve Kyoto BODIK resource download URL without relying on CKAN API search.
3. Add a Busan TTL parser only after confirming the LOD download path.
4. Keep Seoul/Yeosu/Daejeon out of primary scoring until city-wide official facility datasets are downloaded or API keys are configured.
