# 本文件核心功能：执行TASK_024A官方交易所与券商来源基线验证。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本脚本核心功能：离线验证官方交易所与券商优先的来源权威目录。
"""运行TASK_024A官方来源基线检查。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.source_authority import (
    build_source_authority_report,
    load_official_interface_catalog,
    load_source_authority_policy,
    write_source_authority_report,
)


# 本段代码核心功能：定义 `parse_args`，集中声明命令行参数并把用户输入解析为类型明确的Namespace。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `argparse.Namespace`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--policy",
        default="configs/providers/source_authority_policy_v1.json",
    )
    parser.add_argument(
        "--catalog",
        default="configs/providers/official_interface_catalog_v1.json",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


# 本段代码核心功能：定义 `main`，执行TASK_024A官方交易所与券商来源基线验证。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `int`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def main() -> int:
    args = parse_args()
    policy = load_source_authority_policy(args.policy)
    catalog = load_official_interface_catalog(args.catalog)
    report = build_source_authority_report(policy, catalog)
    output = write_source_authority_report(report, Path(args.output))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report: {output}")
    return 0 if report["overall_status"] == "PASSED" else 2


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    raise SystemExit(main())
