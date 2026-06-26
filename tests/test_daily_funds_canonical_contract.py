from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from a_stock_quant.daily_funds_canonical_contract import (
    load_contract,
    validate_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "mappings"
    / "a_stock_daily_funds_canonical_v0.yaml"
)
DICTIONARY_PATH = PROJECT_ROOT / "schemas" / "canonical_fields.yaml"


class DailyFundsCanonicalContractTests(unittest.TestCase):
    def test_contract_passes_with_warnings(self) -> None:
        result = validate_contract(CONTRACT_PATH, DICTIONARY_PATH)
        self.assertEqual(result["overall_status"], "PASSED_WITH_WARNINGS")
        self.assertEqual(result["dataset_count"], 7)
        self.assertEqual(result["ready_with_warning_count"], 7)
        self.assertEqual(result["blocked_count"], 0)
        self.assertEqual(result["issues"], [])

    def test_hq_is_supplemental_not_authoritative(self) -> None:
        hq = load_contract(CONTRACT_PATH).datasets["hq"]
        self.assertEqual(hq["source_role"], "SUPPLEMENTAL_RECONCILIATION")
        self.assertEqual(hq["canonical_object"], "DailyBar")

    def test_kphq_uses_date_only_without_fabricated_time(self) -> None:
        kphq = load_contract(CONTRACT_PATH).datasets["kphq"]
        mapping = {item["target"]: item for item in kphq["mappings"]}
        self.assertEqual(mapping["snapshot_time"]["status"], "NOT_APPLICABLE")
        self.assertIsNone(mapping["snapshot_time"]["source"])
        self.assertEqual(
            mapping["snapshot_time_precision"]["transform"],
            "constant_DATE_ONLY",
        )
        self.assertEqual(kphq["readiness"], "READY_WITH_WARNING")

    def test_classification_snapshot_is_ready_and_not_membership(self) -> None:
        contract = load_contract(CONTRACT_PATH)
        for dataset_id in ("hy", "gn", "kphy", "kpgn"):
            dataset = contract.datasets[dataset_id]
            self.assertEqual(
                dataset["canonical_object"],
                "ClassificationMarketSnapshot",
            )
            self.assertEqual(dataset["readiness"], "READY_WITH_WARNING")
            self.assertIn("average_shares", dataset["source_extensions"])

    def test_zj_preserves_source_outflow_sign(self) -> None:
        contract = load_contract(CONTRACT_PATH)
        self.assertEqual(
            contract.datasets["zj"]["sign_policy"],
            "PRESERVE_SOURCE_SIGN",
        )

    def test_dictionary_revision_drift_fails(self) -> None:
        payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        payload["dictionary_revision"] = "0.0.0"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.yaml"
            path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = validate_contract(path, DICTIONARY_PATH)
        self.assertEqual(result["overall_status"], "FAILED")
        self.assertIn(
            "DICTIONARY_REVISION_MISMATCH",
            {item["code"] for item in result["issues"]},
        )

    def test_unknown_mapping_status_fails(self) -> None:
        payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["datasets"]["hq"]["mappings"][0]["status"] = "MAGIC"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.yaml"
            path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = validate_contract(path, DICTIONARY_PATH)
        self.assertEqual(result["overall_status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
