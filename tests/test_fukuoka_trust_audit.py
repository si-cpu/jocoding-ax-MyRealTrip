import csv
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_fukuoka_product_city_scope as city_scope
import audit_fukuoka_match_confidence as confidence
import build_fukuoka_mcp_minus_official81_list as reverse_list


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


class FukuokaTrustAuditTest(unittest.TestCase):
    def test_all_180_products_have_cached_detail_payloads(self):
        summary = json.loads(
            (
                ROOT
                / "data"
                / "supply_gap_analysis"
                / "audit"
                / "fukuoka_product_detail_inventory_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(summary["deduplicated_fukuoka_products"], 180)
        self.assertEqual(summary["products_with_cached_payload"], 180)
        self.assertEqual(summary["products_without_cached_payload"], 0)

    def test_non_tour_city_scope_review_is_an_exact_partition(self):
        inventory = read_csv(city_scope.INVENTORY)
        non_tour_ids = {
            row["product_id"]
            for row in inventory
            if row["category_value"] != "tour"
        }
        reviewed = (
            city_scope.LOCAL_NON_TOUR_IDS
            | city_scope.OUTSIDE_OR_MULTI_REGION_NON_TOUR_IDS
        )
        self.assertEqual(len(non_tour_ids), 42)
        self.assertEqual(non_tour_ids, reviewed)
        self.assertFalse(
            city_scope.LOCAL_NON_TOUR_IDS
            & city_scope.OUTSIDE_OR_MULTI_REGION_NON_TOUR_IDS
        )

    def test_every_conditional_current_link_has_an_explicit_override(self):
        rows = [
            row
            for row in read_csv(confidence.MATCHES)
            if row.get("city_id") == "jp-fukuoka"
        ]
        conditional_markers = ("옵션", "방문 여부")
        marked_keys = {
            (row["anchor_id"], row["product_id"])
            for row in rows
            if any(marker in row["evidence_text"] for marker in conditional_markers)
        }
        self.assertTrue(marked_keys)
        self.assertTrue(marked_keys.issubset(confidence.OVERRIDES))
        self.assertIn(
            ("official-fukuoka-guide-26825", "4435009"),
            confidence.OVERRIDES,
        )

    def test_official_tour_collection_matches_declared_count(self):
        summary = json.loads(
            (
                ROOT
                / "data"
                / "official_tourism_sources"
                / "reports"
                / "fukuoka_official_tour_collection_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(summary["declared_result_count"], 11)
        self.assertEqual(summary["collected_result_count"], 11)
        self.assertTrue(summary["complete_against_declared_count"])

    def test_exact_name_false_negative_gate_has_no_unresolved_pairs(self):
        summary = json.loads(
            (
                ROOT
                / "data"
                / "supply_gap_analysis"
                / "audit"
                / "fukuoka_false_negative_candidate_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(summary["exact_name_candidate_pairs"], 8)
        self.assertEqual(summary["unresolved_candidates"], 0)

    def test_reverse_destination_list_keeps_official_and_platform_buckets_separate(self):
        rows = reverse_list.enriched_rows()
        included = [row for row in rows if row["list_status"] == "included"]
        review = [row for row in rows if row["list_status"] == "review_needed"]
        excluded = [row for row in rows if row["list_status"] == "excluded"]
        self.assertEqual(len(included), 7)
        self.assertEqual(len(review), 2)
        self.assertEqual(len(excluded), 5)
        self.assertTrue(
            all(
                row["final_bucket"]
                in {"official_raw_not_in_81", "official_other_catalog_not_in_81"}
                for row in included
            )
        )
        self.assertTrue(
            all(row["final_bucket"] == "platform_only_review_candidate" for row in review)
        )
        included_groups = {row["canonical_group_id"] for row in included}
        self.assertEqual(len(included_groups), 4)
        self.assertEqual(
            {
                row["canonical_place_ko"]
                for row in included
                if row["canonical_group_id"] == "boss-ezo-fukuoka"
            },
            {"BOSS E・ZO FUKUOKA"},
        )
        self.assertEqual(
            {
                row["name_ko"]
                for row in included
                if row["canonical_group_id"] == "nakasu-riverfront"
            },
            {
                "나카스 리버 야카타부네 디너 크루즈",
                "나카가와 리버 크루즈",
                "하카타강 래프팅 크루즈",
            },
        )

    def test_reverse_destination_list_does_not_count_food_or_outside_city(self):
        rows = reverse_list.enriched_rows()
        by_name = {row["name_ko"]: row for row in rows}
        self.assertEqual(by_name["나카스 야타이 거리"]["list_status"], "excluded")
        self.assertEqual(by_name["카와바타 젠자이 광장"]["list_status"], "excluded")
        self.assertEqual(by_name["코로나 온천"]["list_status"], "excluded")
        self.assertEqual(by_name["가요이초 공원"]["list_status"], "excluded")


if __name__ == "__main__":
    unittest.main()
