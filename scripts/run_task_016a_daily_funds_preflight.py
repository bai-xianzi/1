"""运行 TASK_016A 七类日线资金只读预导入。"""
# 本脚本核心功能：执行任务016a日频资金数据预检的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
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

from a_stock_quant.daily_funds_ingest import (  # noqa: E402
    load_daily_funds_contract,
    run_daily_funds_preflight,
    validate_daily_funds_contract,
)


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "TASK_016A 七类日线资金只读预导入；"
            "不会连接或修改DolphinDB。"
        )
    )
    parser.add_argument(
        "--root",
        help="日线资金根目录，下一层必须是YYYYMMDD目录。",
    )
    parser.add_argument(
        "--output-dir",
        help="预导入报告输出目录。",
    )
    parser.add_argument(
        "--contract",
        default=str(
            PROJECT_ROOT
            / "configs"
            / "datasets"
            / "a_stock_daily_funds_raw.yaml"
        ),
        help="来源合同YAML路径。",
    )
    parser.add_argument(
        "--validate-contract-only",
        action="store_true",
        help="只验证合同，不扫描源文件。",
    )
    args = parser.parse_args()

    contract_path = Path(args.contract)
    contract = load_daily_funds_contract(contract_path)
    contract_report = validate_daily_funds_contract(contract)

    # 条件分支：检查 `args.validate_contract_only` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if args.validate_contract_only:
        print(
            json.dumps(
                contract_report,
                ensure_ascii=False,
                indent=2,
            )
        )
        # 输出结果：返回 `0 if contract_report['overall_status'] == 'PASSED' else 1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return (
            0
            if contract_report["overall_status"] == "PASSED"
            else 1
        )

    # 条件分支：检查 `not args.root or not args.output_dir` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not args.root or not args.output_dir:
        parser.error(
            "扫描模式必须同时提供 --root 和 --output-dir。"
        )

    summary = run_daily_funds_preflight(
        root=Path(args.root),
        contract_path=contract_path,
        output_dir=Path(args.output_dir),
    )
    print("TASK_016A 七类日线资金只读预导入完成")
    print(f"总体状态：{summary['overall_status']}")
    print(
        f"快照目录：{summary['snapshot_directory_count']}"
    )
    print(f"画像文件：{summary['profiled_file_count']}")
    print(f"可写入文件：{summary['ready_file_count']}")
    print(
        f"隔离文件：{summary['quarantined_file_count']}"
    )
    print(f"阻断文件：{summary['blocked_file_count']}")
    print(f"解析行：{summary['parsed_row_count']}")
    print(
        f"计划写入行：{summary['planned_insert_row_count']}"
    )
    print(f"输出目录：{args.output_dir}")
    print("本任务没有连接或修改DolphinDB。")
    # 输出结果：返回 `0 if summary['overall_status'] != 'BLOCKED' else 2` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if summary["overall_status"] != "BLOCKED" else 2


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
