import unittest

from scripts.build_official_experience_anchors import (
    FUKUOKA_MUSEUM_KO_NAMES,
    HIROSHIMA_CURATED_KO_NAMES,
    HIROSHIMA_EXCLUDED_FACILITIES,
    kana_to_korean,
    kyoto_korean_name,
    kyoto_facility_classification,
    kyoto_parent_components,
)
from scripts.match_official_anchors_to_mcp import classify, is_review_ready_korean_alias
from scripts.rank_hidden_destination_candidates import has_verified_mrt_supply


def kyoto_row(no: str, name: str, description: str = "", address: str = "", lat: str = "", lng: str = ""):
    return {
        "NO": no,
        "名称": name,
        "説明": description,
        "住所": address,
        "緯度": lat,
        "経度": lng,
    }


class KyotoFacilityClassificationTest(unittest.TestCase):
    def test_fukuoka_official_museums_have_reviewed_korean_names(self):
        self.assertEqual(FUKUOKA_MUSEUM_KO_NAMES["福岡市美術館"], "후쿠오카시미술관")
        self.assertEqual(FUKUOKA_MUSEUM_KO_NAMES["福岡市赤煉瓦文化館"], "후쿠오카시 아카렌가문화관")

    def test_hiroshima_places_have_reviewed_korean_names(self):
        self.assertEqual(HIROSHIMA_CURATED_KO_NAMES["縮景園"], "슛케이엔")
        self.assertEqual(HIROSHIMA_CURATED_KO_NAMES["広島市江波山気象館"], "히로시마시 에바야마 기상관")

    def test_hiroshima_non_tourism_facilities_are_explicitly_excluded(self):
        self.assertEqual(HIROSHIMA_EXCLUDED_FACILITIES["4"][0], "commercial_business")
        self.assertEqual(HIROSHIMA_EXCLUDED_FACILITIES["17"][0], "research_institute")
        self.assertEqual(HIROSHIMA_EXCLUDED_FACILITIES["29"][0], "branch_component")

    def test_directly_verified_mrt_supply_blocks_hidden_candidate(self):
        self.assertTrue(has_verified_mrt_supply("妙心寺 退蔵院"))
        self.assertFalse(has_verified_mrt_supply("未確認の場所"))

    def test_curated_translation_is_used_for_major_place(self):
        name_ko, source, status = kyoto_korean_name(
            {"名称": "清水寺", "名称_カナ": "キヨミズデラ"}
        )
        self.assertEqual(name_ko, "기요미즈데라(청수사)")
        self.assertEqual(source, "curated_standard_translation")
        self.assertEqual(status, "reviewed")

    def test_official_kana_is_fully_transliterated_to_korean(self):
        self.assertEqual(kana_to_korean("ゲンコウアン"), "겐코안")
        name_ko, source, status = kyoto_korean_name(
            {"名称": "源光庵", "名称_カナ": "ゲンコウアン"}
        )
        self.assertEqual(name_ko, "겐코안")
        self.assertEqual(source, "official_kana_transliteration")
        self.assertEqual(status, "auto_needs_review")

    def test_primary_tourism_place_is_kept(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("1", "鹿苑寺（金閣寺）", "北山文化を代表する寺院。")
        )
        self.assertEqual(disposition, "primary")
        self.assertEqual(classification, "religious_site")

    def test_parking_is_excluded(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("2", "京都市清水坂観光駐車場")
        )
        self.assertEqual(disposition, "excluded_non_primary")
        self.assertEqual(classification, "parking")

    def test_shop_with_landmark_word_is_not_misclassified(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("3", "御所西あいぜん 西村兄妹キモノ店", "きもの、帯の制作・小売。")
        )
        self.assertEqual(disposition, "excluded_non_primary")
        self.assertEqual(classification, "retail_or_rental_service")

    def test_restaurant_containing_temple_name_is_excluded(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row(
                "4",
                "南禅寺順正",
                "国の登録有形文化財の順正書院や清雅な庭園を眺めながら、"
                "ゆどうふや引き上げゆばに舌鼓。",
            )
        )
        self.assertEqual(disposition, "excluded_non_primary")
        self.assertEqual(classification, "commercial_business")

    def test_business_inside_preservation_district_is_not_a_district_anchor(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row(
                "10",
                "ぎをん小森",
                "伝統的建造物群保存地区にある町家を使った甘味どころ。料理と商品を販売する。",
            )
        )
        self.assertEqual(disposition, "excluded_non_primary")
        self.assertEqual(classification, "commercial_business")

    def test_ambiguous_facility_waits_for_review(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("5", "名称だけでは不明な施設", "京都にある施設。")
        )
        self.assertEqual(disposition, "needs_review")
        self.assertEqual(classification, "ambiguous_facility")

    def test_named_tourism_district_is_kept(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("8", "祇園", "京都を代表する繁華街で、風情のある町並みの保存地区。")
        )
        self.assertEqual(disposition, "primary")
        self.assertEqual(classification, "district_or_street")

    def test_temple_ending_in_an_is_kept_when_description_confirms_it(self):
        disposition, classification, _ = kyoto_facility_classification(
            kyoto_row("9", "源光庵", "曹洞宗の寺で、本堂と庭園を拝観できる。")
        )
        self.assertEqual(disposition, "primary")
        self.assertEqual(classification, "religious_site")

    def test_same_place_component_is_detected(self):
        rows = [
            kyoto_row("6", "元離宮二条城", "城郭。", "京都府京都市中京区二条城町541", "35.0142", "135.7482"),
            kyoto_row(
                "7",
                "元離宮二条城 特別名勝二の丸庭園",
                "城内の庭園。",
                "京都府京都市中京区二条城町541",
                "35.0142",
                "135.7482",
            ),
        ]
        classifications = {
            row["NO"]: kyoto_facility_classification(row)
            for row in rows
        }
        components = kyoto_parent_components(rows, classifications)
        self.assertEqual(components["7"], ("6", "元離宮二条城"))


class SupplyGapClassificationTest(unittest.TestCase):
    def test_mixed_japanese_korean_alias_is_not_review_ready(self):
        self.assertFalse(is_review_ready_korean_alias("교토祇園らんぷ미술관"))
        self.assertTrue(is_review_ready_korean_alias("니조성"))

    def test_missing_korean_alias_is_not_called_supply_gap(self):
        classification, _, _, _, gap = classify(0, 0, "tourism_facility", 49, False)
        self.assertEqual(classification, "매칭 보류(한국어 번역 부족)")
        self.assertEqual(gap, "")

    def test_tour_title_match_requires_detail(self):
        classification, _, _, _, gap = classify(0, 3, "tourism_facility", 49, True)
        self.assertEqual(classification, "연결 후보(투어 상세 확인 필요)")
        self.assertEqual(gap, "")

    def test_only_review_ready_no_match_becomes_gap_candidate(self):
        classification, _, _, _, gap = classify(0, 0, "tourism_facility", 49, True)
        self.assertEqual(classification, "수집 표본 내 미연결 후보")
        self.assertEqual(gap, "1.0")

    def test_incomplete_mcp_collection_blocks_gap_conclusion(self):
        classification, _, _, _, gap = classify(
            0, 0, "tourism_facility", 49, True, collection_complete=False
        )
        self.assertEqual(classification, "MCP 추가 수집 필요")
        self.assertEqual(gap, "")


if __name__ == "__main__":
    unittest.main()
