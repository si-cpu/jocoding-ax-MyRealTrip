from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "experience_stamp_map.sqlite"
JSON_PATH = ROOT / "data" / "demo-data.json"
SCHEMA_PATH = ROOT / "data" / "schema.sql"
GENERATED_ANCHORS_PATH = ROOT / "data" / "generated_anchor_candidates.json"


CITIES = [
    {
        "id": "osaka",
        "country": "일본",
        "name": "오사카",
        "positioning": "입장권·패스·미식이 풍부한 검증형 도시",
        "demand_signal": "대표 경험 선명 / 공식 상품 연결 많음",
    },
    {
        "id": "fukuoka",
        "country": "일본",
        "name": "후쿠오카",
        "positioning": "야타이·도심 미식·짧은 동선이 강한 야간형 도시",
        "demand_signal": "공식 야타이 자산과 T&A 상품 매칭 여지 큼",
    },
    {
        "id": "busan",
        "country": "한국",
        "name": "부산",
        "positioning": "해안 동선·시장 미식·야경이 타임라인으로 살아나는 도시",
        "demand_signal": "역/해변/시장 앵커 중요, 숙소는 MCP 후보로 별도 수집",
    },
]


EXPERIENCES = [
    # Osaka
    ("usj", "osaka", "유니버설 스튜디오 재팬", "뭐 하지", "공식 상품", 18, 42, "8만~14만원", "반복 근거가 많아 대표 경험으로 노출하고, 패스 포함 여부를 명확히 분리해야 한다.", 1, 0, 0),
    ("harukas", "osaka", "아베노 하루카스 300", "뭐 하지", "공식 상품", 7, 13, "1만~3만원", "독립 전망대라 단독 입장권 비교가 중심이고, 패스·투어는 대체 이용 방식으로 붙인다.", 1, 0, 0),
    ("umeda-sky", "osaka", "우메다 스카이빌딩 공중정원", "뭐 하지", "공식 상품", 6, 12, "1만~3만원", "전망대 계열 경험으로 하루카스와 비교가 가능해 전망대 선택 피로를 줄일 수 있다.", 1, 0, 0),
    ("osaka-castle", "osaka", "오사카성 천수각", "뭐 하지", "공식 상품", 5, 11, "무료~2만원", "역사·도보·공원 동선을 함께 묶을 수 있는 대표 공식 자산이다.", 1, 0, 0),
    ("hep-five", "osaka", "헵파이브 대관람차", "뭐 하지", "공식 상품", 3, 7, "1만원 내외", "도심 야경과 짧은 체류 경험으로 숨은 선택지에 가깝다.", 0, 1, 0),
    ("dotonbori", "osaka", "도톤보리", "뭐 하지", "지역 공식 자산", 2, 8, "무료", "장소 앵커를 먼저 고르게 하고, 야간 산책·스냅·먹거리 상품은 선택 이후의 이용 방식으로 붙인다.", 1, 0, 1),
    ("tsutenkaku", "osaka", "츠텐카쿠", "뭐 하지", "지역 공식 자산", 2, 7, "1만~3만원", "신세카이와 쿠시카츠 동선을 함께 만드는 레트로 전망 앵커다.", 0, 1, 1),
    ("shinsekai", "osaka", "신세카이", "뭐 하지", "지역 공식 자산", 1, 7, "무료~3만원", "오사카다운 거리 분위기와 먹거리 선택을 동시에 보여주는 장소 앵커다.", 0, 1, 1),
    ("kaiyukan", "osaka", "가이유칸", "뭐 하지", "공식 상품", 4, 9, "2만~5만원", "베이 에어리어에서 가족/실내 대안으로 강한 시설 앵커다.", 1, 0, 0),
    ("tempozan", "osaka", "덴포잔", "뭐 하지", "지역 공식 자산", 2, 6, "무료~3만원", "오사카항·가이유칸·대관람차를 연결하는 베이 에어리어 앵커다.", 0, 1, 1),
    ("sumiyoshi-taisha", "osaka", "스미요시타이샤", "뭐 하지", "지역 공식 자산", 1, 5, "무료~1만원", "중심 관광지와 다른 신사/로컬 분위기를 보여주는 숨은 장소 앵커다.", 0, 1, 1),
    ("nakanoshima", "osaka", "나카노시마", "뭐 하지", "지역 공식 자산", 1, 5, "무료", "강변 산책·카페·미술관 후보를 묶는 느슨한 도심 휴식 앵커다.", 0, 1, 1),
    ("shinsaibashi", "osaka", "신사이바시", "뭐 하지", "지역 공식 자산", 1, 6, "무료~쇼핑별도", "난바·도톤보리와 이어지는 쇼핑/거리 산책 앵커다.", 0, 1, 1),
    ("amerika-mura", "osaka", "아메리카무라", "뭐 하지", "지역 공식 자산", 1, 5, "무료~쇼핑별도", "젊은 거리 분위기와 카페/편집숍 탐색을 보여주는 선택지다.", 0, 1, 1),
    ("okonomiyaki", "osaka", "오코노미야키", "뭐 먹지", "지역 공식 자산", 2, 5, "1만~4만원", "음식 앵커를 먼저 고르게 하고, 모던야키·미식 투어·식당 후보는 하위 방식으로 붙인다.", 0, 1, 1),
    ("takoyaki", "osaka", "타코야키", "뭐 먹지", "지역 공식 자산", 2, 7, "5천~2만원", "도톤보리·난바 거리 동선에서 가볍게 선택하는 대표 먹거리 앵커다.", 1, 0, 1),
    ("kushikatsu", "osaka", "쿠시카츠", "뭐 먹지", "지역 공식 자산", 2, 6, "1만~4만원", "신세카이·츠텐카쿠와 결합되는 오사카 로컬 먹거리 앵커다.", 0, 1, 1),
    ("ramen-osaka", "osaka", "오사카 라멘", "뭐 먹지", "지역 공식 자산", 1, 4, "1만~2만원", "밤 일정 이후 짧게 붙일 수 있는 식사 후보로 먹거리 폭을 넓힌다.", 0, 1, 1),
    ("kuromon", "osaka", "구로몬시장 먹거리", "뭐 먹지", "지역 공식 자산", 1, 4, "1만~5만원", "시장형 먹거리 경험은 상품보다 공식 자산과 지도 앵커로 보여주는 편이 자연스럽다.", 0, 1, 1),
    ("namba-station", "osaka", "난바역", "도시 내 이동", "지역 공식 자산", 1, 3, "교통비 별도", "도톤보리·구로몬시장·숙소 후보를 연결하는 도시 내 이동 기준점이다.", 0, 1, 1),
    ("kansai-airport", "osaka", "간사이 국제공항", "도시 내 이동", "지역 공식 자산", 1, 4, "공항 이동비 별도", "오사카 여행의 입출국 앵커로 난바·우메다 숙소 후보와 연결한다.", 0, 0, 1),
    ("shin-osaka-station", "osaka", "신오사카역", "도시 내 이동", "지역 공식 자산", 1, 4, "교통비 별도", "교토·고베·나라 확장 일정과 오사카 시내를 잇는 광역 이동 앵커다.", 0, 0, 1),
    ("umeda-station", "osaka", "우메다역", "도시 내 이동", "지역 공식 자산", 1, 4, "지하철/철도비 별도", "우메다 스카이빌딩·헵파이브·우메다 숙소 후보를 묶는 북부 환승 앵커다.", 0, 1, 1),
    ("hommachi-station", "osaka", "혼마치역", "도시 내 이동", "지역 공식 자산", 1, 3, "지하철비 별도", "난바·우메다·오사카성을 잇는 지하철 환승 기준점이다.", 0, 1, 1),
    ("osakako-station", "osaka", "오사카코역", "도시 내 이동", "지역 공식 자산", 1, 3, "지하철비 별도", "오사카항·덴포잔 베이 에어리어 접근을 위한 지하철 앵커다.", 0, 1, 1),
    ("osaka-port", "osaka", "오사카항", "도시 내 이동", "지역 공식 자산", 1, 3, "교통비 별도", "덴포잔·베이 에어리어·크루즈성 이동을 묶는 항구 앵커다.", 0, 1, 1),
    # Fukuoka
    ("nakasu-yatai", "fukuoka", "나카스 야타이", "뭐 먹지", "지역 공식 자산", 1, 12, "1만~4만원", "공식 야타이 데이터셋으로 검증 가능한 야간 미식 대표 경험이다.", 1, 0, 1),
    ("tenjin-yatai", "fukuoka", "텐진 야타이", "뭐 먹지", "지역 공식 자산", 1, 10, "1만~4만원", "도심 숙소와 연결하기 좋은 야간 앵커라 짧은 여행 동선에 적합하다.", 1, 0, 1),
    ("tonkotsu-ramen", "fukuoka", "하카타 돈코츠 라멘", "뭐 먹지", "지역 공식 자산", 2, 9, "1만~2만원", "대표 음식이지만 특정 식당 추천보다 먹거리 경험 단위로 보여주는 편이 좋다.", 1, 0, 1),
    ("canal-city", "fukuoka", "캐널시티 하카타", "뭐 하지", "공식 상품", 3, 7, "무료~3만원", "쇼핑·공연·식사를 한 번에 묶는 도심형 경험으로 비 오는 날 대안이 된다.", 1, 0, 0),
    ("ohori-park", "fukuoka", "오호리공원 산책", "뭐 하지", "지역 공식 자산", 1, 6, "무료", "상품 연결은 약하지만 일정의 여백과 회복감을 주는 숨은 선택지다.", 0, 1, 1),
    ("dazaifu", "fukuoka", "다자이후", "뭐 하지", "공식 상품", 4, 8, "2만~8만원", "근교 장소 앵커를 먼저 보여주고, 반나절 투어·교통 직접 이동은 선택 이후의 이용 방식으로 비교한다.", 1, 0, 0),
    ("fukuoka-tower", "fukuoka", "후쿠오카 타워", "뭐 하지", "공식 상품", 3, 6, "1만~3만원", "야경·해변 동선과 결합하기 좋은 전망 경험이다.", 0, 1, 0),
    ("hakata-station", "fukuoka", "하카타역", "도시 내 이동", "지역 공식 자산", 1, 5, "교통비 별도", "공항·야타이·도심 관광지를 연결하는 핵심 시간표 기준점이다.", 0, 0, 1),
    ("fukuoka-airport", "fukuoka", "후쿠오카 공항", "도시 내 이동", "지역 공식 자산", 1, 4, "교통비 별도", "공항 접근성이 강한 도시라 타임라인 첫 이동 앵커로 중요하다.", 0, 0, 1),
    ("tenjin-station", "fukuoka", "텐진역", "도시 내 이동", "지역 공식 자산", 1, 4, "교통비 별도", "텐진 야타이·쇼핑·숙소 후보를 연결하는 도심 이동 앵커다.", 0, 1, 1),
    ("nakasu-kawabata-station", "fukuoka", "나카스카와바타역", "도시 내 이동", "지역 공식 자산", 1, 3, "지하철비 별도", "나카스 야타이·캐널시티·하카타항 사이 야간 동선을 줄이는 지하철 앵커다.", 0, 1, 1),
    ("ohori-koen-station", "fukuoka", "오호리공원역", "도시 내 이동", "지역 공식 자산", 1, 3, "지하철비 별도", "오호리공원과 후쿠오카 타워 방향을 잇는 서쪽 지하철 앵커다.", 0, 1, 1),
    ("hakata-port", "fukuoka", "하카타항", "도시 내 이동", "지역 공식 자산", 1, 3, "항구 이동비 별도", "여객터미널·베이사이드·도심 야간 동선을 연결하는 항구 앵커다.", 0, 1, 1),
    # Busan
    ("haeundae", "busan", "해운대", "뭐 하지", "지역 공식 자산", 5, 11, "무료~2만원", "해안 장소 앵커를 먼저 보여주고, 동백섬·스냅·요트·숙소 선택은 하위 방식으로 연결한다.", 1, 0, 0),
    ("gwangalli-night", "busan", "광안리", "뭐 하지", "공식 상품", 4, 9, "무료~5만원", "장소 앵커로 먼저 보여주고, 야경·요트·스냅 상품은 선택 이후의 이용 방식으로 붙인다.", 1, 0, 0),
    ("gamcheon", "busan", "감천문화마을", "뭐 하지", "공식 상품", 3, 8, "무료~4만원", "스냅·도보·스토리 콘텐츠로 묶기 좋은 대표 경험이다.", 1, 0, 0),
    ("huinnyeoul", "busan", "흰여울문화마을", "뭐 하지", "지역 공식 자산", 2, 6, "무료~3만원", "대표 명소보다는 감성형 숨은 선택지로 보여주면 선택 폭이 넓어진다.", 0, 1, 1),
    ("gukje", "busan", "국제시장", "뭐 먹지", "지역 공식 자산", 2, 5, "1만~3만원", "시장 앵커를 먼저 고르게 하고, 돼지국밥·씨앗호떡 같은 먹거리 후보는 하위 선택지로 붙인다.", 0, 1, 1),
    ("jagalchi", "busan", "자갈치시장", "뭐 먹지", "지역 공식 자산", 2, 5, "2만~6만원", "시장 앵커를 먼저 고르게 하고, 해산물 식사·구도심 코스는 선택 이후의 방식으로 비교한다.", 0, 1, 1),
    ("blueline", "busan", "해운대 블루라인파크", "뭐 하지", "공식 상품", 5, 10, "1만~3만원", "관광형 이동수단이면서 자체 경험이므로 교통 상품과 구분해 보여준다.", 1, 0, 0),
    ("gimhae-airport", "busan", "김해국제공항", "도시 내 이동", "지역 공식 자산", 1, 4, "공항 이동비 별도", "부산 여행의 입출국 앵커로 서면·해운대 숙소 후보와 연결한다.", 0, 0, 1),
    ("busan-station", "busan", "부산역", "도시 내 이동", "지역 공식 자산", 1, 5, "교통비 별도", "KTX·구도심·시장 동선의 시작점이다.", 0, 0, 1),
    ("seomyeon-station", "busan", "서면역", "도시 내 이동", "지역 공식 자산", 1, 4, "교통비 별도", "해운대와 구도심 사이를 잇는 도시 내 이동 기준점이다.", 0, 1, 1),
    ("haeundae-station", "busan", "해운대역", "도시 내 이동", "지역 공식 자산", 1, 4, "도시철도비 별도", "해운대·블루라인파크·해운대 숙소 후보를 잇는 도시철도 앵커다.", 0, 1, 1),
    ("gwangan-station", "busan", "광안역", "도시 내 이동", "지역 공식 자산", 1, 3, "도시철도비 별도", "광안리 야경과 서면·해운대 사이 이동을 보완하는 도시철도 앵커다.", 0, 1, 1),
    ("nampo-station", "busan", "남포역", "도시 내 이동", "지역 공식 자산", 1, 3, "도시철도비 별도", "국제시장·자갈치시장·부산항을 묶는 구도심 도시철도 앵커다.", 0, 1, 1),
    ("busan-port", "busan", "부산항", "도시 내 이동", "지역 공식 자산", 1, 3, "항구 이동비 별도", "국제여객터미널·부산역·구도심을 연결하는 항구 앵커다.", 0, 1, 1),
]


