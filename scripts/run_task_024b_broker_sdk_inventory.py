# 本文件核心功能：提供TASK_024B券商官方SDK证据盘点的命令行入口。
# - 输入：规则配置、可重复的标签化证据目录、TASK_023B报告、非秘密授权确认文件和输出路径。
# - 处理：调用broker_sdk_inventory模块完成安全扫描、证据合并、门禁评估和稳定报告写入。
# - 输出：UTF-8 JSON报告、简要控制台摘要和标准退出码；无候选属于警告结果而不是运行失败。
# - 常量依据：TASK_024B只盘点用户明确提供的官方包，不联网、不导入SDK、不登录、不交易。
# - 为什么这样写：薄命令行入口便于Windows PowerShell、测试和未来调度器复用同一业务实现。
"""Run TASK_024B broker SDK inventory."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from a_stock_quant.broker_sdk_inventory import (
    build_inventory_report,
    evaluate_broker_candidates,
    load_authorization_evidence,
    load_broker_sdk_rules,
    merge_task_023b_evidence,
    scan_evidence_roots,
    write_inventory_report,
)


# 本段代码核心功能：定义 `_parse_root_argument`，把`标签=路径`参数转换为安全键值对。
# - 输入：单个命令行字符串。
# - 处理：要求包含等号且标签和路径均非空。
# - 输出：二元组`(label, Path)`；格式错误时抛出ArgumentTypeError。
# - 常量依据：报告只记录匿名标签，不记录绝对路径。
# - 为什么这样写：显式标签让用户知道哪些目录被扫描，也避免输出目录结构造成隐私泄露。
def _parse_root_argument(value: str) -> tuple[str, Path]:
    """Parse LABEL=PATH evidence-root syntax."""

    # 本段代码核心功能：根据条件 `'=' not in value` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if "=" not in value:
        raise argparse.ArgumentTypeError("evidence root must use LABEL=PATH")
    label, raw_path = value.split("=", 1)
    # 本段代码核心功能：根据条件 `not label.strip() or not raw_path.strip()` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("evidence root label and path are required")
    return label.strip(), Path(raw_path.strip())


# 本段代码核心功能：定义 `_build_parser`，声明TASK_024B所有显式输入和安全扫描上限。
# - 输入：操作系统命令行参数。
# - 处理：要求规则和输出路径，允许零个或多个专用证据目录及可选本地证据文件。
# - 输出：ArgumentParser实例。
# - 常量依据：最大深度默认4、文件上限默认5000，与核心模块安全阈值一致。
# - 为什么这样写：所有外部读取都由参数显式声明，禁止工具自行猜测盘符和用户目录。
def _build_parser() -> argparse.ArgumentParser:
    """Build the TASK_024B command-line parser."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--rules", required=True)
    parser.add_argument("--authorization-evidence")
    parser.add_argument("--task-023b-report")
    parser.add_argument(
        "--evidence-root",
        action="append",
        default=[],
        type=_parse_root_argument,
        metavar="LABEL=PATH",
    )
    parser.add_argument("--maximum-depth", type=int, default=4)
    parser.add_argument("--maximum-files", type=int, default=5000)
    parser.add_argument("--output", required=True)
    return parser


# 本段代码核心功能：定义 `main`，执行完整离线盘点并打印面向用户的结果摘要。
# - 输入：可选argv；未传时读取系统命令行。
# - 处理：加载规则和授权、扫描专用目录、合并23B证据、评估候选并写入报告。
# - 输出：成功返回0；配置、JSON或安全门禁错误由异常产生非零退出码。
# - 常量依据：没有READY候选仍是成功盘点，selection_status会明确说明下一步仍停留在证据接收。
# - 为什么这样写：把“程序运行成功”和“已具备券商接入条件”分开表达，避免错误推进TASK_024C。
def main(argv: Sequence[str] | None = None) -> int:
    """Run TASK_024B inventory."""

    args = _build_parser().parse_args(argv)
    rules = load_broker_sdk_rules(args.rules)
    authorization_path = (
        Path(args.authorization_evidence)
        if args.authorization_evidence
        else None
    )
    task_023b_path = Path(args.task_023b_report) if args.task_023b_report else None
    authorization = load_authorization_evidence(
        authorization_path,
        (rule.provider_id for rule in rules),
    )
    roots = {label: path for label, path in args.evidence_root}
    artifacts, scanned_file_count = scan_evidence_roots(
        rules,
        roots,
        maximum_depth=args.maximum_depth,
        maximum_files=args.maximum_files,
    )
    artifacts = merge_task_023b_evidence(
        artifacts,
        task_023b_path,
        provider_aliases={"galaxy_xingyao": "galaxy_xingyao"},
    )
    findings = evaluate_broker_candidates(rules, artifacts, authorization)
    report = build_inventory_report(
        findings,
        scanned_file_count=scanned_file_count,
        task_023b_report_used=bool(task_023b_path and task_023b_path.is_file()),
        authorization_file_used=bool(
            authorization_path and authorization_path.is_file()
        ),
    )
    output_path = write_inventory_report(report, args.output)

    print(f"TASK_024B provider count: {report['provider_count']}")
    print(f"Ready candidate count: {report['ready_candidate_count']}")
    print(f"Selection status: {report['selection_status']}")
    print(f"Next task: {report['next_task']}")
    print(f"Report: {output_path}")
    return 0


# 本段代码核心功能：当脚本被直接运行时把main返回值交给操作系统。
# - 输入：系统命令行参数。
# - 处理：调用main并使用SystemExit保留标准退出码。
# - 输出：成功为0，异常为非零。
# - 常量依据：PowerShell验证脚本依赖真实退出码阻断提交。
# - 为什么这样写：标准入口便于沙盒、本地Windows和自动化环境使用同一命令。
if __name__ == "__main__":
    raise SystemExit(main())
