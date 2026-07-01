# 本脚本核心功能：验证任务018a数据就绪度合同的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


# 函数 `_project_root_from_args`：完成projectroot从args相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成projectroot从args相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `Path`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _project_root_from_args() -> Path:
    parser = argparse.ArgumentParser(
        description=(
            "验证TASK_018A统一数据就绪度合同和政策。"
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="项目根目录。",
    )
    args = parser.parse_args()
    # 输出结果：返回 `Path(args.project_root).resolve()` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return Path(args.project_root).resolve()


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    project_root = _project_root_from_args()
    src_path = project_root / "src"
    # 条件分支：检查 `str(src_path) not in sys.path` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from a_stock_quant.data_readiness import (
        DataReadinessEngine,
        DataReadinessRequest,
        EvidenceStatus,
        ReadinessDimension,
        ReadinessEvidence,
        ReadinessStatus,
        load_data_readiness_policy,
    )
    from a_stock_quant.standard_data_service import (
        StandardDataUsage,
    )

    policy_path = (
        project_root
        / "configs"
        / "quality"
        / "data_readiness_policy_v0.json"
    )
    policy = load_data_readiness_policy(policy_path)

    issues: list[str] = []
    expected_datasets = {
        "a_stock_daily_k",
        "a_stock_fundamental_snapshot",
        "hq",
        "hy",
        "gn",
        "kphq",
        "kphy",
        "kpgn",
        "zj",
    }
    actual_datasets = {
        item.dataset_id
        for item in policy.dataset_catalog
    }
    # 条件分支：检查 `actual_datasets != expected_datasets` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if actual_datasets != expected_datasets:
        issues.append(
            "dataset_catalog与预期九个数据集不一致。"
        )

    # 条件分支：检查 `not policy.raw_access_forbidden` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not policy.raw_access_forbidden:
        issues.append(
            "政策没有禁止下游直接访问Raw层。"
        )
    # 条件分支：检查 `not policy.standard_data_service_required` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not policy.standard_data_service_required:
        issues.append(
            "政策没有要求通过StandardDataService。"
        )

    selector_counts = {
        "INSTRUMENT_ID": 0,
        "ENTITY_ID": 0,
    }
    canonical_objects: set[str] = set()
    # 循环处理：将 `policy.dataset_catalog` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in policy.dataset_catalog:
        selector_counts[item.selector_mode] += 1
        canonical_objects.update(item.canonical_objects)

    all_passed = tuple(
        ReadinessEvidence(
            dimension=dimension,
            status=EvidenceStatus.PASSED,
            code="VALIDATION_PASSED",
            message="验证证据通过。",
        )
        for dimension in ReadinessDimension
    )
    engine = DataReadinessEngine(policy)
    status_by_usage: dict[str, str] = {}
    # 循环处理：将 `StandardDataUsage` 中的元素逐项绑定到 `usage`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for usage in StandardDataUsage:
        request = DataReadinessRequest(
            dataset_id="a_stock_daily_k",
            usage=usage,
            evidence=all_passed,
            decision_time=(
                __import__("datetime").datetime(
                    2026,
                    6,
                    27,
                    15,
                    0,
                    tzinfo=__import__(
                        "datetime"
                    ).timezone.utc,
                )
                if usage
                is StandardDataUsage.MANUAL_DECISION_SUPPORT
                else None
            ),
        )
        result = engine.evaluate(request)
        status_by_usage[usage.value] = result.status.value
        # 条件分支：检查 `result.status is not ReadinessStatus.PASSED` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if result.status is not ReadinessStatus.PASSED:
            issues.append(
                f"全PASSED证据未产生PASSED：{usage.value}"
            )

    temporal_warning = tuple(
        ReadinessEvidence(
            dimension=dimension,
            status=(
                EvidenceStatus.WARNING
                if dimension
                is ReadinessDimension.TEMPORAL_SAFETY
                else EvidenceStatus.PASSED
            ),
            code=(
                "TEMPORAL_WARNING"
                if dimension
                is ReadinessDimension.TEMPORAL_SAFETY
                else "VALIDATION_PASSED"
            ),
            message="用途级时点验证。",
        )
        for dimension in ReadinessDimension
    )

    current_result = engine.evaluate(
        DataReadinessRequest(
            dataset_id="hq",
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
            evidence=temporal_warning,
        )
    )
    historical_result = engine.evaluate(
        DataReadinessRequest(
            dataset_id="hq",
            usage=(
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST
            ),
            evidence=temporal_warning,
        )
    )
    # 条件分支：检查 `current_result.status is not ReadinessStatus.WARNING` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if current_result.status is not ReadinessStatus.WARNING:
        issues.append(
            "当前快照研究没有把时点WARNING保留为WARNING。"
        )
    # 条件分支：检查 `historical_result.status is not ReadinessStatus.BLOCKED` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if (
        historical_result.status
        is not ReadinessStatus.BLOCKED
    ):
        issues.append(
            "严格历史回测没有阻断时点WARNING。"
        )

    result = {
        "task_id": "TASK_018A",
        "contract_version": policy.contract_version,
        "policy_version": policy.policy_version,
        "dataset_count": len(policy.dataset_catalog),
        "usage_count": len(policy.usage_policies),
        "dimension_count": len(ReadinessDimension),
        "decision_status_count": len(ReadinessStatus),
        "evidence_status_count": len(EvidenceStatus),
        "instrument_selector_dataset_count": (
            selector_counts["INSTRUMENT_ID"]
        ),
        "entity_selector_dataset_count": (
            selector_counts["ENTITY_ID"]
        ),
        "canonical_object_count": len(canonical_objects),
        "raw_access_forbidden": (
            policy.raw_access_forbidden
        ),
        "standard_data_service_required": (
            policy.standard_data_service_required
        ),
        "all_passed_status_by_usage": status_by_usage,
        "current_temporal_warning_status": (
            current_result.status.value
        ),
        "historical_temporal_warning_status": (
            historical_result.status.value
        ),
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "overall_status": (
            "PASSED" if not issues else "FAILED"
        ),
        "issues": issues,
    }
    print(
        json.dumps(
            result,
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
