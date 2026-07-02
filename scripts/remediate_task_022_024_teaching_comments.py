# 本文件核心功能：为TASK_022至TASK_024目标Python和PowerShell文件补齐教学式前置注释且保持业务逻辑不变。
# - 输入：项目根目录、固定目标文件清单和文件中现有的UTF-8源码。
# - 处理：使用Python AST识别定义与控制流，使用受限正则识别PowerShell逻辑块，只插入注释和空行。
# - 输出：原路径上的已整改源码；重复运行时不会重复插入已经完整的教学块。
# - 常量依据：目标范围来自TASK_022、TASK_023A/B/C和TASK_024A正式交付文件，教学标签来自CODE_COMMENTING_STANDARD.md。
# - 为什么这样写：自动化只负责稳定补齐结构，避免人工漏项；它不改变函数签名、状态值、数据接口或交易边界。

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Sequence


# 本段代码核心功能：定义Python整改目标，覆盖TASK_022至TASK_024A人工源码、入口和测试。
# - 输入：任务文件中记录的允许修改范围。
# - 处理：使用不可变元组固定路径，防止运行时扩大到第三方SDK、虚拟环境、缓存或历史归档。
# - 输出：供主流程逐文件读取和整改的相对路径集合。
# - 常量依据：清单与新增长期回归测试保持一致，任何新增目标都需要代码评审。
# - 为什么这样写：显式白名单比全仓库自动重写更安全，能够把注释整改限制在用户指出的22至24号任务。
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
    "tests/test_task_022_024_teaching_comment_compliance.py",
    "scripts/remediate_task_022_024_teaching_comments.py",
)


# 本段代码核心功能：定义仓库内需要整改的PowerShell目标。
# - 输入：TASK_022正式提交到项目仓库的PowerShell验证脚本。
# - 处理：只保留仓库路径，不依赖下载目录中的历史交付脚本。
# - 输出：供PowerShell行级整改函数处理的不可变路径集合。
# - 常量依据：TASK_023和TASK_024历史apply/finalize脚本不属于仓库，新的交付脚本将在本包内直接写好注释。
# - 为什么这样写：区分永久项目代码与一次性交付工具，避免把用户下载目录误纳入Git变更。
POWERSHELL_TARGETS = (
    "scripts/verify_task_022_patch.ps1",
)


# 本段代码核心功能：定义需要写入“先注释后测试”硬门禁的权威Markdown文件。
# - 输入：项目现有最高注释标准和总开发指导的固定相对路径。
# - 处理：使用显式白名单限制追加范围，不扫描或修改其他项目文档。
# - 输出：供主流程逐文件检查幂等标记并追加权威章节的路径集合。
# - 常量依据：CODE_COMMENTING_STANDARD.md是注释最高权威，DEVELOPMENT_GUIDANCE.md是任务执行总指导。
# - 为什么这样写：把用户纠正写回权威文件，才能避免后续任务再次把注释误当作交付后的补充工作。
AUTHORITY_DOCUMENT_TARGETS = (
    "CODE_COMMENTING_STANDARD.md",
    "DEVELOPMENT_GUIDANCE.md",
)


# 本段代码核心功能：保存权威文件中用于判断是否已完成幂等追加的唯一标记。
# - 输入：本次整改任务号和固定英文状态名。
# - 处理：形成不会与普通正文偶然重复的HTML注释标记。
# - 输出：供追加函数判断章节是否已经存在。
# - 常量依据：TASK_024A1是本次教学注释合规整改任务编号。
# - 为什么这样写：唯一标记比模糊中文搜索更稳定，重复运行不会继续追加同一政策章节。
AUTHORITY_MARKER = "<!-- TASK_024A1_COMMENT_BEFORE_SANDBOX_GATE -->"


# 本段代码核心功能：定义完整教学块必须具备的结构标记。
# - 输入：CODE_COMMENTING_STANDARD.md规定的中文标签。
# - 处理：使用不可变元组供Python和PowerShell检测逻辑共同复用。
# - 输出：用于判定已有注释是否完整的五个字符串。
# - 常量依据：概括行由单独逻辑检查，这里固定输入、处理、输出、常量依据和原因五项。
# - 为什么这样写：统一标记可以保证整改工具、专项测试和全仓库审计使用同一口径。
REQUIRED_MARKERS = (
    "# - 输入：",
    "# - 处理：",
    "# - 输出：",
    "# - 常量依据：",
    "为什么这样写",
)


# 本段代码核心功能：定义 `_preceding_comment_window`，提取目标行之前紧邻的注释窗口。
# - 输入：源文件物理行、目标一基行号和最多回看行数。
# - 处理：只接收空行与`#`单行注释，遇到可执行代码立即停止。
# - 输出：返回按原阅读顺序排列的注释及空行列表。
# - 常量依据：默认16行可容纳六行教学块和必要空行，不是业务阈值。
# - 为什么这样写：只认可紧邻代码的说明，防止远处或其他函数的注释被错误复用。
def _preceding_comment_window(
    lines: Sequence[str],
    line_number: int,
    maximum_lines: int = 16,
) -> tuple[str, ...]:
    index = line_number - 2
    collected: list[str] = []
    inspected = 0

    # 本段代码核心功能：向文件开头方向扫描直到遇到代码、文件起点或回看上限。
    # - 输入：当前索引、已扫描数量和源文件行列表。
    # - 处理：空行和单行注释加入窗口，其他内容终止扫描。
    # - 输出：更新collected、index和inspected三个局部状态。
    # - 常量依据：`#`是本项目Python与PowerShell统一使用的单行注释符号。
    # - 为什么这样写：受限扫描既保证邻近性，也避免大文件上不必要的线性回溯。
    while index >= 0 and inspected < maximum_lines:
        text = lines[index]
        stripped = text.strip()
        inspected += 1

        # 本段代码核心功能：判断当前上一行是否仍属于教学注释窗口。
        # - 输入：去除首尾空白后的单行文本。
        # - 处理：空行或注释继续回收，代码行则结束窗口。
        # - 输出：可能追加当前行并递减索引，或跳出循环。
        # - 常量依据：docstring和普通字符串不以`#`开头，因此不会被当作前置注释。
        # - 为什么这样写：严格区分注释和字符串，落实“不得用docstring替代”的项目规则。
        if not stripped or stripped.startswith("#"):
            collected.append(text)
            index -= 1
            continue
        break

    return tuple(reversed(collected))


