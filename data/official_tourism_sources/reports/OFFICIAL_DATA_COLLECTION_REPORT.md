# Official Tourism Data Collection Report

- Generated at: 2026-07-18T11:46:39+0900
- Successful downloads: 5
- Failed/manual items: 18

## Successful downloads

| City | Dataset | Rows | File | Source |
|---|---|---:|---|---|
| Japan | Digital Agency prefecture open-data list | 47 | `data/official_tourism_sources/raw/digital_agency_pref_open_data_list.csv` | https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/2b1128e2-c699-4aa0-9206-37169a6697c8/7192f365/20260228_resources_opendata_lg_pref_list_02.csv |
| Japan | Digital Agency municipality open-data list | 1558 | `data/official_tourism_sources/raw/digital_agency_municipality_open_data_list.csv` | https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/2b1128e2-c699-4aa0-9206-37169a6697c8/821f1348/20260228_resources_opendata_lg_mani_list_03.csv |
| Hiroshima | Hiroshima open data: tourism facilities | 33 | `data/official_tourism_sources/raw/hiroshima_tourism_facilities.csv` | https://hiroshima-opendata.dataeye.jp/resource_download/9858 |
| Hiroshima | Hiroshima open data: events | 32 | `data/official_tourism_sources/raw/hiroshima_events.csv` | https://hiroshima-opendata.dataeye.jp/resource_download/9846 |
| Hiroshima | Hiroshima open data: public Wi-Fi access points | 451 | `data/official_tourism_sources/raw/hiroshima_public_wifi.csv` | https://hiroshima-opendata.dataeye.jp/resource_download/9855 |

## Failed or manual lookup needed

| City | Dataset/Need | Status | Reason | URL |
|---|---|---|---|---|
| Fukuoka | FAILED CKAN search: 屋台 | catalog_failed | Fukuoka city BODIK/CKAN catalog. Error: HTTP Error 404: Not Found | https://odcs.bodik.jp/401307/api/3/action/package_search?q=%E5%B1%8B%E5%8F%B0 |
| Fukuoka | FAILED CKAN search: 観光 | catalog_failed | Fukuoka city BODIK/CKAN catalog. Error: HTTP Error 404: Not Found | https://odcs.bodik.jp/401307/api/3/action/package_search?q=%E8%A6%B3%E5%85%89 |
| Fukuoka | FAILED CKAN search: 文化財 | catalog_failed | Fukuoka city BODIK/CKAN catalog. Error: HTTP Error 404: Not Found | https://odcs.bodik.jp/401307/api/3/action/package_search?q=%E6%96%87%E5%8C%96%E8%B2%A1 |
| Fukuoka | FAILED CKAN search: イベント | catalog_failed | Fukuoka city BODIK/CKAN catalog. Error: HTTP Error 404: Not Found | https://odcs.bodik.jp/401307/api/3/action/package_search?q=%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88 |
| Fukuoka | FAILED CKAN search: 地域の魅力 | catalog_failed | Fukuoka city BODIK/CKAN catalog. Error: HTTP Error 404: Not Found | https://odcs.bodik.jp/401307/api/3/action/package_search?q=%E5%9C%B0%E5%9F%9F%E3%81%AE%E9%AD%85%E5%8A%9B |
| Hiroshima | FAILED CKAN search: 観光施設 | catalog_failed | Candidate Hiroshima open-data CKAN endpoint. Error: <urlopen error [Errno 8] nodename nor servname provided, or not known> | https://hiroshima-city.dataeye.jp/api/3/action/package_search?q=%E8%A6%B3%E5%85%89%E6%96%BD%E8%A8%AD |
| Hiroshima | FAILED CKAN search: イベント | catalog_failed | Candidate Hiroshima open-data CKAN endpoint. Error: <urlopen error [Errno 8] nodename nor servname provided, or not known> | https://hiroshima-city.dataeye.jp/api/3/action/package_search?q=%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88 |
| Hiroshima | FAILED CKAN search: 文化財 | catalog_failed | Candidate Hiroshima open-data CKAN endpoint. Error: <urlopen error [Errno 8] nodename nor servname provided, or not known> | https://hiroshima-city.dataeye.jp/api/3/action/package_search?q=%E6%96%87%E5%8C%96%E8%B2%A1 |
| Hiroshima | FAILED CKAN search: 観光 | catalog_failed | Candidate Hiroshima open-data CKAN endpoint. Error: <urlopen error [Errno 8] nodename nor servname provided, or not known> | https://hiroshima-city.dataeye.jp/api/3/action/package_search?q=%E8%A6%B3%E5%85%89 |
| Hiroshima | FAILED CKAN search: 観光施設 | catalog_failed | Fallback if official site exposes CKAN-compatible endpoint. Error: HTTP Error 404: Not Found | https://www.city.hiroshima.lg.jp/api/3/action/package_search?q=%E8%A6%B3%E5%85%89%E6%96%BD%E8%A8%AD |
| Hiroshima | FAILED CKAN search: イベント | catalog_failed | Fallback if official site exposes CKAN-compatible endpoint. Error: HTTP Error 404: Not Found | https://www.city.hiroshima.lg.jp/api/3/action/package_search?q=%E3%82%A4%E3%83%99%E3%83%B3%E3%83%88 |
| Hiroshima | FAILED CKAN search: 文化財 | catalog_failed | Fallback if official site exposes CKAN-compatible endpoint. Error: HTTP Error 404: Not Found | https://www.city.hiroshima.lg.jp/api/3/action/package_search?q=%E6%96%87%E5%8C%96%E8%B2%A1 |
| Hiroshima | FAILED CKAN search: 観光 | catalog_failed | Fallback if official site exposes CKAN-compatible endpoint. Error: HTTP Error 404: Not Found | https://www.city.hiroshima.lg.jp/api/3/action/package_search?q=%E8%A6%B3%E5%85%89 |
| Osaka | Map Navi Osaka facility points: culture/tourism | download_failed | <urlopen error timed out> | https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1005.csv |
| Osaka | Map Navi Osaka facility points: famous/historic sites | download_failed | <urlopen error timed out> | https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1008.csv |
| Osaka | Map Navi Osaka facility points: parks/sports | download_failed | <urlopen error timed out> | https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1003.csv |
| Nara | Find Nara prefecture/city official open-data resources for tourist facilities, events, cultural properties. | manual_lookup_needed | No verified direct resource URL yet. |  |
| Beppu/Yufuin | Find Oita/Beppu/Yufu official open-data resources for onsen, tourist facilities, events. | manual_lookup_needed | No verified direct resource URL yet. |  |
