"""测试DolphinDB数据集覆盖边界核验。"""
# 测试模块总览：验证 `test_dolphindb_dataset_coverage` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

from __future__ import annotations

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

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.dolphindb_dataset_coverage import (
    DolphinDBDatasetCoverageVerifier,
    _extract_date_from_filename,
)


# 测试类 `FakeCoverageAdapter`：集中验证 `test_dolphindb_dataset_coverage` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeCoverageAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：max_date。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        max_date: str = "2026-05-29",
    ) -> None:
        self.max_date = max_date
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
            raise DataContractError("bad name")

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        normalized = " ".join(script.split())

        # 测试分支：根据 `'min(trade_date)' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "min(trade_date)" in normalized:
            return [{
                "row_count": 16_548_275,
                "min_data_date": "1990-12-19",
                "max_data_date": self.max_date,
            }]

        # 测试分支：根据 `'select distinct stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select distinct stock_code" in normalized:
            return [{"entity_count": 5_523}]

        raise AssertionError(f"未识别的查询：{normalized}")


# 测试类 `TestDatasetCoverageVerifier`：集中验证 `test_dolphindb_dataset_coverage` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDatasetCoverageVerifier(unittest.TestCase):
    # 测试函数 `_verifier`：封装 `_verifier` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：max_date、cutoff、source_dirs、import_logs。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _verifier(
        self,
        *,
        max_date: str = "2026-05-29",
        cutoff: date = date(2026, 5, 29),
        source_dirs=(),
        import_logs=(),
    ) -> DolphinDBDatasetCoverageVerifier:
        return DolphinDBDatasetCoverageVerifier(
            adapter=FakeCoverageAdapter(max_date),
            dataset_id="a_stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            table_name="stock_daily_k",
            date_field="trade_date",
            entity_field="stock_code",
            declared_cutoff_date=cutoff,
            source_dirs=source_dirs,
            import_logs=import_logs,
        )

    # 测试函数 `test_matching_snapshot_cutoff_passes`：验证 `matching、snapshot、cutoff、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_matching_snapshot_cutoff_passes(self) -> None:
        report = self._verifier().collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.PASSED,
        )
        self.assertFalse(report.blocks_downstream)
        self.assertEqual(
            report.coverage_evaluation["coverage_version"],
            "a_stock_daily_k@2026-05-29",
        )

    # 测试函数 `test_calendar_lag_is_informational_only`：验证 `calendar、lag、is、informational、only` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_calendar_lag_is_informational_only(self) -> None:
        report = self._verifier().collect()

        self.assertFalse(
            report.coverage_evaluation[
                "calendar_lag_is_blocking"
            ]
        )
        self.assertFalse(report.blocks_downstream)

    # 测试函数 `test_database_before_declared_cutoff_fails`：验证 `database、before、declared、cutoff、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_database_before_declared_cutoff_fails(self) -> None:
        report = self._verifier(
            max_date="2026-05-28",
        ).collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.FAILED,
        )
        self.assertTrue(report.blocks_downstream)

    # 测试函数 `test_database_after_declared_cutoff_warns`：验证 `database、after、declared、cutoff、warns` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_database_after_declared_cutoff_warns(self) -> None:
        report = self._verifier(
            max_date="2026-05-30",
        ).collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.WARNING,
        )
        self.assertFalse(report.blocks_downstream)

    # 测试函数 `test_source_inventory_detects_pending_date`：验证 `source、inventory、detects、pending、date` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_source_inventory_detects_pending_date(self) -> None:
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "daily_2026-05-29.csv").write_text(
                "x",
                encoding="utf-8",
            )
            (root / "daily_20260530.xlsx").write_text(
                "x",
                encoding="utf-8",
            )

            report = self._verifier(
                source_dirs=[directory],
            ).collect()

        self.assertTrue(
            report.coverage_evaluation[
                "pending_import_detected"
            ]
        )
        self.assertEqual(
            report.overall_status,
            QualityStatus.WARNING,
        )

    # 测试函数 `test_import_log_inventory_reads_last_line`：验证 `import、log、inventory、reads、last、line` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_import_log_inventory_reads_last_line(self) -> None:
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "import_success.csv"
            path.write_text(
                "file,status\nold.csv,ok\nnew.csv,ok\n",
                encoding="utf-8",
            )

            report = self._verifier(
                import_logs=[str(path)],
            ).collect()

        self.assertEqual(
            report.import_log_inventory[0][
                "last_nonempty_line"
            ],
            "new.csv,ok",
        )

    # 测试函数 `test_filename_date_extractor`：验证 `filename、date、extractor` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_filename_date_extractor(self) -> None:
        self.assertEqual(
            _extract_date_from_filename(
                "A股日K_2026年5月29日.xlsx"
            ),
            date(2026, 5, 29),
        )
        self.assertEqual(
            _extract_date_from_filename("daily_20260530.csv"),
            date(2026, 5, 30),
        )

    # 测试函数 `test_entity_count_uses_separate_query`：验证 `entity、count、uses、separate、query` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_entity_count_uses_separate_query(self) -> None:
        adapter = FakeCoverageAdapter()
        report = DolphinDBDatasetCoverageVerifier(
            adapter=adapter,
            dataset_id="a_stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            table_name="stock_daily_k",
            date_field="trade_date",
            entity_field="stock_code",
            declared_cutoff_date=date(2026, 5, 29),
        ).collect()

        self.assertEqual(
            report.database_summary["entity_count"],
            5_523,
        )
        self.assertEqual(len(adapter.scripts), 2)
        self.assertNotIn(
            "count(distinct",
            " ".join(adapter.scripts).lower(),
        )
        self.assertIn(
            "select distinct stock_code",
            " ".join(adapter.scripts).lower(),
        )

    # 测试函数 `test_invalid_identifier_is_rejected`：验证 `invalid、identifier、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_identifier_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DolphinDBDatasetCoverageVerifier(
                adapter=FakeCoverageAdapter(),
                dataset_id="a_stock_daily_k",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
                table_name="stock_daily_k",
                date_field="trade_date;drop",
                entity_field="stock_code",
                declared_cutoff_date=date(2026, 5, 29),
            )


if __name__ == "__main__":
    unittest.main()
