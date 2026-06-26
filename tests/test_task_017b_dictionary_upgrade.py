from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

import yaml

from a_stock_quant.daily_funds_canonical_contract import validate_contract
from a_stock_quant.field_dictionary_governance import (
    field_index,
    load_yaml,
    validate_dictionary_governance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Task017BDictionaryUpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical = load_yaml(
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml"
        )
        self.index = field_index(self.canonical)

    def test_revision_and_counts(self) -> None:
        lifecycle = Counter(
            field["lifecycle_stage"]
            for domain in self.canonical["domains"]
            for field in domain["fields"]
        )
        self.assertEqual(str(self.canonical["dictionary_revision"]), "0.6.0")
        self.assertEqual(len(self.canonical["domains"]), 46)
        self.assertEqual(sum(lifecycle.values()), 1235)
        self.assertEqual(lifecycle["core"], 744)

    def test_auction_date_only_time_governance(self) -> None:
        snapshot_time = self.index[("auction", "snapshot_time")]
        precision = self.index[("auction", "snapshot_time_precision")]
        self.assertTrue(snapshot_time["nullable"])
        self.assertEqual(snapshot_time["time_semantics"], "observation_time")
        self.assertFalse(precision["nullable"])
        self.assertEqual(precision["enum_ref"], "snapshot_time_precision")

    def test_classification_market_object_exists(self) -> None:
        domain = next(
            item for item in self.canonical["domains"]
            if item["canonical_object"] == "ClassificationMarketSnapshot"
        )
        fields = {item["canonical_name"] for item in domain["fields"]}
        self.assertIn("snapshot_phase", fields)
        self.assertIn("breadth_status", fields)
        self.assertIn("leading_instrument_id", fields)
        self.assertNotIn("average_shares", fields)

    def test_required_enums_exist(self) -> None:
        enums = yaml.safe_load(
            (PROJECT_ROOT / "schemas" / "enum_definitions.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("DATE_ONLY", enums["snapshot_time_precision"])
        self.assertIn("OPENING_AUCTION", enums["snapshot_phase"])
        self.assertIn("RATIO_MISMATCH_WARNING", enums["breadth_status"])

    def test_field_governance_passes(self) -> None:
        result = validate_dictionary_governance(PROJECT_ROOT)
        self.assertEqual(result["overall_status"], "PASSED")
        self.assertEqual(result["issues"], [])

    def test_all_seven_mappings_are_unblocked(self) -> None:
        result = validate_contract(
            PROJECT_ROOT / "configs" / "mappings" / "a_stock_daily_funds_canonical_v0.yaml",
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml",
        )
        self.assertEqual(result["overall_status"], "PASSED_WITH_WARNINGS")
        self.assertEqual(result["ready_with_warning_count"], 7)
        self.assertEqual(result["blocked_count"], 0)


if __name__ == "__main__":
    unittest.main()
