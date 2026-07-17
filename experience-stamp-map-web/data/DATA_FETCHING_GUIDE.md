# Data Fetching Guide

마이리얼트립 MCP/Partner API와 도시·국가 공식 데이터를 실제로 가져오기 위한 호출 방식 정리다.

실제 1차 MVP 수집 범위는 `MVP_DATA_SCOPE.md`를 따른다. 아래 API들은 확장 후보까지 포함하므로, 구현 시 모든 데이터를 한 번에 수집하지 않는다.

## 0. 일본 소스 우선 확인 결과

| 소스 | 실제 수집 방식 | 인증/신청 | MVP 판단 |
|---|---|---|---|
| 후쿠오카 야타이 | BODIK/CKAN 공개 데이터셋 다운로드 | 공개 데이터셋 리소스 사용 | 야간 미식/지도 앵커로 최우선 |
| BODIK API | `https://wapi.bodik.jp/{apiname}` REST API 또는 CKAN 리소스 다운로드 | 표준 API는 대체로 공개. 일부 지자체 API는 별도 신청 가능 | 일본 지자체 데이터 탐색용 |
| 도쿄 관광 데이터 | CSV 다운로드 + Tokyo Open Data API Catalog | 대체로 공개/CC BY. 일부 API는 카탈로그에서 endpoint 확인 | 사용자 화면보다 내부 수요 리포트용 |
| 오사카 Map Navi | CSV 다운로드형 오픈데이터 | 공개/CC BY | 지도 앵커/명소/역·버스 기준점용 |

주의:

- 후쿠오카는 `공개 CKAN/BODIK 리소스 다운로드형`만 사용한다. 신청형 API와 실시간 개점 상태 API는 현재 MVP/포트폴리오 범위에서 제외한다.
- 도쿄 관광 데이터는 개별 식당/상품 데이터라기보다 관광 통계·방문지 수요 데이터에 가깝다.
- 오사카 Map Navi는 API가 아니라 CSV 다운로드 수집기로 보는 것이 안전하다.

## 1. MyRealTrip MCP

목적:

- 도시별 T&A 상품 검색
- 카테고리별 상품 수집
- 상품 상세에서 일정/포함사항/불포함사항 확인
- 공식 상품 URL 연결

### MCP endpoint

```text
https://mcp-servers.myrealtrip.com/mcp
```

### 카테고리 조회

```bash
curl -sS 'https://mcp-servers.myrealtrip.com/mcp' \
  -H 'Accept: application/json, text/event-stream' \
  --json '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "getCategoryList",
      "arguments": {
        "city": "오사카"
      }
    }
  }'
```

### 상품 검색

```bash
curl -sS 'https://mcp-servers.myrealtrip.com/mcp' \
  -H 'Accept: application/json, text/event-stream' \
  --json '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "searchTnas",
      "arguments": {
        "query": "오사카",
        "category": "ticket_v2",
        "page": 1,
        "perPage": 20
      }
    }
  }'
```

### 상품 상세

```bash
curl -sS 'https://mcp-servers.myrealtrip.com/mcp' \
  -H 'Accept: application/json, text/event-stream' \
  --json '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "getTnaDetail",
      "arguments": {
        "gid": "상품ID",
        "url": "https://experiences.myrealtrip.com/products/상품ID"
      }
    }
  }'
```

### MVP 수집 규칙

- 입장권: 상품 제목에서 경험명 추출
- 투어: 상세 일정/포함사항까지 조회
- 패스: 처음부터 경험으로 펼치지 않고, 사용자가 경험을 선택한 뒤 포함 여부 확인
- 불포함사항: 긍정 근거로 사용하지 않음
- 공식 URL이 있는 상품만 `예약 가능 경험`

## 2. MyRealTrip Partner API

기존 제출물의 Python 클라이언트:

```text
submission/src/scripts/myrealtrip_api.py
```

환경변수:

```bash
export MYREALTRIP_API_KEY='발급받은 키'
```

역할:

- 실제 Partner API 키가 있을 때 상품 검색/상세/옵션/URL 검사 자동화
- 현재 웹 MVP에서는 MCP 수집 결과와 공식 데이터를 합친 seed 생성 스크립트로 확장 예정

## 3. 한국관광공사 TourAPI

목적:

- 한국 도시별 관광지, 음식점, 행사, 문화시설, 쇼핑, 레포츠 등 공식 관광 콘텐츠 확보

기본 호출 형식:

```text
https://apis.data.go.kr/B551011/KorService1/{operation}
```

공통 파라미터:

- `serviceKey`: 공공데이터포털 인증키
- `MobileOS`: `ETC`
- `MobileApp`: 앱 이름. 예: `ExperienceStampMap`
- `_type`: `json`
- `pageNo`: 페이지 번호
- `numOfRows`: 페이지당 건수
- `arrange`: 정렬. 예: `A` 제목순, `C` 수정일순

### 지역 기반 목록

```bash
curl 'https://apis.data.go.kr/B551011/KorService1/areaBasedList1?serviceKey=SERVICE_KEY&MobileOS=ETC&MobileApp=ExperienceStampMap&_type=json&pageNo=1&numOfRows=100&arrange=A&areaCode=6'
```

