"""测试A股日K标准映射插件与读取服务。"""
# 测试模块总览：验证 `test_dolphindb_daily_k_service` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dataset_registry import (
    DatasetRegistration,
)
from a_stock_quant.dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_daily_k.json"
)


# 测试类 `FakeDailyKAdapter`：集中验证 `test_dolphindb_daily_k_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeDailyKAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self) -> None:
        self.scripts: list[str] = []

    # 测试函数 `_validate_database_uri`：封装 `_validate_database_uri` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：value。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _validate_database_uri(self, value: str) -> None:
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
    def _validate_table_name(self, value: str) -> None:
        # 测试分支：根据 `not value.replace('_', '').isalnum()` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        normalized = " ".join(script.split())

        # 测试分支：根据 `'select top 1 close' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select top 1 close" in normalized:
            # 测试分支：根据 `'"000001"' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if '"000001"' in normalized:
                return [{"close": 10.0}]
            return []

        # 测试分支：根据 `'select top' in normalized and 'stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select top" in normalized and "stock_code" in normalized:
            # 测试分支：根据 `'"000001"' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if '"000001"' in normalized:
                return [
                    self._row(
                        stock_code="000001",
                        trade_date="2026-05-28",
                        close=11.0,
                        price_change=1.0,
                        pct_change=-10.0,
                    ),
                    self._row(
                        stock_code="000001",
                        trade_date="2026-05-29",
                        close=12.1,
                        price_change=1.1,
                        pct_change=-10.0,
                    ),
                ]

            # 测试分支：根据 `'"000002"' in normalized` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if '"000002"' in normalized:
                return [
                    self._row(
                        stock_code="000002",
                        trade_date="2026-05-29",
                        close=20.0,
                        price_change=0.0,
                        pct_change=0.0,
                    )
                ]

        raise AssertionError(f"未识别的查询：{normalized}")

    # 测试函数 `_row`：封装 `_row` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：stock_code、trade_date、close、price_change、pct_change。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    @staticmethod
    def _row(
        *,
        stock_code: str,
        trade_date: str,
        close: float,
        price_change: float,
        pct_change: float,
    ) -> dict[str, Any]:
        row = {
            "stock_code": stock_code,
            "trade_date": trade_date,
            "open": close - 0.2,
            "high": close + 0.3,
            "low": close - 0.4,
            "close": close,
            "amount": close * 1_000,
            "volume": 1_000,
            "BS": "B",
            "chanlun": "X",
            "turnover_rate": 0.1,
            "pct_change": pct_change,
            "price_change": price_change,
            "pct_3d": None,
            "pct_5d": None,
            "pct_10d": None,
            "pct_20d": None,
            "pct_30d": None,
            "ma5": close,
            "ma10": close,
            "ma20": close,
            "ma30": close,
            "ma60": close,
            "ma120": close,
            "ma250": close,
            "macd": 0.1,
            "dif": 0.1,
            "dea": 0.1,
            "k": 50.0,
            "d": 50.0,
            "j": 50.0,
            "rsi6": 50.0,
            "rsi12": 50.0,
            "rsi24": 50.0,
            "bias": 0.0,
            "boll": close,
            "boll_up": close + 1,
            "boll_down": close - 1,
            "float_shares": 100.0,
            "total_shares": 200.0,
            "adj_factor": 2.0,
            "deduct_value": 1.0,
            "adj_price": close * 2.0 + 1.0,
            "dividend": None,
            "bonus_share": None,
            "convert_share": None,
            "allot_share": None,
            "allot_price": None,
        }
        return row


# 测试函数 `load_registration`：封装 `load_registration` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def load_registration() -> DatasetRegistration:
    return DatasetRegistration.from_dict(
        json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    )


# 测试类 `TestDailyKReadRequest`：集中验证 `test_dolphindb_daily_k_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyKReadRequest(unittest.TestCase):
    # 测试函数 `test_rejects_duplicate_instruments`：验证 `rejects、duplicate、instruments` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_rejects_duplicate_instruments(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DailyKReadRequest(
                instrument_ids=("000001", "000001"),
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 29),
            )

    # 测试函数 `test_rejects_invalid_date_range`：验证 `rejects、invalid、date、range` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_rejects_invalid_date_range(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 30),
                end_date=date(2026, 5, 29),
            )


