# 本文件核心功能：验证TASK_022至TASK_024人工代码在交付前具备完整教学式前置注释。
# - 输入：项目根目录中的目标Python和PowerShell文件，以及每个文件的源代码文本。
# - 处理：解析Python语法树并扫描PowerShell控制结构，检查文件头、定义和主要逻辑块之前的教学说明。
# - 输出：全部检查通过时单元测试成功；任一文件缺少输入、处理、输出、常量依据或原因说明时给出精确行号。
# - 常量依据：目标文件清单来自TASK_022、TASK_023A/B/C和TASK_024A的正式交付范围。
# - 为什么这样写：把用户要求转化为可重复门禁，防止后续沙盒代码再次先开发、后补注释。

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


# 本段代码核心功能：定义教学块必须同时出现的五类结构标记。
# - 输入：固定中文标签来自项目CODE_COMMENTING_STANDARD.md，不读取外部配置。
# - 处理：使用不可变元组保存标签，供Python和PowerShell检查逻辑共同复用。
# - 输出：输出五个前缀字符串，缺少任一项都视为教学说明不完整。
# - 常量依据：标签依次对应输入、处理、输出、常量依据和为什么这样写五项强制内容。
# - 为什么这样写：统一常量可以避免不同语言审计口径漂移，也便于未来升级标准。
REQUIRED_MARKERS = (
    "# - 输入：",
    "# - 处理：",
    "# - 输出：",
    "# - 常量依据：",
    "为什么这样写",
)


# 本段代码核心功能：定义TASK_022至TASK_024需要接受教学注释回归检查的Python文件。
# - 输入：任务交付历史中的人工Python源码、入口脚本和测试文件相对路径。
# - 处理：用不可变元组固定范围，不扫描第三方SDK、JSON、缓存或自动生成文件。
# - 输出：输出相对项目根目录的路径集合，供逐文件检查循环使用。
# - 常量依据：清单覆盖TASK_022激活、TASK_023发现/盘点/选择和TASK_024A来源权威基线。
# - 为什么这样写：明确范围既能覆盖本次缺陷，又不会误改第三方或历史归档代码。
PYTHON_TARGETS = (
    "src/a_stock_quant/dolphindb_provider_plugin.py",
    "scripts/run_task_022_real_registry_route_acceptance.py",
    "scripts/validate_task_022_provider_activation.py",
    "scripts/finalize_task_022_status.py",
    "tests/test_task_022_provider_activation.py",
    "tests/test_task_022_validation_false_positive.py",
    "src/a_stock_quant/provider_environment_discovery.py",
    "scripts/run_task_023_provider_environment_discovery.py",
    "tests/test_provider_environment_discovery.py",
    "src/a_stock_quant/provider_windows_inventory.py",
    "scripts/run_task_023b_windows_provider_inventory.py",
    "tests/test_provider_windows_inventory.py",
    "src/a_stock_quant/provider_selection.py",
    "scripts/run_task_023c_provider_selection.py",
    "tests/test_provider_selection.py",
    "src/a_stock_quant/source_authority.py",
    "scripts/run_task_024a_official_source_baseline.py",
    "scripts/run_task_024a_syntax_check.py",
    "tests/test_source_authority.py",
)


# 本段代码核心功能：定义需要接受同一教学标准检查的PowerShell项目脚本。
# - 输入：TASK_022提交到仓库的验证脚本相对路径。
# - 处理：保持为不可变元组；交付包自身的PowerShell脚本由包内静态检查单独验证。
# - 输出：输出PowerShell目标路径集合。
# - 常量依据：TASK_023和TASK_024的apply/finalize脚本属于交付包而非仓库，因此不写入项目清单。
# - 为什么这样写：区分仓库源码与一次性交付工具，避免测试依赖用户下载目录。
POWERSHELL_TARGETS = (
    "scripts/verify_task_022_patch.ps1",
)


