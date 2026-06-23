"""测试DolphinDB基本面快照发现与画像。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    RawDataBatch,
    SourceType,
)
from a_stock_quant.dolphindb_fundamental_profile import (
    DolphinDBFundamentalProfiler,
    EXPECTED_FIELDS,
    _json_safe,
    render_markdown,
)


class FakeFundamentalAdapter:
    def __init__(
        self,
        *,
        duplicate_extra_rows: int = 0,
        missing_field: str | None = None,
    ) -> None:
        self.duplicate_extra_rows = (
            duplicate_extra_rows
        )
        self.missing_field = missing_field
        self.scripts: list[str] = []

    def _validate_database_uri(
        self,
        value: str,
    ) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(
        self,
        value: str,
    ) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        fields = list(EXPECTED_FIELDS)
        if self.missing_field is not None:
            fields.remove(self.missing_field)

        return RawDataBatch(
            source_id="fake",
            source_type=SourceType.DOLPHINDB,
            source_object_name=source_object_name,
            raw_fields=fields,
            records=[],
        )

    def run_readonly_query(
        self,
        script: str,
    ) -> Any:
        normalized = " ".join(script.split())
        self.scripts.append(normalized)

        if "not isNull" in normalized:
            raise AssertionError(
                "DolphinDB空值判断仍有逻辑优先级歧义。"
            )

        if "nunique(stock_code" in normalized:
            return [{
                "row_count": 5541,
                "stock_count": 5541,
                "min_snapshot_date": "2026-06-19",
                "max_snapshot_date": "2026-06-19",
                "min_update_date": "2026-04-01",
                "max_update_date": "2026-06-17",
                "min_listing_date": "1990-12-19",
                "max_listing_date": "2026-06-18",
                "first_imported_at":
                    "2026-06-19T19:36:51.269",
                "last_imported_at":
                    "2026-06-19T19:36:51.269",
            }]

        if (
            "group by snapshot_date" in normalized
            and "stock_code" not in normalized
        ):
            return [{
                "snapshot_date": "2026-06-19",
                "row_count": 5541,
            }]

        if "group by report_period" in normalized:
            return [
                {
                    "report_period": float("nan"),
                    "row_count": 13,
                },
                {
                    "report_period": 3,
                    "row_count": 5491,
                },
                {
                    "report_period": 9,
                    "row_count": 11,
                },
                {
                    "report_period": 12,
                    "row_count": 26,
                },
            ]

        if "group by market" in normalized:
            return [
                {"market": "sh", "row_count": 2300},
                {"market": "sz", "row_count": 3200},
                {"market": "bj", "row_count": 41},
            ]

        if "group by source_file" in normalized:
            return [{
                "source_file":
                    "2026-06-19更新简化个股基本面数据.xlsx",
                "row_count": 5541,
                "min_snapshot_date": "2026-06-19",
                "max_snapshot_date": "2026-06-19",
                "first_imported_at":
                    "2026-06-19T19:36:51.269",
                "last_imported_at":
                    "2026-06-19T19:36:51.269",
            }]

        if (
            "sum(isNull(" in normalized
            and "_null_count" in normalized
        ):
            return {
                f"{field}_null_count": (
                    5541 if field == "zpg" else 0
                )
                for field in EXPECTED_FIELDS
            }

        if "duplicate_group_count" in normalized:
            return [{
                "duplicate_group_count": (
                    1
                    if self.duplicate_extra_rows
                    else 0
                ),
                "duplicate_extra_row_count":
                    self.duplicate_extra_rows,
            }]

        if (
            "count(*) as duplicate_count" in normalized
            and "top 20" in normalized
        ):
            return (
                [{
                    "stock_code": "000001",
                    "snapshot_date": "2026-06-19",
                    "duplicate_count": 2,
                }]
                if self.duplicate_extra_rows
                else []
            )

        if "select top 20" in normalized:
            return [{
                "stock_code": "000001",
                "stock_name": "平安银行",
                "market": "sz",
                "snapshot_date": "2026-06-19",
                "update_date": "2026-04-25",
                "report_period": 3,
            }]

        if "select count(*) as row_count" in normalized:
            if (
                "net_assets / "
                "(total_shares * 10.0)"
                in normalized
            ):
                return [{"row_count": 5000}]

            if (
                "net_assets / total_shares"
                in normalized
            ):
                return [{"row_count": 10}]

            if (
                "not(isNull(net_assets))"
                in normalized
                and "adjusted_nav_per_share"
                in normalized
            ):
                return [{"row_count": 5100}]

            if (
                "after_tax_profit" in normalized
                and "abs(after_tax_profit" in normalized
            ):
                return [{"row_count": 1000}]

            if (
                "after_tax_profit" in normalized
                and "not(isNull(net_profit))"
                in normalized
            ):
                return [{"row_count": 5400}]

            return [{"row_count": 0}]

        raise AssertionError(
            f"未识别的查询：{normalized}"
        )


class TestFundamentalProfiler(unittest.TestCase):
    def test_collect_builds_report(self) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()

        self.assertEqual(
            report.summary["row_count"],
            5541,
        )
        self.assertEqual(
            report.summary["stock_count"],
            5541,
        )
        self.assertTrue(
            report.allows_current_snapshot_research
        )
        self.assertTrue(
            report.blocks_strict_historical_backtest
        )

    def test_schema_matches_54_fields(self) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()

        self.assertEqual(
            report.schema_comparison[
                "actual_field_count"
            ],
            54,
        )
        self.assertTrue(
            report.schema_comparison[
                "field_order_matches"
            ]
        )

    def test_missing_required_field_fails(self) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(
                missing_field="stock_code"
            ),
        ).collect()

        self.assertEqual(
            report.overall_status.value,
            "FAILED",
        )
        self.assertFalse(
            report.allows_current_snapshot_research
        )

    def test_duplicate_key_fails(self) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(
                duplicate_extra_rows=1
            ),
        ).collect()

        self.assertEqual(
            report.overall_status.value,
            "FAILED",
        )

    def test_report_period_candidate_detected(self) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()

        item = next(
            value
            for value
            in report.pending_confirmations
            if value["category"]
            == "FUNDAMENTAL_REPORT_PERIOD"
        )
        self.assertTrue(
            item["evidence"][
                "period_month_candidate"
            ]
        )
        self.assertEqual(
            item["evidence"]["observed_values"],
            [3, 9, 12],
        )

    def test_count_where_normalizes_not_isnull(
        self,
    ) -> None:
        adapter = FakeFundamentalAdapter()
        DolphinDBFundamentalProfiler(
            adapter=adapter,
        ).collect()

        self.assertTrue(
            any(
                "not(isNull(update_date))"
                in script
                for script in adapter.scripts
            )
        )
        self.assertTrue(
            all(
                "not isNull" not in script
                for script in adapter.scripts
            )
        )

    def test_unit_candidate_prefers_thousand_cny(
        self,
    ) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()

        units = report.unit_candidate_summary
        self.assertGreater(
            units[
                "money_thousand_cny_and_shares_10k_match_ratio"
            ],
            units[
                "money_10k_cny_and_shares_10k_match_ratio"
            ],
        )

    def test_pending_time_confirmation_exists(
        self,
    ) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()

        categories = {
            item["category"]
            for item in report.pending_confirmations
        }
        self.assertIn(
            "FUNDAMENTAL_AVAILABLE_AT",
            categories,
        )
        self.assertIn(
            "FUNDAMENTAL_COMPANY_ID",
            categories,
        )

    def test_markdown_contains_blocking_notice(
        self,
    ) -> None:
        report = DolphinDBFundamentalProfiler(
            adapter=FakeFundamentalAdapter(),
        ).collect()
        markdown = render_markdown(report)

        self.assertIn(
            "阻断严格历史回测",
            markdown,
        )
        self.assertIn(
            "不得用于严格历史点时回测",
            markdown,
        )

    def test_json_safe_converts_nan(self) -> None:
        value = _json_safe({"x": float("nan")})
        self.assertIsNone(value["x"])


if __name__ == "__main__":
    unittest.main()
