# 测试模块总览：验证 `test_reuse_first_policy` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.reuse_first_policy import (
    ReuseCandidateAssessment,
    ReuseCandidateType,
    ReuseDecisionRecord,
    ReuseDecisionType,
    ReviewStatus,
    load_reuse_first_policy,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "configs"
    / "engineering"
    / "reuse_first_policy_v0.json"
)


# 测试函数 `reusable_candidate`：封装 `reusable_candidate` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def reusable_candidate():
    return ReuseCandidateAssessment(
        candidate_id="existing-adapter",
        candidate_type=(
            ReuseCandidateType.EXISTING_PROJECT_COMPONENT
        ),
        name="DolphinDBDataSourceAdapter",
        source_ref="repo:src/a_stock_quant/dolphindb_adapter.py",
        version="current",
        license_id="PROJECT_INTERNAL",
        license_status=ReviewStatus.PASSED,
        security_status=ReviewStatus.PASSED,
        maintenance_status=ReviewStatus.PASSED,
        compatibility_status=ReviewStatus.PASSED,
        semantic_gap_status=ReviewStatus.PASSED_WITH_WARNINGS,
        supported_requirements=("readonly-query", "health-check"),
        gaps=("provider-plugin-protocol",),
        warnings=("thin-bridge-required",),
        evidence_refs=("repo:dolphindb_adapter.py",),
    )


