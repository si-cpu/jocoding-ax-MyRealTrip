# T&A Supply Gap Map 파이프라인

## 목적

저장된 공식 관광 데이터와 마이리얼트립 MCP 상품·투어 상세를 같은 순서로 다시 처리해, 장소별 공급 연결과 상품개발 검토 후보를 재현한다.

## 실행

기본 실행은 네트워크를 사용하지 않고 저장된 입력으로 파생 데이터를 다시 만든다.

```bash
python3 scripts/run_supply_gap_pipeline.py --mode rebuild
```

실행 계획만 확인한다.

```bash
python3 scripts/run_supply_gap_pipeline.py --mode rebuild --dry-run
```

보고서와 PDF만 다시 생성한다.

```bash
python3 scripts/run_supply_gap_pipeline.py --mode report
```

테스트만 실행한다.

```bash
python3 scripts/run_supply_gap_pipeline.py --mode verify
```

공식 데이터와 MCP를 새로 수집한다. 네트워크 요청과 MCP 요청 제한의 영향을 받으므로 의도적으로 실행할 때만 사용한다.

```bash
python3 scripts/run_supply_gap_pipeline.py \
  --mode refresh \
  --cities 후쿠오카 히로시마 \
  --max-pages 7
```

공식 원천은 유지하고 MCP만 갱신하려면 `--skip-official-refresh`를 추가한다.

## 단계

```text
공식·MCP 원천 수집(refresh만)
→ 도시·비관광 데이터 필터
→ 공식 장소 앵커 생성
→ 제한된 한국어 별칭 후보 생성
→ 투어 상세·공개 일정의 실제 방문 장소 매칭
→ 공식 장소와 MCP 상품 연결
→ 상위 장소·권역 포함 관계 검수 게이트
→ 후쿠오카 180개 상세 완전성·비투어 도시 범위 감사
→ 확정 방문·옵션·포함 관계·단순 언급 분리
→ 공식명 직접 일치 거짓 음성 후보 검수
→ 도시별 일치율·정확한 리스트 산출
→ 후쿠오카·교토 상품개발 후보 생성
→ PDF 생성
→ 단위 테스트
```

## 자동화와 사람 검수의 경계

- 자동: 공식 데이터 필터, 명칭 정규화, 일정의 긍정 방문 근거, 집결·조망·불포함 제외, 상세 완전성, 일치율, 후보 리포트
- 사람 검수: `MCP만 있음` 후보가 거리·테마파크·복합시설의 하위 경험인지 확인
- 검수 원장: 역방향 계층, 장소×상품 연결 강도, 도시 범위, 거짓 음성 후보 CSV
- 검수 실패 시 파이프라인은 보고서 생성 전에 중단한다.

## 주요 산출물

- `data/supply_gap_analysis/city_supply_coverage.csv`
- `data/supply_gap_analysis/exports/supply_gap_exact_list.csv`
- `data/supply_gap_analysis/reports/FUKUOKA_REANALYSIS.md`
- `data/supply_gap_analysis/reports/FUKUOKA_MCP_REVERSE_HIERARCHY_AUDIT.md`
- `data/supply_gap_analysis/reports/FUKUOKA_TRUST_AUDIT.md`
- `data/supply_gap_analysis/audit/fukuoka_place_product_link_audit.csv`
- `data/supply_gap_analysis/audit/fukuoka_product_city_scope_audit.csv`
- `data/supply_gap_analysis/reports/FUKUOKA_PRODUCT_OPPORTUNITY_CANDIDATES.md`
- `output/pdf/ta_supply_gap_first_pass.pdf`
- `data/supply_gap_analysis/reports/pipeline_run_summary.json`

## 해석 원칙

- `없음`은 현재 수집·검증 범위에서 공급 근거를 확인하지 못했다는 뜻이다.
- 투어의 집결지·조망 대상·주변 시설은 실제 방문으로 계산하지 않는다.
- 공식 `/spots`에 없더라도 공식 `/tours`, 체험, 쇼핑 카탈로그에 있을 수 있다.
- `MCP만 있음`은 상위 장소와 다른 공식 카탈로그를 확인한 뒤 `민간 콘텐츠 확장`으로 판정한다.
- 공급 공백은 상품개발 후보이지 수요 증명이 아니다.
