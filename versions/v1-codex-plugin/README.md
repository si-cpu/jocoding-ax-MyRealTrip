# v1 · 여행 경험 진열대 Codex 플러그인

- 형태: Codex 플러그인
- 기준 문서 버전: Project Charter 0.7.0
- 상태: 해커톤 제출 완료본

## 주요 파일

- `PROJECT_CHARTER.md`: 문제 정의와 제품 원칙
- `DATA_EXPLORATION.md`: TNA 데이터 실행 가능성 검토
- `submission/`: 최종 제출 구조
- `submission.zip`: 제출 당시 압축본

## 검증

```bash
cd versions/v1-codex-plugin
python3 -m unittest discover -s submission/tests -p 'test_*.py'
```

이 버전은 여행자가 도시를 입력하면 상품 유형이 아니라 겹치지 않는 장소·음식·
경험을 먼저 보고, 선택한 경험의 구매 방식과 공식 상품 URL을 확인하는 흐름에
집중한다.
