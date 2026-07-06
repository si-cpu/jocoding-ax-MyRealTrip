import importlib.util
import pathlib
import types
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "src" / "scripts" / "myrealtrip_api.py"
SPEC = importlib.util.spec_from_file_location("myrealtrip_api", SCRIPT)
api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(api)


class ContentCollectionTests(unittest.TestCase):
    def test_strip_html_produces_plain_evidence(self):
        self.assertEqual("USJ & 닌텐도", api.strip_html("<b>USJ</b> &amp; 닌텐도"))

    def test_partition_rejects_city_mismatch_and_utility(self):
        items = [
            {"gid": "1", "description": "오사카 ∙ 투어", "category": "투어"},
            {"gid": "2", "description": "교토 ∙ 투어", "category": "투어"},
            {"gid": "3", "description": "오사카 ∙ 이동·교통", "category": "이동·교통"},
        ]
        accepted, rejected = api.partition_tna_items(items, "오사카")
        self.assertEqual(["1"], [item["gid"] for item in accepted])
        self.assertEqual(
            ["CITY_MISMATCH_OR_MISSING", "UTILITY_CATEGORY"],
            [item["reason"] for item in rejected],
        )

    def test_collect_search_paginates_deduplicates_and_reports_complete(self):
        pages = [
            {
                "items": [
                    {"gid": "1", "description": "오사카 ∙ 투어", "category": "투어"},
                    {"gid": "2", "description": "오사카 ∙ 입장권", "category": "입장권"},
                ],
                "totalCount": 3,
                "hasNextPage": True,
            },
            {
                "items": [
                    {"gid": "2", "description": "오사카 ∙ 입장권", "category": "입장권"},
                    {"gid": "3", "description": "오사카 ∙ 체험", "category": "체험"},
                ],
                "totalCount": 3,
                "hasNextPage": False,
            },
        ]
        with mock.patch.object(api, "search_page", side_effect=pages):
            result = api.collect_search("오사카", max_pages=0)
        self.assertEqual(["1", "2", "3"], [item["gid"] for item in result["items"]])
        self.assertTrue(result["coverage"]["completeSearch"])
        self.assertEqual(2, result["coverage"]["pagesFetched"])

    def test_collect_search_marks_page_limit(self):
        page = {
            "items": [{"gid": "1", "description": "부산 ∙ 투어", "category": "투어"}],
            "totalCount": 200,
            "hasNextPage": True,
        }
        with mock.patch.object(api, "search_page", return_value=page):
            result = api.collect_search("부산", max_pages=1)
        self.assertFalse(result["coverage"]["completeSearch"])
        self.assertTrue(result["coverage"]["truncatedByPageLimit"])

    def test_collect_corpus_preserves_product_url_and_cleans_detail(self):
        collected = {
            "city": "런던",
            "items": [
                {"gid": "9", "productUrl": "https://example.test/9", "category": "투어"}
            ],
            "discarded": [],
            "coverage": {},
        }
        response = {
            "data": {
                "gid": "9",
                "title": "<b>해리포터</b>",
                "description": "스튜디오",
                "included": ["입장권"],
                "excluded": [],
                "itineraries": [{"title": "다이애건 앨리", "description": "관람"}],
            },
            "result": {"status": 200},
        }
        with (
            mock.patch.object(api, "collect_search", return_value=collected),
            mock.patch.object(api, "post", return_value=response),
        ):
            result = api.collect_corpus("런던", detail_limit=0)
        self.assertEqual("해리포터", result["details"][0]["title"])
        self.assertEqual("https://example.test/9", result["details"][0]["productUrl"])
        self.assertTrue(result["coverage"]["completeDetails"])

    def test_collect_corpus_records_detail_failure_without_losing_search_item(self):
        collected = {
            "city": "전주",
            "items": [
                {"gid": "7", "productUrl": "https://example.test/7", "category": "투어"}
            ],
            "discarded": [],
            "coverage": {},
        }
        with (
            mock.patch.object(api, "collect_search", return_value=collected),
            mock.patch.object(api, "post", side_effect=api.ApiError("detail unavailable")),
        ):
            result = api.collect_corpus("전주", detail_limit=0)
        self.assertEqual([], result["details"])
        self.assertEqual("7", result["detailFailures"][0]["gid"])
        self.assertEqual("7", result["items"][0]["gid"])
        self.assertFalse(result["coverage"]["completeDetails"])

    def test_options_requires_actual_options(self):
        response = {"data": {"options": []}, "result": {"status": 200}}
        args = types.SimpleNamespace(command="tna-options", gid="1", date="2026-07-06")
        with mock.patch.object(api, "post", return_value=response):
            result = api.run(args)
        self.assertFalse(result["bookable"])


if __name__ == "__main__":
    unittest.main()