TAGS = {
    "usj": ["대표 경험", "많이 검증된 경험 TOP 5", "입장권 중심"],
    "harukas": ["전망대", "단독 입장권", "패스 대체"],
    "umeda-sky": ["전망대", "대표 경험", "도심 야경"],
    "osaka-castle": ["역사", "공식 자산", "도보"],
    "hep-five": ["숨은 선택지", "짧은 체류", "야경"],
    "dotonbori": ["대표 장소", "야간 산책 가능", "스토리 엔딩"],
    "tsutenkaku": ["레트로 전망", "신세카이", "숨은 선택지"],
    "shinsekai": ["거리 앵커", "로컬 분위기", "먹거리 연결"],
    "kaiyukan": ["실내", "가족", "베이 에어리어"],
    "tempozan": ["베이 에어리어", "대관람차", "항구 연결"],
    "sumiyoshi-taisha": ["신사", "로컬", "숨은 선택지"],
    "nakanoshima": ["강변", "산책", "카페"],
    "shinsaibashi": ["쇼핑", "거리 산책", "난바 연결"],
    "amerika-mura": ["거리 문화", "카페", "편집숍"],
    "okonomiyaki": ["먹거리", "숨은 선택지", "콘텐츠 후보"],
    "takoyaki": ["대표 음식", "거리 먹거리", "도톤보리"],
    "kushikatsu": ["로컬 음식", "신세카이", "저녁 후보"],
    "ramen-osaka": ["먹거리", "야식", "짧은 식사"],
    "kuromon": ["먹거리", "시장", "지도 앵커"],
    "namba-station": ["역 접근", "도시 내 이동", "일정 최적화"],
    "kansai-airport": ["공항 앵커", "입출국", "숙소 후보 연결"],
    "shin-osaka-station": ["역 앵커", "광역 이동", "신칸센"],
    "umeda-station": ["지하철/철도", "환승", "우메다"],
    "hommachi-station": ["지하철", "환승", "중간 거점"],
    "osakako-station": ["지하철", "베이 에어리어", "항구 접근"],
    "osaka-port": ["항구 앵커", "베이 에어리어", "도시 내 이동"],
    "nakasu-yatai": ["먹거리", "공식 야타이", "야간 코스"],
    "tenjin-yatai": ["먹거리", "도심 야타이", "야간 앵커"],
    "tonkotsu-ramen": ["대표 음식", "짧은 식사", "콘텐츠 후보"],
    "canal-city": ["쇼핑", "비 오는 날", "도심형"],
    "ohori-park": ["숨은 선택지", "산책", "무료"],
    "dazaifu": ["대표 장소", "근교", "반나절 가능"],
    "fukuoka-tower": ["전망", "야경", "해변 동선"],
    "hakata-station": ["역 앵커", "도시 내 이동", "시간표"],
    "fukuoka-airport": ["공항 앵커", "도심 접근", "도시 내 이동"],
    "tenjin-station": ["역 앵커", "도심 이동", "야간 동선"],
    "nakasu-kawabata-station": ["지하철", "나카스", "야간 동선"],
    "ohori-koen-station": ["지하철", "공원", "서쪽 동선"],
    "hakata-port": ["항구 앵커", "베이사이드", "도시 내 이동"],
    "haeundae": ["대표 경험", "해안", "숙소 후보 연결"],
    "gwangalli-night": ["야경", "스토리 엔딩", "공유 강함"],
    "gamcheon": ["대표 경험", "스냅", "도보"],
    "huinnyeoul": ["숨은 선택지", "해안 마을", "카페"],
    "gukje": ["먹거리", "구도심", "콘텐츠 후보"],
    "jagalchi": ["먹거리", "시장", "해산물"],
    "blueline": ["관광형 이동", "해안", "입장권"],
    "gimhae-airport": ["공항 앵커", "입출국", "숙소 후보 연결"],
    "busan-station": ["역 앵커", "구도심", "KTX"],
    "seomyeon-station": ["역 앵커", "중심지", "도시 내 이동"],
    "haeundae-station": ["도시철도", "해운대", "숙소 후보 연결"],
    "gwangan-station": ["도시철도", "광안리", "야간 동선"],
    "nampo-station": ["도시철도", "구도심", "시장 접근"],
    "busan-port": ["항구 앵커", "국제여객터미널", "구도심"],
}