# 本段代码核心功能：定义必须包含沙盒前置门禁标记的权威Markdown文件。
# - 输入：项目最高注释标准和开发总指导的固定路径。
# - 处理：使用不可变元组保存，测试只读取不修改。
# - 输出：供权威流程回归测试逐文件验证。
# - 常量依据：两个文件分别管理注释规范和任务执行顺序。
# - 为什么这样写：只有代码和权威流程同时受测试保护，才能防止后续再次交付无注释代码。
AUTHORITY_DOCUMENT_TARGETS = (
    "CODE_COMMENTING_STANDARD.md",
    "DEVELOPMENT_GUIDANCE.md",
)


# 本段代码核心功能：保存TASK_024A1写入权威文档的唯一幂等标记。
# - 输入：固定任务号和门禁名称。
# - 处理：形成精确HTML注释字符串。
# - 输出：供测试执行字符串包含断言。
# - 常量依据：与整改脚本AUTHORITY_MARKER保持一致。
# - 为什么这样写：精确标记可识别规则是否真正落库，避免普通正文关键词造成假阳性。
AUTHORITY_MARKER = "<!-- TASK_024A1_COMMENT_BEFORE_SANDBOX_GATE -->"


# 本段代码核心功能：定义 `_preceding_comment_window`，提取目标代码行之前连续的注释窗口。
# - 输入：参数为 `lines、line_number、maximum_lines`；line_number使用一基行号，maximum_lines默认回看16行。
# - 处理：从目标上一行向前扫描，只接收空行和单行注释，遇到可执行代码立即停止。
# - 输出：返回类型为 `list[str]`；顺序恢复为源文件从上到下的阅读顺序。
# - 常量依据：16行足以容纳六行教学块和少量空行，同时避免远处注释误解释当前代码。
# - 为什么这样写：只有紧邻代码的说明才能形成一一对应关系，过远的注释不能算作前置教学注释。
def _preceding_comment_window(
    lines: list[str],
    line_number: int,
    maximum_lines: int = 16,
) -> list[str]:
    index = line_number - 2
    collected: list[str] = []
    inspected = 0

    # 本段代码核心功能：在达到文件开头、扫描上限或前一段可执行代码前持续回收注释行。
    # - 输入：当前零基索引、已检查行数和源文件物理行列表。
    # - 处理：空行与`#`注释继续向前扫描，其他内容立即结束窗口。
    # - 输出：更新collected、index和inspected三个局部变量。
    # - 常量依据：扫描上限来自maximum_lines参数，默认值16不是业务阈值，只是审计邻近范围。
    # - 为什么这样写：受限回看可避免无限扫描，也防止把其他函数的说明误算到当前定义。
    while index >= 0 and inspected < maximum_lines:
        stripped = lines[index].strip()
        inspected += 1

        # 本段代码核心功能：判断当前上一行是否仍属于可接受的前置注释窗口。
        # - 输入：去除首尾空白后的单行文本。
        # - 处理：空行或`#`开头行被收集；遇到代码则终止扫描。
        # - 输出：可能追加一行并递减索引，或直接跳出循环。
        # - 常量依据：Python与PowerShell在本项目中都使用`#`作为单行注释符号。
        # - 为什么这样写：只接收合法单行注释，确保docstring和普通字符串不能冒充前置说明。
        if not stripped or stripped.startswith("#"):
            collected.append(lines[index])
            index -= 1
            continue
        break

    return list(reversed(collected))


