# 测试模块总览：验证 `test_market_state_real_acceptance` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试类 `TestMarketStateRealAcceptance`：集中验证 `test_market_state_real_acceptance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestMarketStateRealAcceptance(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_plan_loads`：验证 `plan、loads` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_plan_loads(self):
        self.assertEqual(self.plan.task_id, "TASK_019C")
        self.assertEqual(self.plan.mode, REAL_FEATURE_ACCEPTANCE_MODE)

    # 测试函数 `test_plan_has_two_required_datasets`：验证 `plan、has、two、required、datasets` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_plan_has_two_required_datasets(self):
        self.assertEqual(len(self.plan.required_datasets), 2)
        self.assertEqual(
            {item.dataset_id for item in self.plan.required_datasets},
            {"a_stock_daily_k", "hy"},
        )

    # 测试函数 `test_plan_never_claims_full_market`：验证 `plan、never、claims、full、market` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_plan_never_claims_full_market(self):
        self.assertFalse(self.plan.claim_full_market_coverage)

    # 测试函数 `test_recent_date_query_is_readonly`：验证 `recent、date、query、is、readonly` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_recent_date_query_is_readonly(self):
        script = build_recent_date_rows_query(
            self.hy_source,
            100,
        )
        assert_readonly_query(script)
        self.assertIn("select top 100", script)
        self.assertIn("dataset_id=`hy", script)

    # 测试函数 `test_presence_query_is_readonly`：验证 `presence、query、is、readonly` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_presence_query_is_readonly(self):
        script = build_date_presence_query(
            self.daily_source,
            date(2025, 12, 31),
        )
        assert_readonly_query(script)
        self.assertIn("2025.12.31", script)

    # 测试函数 `test_selector_query_is_deterministic`：验证 `selector、query、is、deterministic` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_selector_query_is_deterministic(self):
        script = build_selector_rows_query(
            self.daily_source,
            date(2025, 12, 31),
            30,
        )
        assert_readonly_query(script)
        self.assertIn("order by stock_code", script)

    # 测试函数 `test_write_query_is_rejected`：验证 `write、query、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_write_query_is_rejected(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            assert_readonly_query("delete from x")

    # 测试函数 `test_unique_dates_preserve_descending_order`：验证 `unique、dates、preserve、descending、order` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_unique_selectors_remove_empty_and_duplicate`：验证 `unique、selectors、remove、empty、and、duplicate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_daily_query_uses_current_research`：验证 `daily、query、uses、current、research` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_hy_query_uses_entity_ids`：验证 `hy、query、uses、entity、ids` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_empty_selectors_are_rejected`：验证 `empty、selectors、are、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_empty_selectors_are_rejected(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            build_feature_acceptance_query(
                self.plan.dataset("hy"),
                (),
                date(2025, 12, 31),
                self.plan.as_of_date,
            )

    # 测试函数 `test_report_contract_accepts_valid_report`：验证 `report、contract、accepts、valid、report` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_report_contract_detects_blocked_query`：验证 `report、contract、detects、blocked、query` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_plan_rejects_full_market_claim`：验证 `plan、rejects、full、market、claim` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_plan_rejects_full_market_claim(self):
        raw = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        raw["universe_policy"]["claim_full_market_coverage"] = True
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.assertRaises(DataContractError):
                load_real_feature_acceptance_plan(path)


if __name__ == "__main__":
    unittest.main()
