from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.market_state_real_acceptance import (
    REAL_FEATURE_ACCEPTANCE_MODE,
    ReadonlySourceDescriptor,
    assert_readonly_query,
    build_date_presence_query,
    build_feature_acceptance_query,
    build_recent_date_rows_query,
    build_selector_rows_query,
    load_real_feature_acceptance_plan,
    unique_dates_from_rows,
    unique_selectors_from_rows,
    validate_real_feature_acceptance_report,
)
from a_stock_quant.standard_data_service import (
    StandardDataUsage,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = (
    ROOT
    / "configs"
    / "market_state"
    / "task_019c_real_feature_acceptance_plan_v0.json"
)


class TestMarketStateRealAcceptance(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_real_feature_acceptance_plan(PLAN_PATH)
        self.daily_source = ReadonlySourceDescriptor(
            dataset_id="a_stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            table_name="stock_daily_k",
            entity_field="stock_code",
            date_field="trade_date",
        )
        self.hy_source = ReadonlySourceDescriptor(
            dataset_id="hy",
            database_uri="dfs://A_STOCK_DAILY_FUNDS_DB",
            table_name="classification_snapshot",
            entity_field="node_name",
            date_field="snapshot_date",
            dataset_filter="dataset_id=`hy",
        )

    def test_plan_loads(self):
        self.assertEqual(self.plan.task_id, "TASK_019C")
        self.assertEqual(self.plan.mode, REAL_FEATURE_ACCEPTANCE_MODE)

    def test_plan_has_two_required_datasets(self):
        self.assertEqual(len(self.plan.required_datasets), 2)
        self.assertEqual(
            {item.dataset_id for item in self.plan.required_datasets},
            {"a_stock_daily_k", "hy"},
        )

    def test_plan_never_claims_full_market(self):
        self.assertFalse(self.plan.claim_full_market_coverage)

    def test_recent_date_query_is_readonly(self):
        script = build_recent_date_rows_query(
            self.hy_source,
            100,
        )
        assert_readonly_query(script)
        self.assertIn("select top 100", script)
        self.assertIn("dataset_id=`hy", script)

    def test_presence_query_is_readonly(self):
        script = build_date_presence_query(
            self.daily_source,
            date(2025, 12, 31),
        )
        assert_readonly_query(script)
        self.assertIn("2025.12.31", script)

    def test_selector_query_is_deterministic(self):
        script = build_selector_rows_query(
            self.daily_source,
            date(2025, 12, 31),
            30,
        )
        assert_readonly_query(script)
        self.assertIn("order by stock_code", script)

    def test_write_query_is_rejected(self):
        with self.assertRaises(DataContractError):
            assert_readonly_query("delete from x")

    def test_unique_dates_preserve_descending_order(self):
        rows = [
            {"snapshot_date": "2025.12.30"},
            {"snapshot_date": "2025.12.31"},
            {"snapshot_date": "2025.12.31"},
            {"snapshot_date": None},
        ]
        self.assertEqual(
            unique_dates_from_rows(
                rows,
                "snapshot_date",
                10,
            ),
            (date(2025, 12, 31), date(2025, 12, 30)),
        )

    def test_unique_selectors_remove_empty_and_duplicate(self):
        rows = [
            {"stock_code": "000001"},
            {"stock_code": "000001"},
            {"stock_code": ""},
            {"stock_code": "000002"},
        ]
        self.assertEqual(
            unique_selectors_from_rows(
                rows,
                "stock_code",
                10,
            ),
            ("000001", "000002"),
        )

    def test_daily_query_uses_current_research(self):
        query = build_feature_acceptance_query(
            self.plan.dataset("a_stock_daily_k"),
            ("000001", "000002", "000003"),
            date(2025, 12, 31),
            self.plan.as_of_date,
        )
        self.assertIs(
            query.usage,
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        )
        self.assertEqual(query.instrument_ids[0], "000001")
        self.assertEqual(query.entity_ids, ())

    def test_hy_query_uses_entity_ids(self):
        query = build_feature_acceptance_query(
            self.plan.dataset("hy"),
            ("industry-a", "industry-b"),
            date(2025, 12, 31),
            self.plan.as_of_date,
        )
        self.assertEqual(query.instrument_ids, ())
        self.assertEqual(
            query.entity_ids,
            ("industry-a", "industry-b"),
        )

    def test_empty_selectors_are_rejected(self):
        with self.assertRaises(DataContractError):
            build_feature_acceptance_query(
                self.plan.dataset("hy"),
                (),
                date(2025, 12, 31),
                self.plan.as_of_date,
            )

    def test_report_contract_accepts_valid_report(self):
        report = {
            "task_id": "TASK_019C",
            "mode": REAL_FEATURE_ACCEPTANCE_MODE,
            "required_dataset_count": 2,
            "required_feature_family_count": 5,
            "feature_definition_count": 15,
            "generated_feature_count": 15,
            "unique_source_query_id_count": 2,
            "database_connection_attempted": True,
            "database_readonly_query_mode": True,
            "write_operation_count": 0,
            "manual_decision_allowed": False,
            "official_market_state_allowed": False,
            "regime_label": None,
            "universe_scope": (
                "DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE"
            ),
            "claim_full_market_coverage": False,
            "input_assessment_status": "READY_WITH_WARNINGS",
            "feature_snapshot_status": "READY_WITH_WARNINGS",
            "research_feature_build_allowed": True,
            "common_trade_date": "2025-12-31",
            "query_summaries": [
                {
                    "dataset_id": "a_stock_daily_k",
                    "result_count": 30,
                    "blocks_downstream": False,
                },
                {
                    "dataset_id": "hy",
                    "result_count": 20,
                    "blocks_downstream": False,
                },
            ],
            "features": [
                {"feature_id": f"f{index}"}
                for index in range(15)
            ],
        }
        self.assertEqual(
            validate_real_feature_acceptance_report(
                report,
                self.plan,
            ),
            (),
        )

    def test_report_contract_detects_blocked_query(self):
        report = {
            "task_id": "TASK_019C",
            "mode": REAL_FEATURE_ACCEPTANCE_MODE,
            "required_dataset_count": 2,
            "required_feature_family_count": 5,
            "feature_definition_count": 15,
            "generated_feature_count": 15,
            "unique_source_query_id_count": 2,
            "database_connection_attempted": True,
            "database_readonly_query_mode": True,
            "write_operation_count": 0,
            "manual_decision_allowed": False,
            "official_market_state_allowed": False,
            "regime_label": None,
            "universe_scope": (
                "DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE"
            ),
            "claim_full_market_coverage": False,
            "input_assessment_status": "READY_WITH_WARNINGS",
            "feature_snapshot_status": "READY_WITH_WARNINGS",
            "research_feature_build_allowed": True,
            "common_trade_date": "2025-12-31",
            "query_summaries": [
                {
                    "dataset_id": "a_stock_daily_k",
                    "result_count": 30,
                    "blocks_downstream": False,
                },
                {
                    "dataset_id": "hy",
                    "result_count": 20,
                    "blocks_downstream": True,
                },
            ],
            "features": [
                {"feature_id": f"f{index}"}
                for index in range(15)
            ],
        }
        issues = validate_real_feature_acceptance_report(
            report,
            self.plan,
        )
        self.assertIn("query_blocked:hy", issues)

    def test_plan_rejects_full_market_claim(self):
        raw = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        raw["universe_policy"]["claim_full_market_coverage"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_real_feature_acceptance_plan(path)


if __name__ == "__main__":
    unittest.main()