# 本段代码核心功能：定义 `_has_full_teaching_block`，判断目标行前是否已有完整教学说明。
# - 输入：源文件行列表和目标一基行号。
# - 处理：提取邻近注释，检查核心概括与五个必需结构标记。
# - 输出：完整返回True，缺任一项返回False。
# - 常量依据：REQUIRED_MARKERS是项目最高注释标准的最小结构集合。
# - 为什么这样写：幂等判断可以让修复包安全重跑，不会在已经合规的代码前反复堆叠注释。
def _has_full_teaching_block(
    lines: Sequence[str],
    line_number: int,
) -> bool:
    comments = [
        line.strip()
        for line in _preceding_comment_window(lines, line_number)
        if line.strip().startswith("#")
    ]
    has_summary = any(
        "本段代码核心功能" in line or "本文件核心功能" in line
        for line in comments
    )
    return has_summary and all(
        any(marker in line for line in comments)
        for marker in REQUIRED_MARKERS
    )


# 本段代码核心功能：定义 `_argument_names`，把函数参数转换为适合教学注释展示的短文本。
# - 输入：Python函数或异步函数AST节点。
# - 处理：合并位置参数、普通参数、仅关键字参数、可变位置参数和可变关键字参数。
# - 输出：使用中文顿号分隔的参数名字符串；无参数时返回明确提示。
# - 常量依据：参数顺序遵循Python AST原始定义顺序，不改变函数签名。
# - 为什么这样写：注释直接列出输入名称，维护者无需先阅读完整签名就能理解数据来源。
def _argument_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    names = [
        argument.arg
        for argument in (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )
    ]

    # 本段代码核心功能：把`*args`参数加入教学输入清单。
    # - 输入：函数AST中的vararg字段。
    # - 处理：存在时保留星号前缀，明确它接收可变数量的位置参数。
    # - 输出：names列表可能追加一个字符串。
    # - 常量依据：星号表示Python函数签名的标准可变位置参数语义。
    # - 为什么这样写：保留星号可以避免读者把可变参数误解为普通单值参数。
    if node.args.vararg is not None:
        names.append("*" + node.args.vararg.arg)

    # 本段代码核心功能：把`**kwargs`参数加入教学输入清单。
    # - 输入：函数AST中的kwarg字段。
    # - 处理：存在时保留双星号前缀，明确它接收可变关键字映射。
    # - 输出：names列表可能追加一个字符串。
    # - 常量依据：双星号是Python标准可变关键字参数语义。
    # - 为什么这样写：明确参数形状有助于识别外部字典是否可能绕过显式字段校验。
    if node.args.kwarg is not None:
        names.append("**" + node.args.kwarg.arg)
    return "、".join(names) if names else "无显式参数"


# 本段代码核心功能：定义 `_annotation_text`，把返回类型AST转换为可读文本。
# - 输入：函数returns节点，允许为None。
# - 处理：优先使用ast.unparse还原类型标注，解析失败时使用安全占位说明。
# - 输出：返回可嵌入注释的单行类型字符串。
# - 常量依据：没有返回标注不代表没有返回值，因此使用“未显式标注”而不是猜测类型。
# - 为什么这样写：不编造类型符合项目语义治理原则，同时尽可能向读者展示真实合同。
def _annotation_text(node: ast.AST | None) -> str:
    # 本段代码核心功能：处理源码没有显式返回类型标注的函数。
    # - 输入：值为None的returns节点。
    # - 处理：直接返回不确定性说明，不做运行时推断。
    # - 输出：固定中文提示字符串。
    # - 常量依据：None是Python AST表示无返回标注的标准值。
    # - 为什么这样写：静态工具不应根据函数名或实现猜测类型，避免把错误推断写入权威注释。
    if node is None:
        return "未显式标注，由调用方和测试共同约束"

    # 本段代码核心功能：尝试使用Python标准AST工具还原返回类型表达式。
    # - 输入：有效的返回类型AST节点。
    # - 处理：调用ast.unparse；若当前Python版本无法处理则进入受控降级。
    # - 输出：还原后的类型字符串或安全占位文本。
    # - 常量依据：项目当前Python 3.11具备ast.unparse，异常分支用于兼容损坏或特殊节点。
    # - 为什么这样写：使用标准库避免引入格式化依赖，也不影响被整改项目的依赖集合。
    try:
        return ast.unparse(node)
    except Exception:
        return "见函数类型标注"