활용:

- 서울/전주/여수/부산/대구의 `뭐 하지`, `뭐 먹지` 기본 후보 생성
- `contentTypeId`로 관광지/문화시설/행사/음식점 등을 분리 가능

주의:

- 인증키 필요
- 지역코드/시군구코드는 코드 조회 API로 먼저 확보해야 함
- TourAPI에 있어도 마이리얼트립 예약 상품은 아니므로 `지역 공식 자산`으로 표시

## 4. 공공데이터포털 관광식당 API

목적:

- 전국 관광식당/관광객 대상 음식점 인허가 데이터 확보
- 인증 식당/공식 식당 후보 보강

서비스:

```text
Ministry of the Interior and Safety_Food, Tourism, and Restaurant Inquiry Service
```

Endpoint:

```text
http://apis.data.go.kr/1741000/tourist_restaurants/info
```

파라미터:

- `serviceKey`: 공공데이터포털 인증키
- `pageNo`: 페이지 번호
- `numOfRows`: 페이지당 건수
- `returnType`: `json`
- `cond[BPLC_NM::LIKE]`: 사업장명 검색
- `cond[ROAD_NM_ADDR::LIKE]`: 도로명 주소 검색
- `cond[SALS_STTS_CD::EQ]`: 영업 상태 코드

예시:

```bash
curl 'http://apis.data.go.kr/1741000/tourist_restaurants/info?serviceKey=SERVICE_KEY&pageNo=1&numOfRows=100&returnType=json&cond%5BROAD_NM_ADDR%3A%3ALIKE%5D=부산'
```

활용:

- 도시별 인증성 식당 후보
- `뭐 먹지` 공식 자산 보강

## 5. 부산광역시 부산맛집정보 서비스

목적:

- 비짓부산 미식투어 기반 추천 식당/카페 데이터 확보
- 부산 `뭐 먹지` 경험 강화

데이터 특징:

- 이름, 주소, 홈페이지, 전화번호, 좌표, 상세정보
- 주변 관광지, 여행사진, 리뷰
- 한국어/영어/일본어/중국어 간체/번체 다국어
- JSON/XML

공공데이터포털:

```text
부산광역시_부산맛집정보 서비스
```

수집 방법:

1. 공공데이터포털에서 활용신청
2. 참고문서의 서비스 URL/operation 확인
3. `serviceKey`, `pageNo`, `numOfRows`, 응답 타입을 붙여 호출

예상 형태:

```bash
curl '부산맛집서비스_ENDPOINT/operation?serviceKey=SERVICE_KEY&pageNo=1&numOfRows=100&resultType=json'
```

주의:

- 상세 endpoint/operation은 공공데이터포털 참고문서 DOCX에서 확인해야 함
- MVP에서는 우선 수동 seed 또는 문서 기반 connector 작성 후 키 발급 시 자동화

## 6. 대구광역시 맛집 API

목적:

- 대구푸드 공식 맛집 데이터 확보
- 대구10미, 대구명품빵, 대구우수식품, 먹거리골목 보강

인증:

- 별도 공공데이터포털 serviceKey 없이 공개 URL 호출형으로 확인됨

Endpoint 예시:

```text
https://www.daegufood.go.kr/kor/api/tasty.html?mode=json&addr=중구
```

예시:

```bash
curl 'https://www.daegufood.go.kr/kor/api/tasty.html?mode=json&addr=%EC%A4%91%EA%B5%AC'
```

파라미터:

- `mode=json`
- `addr`: 구/군명. 예: `중구`

활용:

- 음식점명, 주소, 메뉴, 영업시간, 가능언어, 예약가능여부, 조식여부 등
- 대구 `뭐 먹지`, 인증 식당, 조식 가능한 식당, 외국어 가능 식당 필터

## 7. 서울 열린데이터광장

목적:

- 서울 관광/문화/상권/도시 데이터 확보

인증:

- 서울 열린데이터광장 인증키 필요

기본 호출 형식:

```text
http://openapi.seoul.go.kr:8088/{KEY}/{TYPE}/{SERVICE}/{START_INDEX}/{END_INDEX}/{검색어}
```

파라미터:

- `KEY`: 인증키
- `TYPE`: `json`, `xml`, `xls` 등
- `SERVICE`: 서비스명
- `START_INDEX`: 시작 위치
- `END_INDEX`: 종료 위치
- 검색어: 서비스별 선택

예시 형식:

```bash
curl 'http://openapi.seoul.go.kr:8088/KEY/json/SERVICE_NAME/1/100'
```

활용:

- 서울 관광특구/고궁/공원/발달상권 등 공식 자산
- 서울 실시간 도시데이터는 내부 리포트 보조 지표로만 사용

## 8. 스마트서울맵 OpenAPI

목적:

- 서울 다국어 POI, 테마 지도, 주소/좌표 변환

인증:

- OpenAPI 사용신청 필요

수집 방법:

