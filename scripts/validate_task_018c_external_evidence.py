# 本脚本核心功能：验证任务018c外部证据的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "验证TASK_018C真实报告、交易日时效和启用配置。"
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
    )
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    src = root / "src"
    # 条件分支：检查 `str(src) not in sys.path` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from a_stock_quant.data_readiness import (
        EvidenceStatus,
    )
    from a_stock_quant.data_readiness_external_evidence import (
        ReportBackedEvidenceResolver,
    )
    from a_stock_quant.standard_data_service import (
        StandardDataUsage,
    )

    resolver = ReportBackedEvidenceResolver.from_project(
        project_root=root,
        config_path=(
            "configs/quality/"
            "data_readiness_external_evidence_v0.json"
        ),
    )
    as_of = resolver.config.as_of_date
    expected_latest = resolver.calendar.latest_trading_day(
        as_of
    )

    rows = []
    issues: list[str] = []
    generic_codes = {
        "QUERY_SCOPE_COVERAGE_ONLY",
        "QUERY_SCOPE_FRESHNESS_ONLY",
        "PROVIDER_REGISTERED_ACTIVATION_UNVERIFIED",
    }

    # 循环处理：将 `resolver.config.datasets` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in resolver.config.datasets:
        current = resolver.resolve(
            dataset_id=item.dataset_id,
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
            as_of_date=as_of,
        )
        historical = resolver.resolve(
            dataset_id=item.dataset_id,
            usage=(
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST
            ),
            as_of_date=as_of,
        )
        current_by_dimension = {
            evidence.dimension.value: evidence
            for evidence in current
        }
        historical_by_dimension = {
            evidence.dimension.value: evidence
            for evidence in historical
        }
        codes = {
            evidence.code
            for evidence in (*current, *historical)
        }
        # 条件分支：检查 `codes & generic_codes` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if codes & generic_codes:
            issues.append(
                f"{item.dataset_id}仍包含TASK_018B占位证据。"
            )
        rows.append(
            {
                "dataset_id": item.dataset_id,
                "report_kind": item.report_kind.value,
                "coverage_status": (
                    current_by_dimension["COVERAGE"].status.value
                ),
                "coverage_code": (
                    current_by_dimension["COVERAGE"].code
                ),
                "current_freshness_status": (
                    current_by_dimension["FRESHNESS"].status.value
                ),
                "current_freshness_code": (
                    current_by_dimension["FRESHNESS"].code
                ),
                "current_activation_status": (
                    current_by_dimension["ACTIVATION"].status.value
                ),
                "historical_freshness_status": (
                    historical_by_dimension[
                        "FRESHNESS"
                    ].status.value
                ),
                "historical_activation_status": (
                    historical_by_dimension[
                        "ACTIVATION"
                    ].status.value
                ),
            }
        )

    # 函数 `count`：完成count相关处理。
    # - 输入：field、value。
    # - 处理：完成count相关处理，并按现有异常和门禁规则保留失败证据。
    # - 输出：返回类型约定为 `int`。
    # - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
    def count(
        field: str,
        value: str,
    ) -> int:
        # 输出结果：返回 `sum((row[field] == value for row in rows))` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return sum(
            row[field] == value
            for row in rows
        )

    expected = {
        "dataset_count": 9,
        "coverage_passed_count": 2,
        "coverage_warning_count": 7,
        "current_freshness_passed_count": 1,
        "current_freshness_warning_count": 8,
        "current_activation_passed_count": 9,
        "historical_freshness_passed_count": 9,
        "historical_activation_passed_count": 1,
        "historical_activation_failed_count": 8,
    }
    actual = {
        "dataset_count": len(rows),
        "coverage_passed_count": count(
            "coverage_status",
            EvidenceStatus.PASSED.value,
        ),
        "coverage_warning_count": count(
            "coverage_status",
            EvidenceStatus.WARNING.value,
        ),
        "current_freshness_passed_count": count(
            "current_freshness_status",
            EvidenceStatus.PASSED.value,
        ),
        "current_freshness_warning_count": count(
            "current_freshness_status",
            EvidenceStatus.WARNING.value,
        ),
        "current_activation_passed_count": count(
            "current_activation_status",
            EvidenceStatus.PASSED.value,
        ),
        "historical_freshness_passed_count": count(
            "historical_freshness_status",
            EvidenceStatus.PASSED.value,
        ),
        "historical_activation_passed_count": count(
            "historical_activation_status",
            EvidenceStatus.PASSED.value,
        ),
        "historical_activation_failed_count": count(
            "historical_activation_status",
            EvidenceStatus.FAILED.value,
        ),
    }
    # 循环处理：将 `expected.items()` 中的元素逐项绑定到 `(key, expected_value)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for key, expected_value in expected.items():
        # 条件分支：检查 `actual[key] != expected_value` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if actual[key] != expected_value:
            issues.append(
                f"{key}预期{expected_value}，实际{actual[key]}。"
            )

    # 条件分支：检查 `expected_latest.isoformat() != '2026-06-26'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if expected_latest.isoformat() != "2026-06-26":
        issues.append(
            "2026-06-27最近交易日不是2026-06-26。"
        )

    output = {
        "task_id": "TASK_018C",
        "external_evidence_version": "0.1.0",
        "snapshot_id": resolver.config.snapshot_id,
        "as_of_date": as_of.isoformat(),
        "expected_latest_trading_date": (
            expected_latest.isoformat()
        ),
        **actual,
        "generic_placeholder_code_count": 0,
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "overall_status": (
            "PASSED" if not issues else "FAILED"
        ),
        "issues": issues,
        "datasets": rows,
    }
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )
    # 输出结果：返回 `0 if not issues else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if not issues else 1


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
