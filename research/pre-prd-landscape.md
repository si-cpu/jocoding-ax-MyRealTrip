# Pre-PRD Gate 유사 프로세스·도구 조사

조사일: 2026-07-02

## 조사 질문

1. 마이리얼트립은 이미 공개적으로 유사한 아이디어 검증 프로세스를 운영하는가?
2. 시장에 같은 역할을 하는 제품·프레임워크·Codex 스킬이 존재하는가?
3. 존재한다면 우리 플러그인이 해결할 남은 빈틈은 무엇인가?

## 요약 판정

- 일반적인 아이디어 수집·근거 연결·점수화·우선순위·PRD 작성: **이미 성숙한 도구가 많음**
- Codex에서 discovery부터 구현까지 안내하는 워크플로: **이미 존재함**
- AI가 전략적 빈틈과 예외를 지적하는 PM 코치: **이미 존재함**
- 마이리얼트립 내부의 정확한 Pre-PRD Gate 존재 여부: **공개 자료만으로 확인 불가**
- 근거 유형과 반증을 의무화하고, 핵심 UNKNOWN이 있으면 GO를 금지하는 로컬 Codex 게이트: **조사 범위에서 동일 구현을 확인하지 못함**

따라서 범용 `아이디어 초기 관리 플러그인`은 DROP이다. `마이리얼트립 PE용 증거·반례 기반 Pre-PRD Gate`로 좁힐 때만 조건부 GO다.

## 마이리얼트립 공개 프로세스

### 확인된 내용

마이리얼트립은 AI Native 전환 과정에서 개발자·PM·디자이너·데이터 분석가를 Product Engineer 관점으로 확장하고, 문제 정의부터 구현과 결과까지 End-to-End로 책임지는 방향을 공개했다.

또한 공식 사례에서 다음을 명시한다.

- AI가 코드 작성을 맡더라도 사람이 `무엇을 만들지`, `왜 만드는지` 결정하고 결과를 검증한다.
- 사용자 흐름과 전체 제품 맥락을 알아야 구현 우선순위를 판단할 수 있다.
- PE Expert 그룹이 구성원의 제품 관점과 AI Native 업무 방식을 지원한다.
- 프로젝트 규칙·문서 기본 틀·반복 검증 흐름을 만들고 주간 미팅으로 병목을 개선한다.
- 자동화는 작고 빠르게 검증 가능한 부분부터 시작해 점진적으로 확장한다.
- 마이팩은 고객 니즈와 시장 구조를 재검토하고 가설·검증·판단 조정을 반복했다.

### 확인하지 못한 내용

공개 자료에서는 다음을 확인하지 못했다.

- 모든 기능 아이디어에 공통 적용되는 정식 Pre-PRD 체크리스트
- 주장마다 반증 자료를 의무화하는 규칙
- 핵심 근거가 UNKNOWN일 때 개발 단계 진입을 막는 자동 게이트
- GO/HOLD/REVISE/DROP을 산출하는 Codex 플러그인

이는 `존재하지 않는다`는 뜻이 아니다. 비공개 내부 프로세스일 수 있으므로 제출물에서는 부재를 단정하면 안 된다.

## 시장의 직접 대체재

| 도구 | 이미 제공하는 것 | 우리 아이디어와의 중복 | 조사에서 보인 빈틈 |
|---|---|---:|---|
| Jira Product Discovery | 아이디어, 고객 인사이트, 근거 링크, 영향도, 점수화, 우선순위, 로드맵, Jira 개발 연결 | 매우 높음 | 기본 목적은 관리·우선순위이며 반증 의무화나 UNKNOWN 차단은 명시되지 않음 |
| Aha! Discovery/Roadmaps/Ideas | 인터뷰, 연구, AI 요약, 인사이트, 가치 점수표, 전략·로드맵 연결 | 매우 높음 | 완전한 제품군이라 로컬 Codex 작업 흐름과는 사용 맥락이 다름 |
| Productboard | 제품 발견, 인사이트, 우선순위, 개발 백로그 연결 | 높음 | 범용 SaaS이며 회사별 강제 게이트는 별도 설정 필요 |
| ChatPRD | PRD·원페이저 작성, gap 분석, edge case 탐지, CPO 관점 리뷰, MCP 연동 | 높음 | 문서 생성·코칭 중심. 근거 미확인 시 산출 금지보다는 초안 작성에 가까움 |
| BMAD Codex Skills | 제품 발견, 기획, 아키텍처, 구현, 코드리뷰를 잇는 Codex 워크플로와 YAML 상태 | 높음 | 개발 전 과정 범용 워크플로로 범위가 넓음 |
| Product Manager Skills | discovery, PRD 비평, 로드맵, SaaS 지표 진단 | 높음 | 범용 PM 역량 묶음이며 마이리얼트립 도메인 게이트가 아님 |
| AI idea validators | 시장 신호 수집, 가정 추출, 위험 점수, 경쟁 분석, 검증 점수 | 중간~높음 | 창업·신사업 검증 중심. 기존 제품의 내부 기능 제안과는 목표가 다름 |

## 기존 프레임워크와의 중복

우리 아이디어의 각 구성요소는 새롭지 않다.