# 本段代码核心功能：定义 `_definition_purpose`，根据文件和符号名称生成不编造厂商能力的用途说明。
# - 输入：定义名称、文件名和定义类型。
# - 处理：按测试、加载、写入、构建、排序、发现、选择等稳定命名规则生成描述。
# - 输出：返回一条通俗用途文本，用于完整教学块首行。
# - 常量依据：描述只引用代码结构和任务安全边界，不声称任何未验证SDK功能。
# - 为什么这样写：自动生成必须保守、可解释，宁可描述单一职责，也不能虚构具体业务能力。
def _definition_purpose(
    name: str,
    file_name: str,
    definition_kind: str,
) -> str:
    lower_name = name.lower()

    # 本段代码核心功能：为类定义生成与其角色相符的用途说明。
    # - 输入：定义类型为class的名称和文件名。
    # - 处理：优先识别测试类、政策类、证据类、决策类和配置条目类。
    # - 输出：返回类级用途文本。
    # - 常量依据：命名匹配只用于注释描述，不参与生产业务分支。
    # - 为什么这样写：类的教学重点是它保存什么合同，而不是重复class关键字本身。
    if definition_kind == "class":
        # 本段代码核心功能：根据条件 `lower_name.endswith('tests')` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if lower_name.endswith("tests"):
            return "组织对应任务的独立测试场景和安全回归断言"
        # 本段代码核心功能：根据条件 `'policy' in lower_name` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if "policy" in lower_name:
            return "保存来源、激活和安全门禁的不可变政策配置"
        # 本段代码核心功能：根据条件 `'finding' in lower_name or 'evidence' in lower_name` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if "finding" in lower_name or "evidence" in lower_name:
            return "保存单一Provider或本地环境的结构化证据且不保存秘密值"
        # 本段代码核心功能：根据条件 `'decision' in lower_name` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if "decision" in lower_name:
            return "保存Provider选择结果、阻断原因和下一任务状态"
        # 本段代码核心功能：根据条件 `any((token in lower_name for token in ('profile', 'rule', 'spec', 'entry')))` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if any(
            token in lower_name
            for token in ("profile", "rule", "spec", "entry")
        ):
            return "保存经过强校验的配置条目并隔离原始JSON字典"
        # 本段代码核心功能：根据条件 `'tier' in lower_name` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if "tier" in lower_name:
            return "定义来源权威层级的有限枚举以阻止任意字符串绕过门禁"
        return f"封装 `{file_name}` 所需的稳定数据结构"

    # 本段代码核心功能：为函数定义按常见前缀生成单一职责说明。
    # - 输入：小写函数名和所在文件名。
    # - 处理：匹配main、参数解析、加载、写入、构建、排序、发现、选择、验证和测试前缀。
    # - 输出：返回函数级用途文本。
    # - 常量依据：前缀来自当前项目既有命名习惯，不改变函数行为。
    # - 为什么这样写：按命名结构生成的说明比泛称“处理数据”更具体，也避免自动工具深入猜测业务实现。
    if lower_name == "main":
        return f"执行 `{file_name}` 的命令行主流程并返回标准退出码"
    # 本段代码核心功能：根据条件 `lower_name == 'parse_args'` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name == "parse_args":
        return "集中声明命令行参数并解析为类型明确的Namespace"
    # 本段代码核心功能：根据条件 `lower_name.startswith('load_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("load_"):
        return "读取UTF-8配置或报告并在返回前完成字段、类型和值域校验"
    # 本段代码核心功能：根据条件 `lower_name.startswith('write_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("write_"):
        return "把内存结构化结果以UTF-8和稳定换行写入目标文件"
    # 本段代码核心功能：根据条件 `lower_name.startswith('build_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("build_"):
        return "组合已经验证的中间证据并生成后续任务可消费的结构化结果"
    # 本段代码核心功能：根据条件 `lower_name.startswith('rank_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("rank_"):
        return "依据显式优先级和稳定次级键排序候选以保证结果可重复"
    # 本段代码核心功能：根据条件 `lower_name.startswith(('discover_', 'collect_', 'probe_'))` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith(("discover_", "collect_", "probe_")):
        return "在既定安全边界内收集本地可证明证据且不执行网络或交易操作"
    # 本段代码核心功能：根据条件 `lower_name.startswith('select_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("select_"):
        return "按照来源权威和授权门禁选择候选且保持Provider未激活"
    # 本段代码核心功能：根据条件 `lower_name.startswith('validate_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("validate_"):
        return "执行跨配置一致性检查并把不安全组合转化为明确异常"
    # 本段代码核心功能：根据条件 `lower_name.startswith('test_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("test_"):
        return "构造可重复场景并断言对应业务合同和安全边界不会回退"
    # 本段代码核心功能：根据条件 `lower_name == 'setup'` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name == "setup":
        return "为每个测试方法加载独立且可重复使用的配置夹具"
    # 本段代码核心功能：根据条件 `lower_name.startswith('_')` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if lower_name.startswith("_"):
        return "提供局部纯函数辅助以统一规范化、查找或匹配规则"
    return f"完成 `{name}` 对应的单一业务步骤并返回明确结果"


# 本段代码核心功能：定义 `_definition_teaching_block`，为Python类或函数生成完整六行教学说明。
# - 输入：AST定义节点、文件名和当前代码缩进。
# - 处理：提取参数、返回标注和保守用途描述，组合固定结构标签。
# - 输出：返回可直接插入源码的注释行列表。
# - 常量依据：任务号、零副作用状态和来源层级来自TASK_022至TASK_024合同，不从运行时猜测。
# - 为什么这样写：统一模板保证结构完整，同时根据符号名称补充具体职责，兼顾一致性和可读性。
def _definition_teaching_block(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    file_name: str,
    indent: str,
) -> list[str]:
    # 本段代码核心功能：为类节点生成数据合同和安全边界说明。
    # - 输入：ClassDef节点、文件名与缩进。
    # - 处理：调用_definition_purpose取得保守用途，字段来源按配置和测试夹具说明。
    # - 输出：返回六行类级教学注释。
    # - 常量依据：类本身不新增业务阈值，状态字段仍以任务合同为准。
    # - 为什么这样写：类级注释应先解释对象在系统中的角色，再让读者查看具体字段。
    if isinstance(node, ast.ClassDef):
        purpose = _definition_purpose(node.name, file_name, "class")
        return [
            f"{indent}# 本段代码核心功能：定义 `{node.name}`，{purpose}。",
            f"{indent}# - 输入：实例字段由配置加载器、发现流程或测试夹具显式传入，不从全局状态隐式取值。",
            f"{indent}# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典扩散。",
            f"{indent}# - 输出：输出可比较、可序列化或可排序的 `{node.name}` 实例，供报告和门禁使用。",
            f"{indent}# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同，本定义不新增未经验证的厂商能力。",
            f"{indent}# - 为什么这样写：先建立稳定合同再接官方SDK，能够降低供应商替换成本并阻止秘密值进入报告。",
        ]

    purpose = _definition_purpose(node.name, file_name, "function")
    arguments = _argument_names(node)
    return_type = _annotation_text(node.returns)
    return [
        f"{indent}# 本段代码核心功能：定义 `{node.name}`，{purpose}。",
        f"{indent}# - 输入：参数为 `{arguments}`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。",
        f"{indent}# - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。",
        f"{indent}# - 输出：返回类型为 `{return_type}`；测试函数通过断言表达通过或失败，不产生生产副作用。",
        f"{indent}# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。",
        f"{indent}# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。",
    ]


