"""运行TASK_016B七类日线资金DolphinDB建库与导入。"""
# 本脚本核心功能：执行任务016b日频资金数据导入的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from a_stock_quant.daily_funds_ingest import (
    DailyFundsIngestError,
)
from a_stock_quant.daily_funds_dolphindb_writer import (
    DATABASE_URI,
    DailyFundsDolphinDBError,
    DolphinDBWriteSettings,
    build_create_database_script,
    create_database_and_tables,
    probe_dolphindb_environment,
    resolve_password,
    run_daily_funds_import,
    validate_local_contract,
)


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "TASK_016B七类日线资金DolphinDB Raw层工具。"
        )
    )
    parser.add_argument(
        "--mode",
        choices=("contract", "probe", "create", "import"),
        required=True,
    )
    parser.add_argument(
        "--project-root",
        default=".",
    )
    parser.add_argument(
        "--root",
        default=(
            r"D:\Users\Administrator\Desktop"
            r"\数据导入\日线资金\2025\2025\2025"
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
    )
    parser.add_argument(
        "--host",
        default=os.getenv(
            "DOLPHINDB_HOST",
            "127.0.0.1",
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(
            os.getenv("DOLPHINDB_PORT", "8848")
        ),
    )
    parser.add_argument(
        "--username",
        default=os.getenv(
            "DOLPHINDB_USERNAME",
            "admin",
        ),
    )
    parser.add_argument(
        "--database-uri",
        default=DATABASE_URI,
    )
    parser.add_argument(
        "--expected-planned-row-count",
        type=int,
        default=461966,
    )
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `_print_json`：完成printJSON相关处理。
# - 输入：value。
# - 处理：完成printJSON相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _print_json(value: Any) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


# 函数 `_write_result`：完成写入结果相关处理。
# - 输入：output_dir、mode、result。
# - 处理：完成写入结果相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _write_result(
    output_dir: Path,
    mode: str,
    result: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"task_016b_{mode}_result.json"
    path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：argv。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir)
    contract_path = (
        project_root
        / "configs"
        / "datasets"
        / "a_stock_daily_funds_raw.yaml"
    )

    # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
    # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
    # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
    try:
        # 条件分支：检查 `args.mode == 'contract'` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if args.mode == "contract":
            result = validate_local_contract(
                contract_path
            )
            result["ddl_preview"] = (
                build_create_database_script(
                    args.database_uri
                )
            )
        else:
            settings = DolphinDBWriteSettings(
                host=args.host,
                port=args.port,
                username=args.username,
                password=resolve_password(),
                database_uri=args.database_uri,
            )
            # 条件分支：检查 `args.mode == 'probe'` 后选择对应处理路径。
            # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
            # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
            if args.mode == "probe":
                result = probe_dolphindb_environment(
                    settings
                )
            # 条件分支：检查 `args.mode == 'create'` 后选择对应处理路径。
            # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
            # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
            elif args.mode == "create":
                result = create_database_and_tables(
                    settings
                )
            else:
                result = run_daily_funds_import(
                    settings=settings,
                    root=Path(args.root),
                    contract_path=contract_path,
                    output_dir=output_dir,
                    expected_planned_row_count=(
                        args.expected_planned_row_count
                    ),
                )
        _write_result(
            output_dir,
            args.mode,
            result,
        )
        _print_json(result)
        # 输出结果：返回 `0 if result.get('overall_status') == 'PASSED' else 1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return (
            0
            if result.get("overall_status") == "PASSED"
            else 1
        )
    except (
        DailyFundsDolphinDBError,
        DailyFundsIngestError,
        ValueError,
        OSError,
    ) as exc:
        result = {
            "task_id": "TASK_016B",
            "mode": args.mode.upper(),
            "overall_status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_result(
            output_dir,
            args.mode,
            result,
        )
        _print_json(result)
        # 输出结果：返回 `2` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 2


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
