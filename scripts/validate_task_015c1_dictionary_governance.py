# 本脚本核心功能：验证任务015c1字典治理的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import json
import sys
from pathlib import Path

# 配置常量：集中定义 `PROJECT_ROOT`，供后续流程复用。
# - 当前值或构造表达式：`Path(__file__).resolve().parents[1]`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 配置常量：集中定义 `SRC_ROOT`，供后续流程复用。
# - 当前值或构造表达式：`PROJECT_ROOT / 'src'`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
SRC_ROOT = PROJECT_ROOT / "src"
# 条件分支：检查 `str(SRC_ROOT) not in sys.path` 后选择对应处理路径。
# - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
# - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.field_dictionary_governance import (  # noqa: E402
    validate_dictionary_governance,
)


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    report = validate_dictionary_governance(PROJECT_ROOT)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 条件分支：检查 `report['overall_status'] != 'PASSED'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if report["overall_status"] != "PASSED":
        # 输出结果：返回 `1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 1
    print("TASK_015C-1 dictionary governance validation PASSED.")
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
