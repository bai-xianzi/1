# 本文件核心功能：执行TASK_023C离线Provider候选决策并保持未激活状态。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

#!/usr/bin/env python3
# 本脚本核心功能：读取TASK_023B本地安全报告，生成TASK_023C首个外部Provider选择报告。
# 不安装、不导入、不联网、不读取秘密值，也不激活任何Provider。
"""运行TASK_023C复用优先Provider选择。"""

from __future__ import annotations

import argparse
from pathlib import Path

from a_stock_quant.provider_selection import (
    build_provider_selection_report,
    load_provider_selection_policy,
    load_task_023b_inventory_report,
    select_first_external_provider,
    write_provider_selection_report,
)


# 本段代码核心功能：定义 `parse_args`，集中声明命令行参数并把用户输入解析为类型明确的Namespace。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `argparse.Namespace`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory-report",
        required=True,
        help="TASK_023B local UTF-8 JSON report.",
    )
    parser.add_argument(
        "--policy",
        default="configs/providers/provider_selection_policy_v0.json",
        help="TASK_023C selection policy path.",
    )
    parser.add_argument("--output", required=True, help="TASK_023C output JSON path.")
    return parser.parse_args()


# 本段代码核心功能：定义 `main`，执行TASK_023C离线Provider候选决策并保持未激活状态。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `int`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def main() -> int:
    args = parse_args()
    policy = load_provider_selection_policy(args.policy)
    inventory = load_task_023b_inventory_report(args.inventory_report)
    decision = select_first_external_provider(policy, inventory)
    report = build_provider_selection_report(decision, inventory)
    output = write_provider_selection_report(report, Path(args.output))

    print(f"TASK_023C selected provider: {decision.selected_provider_id}")
    print(f"Decision status: {decision.decision_status}")
    print(f"Selection basis: {decision.selection_basis}")
    print(f"Activation status: {decision.activation_status}")
    print(f"Next task: {decision.next_task_id}")
    print(f"Report: {output}")
    return 0


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    raise SystemExit(main())
