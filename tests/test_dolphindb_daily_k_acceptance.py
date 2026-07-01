"""测试真实日K标准化抽样验收分析器。"""
# 测试模块总览：验证 `test_dolphindb_daily_k_acceptance` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import MappingStatus, SourceType
from a_stock_quant.dataset_registry import (
    DatasetRegistration,
    FieldMappingRule,
)
from a_stock_quant.dolphindb_daily_k_acceptance import (
    AcceptanceThresholds,
    DailyKAcceptanceAnalyzer,
    _json_safe,
)


# 测试类 `FakeRecord`：集中验证 `test_dolphindb_daily_k_acceptance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
@dataclass
class FakeRecord:
    source_record_id: str
    canonical_objects: dict[str, dict[str, Any]]
    source_extensions: dict[str, Any]
    quality_flags: list[str]
    lineage: list[dict[str, Any]]

    # 测试函数 `to_dict`：封装 `to_dict` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def to_dict(self) -> dict[str, Any]:
        return {
            "source_record_id": self.source_record_id,
            "canonical_objects": self.canonical_objects,
            "source_extensions": self.source_extensions,
            "quality_flags": self.quality_flags,
            "lineage": self.lineage,
        }


# 测试类 `FakeBatch`：集中验证 `test_dolphindb_daily_k_acceptance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
@dataclass
class FakeBatch:
    dataset_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    request: dict[str, Any]
    source_row_count: int
    standardized_record_count: int
    records: list[FakeRecord]
    warnings: list[str]


# 测试函数 `make_registration`：封装 `make_registration` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_registration() -> DatasetRegistration:
    return DatasetRegistration(
        dataset_id="a_stock_daily_k",
        source_type=SourceType.DOLPHINDB,
        source_locator={
            "database_uri": "dfs://TEST",
            "table_name": "daily",
        },
        dataset_mode="SNAPSHOT",
        coverage_version="a_stock_daily_k@2026-05-29",
        schema_version="1.0.0",
        mapping_version="0.2.0",
        dictionary_revision="0.5",
        date_field="trade_date",
        entity_field="stock_code",
        primary_key_fields=("stock_code", "trade_date"),
        source_fields=(
            "stock_code",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "float_shares",
            "total_shares",
            "pct_change",
            "adj_price",
        ),
        canonical_objects=(
            "DailyBar",
            "OwnershipSnapshot",
        ),
        field_mappings=(
            FieldMappingRule(
                source_fields=("stock_code",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="instrument_id",
            ),
            FieldMappingRule(
                source_fields=("pct_change",),
                status=MappingStatus.PENDING_CONFIRMATION,
                target_object="DailyBar",
                canonical_field="pct_change_pct",
            ),
            FieldMappingRule(
                source_fields=("adj_price",),
                status=MappingStatus.PENDING_CONFIRMATION,
            ),
        ),
    )


# 测试函数 `make_record`：封装 `make_record` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：quality_flags、missing_daily_field、computed_mismatch、pending_missing、invalid_lineage。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_record(
    *,
    quality_flags: list[str] | None = None,
    missing_daily_field: str | None = None,
    computed_mismatch: bool = False,
    pending_missing: bool = False,
    invalid_lineage: bool = False,
) -> FakeRecord:
    daily = {
        "instrument_id": "000001",
        "trade_date": date(2026, 5, 29),
        "open_raw_cny": 10.0,
        "high_raw_cny": 11.5,
        "low_raw_cny": 9.8,
        "close_raw_cny": 11.0,
        "pre_close_raw_cny": 10.0,
        "pct_change_pct": 10.0,
        "volume_shares": 1_000.0,
        "volume_lots": 10.0,
        "amount_cny": 11_000.0,
        "vwap_raw_cny": 11.0,
        "float_market_cap_cny": 11_000_000.0,
        "total_market_cap_cny": 22_000_000.0,
    }
    ownership = {
        "instrument_id": "000001",
        "as_of_date": date(2026, 5, 29),
        "float_shares": 1_000_000.0,
        "total_shares": 2_000_000.0,
    }

    # 测试分支：根据 `missing_daily_field is not None` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if missing_daily_field is not None:
        daily.pop(missing_daily_field)

    # 测试分支：根据 `computed_mismatch` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if computed_mismatch:
        daily["volume_lots"] = 99.0

    lineage = [{
        "target_object": "DailyBar",
        "canonical_field": "close_raw_cny",
        "source_fields": ["close"],
        "transform_id": "identity",
        "transform_params": {},
        "mapping_version": (
            "bad" if invalid_lineage else "0.2.0"
        ),
        "dictionary_revision": "0.5",
    }]

    extensions = {
        "pct_change": -10.0,
        "adj_price": 23.0,
    }
    # 测试分支：根据 `pending_missing` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if pending_missing:
        extensions.pop("adj_price")

    return FakeRecord(
        source_record_id="000001|2026-05-29",
        canonical_objects={
            "DailyBar": daily,
            "OwnershipSnapshot": ownership,
        },
        source_extensions=extensions,
        quality_flags=quality_flags or [
            "SOURCE_PCT_CHANGE_SIGN_INVERTED"
        ],
        lineage=lineage,
    )


