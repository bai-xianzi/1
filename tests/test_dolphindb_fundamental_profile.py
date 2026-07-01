"""测试DolphinDB基本面快照发现与画像。"""
# 测试模块总览：验证 `test_dolphindb_fundamental_profile` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

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


# 测试类 `FakeFundamentalAdapter`：集中验证 `test_dolphindb_fundamental_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeFundamentalAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：duplicate_extra_rows、missing_field。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `_validate_database_uri`：封装 `_validate_database_uri` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：value。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _validate_database_uri(
        self,
        value: str,
    ) -> None:
        # 测试分支：根据 `not value.startswith('dfs://')` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    # 测试函数 `_validate_table_name`：封装 `_validate_table_name` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：value。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _validate_table_name(
        self,
        value: str,
    ) -> None:
        # 测试分支：根据 `not value.replace('_', '').isalnum()` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    # 测试函数 `read_raw`：封装 `read_raw` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：source_object_name、**kwargs。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        fields = list(EXPECTED_FIELDS)
        # 测试分支：根据 `self.missing_field is not None` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if self.missing_field is not None:
            fields.remove(self.missing_field)

        return RawDataBatch(
            source_id="fake",
            source_type=SourceType.DOLPHINDB,
            source_object_name=source_object_name,
            raw_fields=fields,
            records=[],
        )

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(
        self,
        script: str,
    ) -> Any:
        normalized = " ".join(script.split())
        self.scripts.append(normalized)

        # 测试分支：根据 `'not isNull' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "not isNull" in normalized:
            raise AssertionError(
                "DolphinDB空值判断仍有逻辑优先级歧义。"
            )

        # 测试分支：根据 `'nunique(stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'group by snapshot_date' in normalized and 'stock_code' not in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if (
            "group by snapshot_date" in normalized
            and "stock_code" not in normalized
        ):
            return [{
                "snapshot_date": "2026-06-19",
                "row_count": 5541,
            }]

        # 测试分支：根据 `'group by report_period' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'group by market' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "group by market" in normalized:
            return [
                {"market": "sh", "row_count": 2300},
                {"market": "sz", "row_count": 3200},
                {"market": "bj", "row_count": 41},
            ]

        # 测试分支：根据 `'group by source_file' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'sum(isNull(' in normalized and '_null_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'duplicate_group_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'count(*) as duplicate_count' in normalized and 'top 20' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'select top 20' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select top 20" in normalized:
            return [{
                "stock_code": "000001",
                "stock_name": "平安银行",
                "market": "sz",
                "snapshot_date": "2026-06-19",
                "update_date": "2026-04-25",
                "report_period": 3,
            }]

        # 测试分支：根据 `'select count(*) as row_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select count(*) as row_count" in normalized:
            # 测试分支：根据 `'net_assets / (total_shares * 10.0)' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if (
                "net_assets / "
                "(total_shares * 10.0)"
                in normalized
            ):
                return [{"row_count": 5000}]

            # 测试分支：根据 `'net_assets / total_shares' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if (
                "net_assets / total_shares"
                in normalized
            ):
                return [{"row_count": 10}]

            # 测试分支：根据 `'not(isNull(net_assets))' in normalized and 'adjusted_nav_per_share' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if (
                "not(isNull(net_assets))"
                in normalized
                and "adjusted_nav_per_share"
                in normalized
            ):
                return [{"row_count": 5100}]

            # 测试分支：根据 `'after_tax_profit' in normalized and 'abs(after_tax_profit' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if (
                "after_tax_profit" in normalized
                and "abs(after_tax_profit" in normalized
            ):
                return [{"row_count": 1000}]

            # 测试分支：根据 `'after_tax_profit' in normalized and 'not(isNull(net_profit))' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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


# 测试类 `TestFundamentalProfiler`：集中验证 `test_dolphindb_fundamental_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestFundamentalProfiler(unittest.TestCase):
    # 测试函数 `test_collect_builds_report`：验证 `collect、builds、report` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_schema_matches_54_fields`：验证 `schema、matches、54、fields` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_missing_required_field_fails`：验证 `missing、required、field、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_duplicate_key_fails`：验证 `duplicate、key、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_report_period_candidate_detected`：验证 `report、period、candidate、detected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_count_where_normalizes_not_isnull`：验证 `count、where、normalizes、not、isnull` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_unit_candidate_prefers_thousand_cny`：验证 `unit、candidate、prefers、thousand、cny` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_pending_time_confirmation_exists`：验证 `pending、time、confirmation、exists` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_markdown_contains_blocking_notice`：验证 `markdown、contains、blocking、notice` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_json_safe_converts_nan`：验证 `json、safe、converts、nan` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_json_safe_converts_nan(self) -> None:
        value = _json_safe({"x": float("nan")})
        self.assertIsNone(value["x"])


if __name__ == "__main__":
    unittest.main()
