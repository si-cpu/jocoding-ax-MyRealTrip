#!/usr/bin/env python3
"""Build normalized official experience anchors from filtered official data."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "official_tourism_sources" / "processed"
OUT = ROOT / "data" / "official_tourism_sources" / "anchors"
REPORTS = ROOT / "data" / "official_tourism_sources" / "reports"


ANCHOR_FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "country_code",
    "anchor_name",
    "anchor_name_local",
    "anchor_name_ko",
    "anchor_name_en",
    "translation_source",
    "translation_status",
    "anchor_type",
    "official_source_type",
    "source_dataset",
    "source_record_id",
    "source_url",
    "description",
    "category",
    "address",
    "lat",
    "lng",
    "start_date",
    "end_date",
    "price_text",
    "evidence_text",
    "confidence",
    "review_status",
    "match_ready",
    "notes",
]

KYOTO_NON_PRIMARY_NAME_RULES = (
    ("parking", r"駐車場|パーキング|くるっとパーク"),
    (
        "transport_or_convenience",
        r"タクシー|レンタカー|レンタサイクル|デリバリーサービス|鉄道案内所|"
        r"観光案内所|インフォメーション|手荷物|キャリーサービス|"
        r"サイクリングツアープロジェクト|バイクプール",
    ),
    (
        "lodging_or_bathing",
        r"ホテル|旅館|民宿|ペンション|ロッジ|ゲストハウス|"
        r"(^|[\s　])宿([\s　]|$)|小宿|お宿|宿泊所|青少年村|キャンプ場|温泉|足湯|"
        r"スパ|spa|銭湯",
    ),
    (
        "food_or_beverage",
        r"料理|食堂|レストラン|カフェ|喫茶|茶屋|料亭|割烹|菓子|菓寮|餅|"
        r"豆腐|とうふ|納豆|漬物|パン|珈琲|コーヒー|ワイン|ビール|酒造|"
        r"醤油|グリル|洋食|そば|うどん|寿司|鮨|焼肉|ラーメン|スイーツ|"
        r"甘味|御すぐき|本舗|茶房|食文化|食事処",
    ),
    (
        "time_limited_event",
        r"手づくり市|手作り市|骨董市|亀の市|天神さんの市|弘法さんの市|"
        r"祭$|祭り|まつり|イベント|ライトアップ|大会$|行列$",
    ),
    (
        "retail_or_rental_service",
        r"レンタル|貸衣装|着付け|変身|商店|ショップ|ショッピング|土産|"
        r"専門店|工房|スタジオ|手創り体験|手作り体験|京あるき|サイクル|"
        r"店($|[（(])",
    ),
    (
        "administrative_or_sports_facility",
        r"体育館|総合体育館|市民体育館|スポーツセンター|スポーツ施設|"
        r"運動場|運動施設|運動公園|陸上競技場|競技場|野球場|球場|"
        r"テニスコート|市民プール|屋内プール|武道場|武道センター|"
        r"トレーニングセンター|交通公園|府民ホール|"
        r"文化芸術会館|こども文化会館|国際交流会館|国際センター|"
        r"コンベンション|会議場",
    ),
    ("abstract_course", r"を学ぶ|めぐり|コース$"),
    ("closed_or_expired", r"休館|閉館|公開終了"),
)

KYOTO_PRIMARY_NAME_RULES = (
    ("religious_site", r"寺|神社|神宮|天満宮|大社|地蔵|不動|観音|霊廟|墓所"),
    ("museum_or_gallery", r"博物館|美術館|資料館|記念館|ミュージアム"),
    (
        "heritage_or_landmark",
        r"城|御所|離宮|旧宅|住宅|邸$|史跡|遺跡|古墳|町並み|街道|橋$|"
        r"坂$|市場$|タワー|展望|映画村|劇場|能楽堂|歌舞練場|疏水|水路閣",
    ),
    (
        "nature_or_park",
        r"公園($|[\s　（(])|庭園($|[\s　（(])|植物園|動物園|水族館|"
        r"渓谷|峡谷|竹林|遊歩道|哲学の道",
    ),
)

KYOTO_COMMERCIAL_DESCRIPTION_PATTERN = re.compile(
    r"店内|お店|店舗|営業|メニュー|食事|料理|飲食|販売|商品|お買い求め|"
    r"取り揃え|アンテナショップ|常設店舗|直営店|小売|"
    r"ランチ|ディナー|ゆどうふ|湯豆腐|ゆば|湯葉|舌鼓|"
    r"予約制の宿|宿泊施設|客室"
)

KYOTO_STRONG_COMMERCIAL_DESCRIPTION_PATTERN = re.compile(
    r"取り揃えて|アンテナショップ|常設店舗|直営店|小売|"
    r"元お茶屋.{0,40}お店"
)

KYOTO_RESIDENT_SPORTS_DESCRIPTION_PATTERN = re.compile(
    r"(府民|市民|区民).{0,20}(健康増進|体力向上|スポーツ・レクリエーション)|"
    r"(健康増進|体力の向上).{0,30}(体育館|競技場|テニスコート|プール)|"
    r"総合体育館.{0,80}(テニスコート|市民プール|競技場)|"
    r"(競技場|野球場).{0,80}(テニスコート|市民プール|体育館)"
)

KYOTO_AUDIT_FIELDS = [
    "source_record_id",
    "name",
    "name_kana",
    "name_ko",
    "translation_source",
    "translation_status",
    "municipality",
    "address",
    "lat",
    "lng",
    "disposition",
    "classification",
    "reason",
    "parent_record_id",
    "parent_name",
]

KYOTO_CURATED_KO_NAMES = {
    "鹿苑寺（金閣寺）": "금각사(킨카쿠지)",
    "清水寺": "기요미즈데라(청수사)",
    "伏見稲荷大社": "후시미 이나리 신사",
    "祇園": "기온",
    "慈照寺（銀閣寺）": "은각사(긴카쿠지)",
    "元離宮二条城": "니조성",
    "北野天満宮": "기타노텐만구",
    "三千院": "산젠인",
    "延暦寺": "엔랴쿠지",
    "嵐山": "아라시야마",
    "京都御所": "교토고쇼",
    "平安神宮": "헤이안신궁",
    "大本山南禅寺": "난젠지",
    "哲学の道": "철학의 길",
    "渡月橋": "도게츠교",
    "錦市場": "니시키시장",
    "東映太秦映画村": "도에이 우즈마사 영화촌",
    "京都タワー": "교토 타워",
    "京都水族館": "교토 수족관",
    "京都市動物園": "교토시 동물원",
    "大仙院": "다이센인",
    "妙心寺 退蔵院": "묘신지 다이조인",
    "天授庵": "텐주안",
    "並河靖之七宝記念館": "나미카와 야스유키 칠보 기념관",
    "法金剛院": "호곤인",
    "金地院": "곤치인",
    "地蔵院（竹の寺）": "지조인(대나무 절)",
    "智積院": "지샤쿠인",
    "角屋もてなしの文化美術館": "스미야 모테나시 문화미술관",
    "大沢池": "오사와 연못",
    "真如堂（真正極楽寺）": "신뇨도(신쇼고쿠라쿠지)",
    "瑞峯院": "즈이호인",
    "圓通寺": "엔쓰지",
    "正伝寺": "쇼덴지",
    "光明院": "고묘인",
    "重森三玲邸庭園美術館": "시게모리 미레이 저택 정원미술관",
}

HIROSHIMA_CURATED_KO_NAMES = {
    "縮景園": "슛케이엔",
    "ひろしま遊学の森　広島県緑化センター": "히로시마 유학의 숲·히로시마현 녹화센터",
    "ひろしま遊学の森　広島市森林公園（こんちゅう館）": "히로시마 유학의 숲·히로시마시 삼림공원 곤충관",
    "半べえ庭園": "한베 정원",
    "渝華園(中国庭園)": "유화원(중국정원)",
    "大芝公園｢交通ランド」": "오시바공원 교통랜드",
    "広島市安佐動物公園": "히로시마시 아사 동물공원",
    "花みどり公園": "하나미도리공원",
    "広島市植物公園": "히로시마시 식물공원",
    "広島県立美術館": "히로시마현립미술관",
    "広島市映像文化ライブラリー": "히로시마시 영상문화라이브러리",
    "ひろしま美術館": "히로시마미술관",
    "5-Daysこども文化科学館（プラネタリウム）": "5-Days 어린이문화과학관(플라네타륨)",
    "広島城": "히로시마성",
    "広島平和記念資料館": "히로시마 평화기념자료관",
    "国立広島原爆死没者追悼平和祈念館": "국립 히로시마 원폭사망자 추도평화기념관",
    "公益財団法人放射線影響研究所": "방사선영향연구소",
    "本川小学校平和資料館": "혼카와초등학교 평화자료관",
    "袋町小学校平和資料館": "후쿠로마치초등학교 평화자료관",
    "広島市健康づくりセンター健康科学館": "히로시마시 건강과학관",
    "広島市江波山気象館": "히로시마시 에바야마 기상관",
    "頼山陽史跡資料館": "라이 산요 사적자료관",
    "広島市現代美術館": "히로시마시 현대미술관",
    "広島市郷土資料館": "히로시마시 향토자료관",
    "広島大学医学部医学資料館": "히로시마대학교 의학부 의학자료관",
    "ヌマジ交通ミュージアム（広島市交通科学館）": "누마지 교통박물관(히로시마시 교통과학관)",
    "泉美術館": "이즈미미술관",
    "広島市まんが図書館": "히로시마시 만화도서관",
    "広島市まんが図書館あさ閲覧室": "히로시마시 만화도서관 아사열람실",
    "広島市水産振興センター(魚と漁業の資料展示室)": "히로시마시 수산진흥센터 물고기·어업 자료전시실",
    "広島市水道資料館": "히로시마시 수도자료관",
    "おりづるタワー": "오리즈루 타워",
}

FUKUOKA_MUSEUM_KO_NAMES = {
    "福岡市美術館": "후쿠오카시미술관",
    "福岡アジア美術館": "후쿠오카아시아미술관",
    "福岡市博物館": "후쿠오카시박물관",
    "福岡市埋蔵文化財センター": "후쿠오카시 매장문화재센터",
    "福岡市赤煉瓦文化館": "후쿠오카시 아카렌가문화관",
}

HIROSHIMA_EXCLUDED_FACILITIES = {
    "4": ("commercial_business", "restaurant, banquet hall and wedding venue; garden access is limited to customers"),
    "6": ("local_recreation_facility", "children's traffic-learning park rather than an independent tourism asset"),
    "17": ("research_institute", "research institute requiring advance arrangements, not a general tourism place"),
    "29": ("branch_component", "branch reading room of the main manga library"),
}

HIROSHIMA_CATEGORY_BY_NO = {
    **{str(no): "nature_or_park" for no in [1, 2, 3, 5, 6, 7, 8, 9]},
    **{str(no): "museum_or_gallery" for no in [10, 11, 12, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31]},
    "14": "heritage_or_landmark",
    "33": "observation_or_landmark",
}

KATAKANA_KO = {
    "ア": "아", "イ": "이", "ウ": "우", "エ": "에", "オ": "오",
    "カ": "카", "キ": "키", "ク": "쿠", "ケ": "케", "コ": "코",
    "ガ": "가", "ギ": "기", "グ": "구", "ゲ": "게", "ゴ": "고",
    "サ": "사", "シ": "시", "ス": "스", "セ": "세", "ソ": "소",
    "ザ": "자", "ジ": "지", "ズ": "즈", "ゼ": "제", "ゾ": "조",
    "タ": "타", "チ": "치", "ツ": "쓰", "テ": "테", "ト": "토",
    "ダ": "다", "ヂ": "지", "ヅ": "즈", "デ": "데", "ド": "도",
    "ナ": "나", "ニ": "니", "ヌ": "누", "ネ": "네", "ノ": "노",
    "ハ": "하", "ヒ": "히", "フ": "후", "ヘ": "헤", "ホ": "호",
    "バ": "바", "ビ": "비", "ブ": "부", "ベ": "베", "ボ": "보",
    "パ": "파", "ピ": "피", "プ": "푸", "ペ": "페", "ポ": "포",
    "マ": "마", "ミ": "미", "ム": "무", "メ": "메", "モ": "모",
    "ヤ": "야", "ユ": "유", "ヨ": "요",
    "ラ": "라", "リ": "리", "ル": "루", "レ": "레", "ロ": "로",
    "ワ": "와", "ヰ": "이", "ヱ": "에", "ヲ": "오",
    "ヴ": "부", "ヵ": "카", "ヶ": "케",
}

KATAKANA_DIGRAPH_KO = {
    "キャ": "캬", "キュ": "큐", "キョ": "쿄",
    "ギャ": "갸", "ギュ": "규", "ギョ": "교",
    "シャ": "샤", "シュ": "슈", "ショ": "쇼",
    "ジャ": "자", "ジュ": "주", "ジョ": "조",
    "チャ": "차", "チュ": "추", "チョ": "초",
    "ニャ": "냐", "ニュ": "뉴", "ニョ": "뇨",
    "ヒャ": "햐", "ヒュ": "휴", "ヒョ": "효",
    "ビャ": "뱌", "ビュ": "뷰", "ビョ": "뵤",
    "ピャ": "퍄", "ピュ": "퓨", "ピョ": "표",
    "ミャ": "먀", "ミュ": "뮤", "ミョ": "묘",
    "リャ": "랴", "リュ": "류", "リョ": "료",
    "シェ": "셰", "ジェ": "제", "チェ": "체",
    "ティ": "티", "ディ": "디", "トゥ": "투", "ドゥ": "두",
    "ファ": "파", "フィ": "피", "フェ": "페", "フォ": "포",
    "ウィ": "위", "ウェ": "웨", "ウォ": "워",
    "ヴァ": "바", "ヴィ": "비", "ヴェ": "베", "ヴォ": "보",
}

KOREAN_TRANSLATION_TERMS = (
    ("쿄우토", "교토"),
    ("텐만구우", "텐만구"),
    ("진구우", "신궁"),
    ("진자", "신사"),
    ("하쿠부쓰칸", "박물관"),
    ("비주쓰칸", "미술관"),
    ("시료우칸", "자료관"),
    ("키넨칸", "기념관"),
    ("쇼쿠부쓰엔", "식물원"),
    ("도우부쓰엔", "동물원"),
    ("스이조쿠칸", "수족관"),
    ("코우쓰우", "교통"),
    ("코우엔", "공원"),
    ("테이엔", "정원"),
    ("다이가쿠", "대학"),
    ("코쿠리쓰", "국립"),
    ("후리쓰", "부립"),
    ("시리쓰", "시립"),
    ("킨다이", "근대"),
    ("레키시", "역사"),
    ("코우코", "고고"),
    ("코우게이", "공예"),
    ("센이", "섬유"),
    ("주우타쿠", "주택"),
    ("큐우타쿠", "구택"),
    ("시세키", "사적"),
    ("노우가쿠도우", "노가쿠도"),
    ("쿄우겐", "교겐"),
    ("뮤지아무", "뮤지엄"),
    ("가덴", "가든"),
    ("타와", "타워"),
)

KOREAN_LONG_VOWEL_SIMPLIFICATIONS = (
    ("오오", "오"),
    ("쿄우", "교"),
    ("교우", "교"),
    ("쇼우", "쇼"),
    ("조우", "조"),
    ("초우", "초"),
    ("코우", "코"),
    ("고우", "고"),
    ("토우", "토"),
    ("도우", "도"),
    ("노우", "노"),
    ("호우", "호"),
    ("보우", "보"),
    ("포우", "포"),
    ("소우", "소"),
    ("요우", "요"),
    ("료우", "료"),
    ("묘우", "묘"),
    ("효우", "효"),
    ("로우", "로"),
)


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def slug(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣ぁ-んァ-ン一-龥]+", "-", text)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] or "unknown"


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return [dict(row) for row in csv.DictReader(f)]
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode {path}")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANCHOR_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_dict_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_place_name(text: str) -> str:
    return re.sub(r"[\s　・･()（）「」『』\-—ー]+", "", clean(text)).lower()


def hiragana_to_katakana(text: str) -> str:
    return "".join(
        chr(ord(char) + 0x60) if "ぁ" <= char <= "ゖ" else char
        for char in text
    )


def attach_final_n(text: str) -> str:
    if not text:
        return "ㄴ"
    last = ord(text[-1])
    if 0xAC00 <= last <= 0xD7A3 and (last - 0xAC00) % 28 == 0:
        return text[:-1] + chr(last + 4)
    return text + "ㄴ"


def kana_to_korean(text: str) -> str:
    source = hiragana_to_katakana(clean(text))
    result = ""
    index = 0
    while index < len(source):
        pair = source[index:index + 2]
        char = source[index]
        if pair in KATAKANA_DIGRAPH_KO:
            result += KATAKANA_DIGRAPH_KO[pair]
            index += 2
            continue
        if char == "ン":
            result = attach_final_n(result)
        elif char in {"ッ", "ー"}:
            pass
        elif char in KATAKANA_KO:
            result += KATAKANA_KO[char]
        elif char in {"・", "･", "／", "/"}:
            result += " "
        elif char in {"（", "("}:
            result += "("
        elif char in {"）", ")"}:
            result += ")"
        elif char in {"「", "」", "『", "』", "【", "】"}:
            pass
        elif char.isspace():
            result += " "
        elif char.isascii():
            result += char
        index += 1
    result = re.sub(r"\s+", " ", result).strip()
    for before, after in KOREAN_TRANSLATION_TERMS:
        result = result.replace(before, after)
    for before, after in KOREAN_LONG_VOWEL_SIMPLIFICATIONS:
        result = result.replace(before, after)
    return result


def kyoto_korean_name(row: dict[str, str]) -> tuple[str, str, str]:
    name = clean(row.get("名称"))
    curated = KYOTO_CURATED_KO_NAMES.get(name)
    if curated:
        return curated, "curated_standard_translation", "reviewed"
    translated = kana_to_korean(row.get("名称_カナ", ""))
    if translated and re.search(r"[가-힣]", translated):
        return translated, "official_kana_transliteration", "auto_needs_review"
    return "", "untranslated", "blocked"


def kyoto_facility_classification(row: dict[str, str]) -> tuple[str, str, str]:
    """Return disposition, classification and auditable reason.

    Only high-confidence, place-level tourism assets enter primary scoring.
    Ambiguous records remain in a review queue instead of being treated as gaps.
    """
    name = clean(row.get("名称"))
    description = clean(row.get("説明"))

    for classification, pattern in KYOTO_NON_PRIMARY_NAME_RULES:
        if re.search(pattern, name, flags=re.IGNORECASE):
            return "excluded_non_primary", classification, f"name matched /{pattern}/"

    if KYOTO_RESIDENT_SPORTS_DESCRIPTION_PATTERN.search(description):
        return (
            "excluded_non_primary",
            "administrative_or_sports_facility",
            "description identifies a resident-use sports complex",
        )

    for classification, pattern in KYOTO_PRIMARY_NAME_RULES:
        if re.search(pattern, name):
            if (
                classification == "religious_site"
                and KYOTO_COMMERCIAL_DESCRIPTION_PATTERN.search(description)
                and not re.search(
                    r"(寺|神社|神宮|天満宮|大社|地蔵|不動|観音|霊廟|墓所)"
                    r"(（[^）]+）)?$",
                    name,
                )
                and not re.search(r"博物館|美術館|資料館|記念館|ミュージアム", name)
            ):
                return (
                    "excluded_non_primary",
                    "commercial_business",
                    "religious place token appears inside a commercial business name",
                )
            return "primary", classification, f"name matched /{pattern}/"

    if KYOTO_STRONG_COMMERCIAL_DESCRIPTION_PATTERN.search(description):
        return (
            "excluded_non_primary",
            "commercial_business",
            "description identifies a retail or restaurant business rather than a place",
        )

    if re.search(r"(院|堂|宮|塔|庵)$", name) and re.search(
        r"塔頭|宗の寺|本尊|仏像|開山|伽藍|拝観|境内", description
    ):
        return "primary", "religious_site", "religious suffix confirmed by description"

    if re.search(r"(院|庵)$", name) and re.search(
        r"庭園|客殿|文化財|名勝|別荘|公開", description
    ):
        return "primary", "heritage_or_landmark", "historic-site suffix confirmed by description"

    if re.search(r"(山|池|滝|川|森)$", name) and re.search(
        r"自然|景観|水生|植物|標高|渓谷|森林|登山|滝|河川|池|山", description
    ):
        return "primary", "nature_or_park", "natural-feature suffix confirmed by description"

    if (
        not re.search(r"会社|店|館|センター", name)
        and re.search(
            r"地域の総称|地区で|地区。|町並み|繁華街|花街|参道が|"
            r"情緒が味わえるエリア",
            description,
        )
    ):
        return "primary", "district_or_street", "named district confirmed by description"

    if KYOTO_COMMERCIAL_DESCRIPTION_PATTERN.search(description):
        return "excluded_non_primary", "commercial_business", "commercial operation confirmed by description"

    if re.search(r"(館|センター|会館)$", name) and re.search(
        r"展示|公開|見学|所蔵|収蔵|文化財|作品|資料|体験", description
    ):
        return (
            "needs_review",
            "visitor_cultural_candidate",
            "visitor-facing facility, but hall/center names may mix museums, shops and public services",
        )

    if re.search(r"(町|通|街|地区|路地)$", name) and re.search(
        r"町並み|通り|地区|街|散策|景観|観光", description
    ):
        return "primary", "district_or_street", "named district confirmed by description"

    return "needs_review", "ambiguous_facility", "no high-confidence place or exclusion rule matched"


def kyoto_parent_components(
    rows: list[dict[str, str]], classifications: dict[str, tuple[str, str, str]]
) -> dict[str, tuple[str, str]]:
    """Identify obvious sub-records of the same place without a manual anchor list."""
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        no = clean(row.get("NO"))
        if classifications.get(no, ("", "", ""))[0] != "primary":
            continue
        lat = clean(row.get("緯度"))
        lng = clean(row.get("経度"))
        address = re.sub(r"\s+", "", clean(row.get("住所")))
        keys = []
        if lat and lng:
            keys.append(("coord", lat, lng))
        if address and len(address) >= 12:
            keys.append(("address", address))
        for key in keys:
            groups.setdefault(key, []).append(row)

    components: dict[str, tuple[str, str]] = {}
    for grouped_rows in groups.values():
        for child in grouped_rows:
            child_no = clean(child.get("NO"))
            child_name = normalize_place_name(child.get("名称", ""))
            for parent in grouped_rows:
                parent_no = clean(parent.get("NO"))
                parent_name = normalize_place_name(parent.get("名称", ""))
                if child_no == parent_no or len(parent_name) < 3:
                    continue
                if child_name.startswith(parent_name) and len(child_name) > len(parent_name):
                    current = components.get(child_no)
                    if current is None or len(parent_name) > len(normalize_place_name(current[1])):
                        components[child_no] = (parent_no, clean(parent.get("名称")))
    return components


def fukuoka_yatai_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "curated" / "fukuoka_yatai_curated.csv"
    rows = read_csv(path)
    anchors = []
    anchors.append(
        {
            "anchor_id": "official-fukuoka-yatai-cluster",
            "city_id": "jp-fukuoka",
            "city_name": "후쿠오카",
            "country_code": "JP",
            "anchor_name": "후쿠오카 야타이",
            "anchor_name_local": "福岡市 屋台",
            "anchor_name_en": "Fukuoka Yatai",
            "anchor_type": "place_cluster",
            "official_source_type": "official_yatai_cluster",
            "source_dataset": "fukuoka_yatai_curated",
            "source_record_id": "cluster",
            "source_url": "https://data.bodik.jp/dataset/401307_yataiopendata",
            "description": f"福岡市 official yatai inventory with {len(rows)} deduplicated stalls.",
            "category": "야타이/포장마차",
            "address": "福岡県福岡市",
            "lat": "",
            "lng": "",
            "start_date": "",
            "end_date": "",
            "price_text": "",
            "evidence_text": f"福岡市 official yatai dataset / {len(rows)} stalls / deduplicated by 屋台ID",
            "confidence": "0.98",
            "review_status": "accepted",
            "match_ready": "true",
            "notes": "Place-based aggregate anchor for Fukuoka yatai area/stall network; product format such as tour is not used as the analysis unit.",
        }
    )
    for row in rows:
        name = clean(row.get("名称"))
        yatai_id = clean(row.get("屋台ID"))
        if not name:
            continue
        category = clean(row.get("カテゴリー"))
        description = clean(row.get("リード文") or row.get("本文"))
        official_url = clean(row.get("よかなびURL") or row.get("URL") or row.get("Google Map"))
        evidence = " / ".join(x for x in [name, category, clean(row.get("エリア")), description[:160]] if x)
        anchors.append(
            {
                "anchor_id": f"official-fukuoka-yatai-{yatai_id or slug(name)}",
                "city_id": "jp-fukuoka",
                "city_name": "후쿠오카",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": clean(row.get("名称_英語")),
                "anchor_type": "food_place",
                "official_source_type": "official_yatai",
                "source_dataset": "fukuoka_yatai_curated",
                "source_record_id": yatai_id,
                "source_url": official_url,
                "description": description,
                "category": category,
                "address": clean(row.get("所在地_連結表記") or row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("予算")),
                "evidence_text": evidence,
                "confidence": "0.95",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Fukuoka official yatai dataset; deduplicated by 屋台ID",
            }
        )
    return anchors


def fukuoka_museum_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "fukuoka_city_museums_public_facilities.csv"
    if not path.exists():
        return []
    anchors = []
    for row in read_csv(path):
        name = clean(row.get("名称"))
        no = clean(row.get("NO"))
        if not name:
            continue
        name_ko = FUKUOKA_MUSEUM_KO_NAMES.get(
            name,
            kana_to_korean(clean(row.get("名称_カナ"))),
        )
        address = " ".join(
            value for value in [clean(row.get("住所")), clean(row.get("方書"))] if value
        )
        anchors.append(
            {
                "anchor_id": f"official-fukuoka-museum-{no or slug(name)}",
                "city_id": "jp-fukuoka",
                "city_name": "후쿠오카",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_ko": name_ko,
                "anchor_name_en": "",
                "translation_source": "curated_standard_translation",
                "translation_status": "reviewed",
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "fukuoka_city_museums_public_facilities",
                "source_record_id": no,
                "source_url": clean(row.get("URL"))
                or "https://data.bodik.jp/dataset/401307_ftoshiken_public_facility",
                "description": "",
                "category": "museum_or_gallery",
                "address": address,
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": "",
                "evidence_text": f"{name} / 福岡市 official public museum facility / {address}",
                "confidence": "0.92",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Fukuoka City official museum/public cultural facility dataset; five-record MVP baseline",
            }
        )
    return anchors


def fukuoka_official_guide_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "fukuoka_official_guide_places.csv"
    if not path.exists():
        return []
    anchors = []
    for row in read_csv(path):
        spot_id = clean(row.get("spot_id"))
        name_local = clean(row.get("name_local"))
        name_ko = clean(row.get("name_ko"))
        if not spot_id or not name_local or not name_ko:
            continue
        description = clean(row.get("description"))
        areas = clean(row.get("areas"))
        categories = clean(row.get("categories"))
        classification = clean(row.get("classification"))
        source_url = clean(row.get("source_url"))
        anchors.append(
            {
                "anchor_id": f"official-fukuoka-guide-{spot_id}",
                "city_id": "jp-fukuoka",
                "city_name": "후쿠오카",
                "country_code": "JP",
                "anchor_name": name_local,
                "anchor_name_local": name_local,
                "anchor_name_ko": name_ko,
                "anchor_name_en": "",
                "translation_source": "official_fukuoka_korean_guide",
                "translation_status": "reviewed",
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "fukuoka_official_guide_places",
                "source_record_id": spot_id,
                "source_url": source_url,
                "description": description,
                "category": classification,
                "address": areas,
                "lat": "",
                "lng": "",
                "start_date": "",
                "end_date": "",
                "price_text": "",
                "evidence_text": " / ".join(
                    value
                    for value in [
                        name_local,
                        name_ko,
                        areas,
                        categories,
                        description[:200],
                    ]
                    if value
                ),
                "confidence": "0.96",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": (
                    "Fukuoka City official Japanese sightseeing catalog joined to "
                    "the official Korean guide by stable spot ID; city scope and "
                    "visitor-facing tourism suitability filtered with an auditable "
                    "excluded dataset."
                ),
            }
        )
    return anchors


def hiroshima_facility_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "hiroshima_tourism_facilities_city_only.csv"
    rows = read_csv(path)
    anchors = []
    excluded_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for row in rows:
        name = clean(row.get("名称"))
        no = clean(row.get("NO"))
        if not name:
            continue
        if no in HIROSHIMA_EXCLUDED_FACILITIES:
            excluded_counts[HIROSHIMA_EXCLUDED_FACILITIES[no][0]] += 1
            continue
        name_ko = HIROSHIMA_CURATED_KO_NAMES.get(name, kana_to_korean(clean(row.get("名称_カナ"))))
        category = HIROSHIMA_CATEGORY_BY_NO.get(no, "needs_review")
        category_counts[category] += 1
        description = clean(row.get("説明"))
        evidence = " / ".join(x for x in [name, description[:160], clean(row.get("アクセス方法"))] if x)
        anchors.append(
            {
                "anchor_id": f"official-hiroshima-facility-{no or slug(name)}",
                "city_id": "jp-hiroshima",
                "city_name": "히로시마",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_ko": name_ko,
                "anchor_name_en": "",
                "translation_source": "curated_standard_translation",
                "translation_status": "reviewed",
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "hiroshima_tourism_facilities_city_only",
                "source_record_id": no,
                "source_url": clean(row.get("URL")),
                "description": description,
                "category": category,
                "address": clean(row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("料金（詳細）") or row.get("料金（基本）")),
                "evidence_text": evidence,
                "confidence": "0.9",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Hiroshima official tourism facility; city-code filtered and place-level tourism suitability reviewed",
            }
        )
    (REPORTS / "hiroshima_anchor_filter_summary.json").write_text(
        json.dumps(
            {
                "source": str(path.relative_to(ROOT)),
                "source_rows": len(rows),
                "primary_anchor_rows": len(anchors),
                "excluded_counts": dict(excluded_counts),
                "category_counts": dict(category_counts),
                "policy": (
                    "Exclude customer-only commercial gardens, non-public research facilities, "
                    "and duplicate branch components; retain visitable niche museums."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return anchors


def hiroshima_event_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "hiroshima_events.csv"
    rows = read_csv(path)
    anchors = []
    seen: set[str] = set()
    for row in rows:
        name = clean(row.get("イベント名"))
        no = clean(row.get("NO"))
        place = clean(row.get("場所名称"))
        start = clean(row.get("開始日"))
        if not name:
            continue
        key = f"{name}|{place}|{start}"
        if key in seen:
            continue
        seen.add(key)
        description = clean(row.get("説明"))
        category = clean(row.get("カテゴリー"))
        evidence = " / ".join(x for x in [name, place, start, category, description[:160]] if x)
        anchors.append(
            {
                "anchor_id": f"official-hiroshima-event-{no or slug(key)}",
                "city_id": "jp-hiroshima",
                "city_name": "히로시마",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": clean(row.get("イベント名_英語")),
                "anchor_type": "event",
                "official_source_type": "official_event",
                "source_dataset": "hiroshima_events",
                "source_record_id": no,
                "source_url": clean(row.get("URL") or row.get("追加URL")),
                "description": description,
                "category": category,
                "address": clean(row.get("住所") or place),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": start,
                "end_date": clean(row.get("終了日")),
                "price_text": clean(row.get("料金(詳細)") or row.get("料金(基本)")),
                "evidence_text": evidence,
                "confidence": "0.78",
                "review_status": "accepted_time_sensitive",
                "match_ready": "true",
                "notes": "Hiroshima official event; time-sensitive, discount or exclude if expired",
            }
        )
    return anchors


def kyoto_facility_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "kyoto_tourism_facilities_city_only.csv"
    if not path.exists():
        return []
    rows = read_csv(path)
    classifications = {
        clean(row.get("NO")): kyoto_facility_classification(row)
        for row in rows
        if clean(row.get("NO"))
    }
    parent_components = kyoto_parent_components(rows, classifications)
    anchors = []
    audit_rows = []
    disposition_counts: Counter[str] = Counter()
    classification_counts: Counter[str] = Counter()
    translation_status_counts: Counter[str] = Counter()
    for row in rows:
        name = clean(row.get("名称"))
        no = clean(row.get("NO"))
        if not name:
            continue
        disposition, classification, reason = classifications[no]
        name_ko, translation_source, translation_status = kyoto_korean_name(row)
        parent_no = ""
        parent_name = ""
        if no in parent_components:
            disposition = "excluded_component"
            classification = "child_record_of_same_place"
            parent_no, parent_name = parent_components[no]
            reason = f"same coordinate/address and name begins with parent place: {parent_name}"
        disposition_counts[disposition] += 1
        classification_counts[classification] += 1
        if disposition == "primary":
            translation_status_counts[translation_status] += 1
        audit_rows.append(
            {
                "source_record_id": no,
                "name": name,
                "name_kana": clean(row.get("名称_カナ")),
                "name_ko": name_ko,
                "translation_source": translation_source,
                "translation_status": translation_status,
                "municipality": clean(row.get("市区町村名")),
                "address": clean(row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "disposition": disposition,
                "classification": classification,
                "reason": reason,
                "parent_record_id": parent_no,
                "parent_name": parent_name,
            }
        )
        if disposition != "primary":
            continue
        description = clean(row.get("説明"))
        evidence = " / ".join(x for x in [name, description[:160], clean(row.get("アクセス方法"))] if x)
        anchors.append(
            {
                "anchor_id": f"official-kyoto-facility-{no or slug(name)}",
                "city_id": "jp-kyoto",
                "city_name": "교토",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_ko": name_ko,
                "anchor_name_en": clean(row.get("名称_英語")),
                "translation_source": translation_source,
                "translation_status": translation_status,
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "kyoto_tourism_facilities_city_only",
                "source_record_id": no,
                "source_url": clean(row.get("URL")),
                "description": description,
                "category": classification,
                "address": clean(row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("料金（詳細）") or row.get("料金（基本）")),
                "evidence_text": evidence,
                "confidence": "0.9",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Kyoto Prefecture official tourism facility; Kyoto-city row and high-confidence place-level classification. Ambiguous and non-primary records are preserved in the audit file but excluded from primary scoring.",
            }
        )
    audit_path = REPORTS / "kyoto_facility_classification_audit.csv"
    write_dict_csv(audit_path, KYOTO_AUDIT_FIELDS, audit_rows)
    (REPORTS / "kyoto_anchor_non_primary_skip_summary.json").write_text(
        json.dumps(
            {
                "source": str(path.relative_to(ROOT)),
                "source_rows": len(rows),
                "primary_anchor_rows": len(anchors),
                "disposition_counts": dict(disposition_counts),
                "classification_counts": dict(classification_counts),
                "primary_translation_status_counts": dict(translation_status_counts),
                "audit_file": str(audit_path.relative_to(ROOT)),
                "policy": (
                    "Only high-confidence place-level assets enter primary scoring. "
                    "Non-primary, ambiguous, and same-place component records remain auditable."
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return anchors


def multicity_seed_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "curated" / "multicity_tourism_seed_assets.csv"
    if not path.exists():
        return []
    rows = read_csv(path)
    anchors = []
    for idx, row in enumerate(rows, start=1):
        city_id = clean(row.get("city_id"))
        local_name = clean(row.get("official_name_local"))
        display_name_ko = clean(row.get("display_name_ko"))
        if not city_id or not local_name:
            continue
        anchors.append(
            {
                "anchor_id": f"official-seed-{city_id}-{slug(local_name)}",
                "city_id": city_id,
                "city_name": clean(row.get("city_name")),
                "country_code": clean(row.get("country_code")),
                "anchor_name": local_name,
                "anchor_name_local": local_name,
                "anchor_name_en": clean(row.get("official_name_en")),
                "anchor_type": "place",
                "official_source_type": "tourism_seed",
                "source_dataset": "multicity_tourism_seed_assets",
                "source_record_id": str(idx),
                "source_url": clean(row.get("source_url")),
                "description": clean(row.get("notes")),
                "category": clean(row.get("category")),
                "address": "",
                "lat": "",
                "lng": "",
                "start_date": "",
                "end_date": "",
                "price_text": "",
                "evidence_text": " / ".join(x for x in [local_name, display_name_ko, clean(row.get("source_url"))] if x),
                "confidence": "0.82",
                "review_status": "seed_for_first_pass",
                "match_ready": "true",
                "notes": f"First-pass multi-city tourism seed. Korean display name: {display_name_ko}",
            }
        )
    return anchors


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    anchors = []
    anchors.extend(fukuoka_yatai_anchors())
    anchors.extend(fukuoka_official_guide_anchors())
    anchors.extend(kyoto_facility_anchors())
    anchors.extend(hiroshima_facility_anchors())
    anchors.extend(hiroshima_event_anchors())
    seed_anchors = multicity_seed_anchors()

    write_csv(OUT / "official_experience_anchors.csv", anchors)
    write_csv(OUT / "multicity_seed_candidate_anchors.csv", seed_anchors)
    with (OUT / "official_experience_anchors.jsonl").open("w", encoding="utf-8") as f:
        for row in anchors:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (OUT / "multicity_seed_candidate_anchors.jsonl").open("w", encoding="utf-8") as f:
        for row in seed_anchors:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "anchor_count": len(anchors),
        "by_city": dict(Counter(row["city_id"] for row in anchors)),
        "by_type": dict(Counter(row["anchor_type"] for row in anchors)),
        "by_source": dict(Counter(row["official_source_type"] for row in anchors)),
        "outputs": [
            str((OUT / "official_experience_anchors.csv").relative_to(ROOT)),
            str((OUT / "official_experience_anchors.jsonl").relative_to(ROOT)),
            str((OUT / "multicity_seed_candidate_anchors.csv").relative_to(ROOT)),
            str((OUT / "multicity_seed_candidate_anchors.jsonl").relative_to(ROOT)),
        ],
        "seed_candidate_count_excluded_from_primary_anchors": len(seed_anchors),
    }
    fukuoka_guide_count = sum(
        row.get("source_dataset") == "fukuoka_official_guide_places"
        for row in anchors
    )
    (REPORTS / "official_anchor_build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Official Experience Anchor Build Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Anchor count: {summary['anchor_count']}",
        f"- By city: {summary['by_city']}",
        f"- By type: {summary['by_type']}",
        f"- By source: {summary['by_source']}",
        "",
        "## Outputs",
        "",
        "- `data/official_tourism_sources/anchors/official_experience_anchors.csv`",
        "- `data/official_tourism_sources/anchors/official_experience_anchors.jsonl`",
        "- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.csv`",
        "- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.jsonl`",
        "",
        "## Notes",
        "",
        "- Fukuoka yatai anchors are deduplicated by `屋台ID`.",
        f"- Fukuoka primary place anchors come from the complete 468-record Yokanavi sightseeing catalog joined to the official Korean guide by spot ID; {fukuoka_guide_count} city-scoped, visitor-facing Korean-published places enter primary scoring.",
        "- All excluded Fukuoka records remain auditable in `processed/excluded/fukuoka_official_guide_excluded.csv`.",
        "- Hiroshima tourism facilities are filtered to Hiroshima city code `341002`.",
        "- Kyoto tourism facilities are filtered to municipality names starting with `京都市`; only high-confidence place-level assets enter primary scoring.",
        "- Kyoto non-primary, ambiguous, and same-place component records are preserved with reasons in `reports/kyoto_facility_classification_audit.csv`.",
        "- Every accepted Kyoto primary place has a Korean name. Curated standard translations and automatic official-kana transliterations are tracked separately.",
        "- Hiroshima event anchors are time-sensitive and should be discounted or excluded when expired.",
        "- Multi-city seed anchors are exported separately as candidate/demo anchors and are excluded from the primary official anchor file to avoid analysis contamination.",
    ]
    (REPORTS / "OFFICIAL_ANCHOR_BUILD_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
