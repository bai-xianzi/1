# 本文件核心功能：执行TASK_023A离线Provider环境发现并输出UTF-8 JSON报告。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本脚本核心功能：在当前Python环境中运行TASK_023A离线Provider环境盘点并写出JSON报告。
# - 输入：发现清单路径和报告输出路径。
# - 输出：不含秘密值的环境发现报告；脚本不导入供应商SDK、不联网、不访问数据库。
"""运行TASK_023A外部Provider环境发现。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
# 本段代码核心功能：根据条件 `str(SRC) not in sys.path` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a_stock_quant.provider_environment_discovery import (  # noqa: E402
    build_provider_environment_report,
    discover_provider_environment,
    load_provider_discovery_manifest,
    write_provider_environment_report,
)


# 本段代码核心功能：定义 `main`，执行TASK_023A离线Provider环境发现并输出UTF-8 JSON报告。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `int`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "configs/providers/provider_discovery_targets_v0.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "reports/task_023_local_provider_environment_inventory.json",
    )
    args = parser.parse_args()

    targets = load_provider_discovery_manifest(args.manifest)
    findings = discover_provider_environment(targets)
    report = build_provider_environment_report(findings)
    output_path = write_provider_environment_report(report, args.output)

    print(f"TASK_023A provider count: {report['provider_count']}")
    print(f"Runtime present count: {report['runtime_present_count']}")
    print(f"Selection status: {report['selection_status']}")
    print(f"Report: {output_path}")
    return 0


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    raise SystemExit(main())
