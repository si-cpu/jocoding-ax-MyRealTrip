# Japan Source Connectors

일본 MVP 도시의 공식/공공 데이터를 수집하기 위한 connector 설계다.

1차 MVP에서는 모든 일본 소스를 자동 수집하지 않는다. 실제 적용 범위는 `MVP_DATA_SCOPE.md`에 따라 오사카와 후쿠오카의 소량 데이터로 제한한다.

## 1. Fukuoka Yatai Connector

### 목적

후쿠오카의 야타이 데이터를 `뭐 먹지`, 야간 일정, 지도 앵커로 사용한다.

### 기본 경로 — BODIK/CKAN 공개 데이터셋

데이터셋:

```text
福岡市　屋台基本情報データセット
```

예상 CKAN 호출:

```bash
curl 'https://data.bodik.jp/api/3/action/package_show?id=401307_yataiopendata'
```

처리:

1. package metadata 조회
2. resources 중 JSON 또는 CSV 리소스 선택
3. resource URL 다운로드
4. 야타이 기본정보를 `official_assets`로 정규화

이 경로를 사용하는 이유:

- 별도 API 이용 신청 없이 재현 가능한 공개 데이터셋을 우선 사용한다.
- GitHub 포트폴리오와 Docker 데모에서 “누가 실행해도 같은 데이터”를 만들기 좋다.
- 기본 야타이 정보는 실시간성이 낮아도 MVP의 `뭐 먹지`, 지도 앵커, 야간 코스 구성에 충분하다.
- 실시간 개점 상태가 없어도 `공식 자산`과 `상품화 후보` 판단에는 문제가 없다.

수집 필드 후보:

- `name`
- `name_kana`
- `name_en`
- `category`
- `address`
- `lat`
- `lng`
- `access`
- `business_hours`
- `regular_holiday`
- `menu`
- `foreign_language_support`
- `reservation_available`
- `cashless_available`
- `google_map_url`
- `official_url`
- `instagram_url`

DB 매핑:

- `official_assets.asset_type = FOOD_STALL`
- `official_assets.category = YATAI`
- `official_assets.is_certified = 1`
- `official_assets.certification_type = FUKUOKA_CITY_YATAI`

현재 제한:

- Codex 셸에서는 DNS 제한으로 직접 호출 검증 불가
- 네트워크 가능한 환경에서 위 URL 검증 필요

제외한 경로:

- 후쿠오카시 데이터 연계기반 신청형 API
- IoT 단말 기반 30분 단위 개점상태 API

제외 이유:

- 현재 프로젝트는 시장 출시용 실시간 서비스가 아니라 MVP/포트폴리오다.
- API 이용 신청이 필요한 경로는 데모 재현성을 떨어뜨린다.
- 현재 영업 여부가 없어도 경험 지도, 야간 미식 후보, 지도 앵커, 상품화 후보 분석에는 충분하다.

## 2. BODIK Generic Connector

### 목적

일본 지자체 표준 오픈데이터를 도시별로 탐색한다.

문서:

```text
https://www.bodik.jp/project/bodik-api/bodik-api-manual/
```

조직 조회:

```bash
curl 'https://wapi.bodik.jp/{apiname}/organization'
```

데이터 조회:

```bash
curl 'https://wapi.bodik.jp/{apiname}?select_type=data&maxResults=100&municipalityName=福岡市'
```

우선 탐색 apiname 후보:

- `tourism`
- `cultural_property`
- `food_business_license`
- `public_facility`
- `event`
- `park`

주의:

- BODIK 표준 API와 각 지자체 고유 API는 다를 수 있다.
- 후쿠오카 신청형 API 카탈로그 항목은 MVP 범위에서 제외한다.

DB 매핑:

- 지자체 시설/관광 데이터 → `official_assets`
- 식품영업/음식 관련 데이터 → `official_assets.asset_type = RESTAURANT`
- 명소/문화재 → `official_assets.asset_type = ATTRACTION`

## 3. Tokyo Tourism Data Connector

### 목적

도쿄의 관광 수요/방문지/소비 데이터를 내부 사업개발 리포트에 사용한다.

공식 데이터:

```text
Tokyo Tourism Data Catalog
```

대표 CSV:

```text
https://www.opendata.metro.tokyo.lg.jp/sangyouroudou/tourist_number_survey/R6tourist_number_survey_1.csv
```

API base:

```text
https://service.api.metro.tokyo.lg.jp
```

수집 방식:

1. CSV 다운로드
2. 인코딩 확인
3. 관광시설/방문객 수/지역/연도/분류 컬럼 정규화
4. 개별 경험 추천이 아니라 내부 리포트 지표로 저장

DB 매핑:

새 테이블 후보:

- `market_demand_signals`

필드:

- `id`
- `city_id`
- `source_id`
- `area_name`
- `asset_name`
- `metric_name`
- `metric_value`
- `year`
- `raw_category`
- `source_url`

사용:

- 대표 경험 판단 보조
- 상품 공급 부족 대비 수요 높은 지역 탐색
- 도쿄의 `많이 검증된 경험`은 MCP 상품 반복 + 관광 수요 지표를 함께 본다.

주의:

- 도쿄 관광 데이터는 통계/수요 데이터다.
- 사용자에게 “예약 가능한 경험”으로 직접 보여주지 않는다.

## 4. Osaka Map Navi Connector

### 목적

오사카의 문화·관광시설, 명소·구적, 철도·버스, 공원 등을 지도 앵커로 사용한다.

공식 페이지:

```text
https://www.city.osaka.lg.jp/toshikeikaku/page/0000250227.html
```

수집 방식:

- CSV 다운로드형
- 라이선스: CC BY
- 위치정보: 세계측지계 JGD2011
- 좌표: X=경도, Y=위도
- CSV 문자코드: UTF-8 안내

우선 다운로드 대상:

1. 시설정보 포인트 데이터 문화·관광
2. 시설정보 포인트 데이터 명所·旧跡
3. 시설정보 포인트 데이터 철도·バス
4. 시설정보 포인트 데이터 공원·스포츠

처리:

1. CSV URL 목록 추출 또는 수동 등록
2. 각 CSV 다운로드
3. 이름, 카테고리, 주소, 경도, 위도 정규화
4. 오사카 MCP 상품 경험과 이름/좌표 기반 매칭

DB 매핑:

- 문화·관광/명소 → `official_assets.asset_type = ATTRACTION`
- 철도·버스 → `official_assets.asset_type = TRANSIT_ANCHOR`
- 공원·스포츠 → `official_assets.asset_type = ACTIVITY_ANCHOR`

주의:

- Map Navi는 상품 데이터가 아니다.
- 오사카 공식 앵커/동선 보강용이다.
- 예약 가능 여부는 MyRealTrip MCP 상품 URL로만 판단한다.

## 5. 구현 순서

### 1차 데모

1. `official_data_sources`에 후쿠오카 야타이와 오사카 Map Navi만 등록
2. 후쿠오카 CKAN package_show 검증
3. 후쿠오카 야타이 공개 리소스 다운로드 parser 작성
4. 오사카 Map Navi CSV 수동 URL 등록 후 parser 작성
5. MCP 상품 데이터와 `experience_source_links`로 소량 매칭

### 2차 확장

1. 도쿄 CSV 다운로드 parser 작성
2. BODIK generic connector 구현
3. 홋카이도/삿포로 오픈데이터 탐색