1. 스마트서울맵 OpenAPI 신청
2. POI 카테고리/다국어 POI/주소 변환 API 선택
3. 서울 경험의 좌표와 다국어 명칭 보강

활용:

- 서울 여행지 지도 배치
- 외국인/일본어/영어 표기 보강

## 9. 후쿠오카 야타이 데이터

목적:

- 후쿠오카 야타이 이름, 주소, 위치, 메뉴, 영업 상태 확보
- 야간 미식 타임라인 구성

### 수집 경로: BODIK/CKAN 공개 데이터셋

데이터셋:

```text
福岡市　屋台基本情報データセット
```

예상 CKAN 호출:

```bash
curl 'https://data.bodik.jp/api/3/action/package_show?id=401307_yataiopendata'
```

처리:

1. CKAN package metadata 조회
2. resources 중 JSON 또는 CSV 다운로드 URL 확인
3. 리소스 다운로드
4. 이름, 주소, 좌표, 메뉴, 영업시간, Google Map URL, 공식 URL 등을 정규화
5. `official_assets`에 `FOOD_STALL`로 저장

이 경로를 사용하는 이유:

- 포트폴리오 재현성이 높다.
- Docker/README 기준으로 누구나 같은 데이터셋을 확인할 수 있다.
- 기본 야타이 정보만으로도 `뭐 먹지`, 야간 코스, 지도 앵커 구성이 가능하다.
- 신청형 API 없이도 MVP 목적을 달성할 수 있다.

활용:

- 후쿠오카 `뭐 먹지`
- 야간 코스
- 지도 앵커

## 10. BODIK API

목적:

- 일본 지자체 표준 오픈데이터 검색
- 후쿠오카 등 BODIK 기반 도시 데이터 보강

기본 형식:

```text
https://wapi.bodik.jp/{apiname}
```

조직 조회:

```bash
curl 'https://wapi.bodik.jp/{apiname}/organization'
```

검색 예시:

```bash
curl 'https://wapi.bodik.jp/aed?select_type=data&maxResults=10&municipalityName=福岡市'
```

활용:

- 표준 데이터셋에서 시설/식품영업/관광 관련 데이터 탐색
- 후쿠오카 외 일본 지자체 확장 후보

## 11. 도쿄 관광 데이터 카탈로그

목적:

- 도쿄 관광 통계, 방문지, 소비, 관광시설 방문자 데이터 확보
- 내부 사업개발 리포트의 시장성/수요 근거

수집 방식:

- 대시보드에서 로데이터 다운로드
- 일부 데이터는 Tokyo Metropolitan Open Data API Catalog 또는 CSV URL 제공

예시 CSV:

```text
https://www.opendata.metro.tokyo.lg.jp/sangyouroudou/tourist_number_survey/R6tourist_number_survey_1.csv
```

API base:

```text
https://service.api.metro.tokyo.lg.jp
```

활용:

- 도쿄 주요 방문지/관광시설 수요 지표
- `많이 검증된 경험` 판단 보조
- 상품 공급과 관광 수요의 gap 분석

주의:

- 개별 예약 상품 데이터가 아니라 통계/수요 데이터
- 사용자 화면보다는 내부 리포트에 적합

## 12. 오사카시 Map Navi Open Data

목적:

- 오사카 문화·관광시설, 명소·구적, 철도·버스, 공원 등 지도 기준점 확보

수집 방식:

- CSV 다운로드형
- 좌표 포함
- 라이선스: CC BY
- 문자 인코딩: CSV는 UTF-8로 안내

주요 데이터:

- 시설정보 포인트 데이터 문화·관광
- 시설정보 포인트 데이터 명所·旧跡
- 시설정보 포인트 데이터 철도·버스
- 공원·스포츠

활용:

- 오사카 지도 앵커
- 공식 명소 seed
- 역/버스 정류장 기반 타임라인

## 13. Google Maps Platform

목적:

- 전 세계 도시의 지도, 좌표, 도보/대중교통 경로

환경변수:

```text
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
```

사용 API:

- Maps JavaScript API
- Directions API 또는 Routes API
- Places API는 필요 시 후보. 단, 공식 도시 데이터와 혼동하지 않도록 출처 분리

활용 원칙:

- 사용자의 실시간 GPS 추적 금지
- 사용자가 선택한 공항·역·숙소·경험 앵커만 경로 계산
- 계산된 경로는 `route_suggestions`로 저장하고, 실제 이동 기록처럼 표현하지 않음

## 14. 우선 구현 순서

### 1차 데모

1. MyRealTrip MCP: 오사카/후쿠오카/부산 상품 데이터만 수집
2. 후쿠오카 야타이 공개 데이터셋: 최대 6개만 사용
3. 오사카 CSV: 문화·관광/명소/철도·버스 중 최대 13개 앵커만 사용
4. 부산 공식/공공 데이터: 맛집·해안·야경 seed 수준으로 최대 10개만 사용

### 2차 확장

1. 대구 맛집 API
2. TourAPI
3. 관광식당 API
4. 부산 맛집 API
5. 도쿄 CSV/API