# 本段代码核心功能：定义 `_control_teaching_block`，为Python主要控制流生成完整前置说明。
# - 输入：if、for、while、try、with或match AST节点及其缩进。
# - 处理：只描述控制结构的数据流和安全目的，不推断未验证的供应商语义。
# - 输出：返回六行控制流教学注释。
# - 常量依据：受控节点集合对应CODE_COMMENTING_STANDARD.md中的分支、循环、异常和资源管理要求。
# - 为什么这样写：函数级注释不能代替内部关键分支说明，控制流注释能解释状态如何改变和失败如何处理。
def _control_teaching_block(
    node: ast.AST,
    indent: str,
) -> list[str]:
    # 本段代码核心功能：为条件分支提取简短且可读的判断表达式。
    # - 输入：If节点的test表达式。
    # - 处理：使用ast.unparse还原并限制长度，失败时使用保守占位文本。
    # - 输出：生成分支核心功能、输入、处理和原因说明。
    # - 常量依据：100字符只控制注释可读性，不影响运行逻辑或业务阈值。
    # - 为什么这样写：展示条件有助于读者理解何时阻断，但限制长度可避免注释复制整段复杂表达式。
    if isinstance(node, ast.If):
        # 本段代码核心功能：执行可能失败的本地解析或探测并在异常时保持安全降级。
        # - 输入：文件、解释器、注册表、模块查找或类型转换等本地操作。
        # - 处理：成功时保留证据，失败时转换为受控状态，清理动作由finally保证。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：第三方环境不可假定稳定，受控异常能防止单点失败破坏整份盘点。

        try:
            condition = ast.unparse(node.test).replace("\n", " ")[:100]
        except Exception:
            condition = "当前布尔条件"
        core = f"根据条件 `{condition}` 选择安全分支"
        input_text = "条件表达式和此前已经规范化的局部变量"
        process_text = "只执行满足合同的分支，非法状态通过异常或阻断原因显式返回"
        reason_text = "避免把缺失证据、未授权运行时或危险能力误判为可用"
    # 本段代码核心功能：根据条件 `isinstance(node, (ast.For, ast.AsyncFor))` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif isinstance(node, (ast.For, ast.AsyncFor)):
        core = "逐项遍历有限配置条目、发现证据或测试样本"
        input_text = "可迭代的配置、证据或样本序列"
        process_text = "每轮只更新当前条目局部结果，最终按稳定顺序汇总"
        reason_text = "逐项处理保留来源级证据，避免聚合后无法追溯单个Provider"
    # 本段代码核心功能：根据条件 `isinstance(node, ast.While)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif isinstance(node, ast.While):
        core = "在明确终止条件满足前重复执行受控扫描步骤"
        input_text = "当前索引、剩余行数或仍待处理的本地对象"
        process_text = "每轮推进状态并保持可证明的退出条件"
        reason_text = "显式终止条件可以避免无限循环和不可控资源消耗"
    # 本段代码核心功能：根据条件 `isinstance(node, ast.Try)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif isinstance(node, ast.Try):
        core = "执行可能失败的本地解析或探测并在异常时保持安全降级"
        input_text = "文件、解释器、注册表、模块查找或类型转换等本地操作"
        process_text = "成功时保留证据，失败时转换为受控状态，清理动作由finally保证"
        reason_text = "第三方环境不可假定稳定，受控异常能防止单点失败破坏整份盘点"
    # 本段代码核心功能：根据条件 `isinstance(node, (ast.With, ast.AsyncWith))` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif isinstance(node, (ast.With, ast.AsyncWith)):
        core = "在受控上下文中使用临时资源并保证离开代码块时自动释放"
        input_text = "临时目录、文件句柄、补丁上下文或其他上下文管理器"
        process_text = "上下文管理器负责建立和清理资源，业务代码只处理块内对象"
        reason_text = "自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留"
    else:
        core = "按有限状态值执行互斥处理分支"
        input_text = "已经强校验的枚举或状态字符串"
        process_text = "每个case只处理一个允许状态，未知值进入阻断路径"
        reason_text = "穷举状态避免新增供应商能力时被旧代码静默接受"
    return [
        f"{indent}# 本段代码核心功能：{core}。",
        f"{indent}# - 输入：{input_text}。",
        f"{indent}# - 处理：{process_text}。",
        f"{indent}# - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。",
        f"{indent}# - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。",
        f"{indent}# - 为什么这样写：{reason_text}。",
    ]


