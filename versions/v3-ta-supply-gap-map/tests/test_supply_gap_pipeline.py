import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_supply_gap_pipeline import rebuild_steps, refresh_steps, report_steps


class SupplyGapPipelineTest(unittest.TestCase):
    def test_rebuild_is_offline_and_has_human_review_gate_before_export(self):
        steps = rebuild_steps()
        self.assertFalse(any(step.network for step in steps))
        names = [step.name for step in steps]
        self.assertLess(
            names.index("validate_reverse_hierarchy"),
            names.index("export_exact_lists"),
        )

    def test_report_regenerates_fukuoka_opportunities(self):
        names = [step.name for step in report_steps()]
        self.assertIn("rank_fukuoka_opportunities", names)

    def test_refresh_marks_collection_steps_as_networked(self):
        args = SimpleNamespace(
            skip_official_refresh=True,
            cities=["후쿠오카", "히로시마"],
            max_pages=7,
            mcp_delay=0.8,
            detail_delay=3.0,
            itinerary_delay=1.0,
        )
        steps = refresh_steps(args)
        by_name = {step.name: step for step in steps}
        self.assertTrue(by_name["collect_mcp_products"].network)
        self.assertTrue(by_name["collect_tour_details"].network)
        self.assertTrue(by_name["collect_public_itineraries"].network)


if __name__ == "__main__":
    unittest.main()