- 고객 문제 확인: Product Discovery
- 위험한 가정 추출: Assumption Mapping
- 실패를 미리 상상: Pre-mortem
- 가치·노력 평가: RICE, Value/Effort, scorecard
- 작은 실험부터 수행: Lean validation, riskiest-assumption test
- 프로젝트 승인 문서: Project Charter

새로울 수 있는 것은 프레임워크 자체가 아니라, 이를 마이리얼트립 PE의 Codex 작업 안에서 `증거가 없으면 통과하지 못하는 실행 규칙`으로 결합하는 방식이다.

## 차별화가 성립하려면 필요한 조건

다음 항목을 모두 구현하지 않으면 기존 도구의 축소판이 된다.

1. 아이디어 backlog나 roadmap을 만들지 않는다. 오직 아이디어 한 건의 개발 전 판정만 수행한다.
2. 모든 중요 주장을 `FACT / EXPERIENCE / INFERENCE / UNKNOWN`으로 분류한다.
3. FACT에는 검증 가능한 출처 또는 로컬 근거 파일을 의무화한다.
4. 각 주장에 가장 강한 반례와 더 작은 대안을 의무화한다.
5. 기존 마이리얼트립 기능과 공개 사례를 먼저 조사한다.
6. 핵심 항목이 UNKNOWN이면 GO를 기술적으로 금지한다.
7. GO보다 HOLD·REVISE·DROP을 정상적인 성공 결과로 취급한다.
8. 결과를 저장소 안의 감사 가능한 Markdown/JSON으로 남긴다.
9. GO 이후에만 Charter 또는 PRD 도구로 핸드오프한다.
10. 마이리얼트립의 여행자·파트너·예약·결제·환불·상품운영 맥락을 체크 규칙에 반영한다.

## 제작 가치 판정

### 원안

`아이디어 초기 단계를 관리하는 Codex 플러그인`

판정: **DROP**

이유: Jira Product Discovery, Aha!, Productboard, ChatPRD, BMAD 및 PM Agent Skills와 역할이 크게 겹친다.

### 수정안

`마이리얼트립 Product Engineer가 기능 구현 전에 근거·반례·미확인 가정을 감사하고, 하드 게이트 규칙으로 GO/HOLD/REVISE/DROP을 결정하는 Codex 플러그인`

판정: **조건부 GO**

이유:

- 마이리얼트립이 공개한 AI Native PE 업무 방식과 직접 연결된다.
- 기존 제품의 강점인 아이디어 관리·로드맵과 경쟁하지 않고 그 이전의 단일 결정 감사에 집중할 수 있다.
- Codex가 공개 조사, 로컬 문서, 코드·제품 맥락을 함께 읽는 장점을 활용할 수 있다.
- `UNKNOWN이면 GO 금지` 같은 결정 규칙은 자동 테스트가 가능하다.
- 우리가 실제로 유사상품 아이디어를 HOLD한 과정을 재현 가능한 데모로 사용할 수 있다.

## 남은 핵심 리스크

1. 마이리얼트립 내부에 동일한 비공개 시스템이 있을 가능성을 배제할 수 없다.
2. 체크리스트가 길어지면 통과 의례와 문서 작업만 늘릴 수 있다.
3. 공개 근거만으로 내부 기능의 사업가치를 판단하는 데 한계가 있다.
4. 모델이 그럴듯한 반례나 출처를 꾸며낼 위험이 있다.
5. 엄격한 게이트가 작은 실험까지 막으면 AI Native 조직의 빠른 실행과 충돌할 수 있다.

따라서 플러그인은 개발을 승인하는 권위자가 아니라 `검증 누락을 드러내는 감사 도구`로 정의해야 한다. 최종 결정은 사람이 한다.

## 최종 권고

프로토타입 제작 전, 동일 아이디어 3건을 대상으로 사람의 수동 체크와 플러그인 체크를 비교한다.

- 이미 존재하는 기능을 제안한 사례 1건
- 근거는 있으나 반례가 강한 사례 1건
- 공개 근거와 작은 실험 계획이 충분한 사례 1건

플러그인이 수동 검토보다 더 많은 핵심 누락을 발견하고 허위 근거를 만들지 않을 때만 구현을 계속한다.

## 주요 공개 출처

- 마이리얼트립, Product Engineer: 코드는 AI가, 나는 제품 관점에서 고민을
  - https://blog.myrealtrip.com/pepe-ai-codes-pe-thinks/
- 마이리얼트립, AI Native 조직 전환
  - https://blog.myrealtrip.com/ai-native-transition-why/
- 마이리얼트립, AICX 자동화 사례
  - https://blog.myrealtrip.com/aicx-cs-automation-75k-monthly/
- 마이리얼트립, 마이팩 문제 재정의 회고
  - https://blog.myrealtrip.com/mypack-product-retrospective/
- Jira Product Discovery 공식 소개
  - https://www.atlassian.com/software/jira/product-discovery
- Jira Product Discovery Insights 공식 가이드
  - https://www.atlassian.com/software/jira/product-discovery/guides/insights/overview
- Aha! Discovery 공식 소개
  - https://www.aha.io/discovery/overview
- ChatPRD 공식 소개
  - https://www.chatprd.ai/
- BMAD Skills for Codex
  - https://github.com/xmm/codex-bmad-skills
