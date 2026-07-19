import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collect_city_tour_details import promote_product_description
from collect_public_tour_itineraries import extract_itineraries
from match_tour_details_to_official_places import (
    has_required_city_context,
    is_visit_itinerary_slot,
    is_visit_evidence_section,
)


class TourDetailCollectionTest(unittest.TestCase):
    def test_html_product_description_becomes_positive_evidence(self):
        section_type, label, text = promote_product_description(
            "neutral",
            "성인 1인",
            "<h3>히로시마성 방문</h3><p>가이드와 함께 성 내부와 역사 전시를 충분히 둘러보는 일정입니다.</p>",
        )
        self.assertEqual(section_type, "positive")
        self.assertTrue(label.startswith("상품 설명"))
        self.assertEqual(
            text,
            "히로시마성 방문 가이드와 함께 성 내부와 역사 전시를 충분히 둘러보는 일정입니다.",
        )

    def test_public_page_itinerary_partition_is_extracted(self):
        payload = {
            "props": {
                "pageProps": {
                    "dehydratedState": {
                        "queries": [
                            {
                                "state": {
                                    "data": {
                                        "data": {
                                            "partitions": [
                                                {
                                                    "partitionData": {
                                                        "itineraries": [
                                                            {
                                                                "title": "코스1",
                                                                "slots": [
                                                                    {
                                                                        "title": "슛케이엔",
                                                                        "description": "정원을 관람합니다.",
                                                                    }
                                                                ],
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertEqual(len(extract_itineraries(payload)), 1)


class TourDetailPlaceMatchingTest(unittest.TestCase):
    def test_meeting_point_is_not_visit_evidence(self):
        self.assertFalse(is_visit_evidence_section("positive", "📍 이용 안내 장소"))
        self.assertTrue(is_visit_evidence_section("positive", "✅ 포함 사항"))

    def test_generic_atomic_bomb_museum_requires_hiroshima_context(self):
        anchor = {"anchor_id": "official-hiroshima-facility-15"}
        nagasaki_section = {
            "product_title": "후쿠오카 출발 나가사키 일일 투어",
            "section_text": "나가사키 원폭 자료관과 평화공원을 방문합니다.",
        }
        hiroshima_section = {
            "product_title": "히로시마 평화기념관 투어",
            "section_text": "원폭 자료관 입장료 포함",
        }
        self.assertFalse(
            has_required_city_context(anchor, nagasaki_section, "원폭 자료관")
        )
        self.assertTrue(
            has_required_city_context(anchor, hiroshima_section, "원폭 자료관")
        )

    def test_negative_section_remains_auditable_but_not_confirmed(self):
        self.assertTrue(is_visit_evidence_section("negative", "❌ 불포함 사항"))

    def test_itinerary_meeting_point_is_not_a_visit(self):
        meeting = {
            "slot_title": "오리즈루 타워 앞 미팅",
            "slot_description": "기념품 가게 앞에서 집결 후 출발합니다.",
        }
        visit = {
            "slot_title": "오리즈루 타워",
            "slot_description": "전망대에 입장해 시내 전경을 감상합니다.",
        }
        self.assertFalse(is_visit_itinerary_slot(meeting, "오리즈루 타워"))
        self.assertTrue(is_visit_itinerary_slot(visit, "오리즈루 타워"))

    def test_titled_course_with_timed_destination_is_a_visit(self):
        slot = {
            "slot_title": "후쿠오카 출발 노코노시마 이토시마 코스",
            "slot_description": (
                "9:15 메이노하마선착장 출발 → 9:25 노코노시마선착장 "
                "9:45 전용버스 탑승 → 9:55 노코노시마 "
                "13:00 노코노시마선착장 출발"
            ),
        }
        self.assertTrue(is_visit_itinerary_slot(slot, "노코노시마"))

    def test_place_mentioned_only_as_a_geographic_connection_is_not_a_visit(self):
        slot = {
            "slot_title": "우미노나카미치 해변 공원",
            "slot_description": "후쿠오카와 시카노시마를 연결하는 해상공원입니다.",
        }
        self.assertFalse(is_visit_itinerary_slot(slot, "시카노시마"))

    def test_conditional_replacement_is_not_a_confirmed_visit(self):
        slot = {
            "slot_title": "큐슈 자연동물원",
            "slot_description": (
                "악천후로 동물원이 휴장할 경우 우미노나카미치 수족관으로 "
                "대체됩니다."
            ),
        }
        self.assertFalse(is_visit_itinerary_slot(slot, "우미노나카미치"))

    def test_explicit_replacement_target_can_be_a_visit(self):
        slot = {
            "slot_title": "후쿠오카 타워",
            "slot_description": "해당 관광지는 후쿠오카성터로 대체됩니다.",
        }
        self.assertFalse(is_visit_itinerary_slot(slot, "후쿠오카 타워"))
        self.assertTrue(is_visit_itinerary_slot(slot, "후쿠오카성터"))

    def test_optional_dropoff_is_not_a_confirmed_visit(self):
        slot = {
            "slot_title": "후쿠오카 타워 정차",
            "slot_description": (
                "후쿠오카타워 주변 정차 가능한 곳에서 하차 가능하며 "
                "하차 인원이 없으면 하카타역으로 이동합니다."
            ),
        }
        self.assertFalse(is_visit_itinerary_slot(slot, "후쿠오카 타워"))


if __name__ == "__main__":
    unittest.main()