# 本段代码核心功能：定义 `_teaching_block_violations`，检查一个注释窗口是否具备完整教学结构。
# - 输入：参数为 `window、label、line_number`；window是目标代码之前的单行注释集合。
# - 处理：逐项检查概括行和五类强制标记，缺失项转换为带文件对象及行号的错误文本。
# - 输出：返回类型为 `list[str]`；空列表表示当前教学块合规。
# - 常量依据：REQUIRED_MARKERS来自项目最高注释标准，不能由被测文件自行降低。
# - 为什么这样写：返回全部缺口而不是第一个错误，可以一次修完同一文件，减少反复运行成本。
def _teaching_block_violations(
    window: list[str],
    *,
    label: str,
    line_number: int,
) -> list[str]:
    comments = [line.strip() for line in window if line.strip().startswith("#")]
    violations: list[str] = []

    # 本段代码核心功能：确认窗口中存在明确概括接下来代码用途的首行。
    # - 输入：过滤后的单行注释列表。
    # - 处理：搜索“本段代码核心功能”或文件级“本文件核心功能”标记。
    # - 输出：缺失时向violations追加一条精确错误。
    # - 常量依据：两个短语分别覆盖逻辑块和文件头，均来自本次整改标准。
    # - 为什么这样写：没有概括行时，读者无法先建立整体模型，后续分点容易失去上下文。
    if not any(
        "本段代码核心功能" in line or "本文件核心功能" in line
        for line in comments
    ):
        violations.append(f"line {line_number}: {label}前缺少核心功能概括")

    # 本段代码核心功能：逐项确认输入、处理、输出、常量依据和原因说明全部存在。
    # - 输入：REQUIRED_MARKERS固定标记及当前窗口注释。
    # - 处理：每个标记独立搜索，不用单一计数掩盖重复标签和缺失标签。
    # - 输出：每缺少一个标记就追加一条可操作错误。
    # - 常量依据：五个标记是项目强制最小集合，不允许只写一句普通注释代替。
    # - 为什么这样写：逐项验证能防止大量泛泛注释通过审计，却仍没有解释数据变化和设计依据。
    for marker in REQUIRED_MARKERS:
        # 本段代码核心功能：根据条件 `not any((marker in line for line in comments))` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not any(marker in line for line in comments):
            violations.append(
                f"line {line_number}: {label}前缺少教学标记 {marker}"
            )

    return violations


# 本段代码核心功能：定义 `_python_violations`，对单个Python文件执行文件头、定义和控制流审计。
# - 输入：参数为 `path`；路径必须指向UTF-8或UTF-8 BOM编码的人工Python文件。
# - 处理：解析AST，检查类、函数、if、for、while、try、with和match节点之前的教学块。
# - 输出：返回类型为 `list[str]`；每条错误包含物理行号和节点类型。
# - 常量依据：节点范围对应CODE_COMMENTING_STANDARD.md列出的定义、分支、循环、异常和资源处理。
# - 为什么这样写：AST比正则更能识别装饰器、多行函数签名和嵌套控制流，降低误报。
def _python_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    tree = ast.parse(text)
    violations = _teaching_block_violations(
        lines[:16],
        label="文件头",
        line_number=1,
    )

    # 本段代码核心功能：遍历语法树中全部可复用定义和主要逻辑控制节点。
    # - 输入：ast.parse产生的完整语法树。
    # - 处理：定义节点把检查位置移动到第一个装饰器；控制节点直接使用其关键字所在行。
    # - 输出：持续扩展violations列表，不改变源代码。
    # - 常量依据：装饰器必须位于类或函数之前，因此教学块也必须放在第一个装饰器之前。
    # - 为什么这样写：统一遍历可覆盖嵌套函数和测试内部辅助函数，避免只检查顶层造成遗漏。
    for node in ast.walk(tree):
        label: str | None = None
        line_number: int | None = None

        # 本段代码核心功能：识别类、同步函数和异步函数，并计算其真正的前置注释位置。
        # - 输入：当前AST节点及其decorator_list。
        # - 处理：有装饰器时取最早装饰器行，否则取定义关键字行。
        # - 输出：设置label和line_number供统一窗口检查使用。
        # - 常量依据：Python语法要求装饰器紧邻定义，不能把注释放在装饰器与定义之间。
        # - 为什么这样写：从装饰器起点检查可保证注释在运行时语义单元之前，而不是插入错误位置。
        if isinstance(node, ast.ClassDef):
            line_number = min(
                [node.lineno]
                + [decorator.lineno for decorator in node.decorator_list]
            )
            label = f"类 {node.name}"
        # 本段代码核心功能：根据条件 `isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_number = min(
                [node.lineno]
                + [decorator.lineno for decorator in node.decorator_list]
            )
            label = f"函数 {node.name}"
        # 本段代码核心功能：根据条件 `isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Ma` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        elif isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.With,
                ast.AsyncWith,
                ast.Match,
            ),
        ):
            line_number = node.lineno
            label = type(node).__name__

        # 本段代码核心功能：仅对成功识别且具有有效行号的节点执行教学窗口检查。
        # - 输入：上一步得到的label和line_number。
        # - 处理：提取邻近注释窗口并追加全部结构缺口。
        # - 输出：violations列表可能增加，也可能保持不变。
        # - 常量依据：None表示当前AST节点不属于本任务强制审计范围。
        # - 为什么这样写：集中执行检查可以让各种节点共用同一口径，减少审计器自身分支差异。
        if label is not None and line_number is not None:
            violations.extend(
                _teaching_block_violations(
                    _preceding_comment_window(lines, line_number),
                    label=label,
                    line_number=line_number,
                )
            )

    return violations


