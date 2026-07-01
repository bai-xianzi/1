# 本测试模块核心功能：验证TASK_021B使用跨Python版本稳定的Token摘要保持业务逻辑不变。
# - tokenize复算当前文件语义摘要。
# - importlib加载生产注释审计器。
# - unittest沿用项目现有测试框架。
# - 为什么这样写：测试不能依赖补丁生成机器特有的ast.dump文本格式。
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import tokenize
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports/task_021b_core_contracts_comment_migration.json"


# 便携语义摘要：将Python源码转换为忽略注释和非语义空行的Token序列，再计算SHA256。
# - tokenize完成词法分析，Token类型和源码值不依赖ast.dump的版本显示格式。
# - COMMENT、NL、ENCODING和ENDMARKER不影响可执行逻辑，因此排除。
# - NEWLINE统一为\n，避免Windows与Linux换行符差异。
# - INDENT、DEDENT、名称、数值、字符串、运算符等全部保留，所以逻辑变化仍会改变摘要。
# - 为什么这样写：ast.dump默认文本会随Python版本变化，Token序列更适合跨机器持久验证。
def semantic_token_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts: list[str] = []
    ignored = {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in ignored:
            continue
        value = "\n" if token.type == tokenize.NEWLINE else token.string
        parts.append(f"{token.type}:{value}")
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


# 审计器加载：动态导入统一教学式注释审计器。
# - 为什么这样写：测试直接覆盖生产审计逻辑。
def load_audit_module():
    path = ROOT / "scripts" / "audit_teaching_comments.py"
    spec = importlib.util.spec_from_file_location("task_021b_test_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载教学式注释审计器。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

# 批次测试类：每个测试读取同一迁移报告和审计器。
# - 为什么这样写：报告是目标、摘要与门禁的唯一事实来源。
class TestTask021BCoreCommentMigration(unittest.TestCase):
    # 测试准备：加载报告与审计器。
    # - 为什么这样写：减少重复I/O。
    def setUp(self) -> None:
        self.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.audit = load_audit_module()

    # 目标数量测试：确认批次边界没有变化。
    # - 为什么这样写：漏文件或越界文件都会被发现。
    def test_target_count(self):
        self.assertEqual(self.report["target_file_count"], 10)
        self.assertEqual(len(self.report["files"]), 10)

    # 语义方法测试：确认启用便携Token摘要。
    # - 为什么这样写：防止退回版本相关AST文本哈希。
    def test_portable_semantic_method(self):
        self.assertEqual(self.report["semantic_verification_method"], "PYTHON_TOKEN_STREAM_V1")
        self.assertTrue(self.report["semantic_token_identity_required"])

    # Token一致性测试：逐文件复算当前摘要。
    # - 为什么这样写：缩进、常量、调用、公式或控制流变化都会失败。
    def test_semantic_tokens_are_identical(self):
        for item in self.report["files"]:
            with self.subTest(path=item["path"]):
                self.assertEqual(semantic_token_sha256(ROOT / item["path"]), item["semantic_token_sha256"])

    # 注释数量测试：确认每个文件达到迁移报告记录值。
    # - 为什么这样写：只有语义一致但没有说明不能算迁移完成。
    def test_comment_counts(self):
        for item in self.report["files"]:
            path = ROOT / item["path"]
            count = sum(line.lstrip().startswith("#") for line in path.read_text(encoding="utf-8").splitlines())
            with self.subTest(path=item["path"]):
                self.assertEqual(count, item["after_comment_line_count"])
                self.assertGreater(count, item["before_comment_line_count"])

    # 教学式结构测试：统一审计器不得发现违规。
    # - 为什么这样写：注释数量高不等于教学价值合格。
    def test_teaching_comment_audit(self):
        for item in self.report["files"]:
            path = ROOT / item["path"]
            with self.subTest(path=item["path"]):
                self.assertEqual(self.audit.audit_python_file(ROOT, path).violations, ())

    # 装饰器回归测试：创建带dataclass装饰器的类并检查前置教学注释。
    # - 为什么这样写：审计器必须从第一个装饰器向上读取注释窗口。
    def test_decorated_class_uses_first_decorator_line(self):
        source = """\
# 测试导入：引入dataclass。
# - dataclass会生成初始化方法。
# - 为什么这样写：构造真实装饰器场景。
from dataclasses import dataclass

# 测试数据类：保存一个整数。
# - value类型为int，示例值1。
# - 为什么这样写：验证注释位于装饰器之前。
@dataclass
class Sample:
    value: int
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "sample.py"
            path.write_text(source, encoding="utf-8")
            self.assertEqual(self.audit.audit_python_file(root, path).violations, ())

    # Git门禁测试：确认迁移未完成前禁止提交与推送。
    # - 为什么这样写：不能发布半完成状态。
    def test_git_remains_blocked(self):
        self.assertFalse(self.report["github_commit_allowed"])
        self.assertFalse(self.report["github_push_allowed"])
        self.assertFalse(self.report["full_repository_migration_complete"])

# 测试入口：兼容直接运行和unittest discover。
# - 为什么这样写：可单独调试，也可加入完整回归。
if __name__ == "__main__":
    unittest.main()
