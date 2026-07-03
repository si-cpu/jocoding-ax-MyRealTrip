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


class ValidationTests(unittest.TestCase):
    def test_exact_city_regions_rejects_station_and_similar_name(self):
        regions = [
            {"regionId": 1, "name": "도쿄", "enName": "Tokyo", "type": "CITY"},
            {"regionId": 2, "name": "도쿄역", "enName": "Tokyo Station", "type": "TRAIN_STATION"},
            {"regionId": 3, "name": "도쿄 베이", "enName": "Tokyo Bay", "type": "CITY"},
        ]
        self.assertEqual([regions[0]], api.exact_city_regions(regions, "도쿄"))

    def test_tna_city_filter_rejects_mismatch_and_missing_city(self):
        items = [
            {"gid": "1", "itemName": "도쿄 공예", "description": "도쿄 ∙ 체험·클래스"},
            {"gid": "2", "itemName": "파리 미술관", "description": "파리 ∙ 투어"},
            {"gid": "3", "itemName": "도시 없음", "description": ""},
        ]
        accepted, rejected = api.filter_tna_items_by_city(items, "도쿄")
        self.assertEqual([items[0]], accepted)
        self.assertEqual(["2", "3"], [item["gid"] for item in rejected])

    def test_iata_uses_airport_code_shape(self):
        self.assertEqual("ICN", api.require_iata("icn"))
        with self.assertRaises(ValueError):
            api.require_iata("SEL1")

    def test_item_city(self):
        self.assertEqual("오사카", api.item_city("오사카 ∙ 투어"))

    def test_iso_date_validation(self):
        self.assertEqual("2026-07-04", api.require_iso_date("2026-07-04"))
        with self.assertRaises(ValueError):
            api.require_iso_date("2026/07/04")

    def test_flight_period_is_limited_to_documented_range(self):
        self.assertEqual(3, api.require_trip_period(3))
        self.assertEqual(7, api.require_trip_period(7))
        with self.assertRaises(ValueError):
            api.require_trip_period(2)

    def test_airport_autocomplete_preserves_airport_code_not_city_code(self):
        response = {
            "data": {
                "airports": [
                    {
                        "airport": {"code": "ICN", "koName": "인천국제공항"},
                        "city": {"code": "SEL", "koName": "서울"},
                        "country": {"code": "KR", "koName": "대한민국"},
                        "isoCode": "KR",
                    }
                ]
            },
            "result": {"status": 200},
        }
        args = types.SimpleNamespace(command="airport-autocomplete", keyword="서울", size=5)
        with mock.patch.object(api, "post", return_value=response):
            result = api.run(args)
        self.assertEqual("ICN", result["data"]["airports"][0]["airportCode"])
        self.assertEqual("SEL", result["data"]["airports"][0]["city"]["code"])

    def test_bulk_lowest_uses_official_flight_endpoint_and_labels_price(self):
        response = {
            "data": [
                {
                    "fromCity": "ICN",
                    "toCity": "BKK",
                    "period": 4,
                    "departureDate": "2026-08-01",
                    "returnDate": "2026-08-04",
                    "totalPrice": 300000,
                }
            ],
            "result": {"status": 200},
        }
        args = types.SimpleNamespace(command="flight-bulk-lowest", departure="icn", period=4)
        with mock.patch.object(api, "post", return_value=response) as post:
            result = api.run(args)
        post.assert_called_once_with(
            "/v1/products/flight/calendar/bulk-lowest",
            {"depCityCd": "ICN", "period": 4},
        )
        self.assertEqual("INTERNATIONAL_ONLY", result["scope"])
        self.assertEqual("CALENDAR_LOWEST_NOT_LIVE_INVENTORY", result["priceType"])


if __name__ == "__main__":
    unittest.main()