# 本段代码核心功能：定义 `_powershell_violations`，检查PowerShell文件头和主要控制结构前置说明。
# - 输入：参数为 `path`；文件按UTF-8 BOM兼容方式读取。
# - 处理：逐行识别function、if、elseif、foreach、for、while、try、catch、finally和switch关键字。
# - 输出：返回类型为 `list[str]`；缺口包含关键字和行号。
# - 常量依据：正则只匹配行首控制关键字，避免字符串内容和注释文本被误认为代码。
# - 为什么这样写：PowerShell没有内置AST依赖要求时，受限正则足以覆盖交付脚本的顺序控制结构。
def _powershell_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    violations = _teaching_block_violations(
        lines[:16],
        label="PowerShell文件头",
        line_number=1,
    )
    pattern = re.compile(
        r"^\s*(function|if|elseif|foreach|for|while|try|catch|finally|switch)\b",
        re.IGNORECASE,
    )

    # 本段代码核心功能：逐行定位PowerShell主要逻辑块并复用统一教学窗口检查。
    # - 输入：带一基行号的PowerShell物理行序列。
    # - 处理：只有行首命中受控关键字时才检查，普通赋值和字符串不进入本循环。
    # - 输出：持续累积缺失教学块的行号和关键字。
    # - 常量依据：关键字集合覆盖项目交付脚本最常见的定义、分支、循环和异常控制。
    # - 为什么这样写：保守匹配能在Windows PowerShell 5.1环境中稳定运行，且不依赖额外解析模块。
    for line_number, line in enumerate(lines, start=1):
        match = pattern.match(line)

        # 本段代码核心功能：跳过不是受控PowerShell逻辑块的普通代码行。
        # - 输入：当前正则匹配结果。
        # - 处理：未命中时直接进入下一行，命中时提取关键字用于错误标签。
        # - 输出：不命中不产生错误；命中后执行窗口检查。
        # - 常量依据：match为None是Python正则的标准未匹配结果。
        # - 为什么这样写：早跳过减少不必要的窗口扫描，也避免普通命令被过度要求重复注释。
        if match is None:
            continue
        keyword = match.group(1)
        violations.extend(
            _teaching_block_violations(
                _preceding_comment_window(lines, line_number),
                label=f"PowerShell {keyword}",
                line_number=line_number,
            )
        )

    return violations


