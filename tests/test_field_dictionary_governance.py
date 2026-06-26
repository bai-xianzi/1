from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.field_dictionary_governance import (  # noqa: E402
    EXPECTED_DICTIONARY_REVISION,
    EXPECTED_VALUE_DOMAIN_KINDS,
    field_index,
    load_yaml,
    validate_dictionary_governance,
)


class TestFieldDictionaryGovernance(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical = load_yaml(
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml"
        )
        self.contract = load_yaml(
            PROJECT_ROOT / "schemas" / "field_governance_contract.yaml"
        )
        self.index = field_index(self.canonical)

    def test_dictionary_revision_is_hardened(self) -> None:
        self.assertEqual(
            str(self.canonical["dictionary_revision"]),
            EXPECTED_DICTIONARY_REVISION,
        )
        self.assertEqual(
            str(self.contract["dictionary_revision"]),
            EXPECTED_DICTIONARY_REVISION,
        )

    def test_value_domain_kinds_are_explicit(self) -> None:
        self.assertEqual(
            set(self.contract["value_domain_kinds"]),
            EXPECTED_VALUE_DOMAIN_KINDS,
        )

    def test_required_metadata_matches_contract(self) -> None:
        for requirement in self.contract["required_metadata"]:
            key = (
                requirement["domain_code"],
                requirement["canonical_name"],
            )
            self.assertIn(key, self.index)
            self.assertEqual(
                self.index[key].get(requirement["key"]),
                requirement["value"],
            )

    def test_semantic_collisions_are_governed(self) -> None:
        report = validate_dictionary_governance(PROJECT_ROOT)
        self.assertEqual(report["overall_status"], "PASSED")
        self.assertEqual(report["issues"], [])

    def test_trade_count_is_not_silently_renamed(self) -> None:
        self.assertIn(("backtest", "trade_count"), self.index)
        self.assertNotIn(("backtest", "executed_trade_count"), self.index)


if __name__ == "__main__":
    unittest.main()