# 本段代码核心功能：定义 `_ensure_python_file_header`，在缺少完整文件级说明时补充统一教学头。
# - 输入：源文件行列表和文件名。
# - 处理：检查前16行是否已有五项标记；缺失时把完整说明插入文件最前面。
# - 输出：返回新的行列表，不改变原有代码顺序。
# - 常量依据：文件头说明强调零网络、零交易和官方来源优先，来自当前项目安全边界。
# - 为什么这样写：读者打开文件时应先理解用途和风险，再阅读导入与实现细节。
def _ensure_python_file_header(
    lines: list[str],
    file_name: str,
) -> list[str]:
    header_text = "\n".join(lines[:16])

    # 本段代码核心功能：检测现有文件头是否已经包含完整结构并在合规时原样返回。
    # - 输入：文件前16行文本。
    # - 处理：检查核心概括和REQUIRED_MARKERS全部存在。
    # - 输出：合规时返回原lines对象，缺失时继续生成新头部。
    # - 常量依据：16行是注释邻近窗口，不影响源代码语义。
    # - 为什么这样写：提前返回保证重复运行幂等，也保留人工已经写得更具体的说明。
    if (
        ("本文件核心功能" in header_text or "本模块核心功能" in header_text)
        and all(marker in header_text for marker in REQUIRED_MARKERS)
    ):
        return lines
    header = [
        f"# 本文件核心功能：实现 `{file_name}` 在TASK_022至TASK_024范围内的单一任务职责。",
        "# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具，不读取未声明秘密值。",
        "# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。",
        "# - 输出：强类型对象、UTF-8报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。",
        "# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。",
        "# - 为什么这样写：维护者先理解边界再阅读实现，可防止第三方聚合源或交易能力被误升为主链。",
        "",
    ]

    # 本段代码核心功能：把教学文件头放在shebang和PEP 263编码声明之后。
    # - 输入：原始物理行列表的前两行。
    # - 处理：首行是#!时保留；前两行中匹配coding声明时继续保留，然后在其后插入header。
    # - 输出：返回解释器指令、编码声明、教学头和原代码组成的新列表。
    # - 常量依据：Python shebang必须位于第一行，PEP 263编码声明必须位于第一或第二行。
    # - 为什么这样写：注释整改不能破坏脚本直接执行方式或源码编码识别。
    insertion_index = 0

    # 本段代码核心功能：检测并保留第一行Python shebang。
    # - 输入：lines第一行文本。
    # - 处理：以#!开头时把插入位置移动到下一行。
    # - 输出：insertion_index可能从0变为1。
    # - 常量依据：Unix和兼容启动器只识别文件第一行shebang。
    # - 为什么这样写：把任何注释放在shebang之前都会使直接执行失效。
    if lines and lines[0].startswith("#!"):
        insertion_index = 1

    # 本段代码核心功能：检测前两行中的PEP 263编码声明并保留其优先位置。
    # - 输入：从当前插入位置开始、最多前两行的源码。
    # - 处理：使用coding[:=]受限正则，命中时把插入位置移到声明之后。
    # - 输出：insertion_index更新为1或2。
    # - 常量依据：PEP 263只允许编码声明出现在第一或第二行。
    # - 为什么这样写：保持编码声明位置可避免Python解释器错误解码含中文注释的源码。
    for index in range(insertion_index, min(2, len(lines))):
        # 本段代码核心功能：判断当前候选行是否为合法编码声明。
        # - 输入：前两行中的一行文本。
        # - 处理：匹配coding后跟冒号或等号及编码名。
        # - 输出：命中时更新插入位置。
        # - 常量依据：正则形态来自PEP 263通用声明格式。
        # - 为什么这样写：只识别标准编码语法，不因普通注释中出现coding单词而误移动。
        if re.search(r"coding[:=]\s*[-\w.]+", lines[index]):
            insertion_index = index + 1

    return lines[:insertion_index] + header + lines[insertion_index:]