# 测试函数 `make_batch`：封装 `make_batch` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：record。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_batch(record: FakeRecord) -> FakeBatch:
    return FakeBatch(
        dataset_id="a_stock_daily_k",
        coverage_version="a_stock_daily_k@2026-05-29",
        mapping_version="0.2.0",
        dictionary_revision="0.5",
        request={
            "instrument_ids": ["000001"],
            "start_date": date(2026, 5, 29),
            "end_date": date(2026, 5, 29),
        },
        source_row_count=1,
        standardized_record_count=1,
        records=[record],
        warnings=[],
    )


# 测试类 `TestAcceptanceThresholds`：集中验证 `test_dolphindb_daily_k_acceptance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestAcceptanceThresholds(unittest.TestCase):
    # 测试函数 `test_invalid_coverage_rejected`：验证 `invalid、coverage、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_coverage_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(Exception)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(Exception):
            AcceptanceThresholds(
                minimum_daily_bar_coverage=1.1
            )


# 测试类 `TestDailyKAcceptanceAnalyzer`：集中验证 `test_dolphindb_daily_k_acceptance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyKAcceptanceAnalyzer(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.analyzer = DailyKAcceptanceAnalyzer(
            make_registration()
        )

    # 测试函数 `test_valid_batch_passes`：验证 `valid、batch、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_valid_batch_passes(self) -> None:
        report = self.analyzer.analyze(
            make_batch(make_record())
        )

        self.assertEqual(report["overall_status"], "PASSED")
        self.assertFalse(report["blocks_downstream"])
        self.assertEqual(
            report["computed_consistency"][
                "total_mismatch_count"
            ],
            0,
        )

    # 测试函数 `test_known_sign_inversion_is_informational`：验证 `known、sign、inversion、is、informational` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_known_sign_inversion_is_informational(self) -> None:
        report = self.analyzer.analyze(
            make_batch(make_record())
        )

        self.assertEqual(
            report["quality_flag_summary"][
                "blocking_flag_count"
            ],
            0,
        )
        self.assertEqual(
            report["quality_flag_summary"][
                "informational_flag_count"
            ],
            1,
        )

    # 测试函数 `test_missing_daily_field_fails`：验证 `missing、daily、field、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_daily_field_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(
                    missing_daily_field="close_raw_cny"
                )
            )
        )

        self.assertEqual(report["overall_status"], "FAILED")
        self.assertTrue(report["blocks_downstream"])

    # 测试函数 `test_computed_mismatch_fails`：验证 `computed、mismatch、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_computed_mismatch_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(computed_mismatch=True)
            )
        )

        self.assertGreater(
            report["computed_consistency"][
                "total_mismatch_count"
            ],
            0,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    # 测试函数 `test_blocking_quality_flag_fails`：验证 `blocking、quality、flag、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_blocking_quality_flag_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(
                    quality_flags=[
                        "SOURCE_ADJ_FORMULA_MISMATCH"
                    ]
                )
            )
        )

        self.assertEqual(
            report["quality_flag_summary"][
                "blocking_flag_count"
            ],
            1,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    # 测试函数 `test_pending_extension_missing_fails`：验证 `pending、extension、missing、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_pending_extension_missing_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(pending_missing=True)
            )
        )

        self.assertLess(
            report["pending_extension_coverage"][
                "coverage"
            ],
            1.0,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    # 测试函数 `test_invalid_lineage_fails`：验证 `invalid、lineage、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_lineage_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(invalid_lineage=True)
            )
        )

        self.assertEqual(
            report["lineage_coverage"][
                "invalid_lineage_count"
            ],
            1,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    # 测试函数 `test_json_safe_converts_non_finite_numbers`：验证 `json、safe、converts、non、finite、numbers` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_json_safe_converts_non_finite_numbers(self) -> None:
        value = _json_safe({
            "nan": float("nan"),
            "positive_infinity": float("inf"),
            "negative_infinity": float("-inf"),
            "normal": 1.25,
        })

        self.assertIsNone(value["nan"])
        self.assertIsNone(value["positive_infinity"])
        self.assertIsNone(value["negative_infinity"])
        self.assertEqual(value["normal"], 1.25)

    # 测试函数 `test_json_safe_converts_nested_dates`：验证 `json、safe、converts、nested、dates` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_json_safe_converts_nested_dates(self) -> None:
        value = _json_safe({
            "a": date(2026, 5, 29),
            "b": [date(2026, 5, 28)],
        })

        self.assertEqual(value["a"], "2026-05-29")
        self.assertEqual(value["b"], ["2026-05-28"])


if __name__ == "__main__":
    unittest.main()