# 测试类 `TestReuseFirstPolicy`：集中验证 `test_reuse_first_policy` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestReuseFirstPolicy(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self):
        self.policy = load_reuse_first_policy(POLICY_PATH)

    # 测试函数 `test_policy_is_reuse_first`：验证 `policy、is、reuse、first` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_is_reuse_first(self):
        self.assertEqual(
            self.policy.principle,
            "REUSE_FIRST_CUSTOM_BUILD_LAST",
        )

    # 测试函数 `test_custom_build_is_not_default`：验证 `custom、build、is、not、default` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_custom_build_is_not_default(self):
        self.assertFalse(
            self.policy.custom_implementation_default_allowed
        )

    # 测试函数 `test_unknown_license_is_forbidden`：验证 `unknown、license、is、forbidden` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_license_is_forbidden(self):
        self.assertFalse(self.policy.unknown_license_reuse_allowed)

    # 测试函数 `test_copy_without_provenance_is_forbidden`：验证 `copy、without、provenance、is、forbidden` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_copy_without_provenance_is_forbidden(self):
        self.assertFalse(self.policy.copy_without_provenance_allowed)

    # 测试函数 `test_vendor_sdk_reimplementation_is_forbidden`：验证 `vendor、sdk、reimplementation、is、forbidden` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_vendor_sdk_reimplementation_is_forbidden(self):
        self.assertFalse(
            self.policy.vendor_sdk_reimplementation_allowed
        )

    # 测试函数 `test_custom_implementation_is_last`：验证 `custom、implementation、is、last` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_custom_implementation_is_last(self):
        self.assertEqual(
            self.policy.reuse_order[-1],
            "CUSTOM_IMPLEMENTATION_LAST_RESORT",
        )

    # 测试函数 `test_reusable_candidate_is_reusable`：验证 `reusable、candidate、is、reusable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_reusable_candidate_is_reusable(self):
        self.assertTrue(reusable_candidate().reusable)

    # 测试函数 `test_passed_license_requires_license_id`：验证 `passed、license、requires、license、id` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_passed_license_requires_license_id(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReuseCandidateAssessment(
                candidate_id="x",
                candidate_type=(
                    ReuseCandidateType.MATURE_OPEN_SOURCE_LIBRARY
                ),
                name="x",
                source_ref="repo:x",
                version="1",
                license_id=None,
                license_status=ReviewStatus.PASSED,
                security_status=ReviewStatus.PASSED,
                maintenance_status=ReviewStatus.PASSED,
                compatibility_status=ReviewStatus.PASSED,
                semantic_gap_status=ReviewStatus.PASSED,
                supported_requirements=(),
                gaps=(),
                warnings=(),
                evidence_refs=("repo:x",),
            )

    # 测试函数 `test_reuse_candidate_requires_evidence`：验证 `reuse、candidate、requires、evidence` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_reuse_candidate_requires_evidence(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReuseCandidateAssessment(
                candidate_id="x",
                candidate_type=(
                    ReuseCandidateType.OFFICIAL_VENDOR_SDK
                ),
                name="x",
                source_ref="vendor:x",
                version="1",
                license_id="PROPRIETARY",
                license_status=ReviewStatus.PASSED,
                security_status=ReviewStatus.PASSED,
                maintenance_status=ReviewStatus.PASSED,
                compatibility_status=ReviewStatus.PASSED,
                semantic_gap_status=ReviewStatus.PASSED,
                supported_requirements=(),
                gaps=(),
                warnings=(),
                evidence_refs=(),
            )

    # 测试函数 `test_thin_adapter_decision_accepts_existing_component`：验证 `thin、adapter、decision、accepts、existing、component` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_thin_adapter_decision_accepts_existing_component(self):
        record = ReuseDecisionRecord(
            decision_id="reuse:dolphindb",
            problem_statement="Bridge legacy adapter to plugin protocol.",
            requirements=("plugin-protocol",),
            candidates=(reusable_candidate(),),
            decision=ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            selected_candidate_id="existing-adapter",
            rationale="Reuse query and session logic.",
            custom_build_evidence={},
            maintenance_owner=None,
            test_plan_ref=None,
            migration_path=None,
            evidence_refs=("repo:dolphindb_adapter.py",),
        )
        self.assertEqual(
            record.decision,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
        )

    # 测试函数 `test_reuse_decision_rejects_blocked_candidate`：验证 `reuse、decision、rejects、blocked、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_reuse_decision_rejects_blocked_candidate(self):
        blocked = ReuseCandidateAssessment(
            candidate_id="blocked",
            candidate_type=ReuseCandidateType.OFFICIAL_VENDOR_SDK,
            name="blocked",
            source_ref="vendor:blocked",
            version="1",
            license_id="UNKNOWN",
            license_status=ReviewStatus.BLOCKED,
            security_status=ReviewStatus.PASSED,
            maintenance_status=ReviewStatus.PASSED,
            compatibility_status=ReviewStatus.PASSED,
            semantic_gap_status=ReviewStatus.PASSED,
            supported_requirements=(),
            gaps=("license",),
            warnings=(),
            evidence_refs=("vendor:blocked",),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="x",
                problem_statement="x",
                requirements=("x",),
                candidates=(blocked,),
                decision=ReuseDecisionType.REUSE_AS_IS,
                selected_candidate_id="blocked",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner=None,
                test_plan_ref=None,
                migration_path=None,
                evidence_refs=("x",),
            )

    # 测试函数 `test_custom_build_requires_complete_evidence`：验证 `custom、build、requires、complete、evidence` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_custom_build_requires_complete_evidence(self):
        custom = ReuseCandidateAssessment(
            candidate_id="custom",
            candidate_type=ReuseCandidateType.CUSTOM_IMPLEMENTATION,
            name="custom",
            source_ref="internal:new",
            version=None,
            license_id=None,
            license_status=ReviewStatus.NOT_REVIEWED,
            security_status=ReviewStatus.NOT_REVIEWED,
            maintenance_status=ReviewStatus.NOT_REVIEWED,
            compatibility_status=ReviewStatus.NOT_REVIEWED,
            semantic_gap_status=ReviewStatus.NOT_REVIEWED,
            supported_requirements=(),
            gaps=(),
            warnings=(),
            evidence_refs=(),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="custom:x",
                problem_statement="x",
                requirements=("x",),
                candidates=(custom,),
                decision=ReuseDecisionType.CUSTOM_BUILD_APPROVED,
                selected_candidate_id="custom",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner="owner",
                test_plan_ref="tests:x",
                migration_path="replace:x",
                evidence_refs=("x",),
            )

    # 测试函数 `test_custom_build_accepts_complete_evidence`：验证 `custom、build、accepts、complete、evidence` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_custom_build_accepts_complete_evidence(self):
        custom = ReuseCandidateAssessment(
            candidate_id="custom",
            candidate_type=ReuseCandidateType.CUSTOM_IMPLEMENTATION,
            name="custom",
            source_ref="internal:new",
            version=None,
            license_id=None,
            license_status=ReviewStatus.NOT_REVIEWED,
            security_status=ReviewStatus.NOT_REVIEWED,
            maintenance_status=ReviewStatus.NOT_REVIEWED,
            compatibility_status=ReviewStatus.NOT_REVIEWED,
            semantic_gap_status=ReviewStatus.NOT_REVIEWED,
            supported_requirements=(),
            gaps=(),
            warnings=(),
            evidence_refs=(),
        )
        keys = self.policy.required_custom_build_evidence
        evidence = {key: f"evidence:{key}" for key in keys}
        record = ReuseDecisionRecord(
            decision_id="custom:x",
            problem_statement="x",
            requirements=("x",),
            candidates=(custom,),
            decision=ReuseDecisionType.CUSTOM_BUILD_APPROVED,
            selected_candidate_id="custom",
            rationale="x",
            custom_build_evidence=evidence,
            maintenance_owner="owner",
            test_plan_ref="tests:x",
            migration_path="replace:x",
            evidence_refs=("x",),
        )
        self.assertEqual(
            record.decision,
            ReuseDecisionType.CUSTOM_BUILD_APPROVED,
        )

    # 测试函数 `test_selected_candidate_must_exist`：验证 `selected、candidate、must、exist` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_selected_candidate_must_exist(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="x",
                problem_statement="x",
                requirements=("x",),
                candidates=(reusable_candidate(),),
                decision=ReuseDecisionType.REUSE_AS_IS,
                selected_candidate_id="missing",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner=None,
                test_plan_ref=None,
                migration_path=None,
                evidence_refs=("x",),
            )

    # 测试函数 `test_to_dict_is_json_safe`：验证 `to、dict、is、json、safe` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_to_dict_is_json_safe(self):
        record = ReuseDecisionRecord(
            decision_id="reuse:dolphindb",
            problem_statement="Bridge adapter.",
            requirements=("plugin-protocol",),
            candidates=(reusable_candidate(),),
            decision=ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            selected_candidate_id="existing-adapter",
            rationale="reuse",
            custom_build_evidence={},
            maintenance_owner=None,
            test_plan_ref=None,
            migration_path=None,
            evidence_refs=("repo:x",),
        )
        encoded = json.dumps(record.to_dict(), ensure_ascii=False)
        self.assertIn("WRAP_WITH_THIN_ADAPTER", encoded)

    # 测试函数 `test_policy_rejects_custom_build_default`：验证 `policy、rejects、custom、build、default` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_rejects_custom_build_default(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["custom_implementation_default_allowed"] = True
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
                load_reuse_first_policy(path)


if __name__ == "__main__":
    unittest.main()