def methods(*values: str) -> list[tuple[str, str, int]]:
    method_types = ["primary", "alternative", "check", "url"]
    return [(value, method_types[index] if index < len(method_types) else "alternative", 1 if index == 0 else 0) for index, value in enumerate(values)]


METHODS = {
    "usj": methods("스튜디오 입장권", "익스프레스 패스", "닌텐도 월드 포함 여부 확인", "공식 상품 URL 비교"),
    "harukas": methods("단독 입장권", "오사카 패스 포함 여부", "하루카스 방문이 명시된 투어", "날짜별 예약 가능 여부"),
    "umeda-sky": methods("단독 입장권", "패스 포함 여부", "야경 시간대 비교", "공식 상품 URL 비교"),
    "osaka-castle": methods("단독 입장권", "도보 코스", "패스 포함 여부", "공식 자산 확인"),
    "hep-five": methods("단독 탑승권", "도심 야경 코스", "패스 대체", "짧은 일정 후보"),
    "dotonbori": methods("무료 산책", "스냅/야경 투어", "먹거리 지도", "스토리 코스"),
    "tsutenkaku": methods("단독 입장권", "신세카이 동선", "쿠시카츠 결합", "야경 시간대 비교"),
    "shinsekai": methods("무료 산책", "쿠시카츠 결합", "츠텐카쿠 연계", "저녁 거리 코스"),
    "kaiyukan": methods("단독 입장권", "덴포잔 연계", "실내 대안", "날짜별 예약 가능 여부"),
    "tempozan": methods("무료 산책", "가이유칸 연계", "오사카항 연결", "대관람차 후보"),
    "sumiyoshi-taisha": methods("무료 방문", "로컬 신사 코스", "도시철도 이동", "혼잡 낮은 시간대"),
    "nakanoshima": methods("강변 산책", "카페 결합", "미술관 후보", "비예약 여백 코스"),
    "shinsaibashi": methods("쇼핑 거리 산책", "도톤보리 연결", "카페 후보", "비예약 코스"),
    "amerika-mura": methods("거리 문화 산책", "카페/편집숍", "신사이바시 연결", "짧은 체류 후보"),
    "okonomiyaki": methods("미식 투어", "지역 식당 후보", "지도형 콘텐츠", "예약 상품 부족 표시"),
    "takoyaki": methods("거리 먹거리", "도톤보리 결합", "난바 야식", "예약 불필요 후보"),
    "kushikatsu": methods("신세카이 식사", "로컬 술집 후보", "츠텐카쿠 결합", "저녁 시간대 추천"),
    "ramen-osaka": methods("야식 후보", "난바/우메다 식사", "짧은 식사", "예약 불필요 후보"),
    "kuromon": methods("시장 산책", "미식 지도", "오전 코스", "상품화 후보"),
    "namba-station": methods("역 접근성 비교", "도보/지하철 이동", "짐 보관 후보", "동선 병목 확인"),
    "kansai-airport": methods("공항→난바 철도 이동", "공항→우메다 철도 이동", "라피트/JR 비교", "도착시간 기준 타임라인"),
    "shin-osaka-station": methods("신칸센/광역 이동", "교토·고베 연계", "시내 지하철 환승", "짐 보관 후보"),
    "umeda-station": methods("우메다 환승", "스카이빌딩 접근", "헵파이브 접근", "우메다 숙소 후보 연결"),
    "hommachi-station": methods("미도스지선 환승", "주오선 환승", "난바↔우메다 중간 이동", "오사카성 방향 이동"),
    "osakako-station": methods("베이 에어리어 접근", "오사카항 연결", "덴포잔 방향 이동", "도심 복귀 동선"),
    "osaka-port": methods("베이 에어리어 이동", "덴포잔 연계", "지하철 이동", "크루즈/항구 동선 후보"),
    "nakasu-yatai": methods("공식 야타이 데이터", "야간 미식 코스", "지도 앵커", "상품화 후보"),
    "tenjin-yatai": methods("공식 야타이 데이터", "도심 야식", "지도 앵커", "상품화 후보"),
    "tonkotsu-ramen": methods("대표 음식 경험", "라멘 지도", "짧은 식사", "상품화 후보"),
    "canal-city": methods("도심 방문", "공연/쇼핑 결합", "비 오는 날 대안", "공식 상품 URL 비교"),
    "ohori-park": methods("무료 산책", "오전 회복 코스", "카페 결합", "공식 자산 확인"),
    "dazaifu": methods("반나절 투어", "교통 직접 이동", "가이드 투어", "날짜별 예약 가능 여부"),
    "fukuoka-tower": methods("단독 입장권", "야경 시간대", "해변 코스", "공식 상품 URL 비교"),
    "hakata-station": methods("역 앵커", "공항 연결", "도심 이동", "타임라인 기준점"),
    "fukuoka-airport": methods("공항 앵커", "도심 이동", "출발/도착 시간", "타임라인 기준점"),
    "tenjin-station": methods("도심 환승", "야타이 접근", "쇼핑 동선", "숙소 후보 연결"),
    "nakasu-kawabata-station": methods("나카스 접근", "캐널시티 접근", "하카타·텐진 사이 이동", "야간 복귀 동선"),
    "ohori-koen-station": methods("오호리공원 접근", "후쿠오카 타워 방향 이동", "오전 산책 동선", "도심 복귀 동선"),
    "hakata-port": methods("항구 앵커", "베이사이드 이동", "하카타역 연결", "여객터미널 기준점"),
    "haeundae": methods("무료 산책", "스냅/요트 결합", "해변 동선", "공식 자산 확인"),
    "gwangalli-night": methods("야경 투어", "요트/스냅 결합", "무료 관람", "저녁 시간대 추천"),
    "gamcheon": methods("도보/스냅 투어", "자유 방문", "카페 코스", "공식 상품 URL 비교"),
    "huinnyeoul": methods("무료 산책", "카페 지도", "스냅 후보", "상품화 후보"),
    "gukje": methods("미식 지도", "시장 동선", "지역 추천 식당", "상품 부족 표시"),
    "jagalchi": methods("시장 방문", "해산물 식사", "구도심 코스", "공식 자산 확인"),
    "blueline": methods("탑승권", "해안 코스", "해운대 연계", "날짜별 예약 가능 여부"),
    "gimhae-airport": methods("공항→서면 경전철 이동", "공항→해운대 도시철도 이동", "경전철/도시철도 환승", "도착시간 기준 타임라인"),
    "busan-station": methods("역 앵커", "구도심 이동", "시장 접근", "타임라인 기준점"),
    "seomyeon-station": methods("환승 기준점", "서면 중심 동선", "야간 이동", "숙소 후보 연결"),
    "haeundae-station": methods("해운대 접근", "블루라인파크 연계", "해운대 숙소 후보 연결", "서면 방향 이동"),
    "gwangan-station": methods("광안리 접근", "야경 동선", "서면↔해운대 중간 이동", "저녁 복귀 동선"),
    "nampo-station": methods("국제시장 접근", "자갈치시장 접근", "부산항 연결", "구도심 도보 동선"),
    "busan-port": methods("항구 앵커", "부산역 연결", "국제여객터미널", "구도심 동선"),
}


