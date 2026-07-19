# T&A Experience Stamp Map Web MVP

Codex 플러그인으로 시작한 마이리얼트립 T&A 경험 인덱싱 아이디어를 웹 화면으로 확장한 MVP입니다.

## 핵심 흐름

1. 도시를 선택한다.
2. 상품 목록보다 먼저 도시의 경험 지도를 본다.
3. 경험을 스탬프 보드에 담는다.
4. 공항·역·숙소·여행지 타임라인을 확인한다.
5. 최초 시간은 저장 시각 기반 초깃값으로 제안하되, 사용자가 직접 일정 시간으로 조정한다.
6. 사진·메모·피드백·공유는 건너뛰거나 글로 대체할 수 있다.
7. 내부 사업개발 화면은 개인 기록이 아니라 비식별 집계 지표만 본다.

## MVP 도시

- 한국: 서울, 전주, 여수, 부산, 대구
- 일본: 도쿄, 오사카, 홋카이도, 후쿠오카

첫 화면 검증용 샘플은 오사카, 전주, 부산을 포함합니다.

## 데이터베이스

MVP는 SQLite 기반 데모 DB를 포함합니다.

- DB 파일: `data/experience_stamp_map.sqlite`
- 스키마: `data/schema.sql`
- 화면용 export: `data/demo-data.json`
- 공식 데이터 소스 계획: `data/OFFICIAL_DATA_SOURCES.md`
- API별 수집 방법: `data/DATA_FETCHING_GUIDE.md`
- 일본 소스 connector 설계: `data/JAPAN_SOURCE_CONNECTORS.md`
- MVP 데이터 축소 기준: `data/MVP_DATA_SCOPE.md`
- 재생성 명령: `npm run db:build`

주요 테이블:

- `cities`
- `experiences`
- `experience_tags`
- `purchase_methods`
- `trips`
- `stamps`
- `trip_timeline_events`
- `event_logs`
- `funnel_metrics`
- `error_logs`
- `feedback`
- `trip_decisions`
- `trip_budget_estimates`

웹 화면은 배포 안정성을 위해 SQLite를 직접 읽지 않고, DB에서 export한 `demo-data.json`을 사용합니다. 따라서 도시·경험·구매방식·타임라인·집계 지표를 수정할 때는 `scripts/build_demo_db.py`의 seed 데이터를 바꾸고 `npm run db:build`로 다시 생성합니다.

## 실행 방법

### 로컬 실행

```bash
npm install
npm run db:build
npm run dev
```

### Docker 실행

배포용이 아니라 로컬 재현성을 위한 실행 방식입니다.

```bash
docker compose up --build
```

실행 후 브라우저에서 `http://localhost:3000`으로 확인합니다.

컨테이너 빌드 과정에서 `npm run db:build`와 `npm run build`가 함께 실행되므로, SQLite 데모 DB와 화면용 JSON이 같은 상태로 맞춰집니다.

Docker 명령에서 `Cannot connect to the Docker daemon`이 나오면 Docker Desktop을 먼저 실행한 뒤 같은 명령을 다시 실행합니다.

## 지도 연동 계획

현재 4번 일정 단계는 API 키 없이도 볼 수 있는 지도형 프리뷰를 제공합니다.

실제 전 세계 도시 경로를 붙일 때는 네이버 지도보다 Google Maps Platform을 우선 사용합니다.

- 환경변수 예시: `.env.example`
- 키 이름: `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
- 1차 연동 대상: Google Maps JavaScript API
- 다음 연동 대상: Directions API 또는 Routes API
- 이동 모드: 도보, 대중교통

개인정보 원칙상 지도는 GPS 실시간 추적이 아니라 사용자가 선택한 공항·역·숙소·경험 앵커를 기준으로 경로를 계산합니다.

## 개인정보 원칙

- GPS/실시간 위치추적을 하지 않습니다.
- 사진 원본, 원문 메모, 개별 여행 스토리는 내부 리포트에 저장하거나 노출하지 않습니다.
- 타임라인 시간은 사용자가 직접 조정·확정한 일정 시간을 우선합니다.
- 모든 기록 기능에는 건너뛰기, 비공개 저장, 텍스트 대체 흐름을 둡니다.
