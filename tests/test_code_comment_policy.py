# 本测试模块核心功能：验证代码注释机器政策、迁移状态和审计器的最小教学式结构判断。
# - json和tempfile用于构造临时政策与临时代码文件，不污染真实仓库。
# - unittest提供项目现有标准测试框架，无需新增第三方依赖。
# - 为什么这样写：规则只有进入自动测试，才能在后续批量改代码时保持稳定。
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


# 测试路径：定位仓库中的机器可读代码注释政策。
# - __file__从当前测试文件出发。
# - parents[1]回到项目根目录。
# - 为什么这样写：测试不依赖当前工作目录，可从IDE、PowerShell或unittest discover运行。
ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "configs"
    / "engineering"
    / "code_comment_policy_v0.json"
)


# 政策测试类：每个测试前加载一次真实政策。
# - setUp避免每个测试重复书写加载逻辑。
# - 为什么这样写：所有断言都基于同一份仓库权威配置。
class TestCodeCommentPolicy(unittest.TestCase):
    # 测试准备：加载并保存CodeCommentPolicy实例。
    # - self.policy在每个测试方法中可直接访问。
    # - 为什么这样写：减少重复并保持测试意图清晰。
    def setUp(self) -> None:
        self.policy = load_code_comment_policy(POLICY_PATH)

    # 原则测试：确认项目启用了教学式前置注释。
    # - 精确字符串断言防止规则被改成宽松的普通注释。
    # - 为什么这样写：这是用户六条规则的核心机器标识。
    def test_principle_is_teaching_style_preceding_comments(self):
        self.assertEqual(
            self.policy.principle,
            "TEACHING_STYLE_PRECEDING_COMMENTS_REQUIRED",
        )

    # 权威文件测试：确认最高标准文件名稳定。
    # - 其他代理和验证脚本依赖该路径。
    # - 为什么这样写：避免规则分散到多个互相冲突的文档。
    def test_authority_document_is_stable(self):
        self.assertEqual(
            self.policy.authority_document,
            "CODE_COMMENTING_STANDARD.md",
        )

    # 迁移状态测试：确认当前处于历史代码分批迁移阶段。
    # - IN_PROGRESS允许盘点模式运行，但不能允许Git提交。
    # - 为什么这样写：123个代码文件不适合一次盲目修改。
    def test_migration_is_in_progress(self):
        self.assertIs(
            self.policy.migration.status,
            CommentMigrationStatus.IN_PROGRESS,
        )

    # Git提交阻断测试：确认全仓库迁移完成前不能提交。
    # - True是当前阶段的硬门禁。
    # - 为什么这样写：防止规则只写进文档但旧代码尚未迁移就被提交。
    def test_commit_is_blocked_until_full_migration(self):
        self.assertTrue(
            self.policy.migration
            .github_commit_blocked_until_full_migration
        )

    # 新代码即时审计测试：确认新改代码不能继续制造注释债务。
    # - 历史迁移可以分批，但新增代码必须立即遵守。
    # - 为什么这样写：否则迁移速度可能赶不上新债务增长。
    def test_new_or_modified_code_enforcement_is_enabled(self):
        self.assertTrue(
            self.policy.migration
            .new_or_modified_code_enforcement_enabled
        )

    # 用户提交确认测试：确认执行git commit前必须得到用户确认。
    # - 该规则来自用户明确要求。
    # - 为什么这样写：把对话约定变成长期机器门禁。
    def test_user_confirmation_is_required_before_commit(self):
        self.assertTrue(
            self.policy.git_gate
            .user_confirmation_required_before_commit
        )

    # 用户推送确认测试：确认执行git push前必须再次满足用户确认。
    # - 提交和推送分别记录，避免本地提交被自动推到GitHub。
    # - 为什么这样写：远程发布是更高风险动作，需要独立门禁。
    def test_user_confirmation_is_required_before_push(self):
        self.assertTrue(
            self.policy.git_gate
            .user_confirmation_required_before_push
        )

    # 注释审计门禁测试：确认Git流程必须运行教学式注释审计。
    # - 仅人工目视无法稳定覆盖上百个文件。
    # - 为什么这样写：自动审计用于发现遗漏，人工评审用于判断解释质量。
    def test_comment_audit_is_required(self):
        self.assertTrue(
            self.policy.git_gate.must_run_comment_audit
        )

    # 完整测试门禁：确认批量补注释后仍需运行全部单元测试。
    # - 注释通常不改变语义，但批量编辑可能误伤缩进或字符串。
    # - 为什么这样写：测试是证明业务行为未改变的主要证据。
    def test_full_tests_are_required(self):
        self.assertTrue(
            self.policy.git_gate.must_run_full_tests
        )

    # 编码审计门禁：确认中文注释加入后必须检查UTF-8和BOM问题。
    # - Windows PowerShell和Python对编码处理可能不同。
    # - 为什么这样写：大量中文注释会提高编码错误风险。
    def test_encoding_audit_is_required(self):
        self.assertTrue(
            self.policy.git_gate.must_run_encoding_audit
        )

    # 规则结构数量测试：确认七个教学式组成部分全部存在。
    # - 数量下限覆盖概括、分点、数据变化、常量、原因、实例和先后顺序。
    # - 为什么这样写：防止后续修改配置时漏掉用户原始要求。
    def test_required_structure_has_seven_parts(self):
        self.assertGreaterEqual(
            len(self.policy.required_comment_structure),
            7,
        )

    # 例外测试：确认JSON文件不会被错误插入#注释。
    # - JSON标准不支持注释。
    # - 为什么这样写：错误注释会使配置无法解析并破坏运行。
    def test_json_without_comment_syntax_is_excepted(self):
        self.assertIn(
            "json_files_without_comment_syntax",
            self.policy.exceptions,
        )

    # docstring禁止替代测试：直接读取原始JSON中的精确布尔值。
    # - 数据类聚焦核心门禁，详细语言规则仍保存在原始政策中。
    # - 为什么这样写：确保用户特别强调的禁止事项没有丢失。
    def test_docstring_cannot_replace_preceding_comments(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertFalse(
            raw["docstring_policy"][
                "docstrings_may_replace_preceding_teaching_comments"
            ]
        )

    # 分点标记测试：确认政策指定# -作为Python和PowerShell教学列表格式。
    # - 精确标记便于审计器识别。
    # - 为什么这样写：统一格式可以提高可读性并降低自动审计误报。
    def test_detail_prefix_is_hash_dash(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            raw["required_markers"]["detail_prefix"],
            "# -",
        )

    # 自定义原因短语测试：确认至少包含“为什么这样写”。
    # - 该短语是用户要求的解释段落标志。
    # - 为什么这样写：自动审计需要一个稳定且通俗的可识别信号。
    def test_reason_phrase_is_present(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertIn(
            "为什么这样写",
            raw["required_markers"]["reason_phrases"],
        )

    # 政策弱化拒绝测试：临时把提交确认改为False，加载时必须失败。
    # - tempfile创建隔离目录。
    # - json.dumps保留合法JSON结构。
    # - 为什么这样写：证明机器数据合同确实能阻止绕过用户确认。
    def test_policy_rejects_disabled_commit_confirmation(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["git_gate"][
            "user_confirmation_required_before_commit"
        ] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad_policy.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_code_comment_policy(path)

    # 迁移弱化拒绝测试：进行中状态关闭提交阻断时必须加载失败。
    # - 该测试覆盖最关键的历史迁移门禁。
    # - 为什么这样写：防止在只完成少量文件时提前提交到GitHub。
    def test_policy_rejects_unblocked_in_progress_migration(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["migration"][
            "github_commit_blocked_until_full_migration"
        ] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad_policy.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_code_comment_policy(path)

    # 对象类型测试：确认加载器返回强类型CodeCommentPolicy。
    # - 这证明脚本不会只得到一个未经校验的字典。
    # - 为什么这样写：类型对象更适合被后续审计和迁移工具复用。
    def test_loader_returns_policy_object(self):
        self.assertIsInstance(
            self.policy,
            CodeCommentPolicy,
        )


# 测试入口：允许直接运行本文件，也兼容unittest discover。
# - unittest.main收集当前模块全部test_方法。
# - 为什么这样写：开发者可以单独调试，也可以加入完整测试套件。
if __name__ == "__main__":
    unittest.main()
