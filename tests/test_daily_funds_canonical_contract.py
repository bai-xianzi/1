# 测试模块总览：验证 `test_daily_funds_canonical_contract` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试类 `DailyFundsCanonicalContractTests`：集中验证 `test_daily_funds_canonical_contract` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class DailyFundsCanonicalContractTests(unittest.TestCase):
    # 测试函数 `test_contract_passes_with_warnings`：验证 `contract、passes、with、warnings` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_passes_with_warnings(self) -> None:
        result = validate_contract(CONTRACT_PATH, DICTIONARY_PATH)
        self.assertEqual(result["overall_status"], "PASSED_WITH_WARNINGS")
        self.assertEqual(result["dataset_count"], 7)
        self.assertEqual(result["ready_with_warning_count"], 7)
        self.assertEqual(result["blocked_count"], 0)
        self.assertEqual(result["issues"], [])

    # 测试函数 `test_hq_is_supplemental_not_authoritative`：验证 `hq、is、supplemental、not、authoritative` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_hq_is_supplemental_not_authoritative(self) -> None:
        hq = load_contract(CONTRACT_PATH).datasets["hq"]
        self.assertEqual(hq["source_role"], "SUPPLEMENTAL_RECONCILIATION")
        self.assertEqual(hq["canonical_object"], "DailyBar")

    # 测试函数 `test_kphq_uses_date_only_without_fabricated_time`：验证 `kphq、uses、date、only、without、fabricated、time` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_classification_snapshot_is_ready_and_not_membership`：验证 `classification、snapshot、is、ready、and、not、membership` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_classification_snapshot_is_ready_and_not_membership(self) -> None:
        contract = load_contract(CONTRACT_PATH)
        # 参数化循环：逐项使用 `('hy', 'gn', 'kphy', 'kpgn')` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for dataset_id in ("hy", "gn", "kphy", "kpgn"):
            dataset = contract.datasets[dataset_id]
            self.assertEqual(
                dataset["canonical_object"],
                "ClassificationMarketSnapshot",
            )
            self.assertEqual(dataset["readiness"], "READY_WITH_WARNING")
            self.assertIn("average_shares", dataset["source_extensions"])

    # 测试函数 `test_zj_preserves_source_outflow_sign`：验证 `zj、preserves、source、outflow、sign` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_zj_preserves_source_outflow_sign(self) -> None:
        contract = load_contract(CONTRACT_PATH)
        self.assertEqual(
            contract.datasets["zj"]["sign_policy"],
            "PRESERVE_SOURCE_SIGN",
        )

    # 测试函数 `test_dictionary_revision_drift_fails`：验证 `dictionary、revision、drift、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_dictionary_revision_drift_fails(self) -> None:
        payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        payload["dictionary_revision"] = "0.0.0"
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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

    # 测试函数 `test_unknown_mapping_status_fails`：验证 `unknown、mapping、status、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_mapping_status_fails(self) -> None:
        payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
        payload = copy.deepcopy(payload)
        payload["datasets"]["hq"]["mappings"][0]["status"] = "MAGIC"
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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
