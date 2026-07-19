# v3 · T&A Supply Gap Map

- 형태: Python 데이터 파이프라인 + CSV/Markdown/PDF 보고서
- 기준 문서 버전: Project Charter 0.1.1
- 상태: 현재 사업개발 분석 버전

## 주요 파일

- `PROJECT_CHARTER.md`: 분석 목적과 판단 기준
- `RETROSPECTIVE.md`: 개발 과정과 한계
- `PIPELINE.md`: 재현 가능한 실행 방법
- `OFFICIAL_DATA_SOURCES.md`: 공식 데이터 출처
- `scripts/`: 수집·정제·매칭·감사·보고서 생성 코드
- `data/`: MCP 및 공식 관광 데이터와 분석 산출물
- `tests/`: 파이프라인과 신뢰도 감사 테스트
- `output/`: PDF 산출물

## 실행

```bash
cd versions/v3-ta-supply-gap-map
python3 scripts/run_supply_gap_pipeline.py --mode rebuild
```

네트워크 재수집 없이 저장된 입력으로 검증만 실행하려면:

```bash
python3 scripts/run_supply_gap_pipeline.py --mode verify
```

현재 후쿠오카 역방향 장소 분석은 세부 장소 7개를 상위 여행지 4개로 중복 제거해
보존하며, 공식 원본·다른 공식 카탈로그·플랫폼 고유 검토 후보를 구분한다.
