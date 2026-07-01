# 本测试模块核心功能：验证全项目教学式注释迁移完成后的唯一机器政策和长期门禁。
# - 输入：读取仓库中的代码注释JSON政策，并通过强类型加载器完成合同校验。
# - 处理：检查迁移完成、全仓库强制审计、提交解锁和推送确认等最终状态。
# - 输出：全部断言通过表示阶段脚本可以删除，长期注释门禁仍然有效。
# - 为什么这样写：用一个稳定政策测试替代A至H阶段测试，减少维护重复而不降低约束。
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.code_comment_policy import (
    CodeCommentPolicy,
    CommentMigrationStatus,
    load_code_comment_policy,
)
from a_stock_quant.data_contracts import DataContractError


# 政策路径：从当前测试文件定位项目根目录，避免依赖PowerShell当前目录。
# - parents[1]固定回到仓库根目录。
# - 为什么这样写：同一测试可由IDE、unittest discover和验证脚本调用。
ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "configs" / "engineering" / "code_comment_policy_v0.json"


# 最终政策测试：集中验证注释迁移完成后的机器合同。
# - setUp和各测试方法分别检查一个长期约束。
# - 为什么这样写：所有长期断言基于同一事实源，避免阶段测试互相重复。
class TestCodeCommentPolicy(unittest.TestCase):

    # 测试准备：加载并保存强类型注释政策对象。
    # - 每个测试都从同一权威JSON重新加载，避免测试间共享可变状态。
    # - 为什么这样写：单元测试应独立运行，并同时覆盖政策加载器的数据合同。
    def setUp(self) -> None:
        self.policy = load_code_comment_policy(POLICY_PATH)

    # 加载器类型测试：确认政策通过强类型对象暴露。
    # - 输入是权威JSON，输出必须是CodeCommentPolicy实例。
    # - 为什么这样写：后续审计器不能依赖未经校验的松散字典。
    def test_loader_returns_policy_object(self) -> None:
        self.assertIsInstance(self.policy, CodeCommentPolicy)

    # 权威与原则测试：锁定最高标准文件和教学式前置注释原则。
    # - 两个字符串是所有审计脚本和开发指导共同依赖的稳定标识。
    # - 为什么这样写：防止迁移关闭时意外弱化或分叉注释规则。
    def test_authority_and_principle_are_stable(self) -> None:
        self.assertEqual(
            self.policy.authority_document,
            "CODE_COMMENTING_STANDARD.md",
        )
        self.assertEqual(
            self.policy.principle,
            "TEACHING_STYLE_PRECEDING_COMMENTS_REQUIRED",
        )

    # 迁移完成测试：验证状态、全仓库审计和临时提交阻断同步切换。
    # - COMPLETE必须配合full_repository_enforcement_enabled=True。
    # - 为什么这样写：不能只修改状态文字而遗漏机器门禁的状态转换。
    def test_migration_is_complete(self) -> None:
        self.assertIs(
            self.policy.migration.status,
            CommentMigrationStatus.COMPLETE,
        )
        self.assertTrue(
            self.policy.migration.full_repository_enforcement_enabled
        )
        self.assertFalse(
            self.policy.migration.github_commit_blocked_until_full_migration
        )

    # 长期门禁测试：确认迁移完成后仍保留审计、测试和用户确认。
    # - 临时迁移阻断解除不等于解除正常的提交与推送安全约束。
    # - 为什么这样写：项目后续新增代码仍必须持续满足相同质量标准。
    def test_permanent_gates_remain_enabled(self) -> None:
        gate = self.policy.git_gate
        self.assertTrue(
            self.policy.migration.new_or_modified_code_enforcement_enabled
        )
        self.assertTrue(
            self.policy.migration.github_push_blocked_until_user_confirmation
        )
        self.assertTrue(gate.must_run_comment_audit)
        self.assertTrue(gate.must_run_specialized_tests)
        self.assertTrue(gate.must_run_full_tests)
        self.assertTrue(gate.must_run_encoding_audit)
        self.assertTrue(gate.must_run_git_diff_check)
        self.assertTrue(gate.user_confirmation_required_before_commit)
        self.assertTrue(gate.user_confirmation_required_before_push)

    # 教学式结构测试：验证七项结构、分点标记、原因短语和docstring限制。
    # - 直接读取原始JSON以覆盖强类型对象没有暴露的语言细节。
    # - 为什么这样写：迁移结束后也不能把教学式注释降级为普通一句话注释。
    def test_teaching_comment_contract_remains_complete(self) -> None:
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(raw["required_comment_structure"]), 7)
        self.assertEqual(raw["required_markers"]["detail_prefix"], "# -")
        self.assertIn(
            "为什么这样写",
            raw["required_markers"]["reason_phrases"],
        )
        self.assertFalse(
            raw["docstring_policy"][
                "docstrings_may_replace_preceding_teaching_comments"
            ]
        )

    # 非法完成状态测试：构造关闭全仓库审计的临时政策。
    # - COMPLETE与full_repository_enforcement_enabled=False必须被加载器拒绝。
    # - 为什么这样写：证明迁移完成门禁由代码强制，而不是只依赖人工约定。
    def test_complete_policy_rejects_disabled_enforcement(self) -> None:
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["migration"]["full_repository_enforcement_enabled"] = False

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad_policy.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_code_comment_policy(path)


# 测试入口：兼容单文件执行和完整unittest发现。
# - unittest.main把测试结果转换成标准进程退出码。
# - 为什么这样写：统一测试既可单独排错，也可进入完整项目测试。
if __name__ == "__main__":
    unittest.main()