# 本段代码核心功能：定义 `TeachingCommentComplianceTests`，组织跨TASK代码注释门禁测试。
# - 输入：项目根目录和两个固定目标清单。
# - 处理：逐文件确认存在，再调用对应语言检查器并把全部缺口汇总为单次断言消息。
# - 输出：输出unittest测试结果；合规时通过，缺失文件或注释时失败。
# - 常量依据：项目根目录按本测试文件上两级目录解析，符合tests目录的标准布局。
# - 为什么这样写：单一测试类把历史修复变成长期回归门禁，后续修改这些文件时不能再次删除注释。
class TeachingCommentComplianceTests(unittest.TestCase):
    # 本段代码核心功能：定义 `test_task_022_to_024_code_has_teaching_comments`，检查全部目标Python文件。
    # - 输入：PYTHON_TARGETS中的相对路径和当前项目根目录。
    # - 处理：逐文件验证存在并运行AST教学注释检查，将错误按文件分组。
    # - 输出：没有错误时断言通过；存在错误时一次显示全部文件和精确行号。
    # - 常量依据：目标数量由任务交付范围决定，不使用模糊的全目录猜测。
    # - 为什么这样写：分组错误便于一次修复全部缺口，也防止只修第一个文件后反复运行。
    def test_task_022_to_024_code_has_teaching_comments(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        failures: list[str] = []

        # 本段代码核心功能：遍历Python目标文件并执行存在性和结构合规检查。
        # - 输入：项目根目录和PYTHON_TARGETS不可变路径列表。
        # - 处理：缺失文件直接记录；存在文件调用_python_violations获取全部缺口。
        # - 输出：向failures追加按文件分组的错误文本。
        # - 常量依据：所有路径均使用POSIX风格相对路径，Path会在Windows和Linux上自动适配分隔符。
        # - 为什么这样写：同一测试可在沙盒Linux和用户Windows环境运行，避免平台相关路径判断。
        for relative_path in PYTHON_TARGETS:
            path = project_root / relative_path

            # 本段代码核心功能：在解析前先确认任务文件确实存在于当前仓库。
            # - 输入：由项目根目录和相对路径组成的绝对Path。
            # - 处理：缺失时记录错误并跳过AST解析，存在时继续审计。
            # - 输出：缺失文件错误或对应文件教学缺口。
            # - 常量依据：Path.is_file只接受普通文件，目录不能冒充源码文件。
            # - 为什么这样写：明确缺失比后续FileNotFoundError更容易判断任务是否尚未正确应用。
            if not path.is_file():
                failures.append(f"{relative_path}: file is missing")
                continue
            violations = _python_violations(path)

            # 本段代码核心功能：仅在当前文件存在教学缺口时把详情加入最终失败报告。
            # - 输入：当前文件的violations列表。
            # - 处理：用换行和缩进保留每一条行号信息。
            # - 输出：failures可能增加一个文件级错误块。
            # - 常量依据：空列表代表该文件所有受控节点均合规。
            # - 为什么这样写：合规文件不输出噪声，失败报告只聚焦需要修复的源码。
            if violations:
                failures.append(
                    relative_path + ":\n  " + "\n  ".join(violations)
                )

        self.assertFalse(failures, "\n\n".join(failures))

    # 本段代码核心功能：定义 `test_task_022_powershell_has_teaching_comments`，检查仓库内TASK_022 PowerShell脚本。
    # - 输入：POWERSHELL_TARGETS中的相对路径。
    # - 处理：逐文件确认存在，再检查文件头和主要逻辑关键字前的完整教学块。
    # - 输出：全部PowerShell目标合规时通过，否则显示缺失标记和行号。
    # - 常量依据：交付包自身PowerShell不在项目仓库内，由包级verify脚本另行检查。
    # - 为什么这样写：仓库测试不能依赖下载目录，同时仍能长期保护已提交的TASK_022脚本。
    def test_task_022_powershell_has_teaching_comments(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        failures: list[str] = []

        # 本段代码核心功能：遍历PowerShell目标并汇总存在性或教学注释缺口。
        # - 输入：项目根目录与POWERSHELL_TARGETS路径集合。
        # - 处理：缺失文件记录后继续；存在文件调用_powershell_violations。
        # - 输出：failures列表保存所有文件级错误块。
        # - 常量依据：路径处理与Python目标保持同一跨平台规则。
        # - 为什么这样写：统一汇总避免测试在第一个PowerShell缺口处提前终止。
        for relative_path in POWERSHELL_TARGETS:
            path = project_root / relative_path

            # 本段代码核心功能：确认PowerShell脚本存在后再读取和解析其控制结构。
            # - 输入：当前PowerShell绝对路径。
            # - 处理：不存在时记录错误并进入下一项。
            # - 输出：缺失错误或后续教学注释检查结果。
            # - 常量依据：文件必须是普通文件，不能是同名目录。
            # - 为什么这样写：先做存在性检查可提供比编码读取异常更直接的任务状态提示。
            if not path.is_file():
                failures.append(f"{relative_path}: file is missing")
                continue
            violations = _powershell_violations(path)

            # 本段代码核心功能：把当前PowerShell文件的全部缺口格式化为单个失败块。
            # - 输入：_powershell_violations返回的错误列表。
            # - 处理：仅非空时加入failures，并保留每条行号信息。
            # - 输出：failures可能增加一个字符串。
            # - 常量依据：空列表代表文件头和全部受控关键字均具有完整教学块。
            # - 为什么这样写：聚合展示比逐条断言更适合一次性维护大量前置注释。
            if violations:
                failures.append(
                    relative_path + ":\n  " + "\n  ".join(violations)
                )

        self.assertFalse(failures, "\n\n".join(failures))


    # 本段代码核心功能：定义 `test_authority_documents_require_comments_before_sandbox_tests`，验证流程规则已经写回权威文件。
    # - 输入：AUTHORITY_DOCUMENT_TARGETS中的Markdown路径和AUTHORITY_MARKER。
    # - 处理：逐文件确认存在、按UTF-8读取并检查唯一标记与核心禁止语句。
    # - 输出：两个权威文档均包含门禁时通过，否则显示缺失文件。
    # - 常量依据：用户明确要求交付代码在沙盒运行前就已经完成教学注释。
    # - 为什么这样写：流程约束进入自动测试后，后续任务无法仅靠口头承诺绕过。
    def test_authority_documents_require_comments_before_sandbox_tests(
        self,
    ) -> None:
        project_root = Path(__file__).resolve().parents[1]
        failures: list[str] = []

        # 本段代码核心功能：逐个读取权威文档并检查唯一门禁标记和禁止后补注释语义。
        # - 输入：项目根目录和两个相对路径。
        # - 处理：缺失文件记录错误；存在文件检查精确标记和“第一次沙盒”关键表达。
        # - 输出：failures保存全部文档缺口。
        # - 常量依据：同一测试同时保护注释标准和开发工作流。
        # - 为什么这样写：一次报告全部缺口，便于维护者同步修复而不是只改一个文件。
        for relative_path in AUTHORITY_DOCUMENT_TARGETS:
            path = project_root / relative_path

            # 本段代码核心功能：阻止缺失权威文件被后续字符串读取异常掩盖。
            # - 输入：当前Markdown绝对路径。
            # - 处理：不是普通文件时记录并进入下一项。
            # - 输出：failures可能追加缺失错误。
            # - 常量依据：Path.is_file不会把目录误当作有效文档。
            # - 为什么这样写：明确错误比FileNotFoundError更适合单元测试汇总。
            if not path.is_file():
                failures.append(f"{relative_path}: file is missing")
                continue
            content = path.read_text(encoding="utf-8-sig")

            # 本段代码核心功能：确认整改规则以唯一标记和明确沙盒前置语义真实存在。
            # - 输入：权威Markdown完整正文。
            # - 处理：同时检查AUTHORITY_MARKER和“第一次沙盒”字符串。
            # - 输出：任一缺失时记录当前文件。
            # - 常量依据：标记保证幂等，中文短语保证规则不是空壳章节。
            # - 为什么这样写：双重断言既防重复追加，也防只保留标记却删掉实际约束。
            if AUTHORITY_MARKER not in content or "第一次沙盒" not in content:
                failures.append(
                    f"{relative_path}: sandbox-first teaching-comment gate missing"
                )

        self.assertFalse(failures, "\n".join(failures))

# 本段代码核心功能：当文件被直接执行时启动标准unittest测试运行器。
# - 输入：操作系统传入的命令行参数，由unittest.main解析。
# - 处理：发现本模块内以test开头的方法并依次运行。
# - 输出：通过标准输出和进程退出码表达测试结果。
# - 常量依据：`__main__`是Python直接执行模块的标准入口判断。
# - 为什么这样写：既支持项目统一discover，也方便开发者单独运行本门禁文件定位问题。
if __name__ == "__main__":
    unittest.main()
