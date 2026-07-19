# Official Tourism Data Filter Report

- Generated at: 2026-07-19T19:58:01+09:00
- CSV files inspected: 38
- Bucket counts: {'rejected_or_later_city': 8, 'needs_review': 20, 'accepted': 7, 'reference': 2, 'secondary': 1}
- Accepted rows: 1264
- Secondary rows: 451
- Reference rows: 1605

## Filtered files

| Bucket | Rows | Source file | Processed file | Reason |
|---|---:|---|---|---|
| rejected_or_later_city | 348 | `data/official_tourism_sources/raw/Fukuoka___202142_cultural_property_68455c08-55a8-49dc-98fc-e49456c181a9.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___202142_cultural_property_68455c08-55a8-49dc-98fc-e49456c181a9.csv` | Detected non-Fukuoka municipality codes: {'202142': 348} |
| rejected_or_later_city | 94 | `data/official_tourism_sources/raw/Fukuoka___202142_cultural_property_80490abf-d237-4ef9-9d04-d4e7295a7dce.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___202142_cultural_property_80490abf-d237-4ef9-9d04-d4e7295a7dce.csv` | Detected non-Fukuoka municipality codes: {'202142': 94} |
| needs_review | 26 | `data/official_tourism_sources/raw/Fukuoka___252115_kanko_e1154b0d-e04c-4e6f-bcb6-e27b5f1989b3.csv` | `` | No city code/name columns detected |
| rejected_or_later_city | 73 | `data/official_tourism_sources/raw/Fukuoka___272078_bunkazai_90757c55-2a97-449e-8474-0355240a8d9e.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___272078_bunkazai_90757c55-2a97-449e-8474-0355240a8d9e.csv` | Detected non-Fukuoka municipality codes: {'272078': 72} |
| rejected_or_later_city | 1 | `data/official_tourism_sources/raw/Fukuoka___272272_31_1b2eb864-e175-453a-abb2-ee33781ac478.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___272272_31_1b2eb864-e175-453a-abb2-ee33781ac478.csv` | Detected non-Fukuoka municipality codes: {'272272': 1} |
| rejected_or_later_city | 33 | `data/official_tourism_sources/raw/Fukuoka___273619_cultural_property_46c051e6-51e3-4764-a31e-8ad5c5b6aaa5.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___273619_cultural_property_46c051e6-51e3-4764-a31e-8ad5c5b6aaa5.csv` | Detected non-Fukuoka municipality codes: {'273619': 17} |
| needs_review | 51 | `data/official_tourism_sources/raw/Fukuoka___282090_event_2faf1a0e-5000-4a46-8b51-0ae68a949895.csv` | `` | No city code/name columns detected |
| needs_review | 30 | `data/official_tourism_sources/raw/Fukuoka___282090_event_45629aa2-cf2d-4a9e-946f-360879a1cf1b.csv` | `` | No city code/name columns detected |
| needs_review | 64 | `data/official_tourism_sources/raw/Fukuoka___282090_event_48c20df5-ba68-445f-a0e4-26a8fe8b55b7.csv` | `` | No city code/name columns detected |
| needs_review | 49 | `data/official_tourism_sources/raw/Fukuoka___282090_event_73d1bc23-53f9-41e7-bb9a-0721da1851ae.csv` | `` | No city code/name columns detected |
| needs_review | 37 | `data/official_tourism_sources/raw/Fukuoka___282090_event_77307107-9cd9-4b42-b294-063f039ca4e4.csv` | `` | No city code/name columns detected |
| needs_review | 14 | `data/official_tourism_sources/raw/Fukuoka___282090_event_8052ca85-591e-4eaf-8bfa-dff03843bda4.csv` | `` | No city code/name columns detected |
| needs_review | 45 | `data/official_tourism_sources/raw/Fukuoka___282090_event_9149497d-fb75-4e6f-90b3-383d95792644.csv` | `` | No city code/name columns detected |
| needs_review | 41 | `data/official_tourism_sources/raw/Fukuoka___282090_event_a888c558-f818-4698-9384-caf7b7021736.csv` | `` | No city code/name columns detected |
| needs_review | 51 | `data/official_tourism_sources/raw/Fukuoka___282090_event_b5af95f0-50ec-4718-b8dc-b156b44bd335.csv` | `` | No city code/name columns detected |
| needs_review | 50 | `data/official_tourism_sources/raw/Fukuoka___282090_event_c4079337-1216-4511-9520-1954d908c86a.csv` | `` | No city code/name columns detected |
| needs_review | 38 | `data/official_tourism_sources/raw/Fukuoka___282090_event_c56ed25a-ecc9-457e-8a7a-b562dc6e3ee0.csv` | `` | No city code/name columns detected |
| needs_review | 27 | `data/official_tourism_sources/raw/Fukuoka___282090_event_cb29ae32-e437-41ff-b605-152418dabbd7.csv` | `` | No city code/name columns detected |
| needs_review | 51 | `data/official_tourism_sources/raw/Fukuoka___282090_event_cfa3957f-9bd5-4ac2-94f7-5692c3e5598e.csv` | `` | No city code/name columns detected |
| needs_review | 66 | `data/official_tourism_sources/raw/Fukuoka___282090_event_d256e097-178c-4d25-85ba-87067f25a1c0.csv` | `` | No city code/name columns detected |
| needs_review | 53 | `data/official_tourism_sources/raw/Fukuoka___282090_event_d9804c76-266d-4fa3-8e67-0b77fc90890e.csv` | `` | No city code/name columns detected |
| accepted | 107 | `data/official_tourism_sources/raw/Fukuoka___401307_yataiopendata_328edbc1-6967-4d0a-8f6d-6678420f4fe2.csv` | `data/official_tourism_sources/processed/accepted/Fukuoka___401307_yataiopendata_328edbc1-6967-4d0a-8f6d-6678420f4fe2.csv` | Fukuoka yatai dataset directly tied to 福岡市 / 401307 |
| rejected_or_later_city | 59 | `data/official_tourism_sources/raw/Fukuoka___402036_0001000_00001_28eafa64-e63b-4b81-adb7-8072390899c9.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/Fukuoka___402036_0001000_00001_28eafa64-e63b-4b81-adb7-8072390899c9.csv` | Detected non-Fukuoka municipality codes: {'402036': 59} |
| needs_review | 59 | `data/official_tourism_sources/raw/Fukuoka___402036_0001000_00001_cf513ea9-80d8-476d-a430-09ba6f99e2ea.csv` | `` | No city code/name columns detected |
| needs_review | 18 | `data/official_tourism_sources/raw/Fukuoka___423831_kakou_73a1f196-e29d-4c46-b294-8e1714451782.csv` | `` | No city code/name columns detected |
| needs_review | 195 | `data/official_tourism_sources/raw/Fukuoka___46201_bunkazai_r050101_3611454e-6d15-48c6-8f34-69e01226340e.csv` | `` | No city code/name columns detected |
| accepted | 107 | `data/official_tourism_sources/raw/Fukuoka___isit_yartai_e03a1f32-25ab-42ec-80c3-e7369e11dadd.csv` | `data/official_tourism_sources/processed/accepted/Fukuoka___isit_yartai_e03a1f32-25ab-42ec-80c3-e7369e11dadd.csv` | Fukuoka yatai dataset directly tied to 福岡市 / 401307 |
| accepted | 101 | `data/official_tourism_sources/raw/Fukuoka___isit_yatai_4f07763f-bc6e-4c4a-8e2c-314eb9032247.csv` | `data/official_tourism_sources/processed/accepted/Fukuoka___isit_yatai_4f07763f-bc6e-4c4a-8e2c-314eb9032247.csv` | All detected municipality codes are 401307 |
| reference | 1558 | `data/official_tourism_sources/raw/digital_agency_municipality_open_data_list.csv` | `data/official_tourism_sources/processed/reference/digital_agency_municipality_open_data_list.csv` | Digital Agency open-data local-government reference list |
| reference | 47 | `data/official_tourism_sources/raw/digital_agency_pref_open_data_list.csv` | `data/official_tourism_sources/processed/reference/digital_agency_pref_open_data_list.csv` | Digital Agency open-data local-government reference list |
| accepted | 107 | `data/official_tourism_sources/raw/fukuoka_yatai_basic_info.csv` | `data/official_tourism_sources/processed/accepted/fukuoka_yatai_basic_info.csv` | Fukuoka yatai dataset directly tied to 福岡市 / 401307 |
| accepted | 32 | `data/official_tourism_sources/raw/hiroshima_events.csv` | `data/official_tourism_sources/processed/accepted/hiroshima_events.csv` | All detected municipality codes are 341002 |
| secondary | 451 | `data/official_tourism_sources/raw/hiroshima_public_wifi.csv` | `data/official_tourism_sources/processed/secondary/hiroshima_public_wifi.csv` | Official Hiroshima public Wi-Fi; useful as convenience data, not a tourism anchor by default |
| accepted | 32 | `data/official_tourism_sources/raw/hiroshima_tourism_facilities.csv` | `data/official_tourism_sources/processed/accepted/hiroshima_tourism_facilities_city_only.csv` | Row-level split: kept 32 rows with municipality code 341002 |
| rejected_or_later_city | 1 | `data/official_tourism_sources/raw/hiroshima_tourism_facilities.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/hiroshima_tourism_facilities_non_city_rows.csv` | Row-level split: stored 1 rows outside Hiroshima city as later-city candidates |
| accepted | 778 | `data/official_tourism_sources/raw/kyoto_pref_tourism_facilities.csv` | `data/official_tourism_sources/processed/accepted/kyoto_tourism_facilities_city_only.csv` | Row-level split: kept 778 rows whose municipality name starts with 京都市 |
| rejected_or_later_city | 853 | `data/official_tourism_sources/raw/kyoto_pref_tourism_facilities.csv` | `data/official_tourism_sources/processed/rejected_or_later_city/kyoto_pref_tourism_facilities_non_city_rows.csv` | Row-level split: stored 853 rows outside Kyoto city as later-city candidates |
| needs_review | 2 | `data/official_tourism_sources/raw/tokyo_tourist_spot_parameter_survey.csv` | `` | No filter rule |