# 测试类 `TestDailyKStandardizedService`：集中验证 `test_dolphindb_daily_k_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyKStandardizedService(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.adapter = FakeDailyKAdapter()
        self.service = DolphinDBDailyKStandardizedService(
            self.adapter,
            load_registration(),
        )

    # 测试函数 `test_reads_and_maps_daily_bar`：验证 `reads、and、maps、daily、bar` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_reads_and_maps_daily_bar(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertEqual(batch.source_row_count, 2)
        self.assertEqual(
            batch.standardized_record_count,
            2,
        )
        first = batch.records[0]
        daily = first.canonical_objects["DailyBar"]

        self.assertEqual(daily["instrument_id"], "000001")
        self.assertEqual(
            daily["trade_date"],
            date(2026, 5, 28),
        )
        self.assertEqual(daily["pre_close_raw_cny"], 10.0)
        self.assertEqual(daily["pct_change_pct"], 10.0)
        self.assertEqual(daily["volume_lots"], 10.0)
        self.assertEqual(daily["vwap_raw_cny"], 11.0)

    # 测试函数 `test_maps_ownership_and_market_cap`：验证 `maps、ownership、and、market、cap` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_maps_ownership_and_market_cap(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        first = batch.records[0]
        ownership = first.canonical_objects[
            "OwnershipSnapshot"
        ]
        daily = first.canonical_objects["DailyBar"]

        self.assertEqual(
            ownership["float_shares"],
            1_000_000.0,
        )
        self.assertEqual(
            ownership["total_shares"],
            2_000_000.0,
        )
        self.assertEqual(
            daily["float_market_cap_cny"],
            11_000_000.0,
        )
        self.assertEqual(
            daily["total_market_cap_cny"],
            22_000_000.0,
        )

    # 测试函数 `test_keeps_pending_fields_in_source_extensions`：验证 `keeps、pending、fields、in、source、extensions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_keeps_pending_fields_in_source_extensions(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        extensions = batch.records[0].source_extensions

        self.assertEqual(extensions["pct_change"], -10.0)
        self.assertEqual(extensions["adj_price"], 23.0)
        self.assertEqual(extensions["BS"], "B")
        self.assertEqual(extensions["ma5"], 11.0)

    # 测试函数 `test_marks_known_source_pct_semantics`：验证 `marks、known、source、pct、semantics` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_marks_known_source_pct_semantics(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        flags = batch.records[0].quality_flags

        self.assertIn(
            "SOURCE_PCT_CHANGE_SIGN_INVERTED",
            flags,
        )
        self.assertNotIn(
            "SOURCE_PRICE_CHANGE_MISMATCH",
            flags,
        )
        self.assertNotIn(
            "SOURCE_ADJ_FORMULA_MISMATCH",
            flags,
        )

    # 测试函数 `test_context_rolls_forward_between_rows`：验证 `context、rolls、forward、between、rows` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_context_rolls_forward_between_rows(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 29),
            )
        )
        second = batch.records[1]
        daily = second.canonical_objects["DailyBar"]

        self.assertEqual(daily["pre_close_raw_cny"], 11.0)
        self.assertEqual(daily["pct_change_pct"], 10.0)

    # 测试函数 `test_multiple_instruments_are_supported`：验证 `multiple、instruments、are、supported` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_multiple_instruments_are_supported(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001", "000002"),
                start_date=date(2026, 5, 29),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertEqual(
            batch.standardized_record_count,
            3,
        )
        ids = [
            item.primary_key["instrument_id"]
            for item in batch.records
        ]
        self.assertEqual(
            ids,
            ["000001", "000001", "000002"],
        )

    # 测试函数 `test_first_record_without_history_gets_flag`：验证 `first、record、without、history、gets、flag` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_first_record_without_history_gets_flag(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000002",),
                start_date=date(2026, 5, 29),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertIn(
            "MISSING_PRE_CLOSE",
            batch.records[0].quality_flags,
        )
        self.assertIsNone(
            batch.records[0]
            .canonical_objects["DailyBar"][
                "pct_change_pct"
            ]
        )

    # 测试函数 `test_request_cannot_exceed_coverage_end`：验证 `request、cannot、exceed、coverage、end` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_request_cannot_exceed_coverage_end(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.service.read(
                DailyKReadRequest(
                    instrument_ids=("000001",),
                    start_date=date(2026, 5, 29),
                    end_date=date(2026, 5, 30),
                )
            )

    # 测试函数 `test_lineage_contains_mapping_versions`：验证 `lineage、contains、mapping、versions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_lineage_contains_mapping_versions(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        lineage = batch.records[0].lineage

        self.assertTrue(lineage)
        self.assertTrue(
            all(
                item["mapping_version"] == "0.2.0"
                for item in lineage
            )
        )
        self.assertTrue(
            all(
                item["dictionary_revision"] == "0.5"
                for item in lineage
            )
        )


if __name__ == "__main__":
    unittest.main()