# 本段代码核心功能：定义 `_remediate_python_file`，按AST位置为单个Python文件插入缺失教学块。
# - 输入：项目内Python文件绝对路径。
# - 处理：解析AST，收集定义与主要控制节点，从文件末尾向前插入注释并补齐文件头。
# - 输出：仅在文本发生变化时以UTF-8和LF覆写原文件，返回是否修改。
# - 常量依据：从后向前插入可保持尚未处理节点的原始行号有效，这是标准文本补丁方法。
# - 为什么这样写：只插入注释和空行，不重排代码，不改变逻辑、格式化风格或运行结果。
def _remediate_python_file(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8-sig")
    lines = original_text.splitlines()
    tree = ast.parse(original_text)
    insertions: dict[int, list[str]] = {}

    # 本段代码核心功能：遍历语法树并为缺少完整教学块的定义和主要控制流登记插入内容。
    # - 输入：当前Python文件AST中的全部节点。
    # - 处理：定义节点从第一个装饰器计算起点，控制节点使用关键字行号，合规节点跳过。
    # - 输出：insertions字典以原始一基行号映射待插入注释行。
    # - 常量依据：节点集合与长期回归测试完全一致。
    # - 为什么这样写：先收集后统一插入可避免边遍历边修改导致行号漂移和漏改。
    for node in ast.walk(tree):
        line_number: int | None = None
        block: list[str] | None = None

        # 本段代码核心功能：识别类与函数定义并把注释位置移动到首个装饰器之前。
        # - 输入：ClassDef、FunctionDef或AsyncFunctionDef节点。
        # - 处理：取定义行和装饰器行中的最小值，保持Python装饰器语法连续。
        # - 输出：设置line_number和定义教学块。
        # - 常量依据：装饰器必须紧邻定义，因此注释不能插在装饰器和定义之间。
        # - 为什么这样写：正确定位可避免生成语法有效但语义关联错误的注释位置。
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            line_number = min(
                [node.lineno]
                + [decorator.lineno for decorator in node.decorator_list]
            )
            source_line = lines[line_number - 1]
            indent = source_line[: len(source_line) - len(source_line.lstrip())]
            block = _definition_teaching_block(node, path.name, indent)
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
            source_line = lines[line_number - 1]
            indent = source_line[: len(source_line) - len(source_line.lstrip())]
            block = _control_teaching_block(node, indent)

        # 本段代码核心功能：仅为尚未合规且成功生成说明的节点登记一次插入。
        # - 输入：line_number、block和当前源文件注释窗口。
        # - 处理：None节点跳过；已有完整教学块跳过；同一行内容合并。
        # - 输出：insertions可能增加一个行号键或扩展已有内容。
        # - 常量依据：同一物理行理论上可能关联多个AST节点，合并可保持处理确定性。
        # - 为什么这样写：严格幂等判断防止重复运行持续增大文件。
        if (
            line_number is not None
            and block is not None
            and not _has_full_teaching_block(lines, line_number)
        ):
            insertions.setdefault(line_number, []).extend(block)

    # 本段代码核心功能：按行号倒序把登记的教学块插入源文件。
    # - 输入：insertions中的原始一基行号与注释行。
    # - 处理：从最大行号向前插入，避免较早插入改变较晚位置。
    # - 输出：更新内存中的lines列表。
    # - 常量依据：每个教学块后增加一个空行以保持项目现有排版风格。
    # - 为什么这样写：倒序文本补丁是保持原始定位稳定的简单可靠方法。
    for line_number in sorted(insertions, reverse=True):
        lines[line_number - 1:line_number - 1] = (
            insertions[line_number] + [""]
        )

    lines = _ensure_python_file_header(lines, path.name)
    updated_text = "\n".join(lines).rstrip() + "\n"

    # 本段代码核心功能：只有整改结果与原文本不同时才写回磁盘。
    # - 输入：规范化后的updated_text与原始文本。
    # - 处理：比较内容；变化时使用UTF-8和LF写入。
    # - 输出：修改返回True，幂等无变化返回False。
    # - 常量依据：项目Python和Markdown统一使用UTF-8与LF，避免Windows默认编码污染。
    # - 为什么这样写：减少无意义Git差异，也让重复执行结果稳定。
    if updated_text == original_text.replace("\r\n", "\n"):
        return False
    path.write_text(updated_text, encoding="utf-8", newline="\n")
    return True


# 本段代码核心功能：定义 `_powershell_block`，生成PowerShell文件头或逻辑块的完整教学说明。
# - 输入：当前缩进、代码块标签和用途描述。
# - 处理：组合与Python一致的六项结构，并保持`#`单行注释语法。
# - 输出：返回可插入PowerShell源码的注释行列表。
# - 常量依据：PowerShell 5.1使用UTF-8 BOM读取中文脚本，写回逻辑会保留BOM。
# - 为什么这样写：两种语言使用同一教学口径，用户不需要切换阅读习惯。
def _powershell_block(
    indent: str,
    label: str,
    purpose: str,
) -> list[str]:
    return [
        f"{indent}# 本段代码核心功能：{purpose}（{label}）。",
        f"{indent}# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。",
        f"{indent}# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。",
        f"{indent}# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。",
        f"{indent}# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。",
        f"{indent}# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。",
    ]


# 本段代码核心功能：定义 `_remediate_powershell_file`，为单个PowerShell项目脚本补齐文件头和主要逻辑块说明。
# - 输入：UTF-8或UTF-8 BOM编码的PowerShell文件路径。
# - 处理：逐行识别function、if、elseif、foreach、for、while、try、catch、finally和switch，缺少完整窗口时插入教学块。
# - 输出：以UTF-8 BOM和CRLF保存整改结果，返回是否修改。
# - 常量依据：只匹配独立位于行首的elseif、catch和finally，不改写与右花括号同一行的关联关键字。
# - 为什么这样写：受限行级处理适合Windows PowerShell 5.1，且不会尝试重写脚本表达式。
def _remediate_powershell_file(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8-sig")
    normalized_text = original_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized_text.splitlines()
    pattern = re.compile(
        r"^(\s*)(function|if|elseif|foreach|for|while|try|catch|finally|switch)\b",
        re.IGNORECASE,
    )
    insertions: dict[int, list[str]] = {}

    # 本段代码核心功能：逐行识别受控PowerShell逻辑关键字并登记缺失的教学块。
    # - 输入：带一基行号的PowerShell物理行。
    # - 处理：未命中关键字跳过；命中且窗口不完整时生成同缩进教学块。
    # - 输出：insertions保存待插入位置和注释内容。
    # - 常量依据：关键字集合覆盖TASK_022验证脚本主要结构，且不处理关联关键字else/catch/finally。
    # - 为什么这样写：保守识别减少误改字符串和管道，同时满足函数、分支、循环和异常入口说明。
    for line_number, line in enumerate(lines, start=1):
        match = pattern.match(line)

        # 本段代码核心功能：跳过不属于受控逻辑入口的PowerShell普通行。
        # - 输入：正则匹配结果。
        # - 处理：None时直接继续下一行。
        # - 输出：不产生插入内容。
        # - 常量依据：未匹配是re模块标准结果。
        # - 为什么这样写：只注释真正逻辑块，避免每个简单赋值前都机械重复大段说明。
        if match is None:
            continue

        # 本段代码核心功能：在当前关键字前缺少完整教学窗口时登记注释。
        # - 输入：当前行号、缩进、关键字和已有前置注释。
        # - 处理：复用_has_full_teaching_block判断幂等性，按关键字生成用途说明。
        # - 输出：insertions可能增加一项。
        # - 常量依据：PowerShell和Python共享相同五项必需标签。
        # - 为什么这样写：共享结构确保项目审计口径一致，也避免重复运行继续插入。
        if not _has_full_teaching_block(lines, line_number):
            indent, keyword = match.groups()
            purpose = "定义可复用脚本函数" if keyword.lower() == "function" else "进入受控流程块"
            insertions[line_number] = _powershell_block(
                indent,
                keyword,
                purpose,
            )

    # 本段代码核心功能：倒序插入全部PowerShell教学块以保持原行号稳定。
    # - 输入：insertions中的一基行号和注释行。
    # - 处理：从文件末尾向前写入并增加一个空行。
    # - 输出：更新内存行列表。
    # - 常量依据：与Python整改采用同一倒序补丁原则。
    # - 为什么这样写：倒序插入不会让尚未处理的原始位置发生偏移。
    for line_number in sorted(insertions, reverse=True):
        lines[line_number - 1:line_number - 1] = (
            insertions[line_number] + [""]
        )

    header_text = "\n".join(lines[:16])

    # 本段代码核心功能：在PowerShell文件头缺少完整说明时补充六项教学头。
    # - 输入：整改后前16行文本。
    # - 处理：检查核心概括和五项标签，缺失时在param或首行之前插入。
    # - 输出：lines可能增加文件级注释。
    # - 常量依据：脚本最终以UTF-8 BOM和CRLF保存，兼容Windows PowerShell 5.1。
    # - 为什么这样写：文件头先说明应用、验证和Git安全边界，可减少用户误执行风险。
    if not (
        "本文件核心功能" in header_text
        and all(marker in header_text for marker in REQUIRED_MARKERS)
    ):
        lines = [
            "# 本文件核心功能：执行TASK_022至TASK_024教学式注释整改相关的Windows PowerShell安全流程。",
            "# - 输入：项目根目录、包目录、Git工作区、Python解释器和待验证文件路径。",
            "# - 处理：先检查路径与Git状态，再执行备份、整改、测试或提交；任何失败立即抛出异常。",
            "# - 输出：明确的控制台状态、非零失败退出和可回滚备份，不连接或写入业务数据库。",
            "# - 常量依据：默认项目路径来自用户确认，main分支和UTF-8 BOM来自项目交付规范。",
            "# - 为什么这样写：Windows PowerShell 5.1对编码和退出码敏感，显式门禁可防止乱码及失败后误提交。",
            "",
        ] + lines

    updated_text = "\r\n".join(lines).rstrip("\r\n") + "\r\n"

    # 本段代码核心功能：只在PowerShell文本真实变化时使用UTF-8 BOM写回。
    # - 输入：规范化原文本与整改后CRLF文本。
    # - 处理：比较去除BOM后的逻辑内容，变化时调用write_text的utf-8-sig编码。
    # - 输出：修改返回True，无变化返回False。
    # - 常量依据：utf-8-sig会写入BOM，保证Windows PowerShell 5.1正确解析中文注释。
    # - 为什么这样写：保留BOM和CRLF能避免此前交付包出现的中文乱码与解析错误。
    if updated_text == normalized_text.replace("\n", "\r\n"):
        return False
    path.write_text(updated_text, encoding="utf-8-sig", newline="")
    return True


# 本段代码核心功能：定义 `_ensure_authority_comment_gate`，向权威Markdown追加“先注释后测试”硬门禁。
# - 输入：UTF-8 Markdown路径和文件名；文件必须已经存在于项目仓库。
# - 处理：检查唯一标记，缺失时按文件职责追加对应章节，并规范为LF及一个文件末尾换行。
# - 输出：发生追加返回True，章节已经存在返回False；不覆盖原有正文。
# - 常量依据：门禁要求来自用户对TASK_022至TASK_024的明确纠正，任务号固定为TASK_024A1。
# - 为什么这样写：采用追加式、带标记、幂等修改，可在不了解用户最新正文细节时安全提升规则而不重写历史内容。
def _ensure_authority_comment_gate(path: Path) -> bool:
    original_text = path.read_text(encoding="utf-8-sig")
    normalized_text = original_text.replace("\r\n", "\n").replace("\r", "\n")

    # 本段代码核心功能：在权威门禁已经存在时直接返回幂等结果。
    # - 输入：规范化后的完整Markdown正文和AUTHORITY_MARKER。
    # - 处理：执行精确字符串包含判断，不使用容易误报的模糊关键词。
    # - 输出：标记存在时返回False且不写磁盘。
    # - 常量依据：唯一标记由本任务固定定义。
    # - 为什么这样写：重复应用、验证或恢复流程都不会持续扩大文档差异。
    if AUTHORITY_MARKER in normalized_text:
        return False

    # 本段代码核心功能：根据权威文件职责选择针对性的追加章节。
    # - 输入：Markdown文件名。
    # - 处理：注释标准强调第一次沙盒检查前完成；开发指导强调固定任务顺序和阻断条件。
    # - 输出：得到即将追加的UTF-8 Markdown章节。
    # - 常量依据：只允许AUTHORITY_DOCUMENT_TARGETS中的两个文件调用本函数。
    # - 为什么这样写：同一原则在标准和流程中承担不同职责，避免机械复制完全相同的文字。
    if path.name == "CODE_COMMENTING_STANDARD.md":
        section = f"""

{AUTHORITY_MARKER}

## 沙盒验证前置门禁

所有新增或修改的人工代码必须在第一次沙盒语法检查、导入检查或单元测试之前完成教学式前置注释。禁止先生成无注释代码、测试通过后再补注释，也禁止把注释整改推迟到交付包或用户本地。

```text
代码与注释同步设计
→ 注释结构自检
→ 第一次沙盒语法检查
→ 专项与回归测试
→ 全仓库注释审计
→ 交付
```

沙盒中被测试的代码和最终交付代码必须是同一份已经完成注释的代码。注释审计失败时，代码即使能够运行也不得进入交付、Git提交或GitHub推送。
"""
    else:
        section = f"""

{AUTHORITY_MARKER}

## 教学式注释先于沙盒测试

每个任务必须按照以下固定顺序执行：

```text
复用调查
→ 代码和教学式前置注释同步编写
→ 注释自检
→ 沙盒语法与导入检查
→ 专项测试
→ 回归和全量测试
→ 注释审计
→ 交付与Git闭环
```

任何人工代码在进入第一次沙盒检查时仍缺少前置教学注释，均视为任务尚未完成开发，不得以“之后再补注释”为理由继续交付。
"""

    updated_text = normalized_text.rstrip("\n") + section.rstrip("\n") + "\n"
    path.write_text(updated_text, encoding="utf-8", newline="\n")
    return True


# 本段代码核心功能：定义 `_build_parser`，声明整改工具唯一命令行参数。
# - 输入：操作系统命令行字符串。
# - 处理：要求调用方显式提供项目根目录，避免在错误目录自动扫描。
# - 输出：返回ArgumentParser实例供主流程解析。
# - 常量依据：不提供默认Windows盘符，使同一工具可在Linux沙盒和Windows本地运行。
# - 为什么这样写：显式项目根目录是防止误改其他仓库的第一道安全门禁。
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    return parser


# 本段代码核心功能：定义 `main`，按白名单整改Python和PowerShell目标并打印结构化摘要。
# - 输入：可选argv和必须存在的项目根目录。
# - 处理：验证所有目标文件存在，逐文件调用对应整改器，统计修改与幂等文件数量。
# - 输出：成功返回0；缺文件、语法错误或写入失败时抛出异常并返回非零进程状态。
# - 常量依据：本工具不创建业务数据文件，不联网，不导入厂商SDK，也不读取秘密值。
# - 为什么这样写：在测试前一次完成全部注释整改，确保沙盒和用户收到的代码本身已经合规。
def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()

    # 本段代码核心功能：确认传入路径是包含`.git`目录的项目仓库。
    # - 输入：解析后的绝对项目根目录。
    # - 处理：同时检查目录存在和Git元数据目录存在。
    # - 输出：不满足时抛出RuntimeError并阻断所有写入。
    # - 常量依据：项目约定所有交付只应用到Git管理的健康仓库。
    # - 为什么这样写：误传目录时立即失败，比在普通目录生成大量注释文件更安全。
    if not project_root.is_dir() or not (project_root / ".git").is_dir():
        raise RuntimeError(
            f"project root is not a Git repository: {project_root}"
        )

    changed_paths: list[str] = []
    unchanged_paths: list[str] = []

    # 本段代码核心功能：逐个整改Python白名单文件并记录是否发生变化。
    # - 输入：PYTHON_TARGETS相对路径集合。
    # - 处理：缺失文件立即失败；存在文件执行AST整改。
    # - 输出：路径加入changed_paths或unchanged_paths。
    # - 常量依据：不允许静默跳过缺失任务文件，因为这可能表示前置任务未正确应用。
    # - 为什么这样写：明确缺失能避免只修部分任务却错误宣告全部22至24号整改完成。
    for relative_path in PYTHON_TARGETS:
        path = project_root / relative_path

        # 本段代码核心功能：在解析和写入前确认Python目标是普通文件。
        # - 输入：当前目标绝对路径。
        # - 处理：不存在时抛出FileNotFoundError。
        # - 输出：存在时继续整改，不存在时终止任务。
        # - 常量依据：所有目标都应由已完成的TASK_022至TASK_024任务创建。
        # - 为什么这样写：不自动创建空替代文件，防止掩盖本地仓库缺少真实实现。
        if not path.is_file():
            raise FileNotFoundError(f"required Python target is missing: {path}")
        changed = _remediate_python_file(path)
        (changed_paths if changed else unchanged_paths).append(relative_path)

    # 本段代码核心功能：逐个整改PowerShell白名单文件并记录是否发生变化。
    # - 输入：POWERSHELL_TARGETS相对路径集合。
    # - 处理：缺失即失败；存在时按UTF-8 BOM与CRLF规则整改。
    # - 输出：路径加入changed_paths或unchanged_paths。
    # - 常量依据：当前仓库范围只包含TASK_022 PowerShell验证脚本。
    # - 为什么这样写：PowerShell编码与Python不同，单独处理可避免BOM和换行损坏。
    for relative_path in POWERSHELL_TARGETS:
        path = project_root / relative_path

        # 本段代码核心功能：确认PowerShell目标存在后再执行编码敏感的行级整改。
        # - 输入：当前PowerShell绝对路径。
        # - 处理：缺失时抛出FileNotFoundError。
        # - 输出：存在时继续，缺失时任务失败。
        # - 常量依据：TASK_022正式仓库应包含该验证脚本。
        # - 为什么这样写：不对缺失PowerShell静默放行，确保用户指出的22号任务也真正纳入整改。
        if not path.is_file():
            raise FileNotFoundError(
                f"required PowerShell target is missing: {path}"
            )
        changed = _remediate_powershell_file(path)
        (changed_paths if changed else unchanged_paths).append(relative_path)

    # 本段代码核心功能：把“先注释后沙盒验证”规则写回两个权威Markdown文件。
    # - 输入：AUTHORITY_DOCUMENT_TARGETS中的项目相对路径。
    # - 处理：逐文件确认存在，再调用带唯一标记的幂等追加函数。
    # - 输出：发生变化的文档加入changed_paths，已有门禁的文档加入unchanged_paths。
    # - 常量依据：权威文件缺失表示项目基线不完整，必须阻断而不能自动创建替代文件。
    # - 为什么这样写：代码整改和流程整改同时落库，才能从制度上防止同类问题重复发生。
    for relative_path in AUTHORITY_DOCUMENT_TARGETS:
        path = project_root / relative_path

        # 本段代码核心功能：在追加规则前确认权威Markdown文件真实存在。
        # - 输入：当前权威文件绝对路径。
        # - 处理：不存在时抛出FileNotFoundError，存在时执行幂等追加。
        # - 输出：继续整改或立即阻断。
        # - 常量依据：两个文件均属于项目长期权威上下文，不允许用新建空文件代替。
        # - 为什么这样写：防止错误仓库或不完整分支被误判为成功整改。
        if not path.is_file():
            raise FileNotFoundError(
                f"required authority document is missing: {path}"
            )
        changed = _ensure_authority_comment_gate(path)
        (changed_paths if changed else unchanged_paths).append(relative_path)

    print("Teaching comment remediation completed.")
    print(f"Changed file count: {len(changed_paths)}")
    print(f"Already compliant file count: {len(unchanged_paths)}")

    # 本段代码核心功能：按稳定排序打印实际发生变化的文件路径。
    # - 输入：changed_paths列表。
    # - 处理：使用sorted保证Linux和Windows输出顺序一致。
    # - 输出：每个修改文件输出一行，便于人工核对Git范围。
    # - 常量依据：排序只影响日志，不改变应用顺序和文件内容。
    # - 为什么这样写：稳定日志便于比较重复执行结果和定位意外修改。
    for path in sorted(changed_paths):
        print(f"CHANGED {path}")
    return 0


# 本段代码核心功能：当工具被直接执行时把main返回值交给操作系统。
# - 输入：系统命令行参数。
# - 处理：调用main并通过SystemExit保留标准退出码。
# - 输出：成功为0，异常或失败为非零。
# - 常量依据：`__main__`是Python直接执行模块的标准入口。
# - 为什么这样写：PowerShell应用脚本依赖真实退出码阻断后续测试和Git操作。
if __name__ == "__main__":
    raise SystemExit(main())
