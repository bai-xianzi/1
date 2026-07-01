# 测试模块总览：验证 `test_task_021c_comment_migration` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
# 本测试模块核心功能：使用跨Python版本稳定的完整目标源码摘要验证TASK_021C注释迁移成果。
# - 摘要基于已成功生成并验收的注释后目标源码，不保存Python内部数字Token编号。
# - read_text自动统一Windows与Linux换行，再计算UTF-8 SHA256。
# - 原始迁移报告继续保留迁移时“源代码与目标代码语义一致”的历史证据。
# - 为什么这样写：Python版本会调整Token数字编号，但不会改变项目目标源码正文。
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# 测试函数 `normalized_source_sha256`：封装 `normalized_source_sha256` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：path。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def normalized_source_sha256(path: Path) -> str:
    """Return a line-ending-independent SHA256 for the full annotated source."""
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# 测试函数 `load_audit_module`：封装 `load_audit_module` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def load_audit_module():
    path = ROOT / "scripts" / "audit_teaching_comments.py"
    spec = importlib.util.spec_from_file_location("task_021_portable_target_audit", path)
    # 测试分支：根据 `spec is None or spec.loader is None` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载教学式注释审计器。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

REPORT_PATH = ROOT / "reports" / "task_021c_readiness_market_state_comment_migration.json"


# 测试类 `TestTask021CReadinessMarketStateCommentMigration`：集中验证 `test_task_021c_comment_migration` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestTask021CReadinessMarketStateCommentMigration(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.audit = load_audit_module()

    # 测试函数 `test_target_count`：验证 `target、count` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_target_count(self):
        self.assertEqual(self.report["target_file_count"], 9)
        self.assertEqual(len(self.report["files"]), 9)

    # 测试函数 `test_portable_verification_method`：验证 `portable、verification、method` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_portable_verification_method(self):
        self.assertEqual(
            self.report["semantic_verification_method"],
            "ANNOTATED_TARGET_SOURCE_SHA256_V1",
        )
        self.assertTrue(self.report["target_source_identity_required"])
        self.assertTrue(self.report["historical_source_to_target_semantic_identity_preserved"])
        self.assertFalse(self.report["numeric_token_fingerprint_portable_across_python_versions"])

    # 测试函数 `test_annotated_target_sources_are_identical`：验证 `annotated、target、sources、are、identical` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_annotated_target_sources_are_identical(self):
        # 参数化循环：逐项使用 `self.report['files']` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for item in self.report["files"]:
            # 测试上下文：通过 `self.subTest(path=item['path'])` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(path=item["path"]):
                self.assertEqual(
                    normalized_source_sha256(ROOT / item["path"]),
                    item["normalized_target_source_sha256"],
                )

    # 测试函数 `test_comment_counts`：验证 `comment、counts` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_comment_counts(self):
        # 参数化循环：逐项使用 `self.report['files']` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for item in self.report["files"]:
            path = ROOT / item["path"]
            count = sum(
                line.lstrip().startswith("#")
                for line in path.read_text(encoding="utf-8").splitlines()
            )
            # 测试上下文：通过 `self.subTest(path=item['path'])` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(path=item["path"]):
                self.assertEqual(count, item["after_comment_line_count"])
                self.assertGreater(count, item["before_comment_line_count"])

    # 测试函数 `test_teaching_comment_audit`：验证 `teaching、comment、audit` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_teaching_comment_audit(self):
        # 参数化循环：逐项使用 `self.report['files']` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for item in self.report["files"]:
            path = ROOT / item["path"]
            # 测试上下文：通过 `self.subTest(path=item['path'])` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(path=item["path"]):
                self.assertEqual(self.audit.audit_python_file(ROOT, path).violations, ())

    # 测试函数 `test_safety_gates_remain_closed`：验证 `safety、gates、remain、closed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_safety_gates_remain_closed(self):
        self.assertFalse(self.report["business_logic_changed"])
        self.assertEqual(self.report["database_write_operation_count"], 0)
        self.assertFalse(self.report["github_commit_allowed"])
        self.assertFalse(self.report["github_push_allowed"])
        self.assertFalse(self.report["full_repository_migration_complete"])


if __name__ == "__main__":
    unittest.main()