OFFICIAL_SOURCES = [
    ("src-mrt-mcp", "공통", "osaka", "MyRealTrip MCP", "MCP", "https://mcp-servers.myrealtrip.com/mcp", "Partner/API terms", 0, "on demand", "2026-07-17", 1),
    ("src-osaka-mapnavi", "일본", "osaka", "Osaka City Map Navi Open Data", "CSV", "https://www.city.osaka.lg.jp/toshikeikaku/page/0000250227.html", "CC BY", 0, "as updated", "2026-07-17", 1),
    ("src-fukuoka-yatai", "일본", "fukuoka", "Fukuoka Yatai CKAN/BODIK Dataset", "CKAN_DATASET", "https://data.bodik.jp/dataset/401307_yataiopendata", "CC BY", 0, "as updated", "2026-07-17", 1),
    ("src-busan-seed", "한국", "busan", "Busan Official Tourism/Food Seed", "MANUAL_SEED", "https://www.visitbusan.net", "official reference", 0, "manual", "2026-07-17", 1),
]


OFFICIAL_ASSETS = [
    ("asset-harukas", "osaka", "src-osaka-mapnavi", "ATTRACTION", "아베노 하루카스 300", "전망대", "大阪市阿倍野区", 34.6459, 135.5135, "https://www.abenoharukas-300.jp/", "오사카 전망대 경험의 단독 입장권 기준점", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-umeda-sky", "osaka", "src-osaka-mapnavi", "ATTRACTION", "우메다 스카이빌딩 공중정원", "전망대", "大阪市北区", 34.7053, 135.4906, "https://www.skybldg.co.jp/", "도심 야경과 전망 경험 비교 자산", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-osaka-castle", "osaka", "src-osaka-mapnavi", "ATTRACTION", "오사카성 천수각", "역사", "大阪市中央区", 34.6873, 135.5262, "https://www.osakacastle.net/", "역사·공원·도보 동선의 대표 앵커", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-dotonbori", "osaka", "src-osaka-mapnavi", "ATTRACTION", "도톤보리", "야간 산책", "大阪市中央区", 34.6687, 135.5013, "https://osaka-info.jp/", "야간 산책과 사진 스토리의 대표 구간", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-tsutenkaku", "osaka", "src-osaka-mapnavi", "ATTRACTION", "츠텐카쿠", "전망/레트로", "大阪市浪速区", 34.6525, 135.5063, "https://www.tsutenkaku.co.jp/", "신세카이와 결합되는 레트로 전망 앵커", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-shinsekai", "osaka", "src-osaka-mapnavi", "ATTRACTION", "신세카이", "거리", "大阪市浪速区", 34.6526, 135.5062, "https://osaka-info.jp/", "쿠시카츠와 거리 산책을 묶는 로컬 장소 앵커", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-kaiyukan", "osaka", "src-osaka-mapnavi", "ATTRACTION", "가이유칸", "수족관", "大阪市港区", 34.6545, 135.4289, "https://www.kaiyukan.com/", "베이 에어리어의 실내 시설 앵커", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-tempozan", "osaka", "src-osaka-mapnavi", "ATTRACTION", "덴포잔", "베이 에어리어", "大阪市港区", 34.6557, 135.4305, "https://osaka-info.jp/", "오사카항·가이유칸과 연결되는 베이 에어리어 앵커", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-sumiyoshi-taisha", "osaka", "src-osaka-mapnavi", "ATTRACTION", "스미요시타이샤", "신사", "大阪市住吉区", 34.6127, 135.4938, "https://www.sumiyoshitaisha.net/", "로컬 신사 분위기를 보여주는 숨은 장소 앵커", 1, "OFFICIAL_FACILITY", "2026-07-17"),
    ("asset-nakanoshima", "osaka", "src-osaka-mapnavi", "ATTRACTION", "나카노시마", "강변", "大阪市北区", 34.6914, 135.5018, "https://osaka-info.jp/", "강변 산책과 카페/미술관 후보를 묶는 도심 휴식 앵커", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-shinsaibashi", "osaka", "src-osaka-mapnavi", "ATTRACTION", "신사이바시", "쇼핑 거리", "大阪市中央区", 34.6745, 135.5004, "https://osaka-info.jp/", "도톤보리·난바와 이어지는 쇼핑/거리 산책 앵커", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-amerika-mura", "osaka", "src-osaka-mapnavi", "ATTRACTION", "아메리카무라", "거리 문화", "大阪市中央区", 34.6720, 135.4975, "https://osaka-info.jp/", "카페·편집숍·거리 문화를 보여주는 선택지", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-namba", "osaka", "src-osaka-mapnavi", "TRANSIT_ANCHOR", "난바역", "도시 내 이동", "大阪市中央区", 34.6662, 135.5018, None, "도톤보리·구로몬시장·시내 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-kansai-airport", "osaka", "src-osaka-mapnavi", "AIRPORT", "간사이 국제공항", "공항", "大阪府泉佐野市", 34.4347, 135.2442, "https://www.kansai-airport.or.jp/", "오사카 입출국과 시내 이동의 시작점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-shin-osaka", "osaka", "src-osaka-mapnavi", "STATION", "신오사카역", "역", "大阪市淀川区", 34.7335, 135.5001, None, "신칸센·광역 이동과 시내 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-umeda-station", "osaka", "src-osaka-mapnavi", "SUBWAY_STATION", "우메다역", "지하철/철도", "大阪市北区", 34.7048, 135.4980, None, "우메다 관광지와 북부 숙소 후보를 잇는 환승 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-hommachi-station", "osaka", "src-osaka-mapnavi", "SUBWAY_STATION", "혼마치역", "지하철", "大阪市中央区", 34.6814, 135.5016, None, "난바·우메다·오사카성 사이의 지하철 환승 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-osakako-station", "osaka", "src-osaka-mapnavi", "SUBWAY_STATION", "오사카코역", "지하철", "大阪市港区", 34.6545, 135.4344, None, "오사카항과 베이 에어리어 접근 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-osaka-port", "osaka", "src-osaka-mapnavi", "PORT", "오사카항", "항구", "大阪市港区", 34.6539, 135.4294, None, "베이 에어리어와 항구형 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-nakasu-yatai", "fukuoka", "src-fukuoka-yatai", "FOOD_STALL", "나카스 야타이", "야타이", "福岡市博多区中洲", 33.5914, 130.4063, "https://yokanavi.com/yatai/", "후쿠오카 야간 미식 대표 공식 자산", 1, "FUKUOKA_CITY_YATAI", "2026-07-17"),
    ("asset-tenjin-yatai", "fukuoka", "src-fukuoka-yatai", "FOOD_STALL", "텐진 야타이", "야타이", "福岡市中央区天神", 33.5903, 130.3991, "https://yokanavi.com/yatai/", "숙소와 연결하기 좋은 도심 야타이 구역", 1, "FUKUOKA_CITY_YATAI", "2026-07-17"),
    ("asset-hakata-station", "fukuoka", "src-fukuoka-yatai", "TRANSIT_ANCHOR", "하카타역", "역 앵커", "福岡市博多区博多駅中央街", 33.5902, 130.4207, None, "공항·도심 관광지 연결의 핵심 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-fukuoka-airport", "fukuoka", "src-fukuoka-yatai", "TRANSIT_ANCHOR", "후쿠오카 공항", "공항 앵커", "福岡市博多区", 33.5859, 130.4507, None, "도심 접근성이 강한 일정 시작점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-tenjin-station", "fukuoka", "src-fukuoka-yatai", "STATION", "텐진역", "역", "福岡市中央区天神", 33.5913, 130.3989, None, "야타이·쇼핑·도심 숙소 후보를 잇는 이동 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-nakasu-kawabata-station", "fukuoka", "src-fukuoka-yatai", "SUBWAY_STATION", "나카스카와바타역", "지하철", "福岡市博多区上川端町", 33.5942, 130.4061, None, "나카스 야타이·캐널시티·하카타항 동선을 잇는 지하철 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-ohori-koen-station", "fukuoka", "src-fukuoka-yatai", "SUBWAY_STATION", "오호리공원역", "지하철", "福岡市中央区大手門", 33.5907, 130.3797, None, "오호리공원과 서쪽 해변 방향 이동 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-hakata-port", "fukuoka", "src-fukuoka-yatai", "PORT", "하카타항", "항구", "福岡市博多区築港本町", 33.6064, 130.4017, None, "여객터미널과 베이사이드 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-dazaifu", "fukuoka", "src-fukuoka-yatai", "ATTRACTION", "다자이후", "근교", "太宰府市", 33.5198, 130.5347, "https://www.dazaifutenmangu.or.jp/", "후쿠오카 반나절 근교 경험", 1, "OFFICIAL_AREA", "2026-07-17"),
    ("asset-haeundae", "busan", "src-busan-seed", "ATTRACTION", "해운대", "해안", "부산광역시 해운대구", 35.1587, 129.1604, "https://www.visitbusan.net/", "해안 산책과 액티비티 동선의 대표 앵커", 1, "OFFICIAL_TOURISM", "2026-07-17"),
    ("asset-gwangalli", "busan", "src-busan-seed", "ATTRACTION", "광안리", "야경", "부산광역시 수영구", 35.1532, 129.1187, "https://www.visitbusan.net/", "부산 야경과 공유 스토리의 대표 경험", 1, "OFFICIAL_TOURISM", "2026-07-17"),
    ("asset-gukje", "busan", "src-busan-seed", "MARKET", "국제시장", "시장", "부산광역시 중구", 35.1027, 129.0287, "https://www.visitbusan.net/", "구도심 미식/시장 동선의 기준점", 1, "OFFICIAL_TOURISM", "2026-07-17"),
    ("asset-jagalchi", "busan", "src-busan-seed", "MARKET", "자갈치시장", "시장", "부산광역시 중구", 35.0967, 129.0305, "https://www.visitbusan.net/", "해산물 먹거리와 항구 경험의 공식 자산", 1, "OFFICIAL_TOURISM", "2026-07-17"),
    ("asset-gimhae-airport", "busan", "src-busan-seed", "AIRPORT", "김해국제공항", "공항", "부산광역시 강서구", 35.1796, 128.9382, "https://www.airport.co.kr/gimhae/", "부산 입출국과 시내 이동의 시작점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-busan-station", "busan", "src-busan-seed", "STATION", "부산역", "역", "부산광역시 동구", 35.1152, 129.0415, None, "KTX·구도심·항구 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-seomyeon-station", "busan", "src-busan-seed", "STATION", "서면역", "역", "부산광역시 부산진구", 35.1579, 129.0592, None, "해운대와 구도심 사이 환승 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-haeundae-station", "busan", "src-busan-seed", "SUBWAY_STATION", "해운대역", "도시철도", "부산광역시 해운대구", 35.1630, 129.1580, None, "해운대·블루라인파크·해운대 숙소 후보의 도시철도 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-gwangan-station", "busan", "src-busan-seed", "SUBWAY_STATION", "광안역", "도시철도", "부산광역시 수영구", 35.1578, 129.1134, None, "광안리 야경과 서면·해운대 이동을 보완하는 도시철도 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-nampo-station", "busan", "src-busan-seed", "SUBWAY_STATION", "남포역", "도시철도", "부산광역시 중구", 35.0979, 129.0347, None, "국제시장·자갈치시장·부산항을 잇는 구도심 도시철도 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
    ("asset-busan-port", "busan", "src-busan-seed", "PORT", "부산항", "항구", "부산광역시 동구", 35.1176, 129.0486, None, "국제여객터미널·부산역·구도심 이동의 기준점", 1, "TRANSIT_ANCHOR", "2026-07-17"),
]


SOURCE_LINKS = [
    ("harukas", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-harukas", 0.95, "공식 전망대 자산과 MCP 입장권 경험이 일치"),
    ("umeda-sky", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-umeda-sky", 0.95, "공식 전망대 자산과 MCP 입장권 경험이 일치"),
    ("osaka-castle", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-osaka-castle", 0.9, "오사카 역사 명소와 입장권 경험 매칭"),
    ("dotonbori", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-dotonbori", 0.8, "야간 산책 공식 자산"),
    ("tsutenkaku", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-tsutenkaku", 0.82, "레트로 전망 공식 자산"),
    ("shinsekai", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-shinsekai", 0.8, "신세카이 거리 공식 자산"),
    ("kaiyukan", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-kaiyukan", 0.9, "가이유칸 공식 시설 자산"),
    ("tempozan", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-tempozan", 0.82, "덴포잔 베이 에어리어 공식 자산"),
    ("sumiyoshi-taisha", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-sumiyoshi-taisha", 0.8, "스미요시타이샤 공식 시설 자산"),
    ("nakanoshima", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-nakanoshima", 0.78, "나카노시마 강변 공식 자산"),
    ("shinsaibashi", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-shinsaibashi", 0.78, "신사이바시 쇼핑 거리 공식 자산"),
    ("amerika-mura", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-amerika-mura", 0.76, "아메리카무라 거리 문화 공식 자산"),
    ("namba-station", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-namba", 0.75, "도시 내 이동 앵커"),
    ("kansai-airport", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-kansai-airport", 0.85, "공항 이동 앵커"),
    ("shin-osaka-station", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-shin-osaka", 0.82, "광역 역 이동 앵커"),
    ("umeda-station", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-umeda-station", 0.8, "지하철/철도 이동 앵커"),
    ("hommachi-station", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-hommachi-station", 0.78, "지하철 환승 앵커"),
    ("osakako-station", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-osakako-station", 0.78, "베이 에어리어 지하철 앵커"),
    ("osaka-port", "OFFICIAL_ASSET", "src-osaka-mapnavi", "asset-osaka-port", 0.78, "항구 이동 앵커"),
    ("nakasu-yatai", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-nakasu-yatai", 0.92, "후쿠오카 야타이 공식 데이터셋"),
    ("tenjin-yatai", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-tenjin-yatai", 0.92, "후쿠오카 야타이 공식 데이터셋"),
    ("hakata-station", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-hakata-station", 0.8, "타임라인 역 앵커"),
    ("fukuoka-airport", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-fukuoka-airport", 0.8, "타임라인 공항 앵커"),
    ("tenjin-station", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-tenjin-station", 0.78, "도심 역 이동 앵커"),
    ("nakasu-kawabata-station", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-nakasu-kawabata-station", 0.78, "지하철 야간 동선 앵커"),
    ("ohori-koen-station", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-ohori-koen-station", 0.78, "지하철 공원 동선 앵커"),
    ("hakata-port", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-hakata-port", 0.78, "항구 이동 앵커"),
    ("dazaifu", "OFFICIAL_ASSET", "src-fukuoka-yatai", "asset-dazaifu", 0.82, "근교 반나절 경험"),
    ("haeundae", "OFFICIAL_ASSET", "src-busan-seed", "asset-haeundae", 0.9, "부산 해안 대표 경험"),
    ("gwangalli-night", "OFFICIAL_ASSET", "src-busan-seed", "asset-gwangalli", 0.9, "부산 야경 대표 경험"),
    ("gukje", "OFFICIAL_ASSET", "src-busan-seed", "asset-gukje", 0.85, "구도심 시장/미식 경험"),
    ("jagalchi", "OFFICIAL_ASSET", "src-busan-seed", "asset-jagalchi", 0.85, "해산물 시장 경험"),
    ("gimhae-airport", "OFFICIAL_ASSET", "src-busan-seed", "asset-gimhae-airport", 0.85, "공항 이동 앵커"),
    ("busan-station", "OFFICIAL_ASSET", "src-busan-seed", "asset-busan-station", 0.82, "KTX 역 이동 앵커"),
    ("seomyeon-station", "OFFICIAL_ASSET", "src-busan-seed", "asset-seomyeon-station", 0.78, "도심 환승 앵커"),
    ("haeundae-station", "OFFICIAL_ASSET", "src-busan-seed", "asset-haeundae-station", 0.8, "해운대 도시철도 앵커"),
    ("gwangan-station", "OFFICIAL_ASSET", "src-busan-seed", "asset-gwangan-station", 0.78, "광안리 도시철도 앵커"),
    ("nampo-station", "OFFICIAL_ASSET", "src-busan-seed", "asset-nampo-station", 0.78, "구도심 도시철도 앵커"),
    ("busan-port", "OFFICIAL_ASSET", "src-busan-seed", "asset-busan-port", 0.78, "항구 이동 앵커"),
]

ACCOMMODATION_CANDIDATES = [
    ("stay-osaka-namba-hotel", "osaka", "MCP_ACCOMMODATION", "src-mrt-mcp", "난바", "호텔", "도톤보리·구로몬시장 접근성이 좋아 첫 숙소 후보로 비교", "흡연층 분리/침구 후기 확인 필요", 1, "금연 객실 우선 확인", "침구 냄새 관련 후기 확인 필요", "12만~22만원", 6, "MCP 수집 예정"),
    ("stay-osaka-umeda-hotel", "osaka", "MCP_ACCOMMODATION", "src-mrt-mcp", "우메다", "호텔", "전망대·교통 환승 중심이라 도시 내 이동 피로가 낮음", "역세권 소음 후기 확인 필요", 1, "금연 객실 우선 확인", "최근 후기 확인 필요", "13만~24만원", 5, "MCP 수집 예정"),
    ("stay-fukuoka-hakata-hotel", "fukuoka", "MCP_ACCOMMODATION", "src-mrt-mcp", "하카타", "호텔", "공항·하카타역 접근성이 좋아 짧은 여행에 적합", "객실 크기/소음 후기 확인 필요", 1, "금연 객실 우선 확인", "침구 청결 후기 확인 필요", "9만~18만원", 5, "MCP 수집 예정"),
    ("stay-fukuoka-tenjin-hotel", "fukuoka", "MCP_ACCOMMODATION", "src-mrt-mcp", "텐진", "호텔", "야타이·쇼핑·도심 이동이 쉬워 야간형 일정에 적합", "번화가 소음 후기 확인 필요", 1, "금연 객실 우선 확인", "최근 후기 확인 필요", "10만~19만원", 4, "MCP 수집 예정"),
    ("stay-busan-haeundae-hotel", "busan", "MCP_ACCOMMODATION", "src-mrt-mcp", "해운대", "호텔/리조트", "해변·블루라인파크 중심 일정에 적합", "성수기 가격 급등/오션뷰 과금 확인 필요", 1, "금연 객실 우선 확인", "침구/습도 후기 확인 필요", "12만~28만원", 6, "MCP 수집 예정"),
    ("stay-busan-seomyeon-hotel", "busan", "MCP_ACCOMMODATION", "src-mrt-mcp", "서면", "호텔", "해운대와 구도심 사이 이동 균형이 좋아 다중 앵커 일정에 적합", "야간 유흥가 인접 여부 확인 필요", 1, "금연 객실 우선 확인", "최근 후기 확인 필요", "8만~16만원", 4, "MCP 수집 예정"),
]


TRIPS = [
    ("demo-osaka-trip", "osaka", "오사카에서 완성한 개인 여행", "개인 여행", "사진 없이 글로 대체", "2026-08-10", "2026-08-10", 1),
    ("demo-fukuoka-trip", "fukuoka", "후쿠오카 야타이 밤 산책", "개인 여행", "사진 유형만 선택", "2026-08-12", "2026-08-12", 1),
    ("demo-busan-trip", "busan", "부산 해안과 시장 하루", "단체 여행", "비공개 저장", "2026-08-14", "2026-08-14", 1),
]


TIMELINE_EVENTS = [
    ("tl-osaka-1", "demo-osaka-trip", "osaka", "kansai-airport", "AIRPORT_ARRIVAL", "간사이 국제공항 도착", "2026-08-10T10:00:00", "10:00", "INITIAL_RECORDED", 1, "GENERATED_SUGGESTION", 0),
    ("tl-osaka-2", "demo-osaka-trip", "osaka", "namba-station", "TRANSIT_OR_STAY", "난바역 이동 후 숙소 체크인 또는 짐 보관", "2026-08-10T12:00:00", "12:30", "TIME_SELECTED", 2, "SELECTED_ACCOMMODATION", 1),
    ("tl-osaka-3", "demo-osaka-trip", "osaka", "harukas", "EXPERIENCE_VISIT", "아베노 하루카스 300", "2026-08-10T15:00:00", "16:00", "TIME_SELECTED", 3, "SELECTED_EXPERIENCE", 1),
    ("tl-osaka-4", "demo-osaka-trip", "osaka", "okonomiyaki", "MEAL_OR_BREAK", "오코노미야키", "2026-08-10T18:00:00", "", "TIME_UNDECIDED", 4, "SELECTED_EXPERIENCE", 0),
    ("tl-fukuoka-1", "demo-fukuoka-trip", "fukuoka", "fukuoka-airport", "AIRPORT_ARRIVAL", "후쿠오카 공항 도착", "2026-08-12T11:00:00", "11:00", "INITIAL_RECORDED", 1, "GENERATED_SUGGESTION", 0),
    ("tl-fukuoka-2", "demo-fukuoka-trip", "fukuoka", "hakata-station", "STATION_ARRIVAL", "하카타역 이동", "2026-08-12T11:30:00", "11:40", "TIME_SELECTED", 2, "SELECTED_EXPERIENCE", 1),
    ("tl-fukuoka-3", "demo-fukuoka-trip", "fukuoka", "dazaifu", "EXPERIENCE_VISIT", "다자이후", "2026-08-12T14:00:00", "14:00", "TIME_SELECTED", 3, "SELECTED_EXPERIENCE", 1),
    ("tl-fukuoka-4", "demo-fukuoka-trip", "fukuoka", "nakasu-yatai", "MEAL_OR_BREAK", "나카스 야타이", "2026-08-12T20:00:00", "20:30", "TIME_SELECTED", 4, "SELECTED_EXPERIENCE", 1),
    ("tl-busan-1", "demo-busan-trip", "busan", "busan-station", "STATION_ARRIVAL", "부산역 도착", "2026-08-14T10:00:00", "10:00", "INITIAL_RECORDED", 1, "GENERATED_SUGGESTION", 0),
    ("tl-busan-2", "demo-busan-trip", "busan", "gukje", "MEAL_OR_BREAK", "국제시장", "2026-08-14T12:00:00", "", "TIME_UNDECIDED", 2, "SELECTED_EXPERIENCE", 0),
    ("tl-busan-3", "demo-busan-trip", "busan", "haeundae", "EXPERIENCE_VISIT", "해운대", "2026-08-14T16:00:00", "16:30", "TIME_SELECTED", 3, "SELECTED_EXPERIENCE", 1),
    ("tl-busan-4", "demo-busan-trip", "busan", "gwangalli-night", "EXPERIENCE_VISIT", "광안리", "2026-08-14T20:00:00", "20:00", "TIME_SELECTED", 4, "SELECTED_EXPERIENCE", 1),
]


def reset_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS trip_budget_estimates;
        DROP TABLE IF EXISTS trip_decisions;
        DROP TABLE IF EXISTS feedback;
        DROP TABLE IF EXISTS error_logs;
        DROP TABLE IF EXISTS funnel_metrics;
        DROP TABLE IF EXISTS event_logs;
        DROP TABLE IF EXISTS trip_timeline_events;
        DROP TABLE IF EXISTS stamps;
        DROP TABLE IF EXISTS trips;
        DROP TABLE IF EXISTS accommodation_candidates;
        DROP TABLE IF EXISTS generated_anchor_candidates;
        DROP TABLE IF EXISTS anchor_generation_runs;
        DROP TABLE IF EXISTS experience_source_links;
        DROP TABLE IF EXISTS official_assets;
        DROP TABLE IF EXISTS official_data_sources;
        DROP TABLE IF EXISTS purchase_methods;
        DROP TABLE IF EXISTS experience_tags;
        DROP TABLE IF EXISTS experiences;
        DROP TABLE IF EXISTS cities;
        """
    )
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def seed_db(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT INTO cities (id, country, name, positioning, demand_signal) VALUES (:id, :country, :name, :positioning, :demand_signal)",
        CITIES,
    )
    connection.executemany(
        """
        INSERT INTO experiences
        (id, city_id, title, category, evidence, products, repeats, price_band, business_hint, is_representative, is_hidden_choice, is_productization_candidate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        EXPERIENCES,
    )
    for experience_id, tags in TAGS.items():
        connection.executemany("INSERT INTO experience_tags (experience_id, tag) VALUES (?, ?)", [(experience_id, tag) for tag in tags])
    for experience_id, method_rows in METHODS.items():
        connection.executemany(
            "INSERT INTO purchase_methods (experience_id, method, method_type, is_primary) VALUES (?, ?, ?, ?)",
            [(experience_id, method, method_type, is_primary) for method, method_type, is_primary in method_rows],
        )
    connection.executemany(
        """
        INSERT INTO official_data_sources
        (id, country, city_id, source_name, source_type, base_url, license, requires_api_key, update_cycle, last_checked_at, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        OFFICIAL_SOURCES,
    )
    connection.executemany(
        """
        INSERT INTO official_assets
        (id, city_id, source_id, asset_type, name, category, address, lat, lng, official_url, description, is_certified, certification_type, last_collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        OFFICIAL_ASSETS,
    )
    connection.executemany(
        """
        INSERT INTO experience_source_links
        (experience_id, source_type, source_id, source_record_id, confidence, evidence_text)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        SOURCE_LINKS,
    )
    connection.executemany(
        """
        INSERT INTO accommodation_candidates
        (id, city_id, source_type, source_id, area_name, accommodation_type, decision_reason, risk_signal, breakfast_available, smoking_policy_signal, bedding_signal, price_band, product_count, collection_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ACCOMMODATION_CANDIDATES,
    )
    if GENERATED_ANCHORS_PATH.exists():
        generated = json.loads(GENERATED_ANCHORS_PATH.read_text(encoding="utf-8"))
        summary = generated["summary"]
        connection.execute(
            """
            INSERT INTO anchor_generation_runs
            (id, source_snapshot_path, generated_path, rule_version, total_records, accepted_candidates, review_candidates, rejected_candidates, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary["run_id"],
                summary["source_snapshot_path"],
                summary["generated_path"],
                summary["rule_version"],
                summary["total_records"],
                summary["accepted_candidates"],
                summary["review_candidates"],
                summary["rejected_candidates"],
                summary["created_at"],
            ),
        )
        connection.executemany(
            """
            INSERT INTO generated_anchor_candidates
            (id, run_id, city_id, source_type, source_record_id, raw_name, normalized_name, category, anchor_type, confidence, automation_status, reason, product_signal, official_signal, repeats_signal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    candidate["id"],
                    candidate["run_id"],
                    candidate["city_id"],
                    candidate["source_type"],
                    candidate["source_record_id"],
                    candidate["raw_name"],
                    candidate["normalized_name"],
                    candidate["category"],
                    candidate["anchor_type"],
                    candidate["confidence"],
                    candidate["automation_status"],
                    candidate["reason"],
                    candidate["product_signal"],
                    candidate["official_signal"],
                    candidate["repeats_signal"],
                )
                for candidate in generated["candidates"]
            ],
        )
    connection.executemany(
        "INSERT INTO trips (id, city_id, trip_title, travel_party_type, privacy_mode, start_date, end_date, story_generated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        TRIPS,
    )
    connection.executemany(
        """
        INSERT INTO trip_timeline_events
        (id, trip_id, city_id, experience_id, event_type, label, initial_recorded_at, user_selected_time, time_status, sequence_order, source_type, is_user_confirmed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        TIMELINE_EVENTS,
    )
    connection.executemany(
        "INSERT INTO stamps (trip_id, experience_id, stamp_status, photo_mode, memo_mode) VALUES (?, ?, ?, ?, ?)",
        [
            ("demo-osaka-trip", "harukas", "STAMPED", "TEXT_ONLY", "MEMO_SKIPPED"),
            ("demo-osaka-trip", "okonomiyaki", "PLANNED", "PHOTO_TYPE_ONLY", "TEXT_MEMO"),
            ("demo-fukuoka-trip", "nakasu-yatai", "STAMPED", "PHOTO_TYPE_ONLY", "TEXT_MEMO"),
            ("demo-fukuoka-trip", "dazaifu", "PLANNED", "TEXT_ONLY", "MEMO_SKIPPED"),
            ("demo-busan-trip", "haeundae", "STAMPED", "TEXT_ONLY", "TEXT_MEMO"),
            ("demo-busan-trip", "gwangalli-night", "PLANNED", "PRIVATE", "MEMO_SKIPPED"),
        ],
    )
    connection.executemany(
        "INSERT INTO funnel_metrics (city_id, step_name, started_count, completed_count, dropoff_count) VALUES (?, ?, ?, ?, ?)",
        [
            ("osaka", "city_view", 1284, 1284, 0),
            ("osaka", "experience_select", 1284, 746, 538),
            ("osaka", "timeline_adjust", 746, 392, 354),
            ("osaka", "story_generate", 392, 208, 184),
            ("fukuoka", "city_view", 812, 812, 0),
            ("fukuoka", "experience_select", 812, 438, 374),
            ("fukuoka", "timeline_adjust", 438, 244, 194),
            ("fukuoka", "story_generate", 244, 132, 112),
            ("busan", "city_view", 632, 632, 0),
            ("busan", "experience_select", 632, 338, 294),
            ("busan", "timeline_adjust", 338, 176, 162),
            ("busan", "story_generate", 176, 98, 78),
        ],
    )
    connection.executemany(
        "INSERT INTO trip_budget_estimates (trip_id, transport_cost, accommodation_cost, activity_cost, food_cost_range, source_type) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("demo-osaka-trip", 18000, 120000, 102000, "1만~4만원", "USER_INPUT_AND_PRODUCT_PRICE"),
            ("demo-fukuoka-trip", 9000, 98000, 54000, "1만~4만원", "USER_INPUT_AND_OFFICIAL_ASSET"),
            ("demo-busan-trip", 16000, 110000, 42000, "1만~6만원", "USER_INPUT_AND_PRODUCT_PRICE"),
        ],
    )
    connection.executemany(
        "INSERT INTO feedback (trip_id, experience_id, rating, recommend_intent, discomfort_type, skipped) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("demo-osaka-trip", "harukas", 5, "추천", None, 0),
            ("demo-osaka-trip", "okonomiyaki", None, None, None, 1),
            ("demo-fukuoka-trip", "nakasu-yatai", 5, "추천", None, 0),
            ("demo-fukuoka-trip", "ohori-park", None, None, None, 1),
            ("demo-busan-trip", "gwangalli-night", 5, "추천", None, 0),
            ("demo-busan-trip", "gukje", 4, "추천", "혼잡", 0),
        ],
    )
    connection.executemany(
        "INSERT INTO error_logs (city_id, step_name, error_type, user_safe_message, created_at) VALUES (?, ?, ?, ?, ?)",
        [
            ("fukuoka", "official_asset_fetch", "PUBLIC_DATASET_ONLY", "실시간 개점상태 없이 공개 야타이 기본정보만 사용합니다.", "2026-07-17T12:00:00"),
            ("osaka", "timeline", "TIME_UNDECIDED", "시간을 정하지 않아도 스토리를 만들 수 있습니다.", "2026-07-17T12:05:00"),
            ("busan", "product_match", "SEED_LIMITED", "1차 MVP에서는 공식 자산을 소량 seed로만 사용합니다.", "2026-07-17T12:10:00"),
        ],
    )
    connection.commit()


def export_json(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    cities = []
    order_sql = "CASE id WHEN 'osaka' THEN 1 WHEN 'fukuoka' THEN 2 WHEN 'busan' THEN 3 ELSE 99 END"
    for city in connection.execute(f"SELECT * FROM cities ORDER BY {order_sql}"):
        experiences = []
        for experience in connection.execute("SELECT * FROM experiences WHERE city_id = ? ORDER BY repeats DESC, products DESC", (city["id"],)):
            tags = [row["tag"] for row in connection.execute("SELECT tag FROM experience_tags WHERE experience_id = ? ORDER BY id", (experience["id"],))]
            methods_list = [row["method"] for row in connection.execute("SELECT method FROM purchase_methods WHERE experience_id = ? ORDER BY is_primary DESC, id", (experience["id"],))]
            linked_assets = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT oa.id, oa.asset_type, oa.name, oa.category, oa.lat, oa.lng, oa.official_url, esl.confidence
                    FROM experience_source_links esl
                    JOIN official_assets oa ON oa.id = esl.source_record_id
                    WHERE esl.experience_id = ?
                    ORDER BY esl.confidence DESC
                    """,
                    (experience["id"],),
                )
            ]
            experiences.append(
                {
                    "id": experience["id"],
                    "title": experience["title"],
                    "category": experience["category"],
                    "evidence": experience["evidence"],
                    "products": experience["products"],
                    "repeats": experience["repeats"],
                    "priceBand": experience["price_band"],
                    "tags": tags,
                    "purchaseMethods": methods_list,
                    "businessHint": experience["business_hint"],
                    "officialAssets": linked_assets,
                }
            )
        cities.append(
            {
                "id": city["id"],
                "country": city["country"],
                "name": city["name"],
                "positioning": city["positioning"],
                "demandSignal": city["demand_signal"],
                "experiences": experiences,
            }
        )

    timeline = [
        dict(row)
        for row in connection.execute(
            "SELECT id, trip_id, city_id, experience_id, event_type, label, initial_recorded_at, user_selected_time, time_status, sequence_order, source_type, is_user_confirmed FROM trip_timeline_events ORDER BY city_id, sequence_order"
        )
    ]
    funnel = [dict(row) for row in connection.execute("SELECT city_id, step_name, started_count, completed_count, dropoff_count FROM funnel_metrics ORDER BY city_id, id")]
    errors = [dict(row) for row in connection.execute("SELECT city_id, step_name, error_type, user_safe_message FROM error_logs ORDER BY id")]
    sources = [dict(row) for row in connection.execute("SELECT * FROM official_data_sources ORDER BY priority, id")]
    assets = [dict(row) for row in connection.execute("SELECT * FROM official_assets ORDER BY city_id, asset_type, name")]
    accommodations = [dict(row) for row in connection.execute("SELECT * FROM accommodation_candidates ORDER BY city_id, area_name")]
    generation_runs = [dict(row) for row in connection.execute("SELECT * FROM anchor_generation_runs ORDER BY created_at DESC")]
    generated_candidates = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM generated_anchor_candidates ORDER BY automation_status, city_id, confidence DESC, normalized_name"
        )
    ]

    JSON_PATH.write_text(
        json.dumps(
            {
                "cities": cities,
                "timeline": timeline,
                "funnelMetrics": funnel,
                "errorLogs": errors,
                "officialDataSources": sources,
                "officialAssets": assets,
                "accommodationCandidates": accommodations,
                "anchorAutomation": {
                    "latestRun": generation_runs[0] if generation_runs else None,
                    "candidates": generated_candidates,
                },
                "citySet": ["오사카", "후쿠오카", "부산"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        reset_db(connection)
        seed_db(connection)
        export_json(connection)

    print(f"created {DB_PATH}")
    print(f"exported {JSON_PATH}")


if __name__ == "__main__":
    main()
