# 새로운 나를 찾는 여행 — Codex 플러그인 v0.4

첫 응답에서 세 사용법을 안내하고, 익숙한 선택을 잠시 제외해 새로운 이동·숙소·현지 경험을 발견하도록 돕는 마이리얼트립 여행 넛지 플러그인입니다.

## 처음 보이는 사용법

```text
1. 공항에서 어디로 갈까
   출발 공항의 항공권 데이터에서 익숙하지 않은 해외 목적지 찾기

2. 어디서 잘까
   익숙한 숙소 유형을 제외한 다른 숙박 경험

3. 오늘·내일 뭐 하지
   해당 날짜에 실제 예약 가능한 낯선 투어·티켓
```

사용자는 내부 명령을 알 필요 없이 자연어로 요청합니다. `$discover-new-trip` 하나가 세 입구 중 하나로 분류합니다.

```text
인천공항에서 4일간 갈 새로운 곳을 찾아줘. 일본과 태국은 많이 가봤어.
```

## 사용 예시

### 공항에서 어디로 갈까

```text
인천공항에서 5일간 갈 새로운 해외 여행지를 찾아줘. 도쿄와 방콕은 익숙해.
```

공항 자동완성의 `airport.code`로 출발지를 확인하고, 국제선 전체 목적지 캘린더 최저가에서 익숙한 목적지를 제외합니다. 사용자가 하나를 고르면 같은 날짜의 실제 항공편과 예약 링크를 다시 조회합니다.

### 어디서 잘까

```text
내일 도쿄에서 1박할 거야. 지금까지 호텔에서만 자봤어.
```

정확한 도시 `regionId`를 확인하고, 호텔이 아닌 숙소 유형을 MCP 결과와 교차 검증합니다.

### 오늘·내일 뭐 하지

```text
내일 도쿄에서 뭐 하지? 나는 야구를 좋아해.
```

도쿄로 검증된 투어·티켓 중 야구와 직접 겹치는 상품을 제외하고, 선택 날짜의 옵션이 실제로 존재하는 상품만 보여줍니다.

## 데이터 연결

- Partner REST API: `https://partner-ext-api.myrealtrip.com`
- 공식 MCP: `https://mcp-servers.myrealtrip.com/mcp`
- REST 인증: `MYREALTRIP_API_KEY` 환경변수

API 키를 프롬프트, 소스코드, `.mcp.json`, 테스트 파일 또는 제출 로그에 입력하지 마세요.

## 구조

```text
submission/
├── src/
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── scripts/myrealtrip_api.py
│   └── skills/discover-new-trip/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/search-and-exclusion-rules.md
├── tests/test_myrealtrip_api.py
├── README.md
├── VALIDATION.md
└── logs/
```

해커톤 제출 시 편집하지 않은 전체 AI 대화 로그를 `logs/`에 별도로 넣어야 합니다.

## 로컬 검증

```text
python3 -m unittest discover -s submission/tests -v
```

실제 REST 호출은 셸 환경에 API 키를 설정한 뒤 실행합니다. 키가 없는 경우 플러그인은 가능한 MCP 흐름만 사용하고, REST 검증을 수행하지 못했다는 한계를 표시해야 합니다.

## 제한사항

- 최저가 캘린더는 실시간 예약가가 아닙니다.
- 전체 목적지 최저가 조회는 국제선만 지원합니다.
- 캘린더 최저가는 실시간 좌석이나 최종 결제 가격이 아닙니다.
- REST 숙소 검색만으로는 숙소 유형을 판별할 수 없습니다.
- 사용자가 직접 밝히지 않은 취향·방문 이력을 추론하지 않습니다.
- 예약·결제·취소를 수행하지 않습니다.
