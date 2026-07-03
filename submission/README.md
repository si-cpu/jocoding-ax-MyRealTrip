# MRT Idea Gate

마이리얼트립의 서비스·콘텐츠 기획자가 개인적으로 떠올린 아이디어를 정식 기획으로 발전시키기 전에 문제의 존재, 근거, 반례와 기존 대안을 확인하도록 돕는 Codex 플러그인입니다.

## 핵심 가치

아이디어를 곧바로 PRD로 확장하지 않고 검증 가능한 원자 명제로 분해합니다. 확인된 사실, 사용자 경험, 추론과 미검증 가정을 분리하고 모든 외부 사실을 다시 열어볼 수 있는 출처 원장에 연결합니다. 각 명제를 `SUPPORTED`, `PARTIAL`, `CONTRADICTED`, `UNKNOWN`으로 판정하고, 전체 아이디어에는 `GO`, `REVISE`, `HOLD`, `DROP` 중 하나와 가장 작은 다음 검증 행동을 제안합니다.

## 제출 구조

```text
submission/
├── src/
│   ├── .codex-plugin/plugin.json
│   └── skills/evaluate-travel-idea/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/
└── logs/
```

`src`가 플러그인 루트입니다. 외부 API 키나 별도 서버 없이 스킬만으로 작동합니다.

## 사용 방법

Codex에서 `submission/src`를 플러그인으로 로드한 뒤 다음과 같이 요청합니다.

```text
나는 서비스 기획자야.
친구들과 여행 상품을 예약할 때 한 명이 전액 결제하고 따로 정산해야 해서 불편했어.
마이리얼트립에 분할결제를 추가하는 아이디어의 기획 가치를 검토해줘.
```

최소 입력은 역할, 아이디어 한 문장, 아이디어가 떠오른 경험 또는 관찰입니다. 공개 근거를 확인할 수 있는 환경에서는 중요한 명제부터 출처를 검증합니다.

## 검증 원칙

- 개인 경험은 현상이 한 번 존재했다는 근거로만 사용합니다.
- 사실·경험·추론·가정을 별도 표로 분리합니다.
- 외부 사실에는 원문 제목, 발행 주체, 날짜, URL, 근거 위치와 한계를 기록합니다.
- 검색 결과 요약만 확인한 자료는 사실이나 최종 권고에 사용하지 않습니다.
- 근거를 찾지 못한 경우 반박된 것으로 처리하지 않고 `UNKNOWN`으로 표시합니다.
- 해결책이 약하다는 이유로 문제의 존재까지 부정하지 않습니다.
- 명제 상태를 단순 평균하거나 근거 없는 점수로 환산하지 않습니다.
- 결과는 초기 권고이며 최종 승인이나 중단 결정을 대신하지 않습니다.

## 로컬 검증

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py submission/src/skills/evaluate-travel-idea
python3 /path/to/plugin-creator/scripts/validate_plugin.py submission/src
```

## 제출 전 확인

`submission/logs`에는 플러그인 제작 과정에서 AI와 주고받은 전체 원본 로그를 편집·발췌·삭제 없이 넣어야 합니다. API 키, 비밀번호, 토큰 등 비밀정보가 포함되지 않았는지 로그 생성 전부터 주의합니다.
