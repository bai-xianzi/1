from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

# 本段代码核心功能：定位并动态加载TASK_025A验证脚本，使测试不依赖项目安装方式或PYTHONPATH。
# - 输入：当前测试文件路径和仓库内固定的scripts相对路径。
# - 处理：构造模块规范并执行模块加载。
# - 输出：返回包含验证函数和常量的模块对象。
# - 常量依据：scripts/validate_task_025a_dual_view_authority.py由本任务创建，是专项验收唯一入口。
# - 为什么这样写：仓库当前可能以源码目录方式运行，动态加载能减少环境差异导致的导入错误。
def load_validator_module():
    repository_root = Path(__file__).resolve().parents[1]
    script_path = repository_root / "scripts" / "validate_task_025a_dual_view_authority.py"
    spec = importlib.util.spec_from_file_location("task_025a_validator", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载验证脚本：{script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 本段代码核心功能：验证TASK_025A权威文件、关键设计、Schema和过期引用门禁能够整体通过。
# - 输入：仓库当前工作树和动态加载的验证模块。
# - 处理：分别调用四类验证函数，确保每类错误列表为空。
# - 输出：任何缺失、格式错误或过期引用都会形成可定位的单元测试失败。
# - 为什么这样写：把专项验证函数纳入unittest可以进入项目全量测试，防止后续修改意外删除双视图合同。
class Task025ADualViewAuthorityTests(unittest.TestCase):
    # 本段代码核心功能：为当前测试类加载专项验证器并确定仓库根目录。
    # - 输入：测试文件自身路径和load_validator_module返回的模块。
    # - 处理：把共享对象保存为类属性，避免四个测试重复加载文件。
    # - 输出：后续测试能够直接调用验证函数。
    # - 为什么这样写：一次加载保持测试口径一致并减少无意义的文件系统操作。
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator_module()
        cls.repository_root = Path(__file__).resolve().parents[1]

    # 本段代码核心功能：确认本任务声明的全部权威文件、Schema、脚本和报告存在。
    # - 输入：仓库根目录。
    # - 处理：调用validate_required_files。
    # - 输出：缺失或空文件会产生测试失败。
    # - 为什么这样写：阻止多文件修改包因漏打文件而被提交。
    def test_required_files_exist(self) -> None:
        self.assertEqual([], self.validator.validate_required_files(self.repository_root))

    # 本段代码核心功能：确认双视图、Skill、白箱和当前任务保持原则已经写入对应权威文件。
    # - 输入：仓库根目录和验证器关键短语清单。
    # - 处理：调用validate_authority_content。
    # - 输出：任何权威内容回退都会产生测试失败。
    # - 为什么这样写：文件存在不代表设计有效，内容门禁可防止后续误删核心原则。
    def test_authority_content_is_present(self) -> None:
        self.assertEqual([], self.validator.validate_authority_content(self.repository_root))

    # 本段代码核心功能：确认六个B2C与Skill机器合同保持可解析和结构完整。
    # - 输入：schemas目录中的JSON Schema。
    # - 处理：调用validate_schemas。
    # - 输出：格式、版本、标题或基础合同错误会产生测试失败。
    # - 为什么这样写：机器合同是未来动态表单、API和工作流的共同边界，必须防止文档与Schema脱节。
    def test_machine_readable_schemas_are_valid(self) -> None:
        self.assertEqual([], self.validator.validate_schemas(self.repository_root))

    # 本段代码核心功能：确认核心权威文件没有重新引入已停用工具或已淘汰开发型Skill。
    # - 输入：验证器限定的核心权威文件范围。
    # - 处理：调用validate_obsolete_references。
    # - 输出：发现过期默认依赖时产生测试失败。
    # - 为什么这样写：项目应继承稳定能力而不是绑定临时工具，避免新对话回到已否定的工作流。
    def test_obsolete_default_dependencies_are_absent(self) -> None:
        self.assertEqual([], self.validator.validate_obsolete_references(self.repository_root))


# 本段代码核心功能：允许用户直接运行本测试文件并获得标准unittest退出码。
# - 输入：命令行直接执行测试文件的运行标志。
# - 处理：调用unittest.main发现并执行当前测试类。
# - 输出：终端显示测试数量和通过或失败状态。
# - 为什么这样写：既支持unittest discover，也支持专项文件直接运行，方便PowerShell验证脚本调用。
if __name__ == "__main__":
    unittest.main()
