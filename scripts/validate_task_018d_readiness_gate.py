"""离线验证TASK_018D验收计划与统一门禁合同。"""
# 本脚本核心功能：验证任务018d就绪度门禁的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument(
        "--plan",
        default=(
            "configs/quality/"
            "task_018d_acceptance_plan_v0.json"
        ),
    )
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.project_root).resolve()
    src = root / "src"
    # 条件分支：检查 `str(src) not in sys.path` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from a_stock_quant.data_readiness import (
        ReadinessDimension,
        load_data_readiness_policy,
    )
    from a_stock_quant.data_readiness_external_evidence import (
        ReportBackedEvidenceResolver,
    )
    from a_stock_quant.readiness_gated_data_service import (
        READINESS_GATED_SERVICE_VERSION,
    )
    from a_stock_quant.standard_data_service import (
        StandardDataUsage,
    )

    plan_path = Path(args.plan)
    # 条件分支：检查 `not plan_path.is_absolute()` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    policy = load_data_readiness_policy(
        root / str(plan["readiness_policy"])
    )
    resolver = ReportBackedEvidenceResolver.from_project(
        project_root=root,
        config_path=str(plan["external_evidence_config"]),
    )

    issues: list[str] = []
    plan_ids = [
        str(item["dataset_id"])
        for item in plan["datasets"]
    ]
    policy_ids = [
        item.dataset_id
        for item in policy.dataset_catalog
    ]
    external_ids = [
        item.dataset_id
        for item in resolver.config.datasets
    ]

    # 条件分支：检查 `len(plan_ids) != len(set(plan_ids))` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(plan_ids) != len(set(plan_ids)):
        issues.append("验收计划dataset_id重复。")
    # 条件分支：检查 `set(plan_ids) != set(policy_ids)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if set(plan_ids) != set(policy_ids):
        issues.append("验收计划与就绪度政策数据集不一致。")
    # 条件分支：检查 `set(plan_ids) != set(external_ids)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if set(plan_ids) != set(external_ids):
        issues.append("验收计划与外部证据配置数据集不一致。")

    # 循环处理：将 `plan['datasets']` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in plan["datasets"]:
        dataset = policy.dataset(str(item["dataset_id"]))
        # 条件分支：检查 `str(item['canonical_object']) not in dataset.canonical_objects` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if str(item["canonical_object"]) not in dataset.canonical_objects:
            issues.append(
                f"{dataset.dataset_id}的canonical_object未登记。"
            )

    usages = tuple(
        StandardDataUsage(value)
        for value in plan["usages"]
    )
    # 条件分支：检查 `set(usages) != set(StandardDataUsage)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if set(usages) != set(StandardDataUsage):
        issues.append("验收计划没有完整覆盖四种数据用途。")

    as_of_date = resolver.config.as_of_date
    current_activation_passed = 0
    manual_activation_failed = 0
    strict_activation_failed = 0
    training_activation_failed = 0
    coverage_failed = 0

    # 循环处理：将 `plan_ids` 中的元素逐项绑定到 `dataset_id`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for dataset_id in plan_ids:
        coverage = resolver.coverage_evidence(dataset_id)
        # 条件分支：检查 `coverage.status.value == 'FAILED'` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if coverage.status.value == "FAILED":
            coverage_failed += 1

        current = resolver.activation_evidence(
            dataset_id,
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            as_of_date,
        )
        manual = resolver.activation_evidence(
            dataset_id,
            StandardDataUsage.MANUAL_DECISION_SUPPORT,
            as_of_date,
        )
        strict = resolver.activation_evidence(
            dataset_id,
            StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            as_of_date,
        )
        training = resolver.activation_evidence(
            dataset_id,
            StandardDataUsage.HISTORICAL_MODEL_TRAINING,
            as_of_date,
        )
        current_activation_passed += (
            current.status.value == "PASSED"
        )
        manual_activation_failed += (
            manual.status.value == "FAILED"
        )
        strict_activation_failed += (
            strict.status.value == "FAILED"
        )
        training_activation_failed += (
            training.status.value == "FAILED"
        )

    expected = plan["acceptance_invariants"]
    checks = {
        "provider_count": len(plan_ids) == int(
            expected["provider_count"]
        ),
        "usage_count": len(usages) == int(
            expected["usage_count"]
        ),
        "assessment_count": (
            len(plan_ids) * len(usages)
            == int(expected["assessment_count"])
        ),
        "evidence_dimension_count": (
            len(ReadinessDimension)
            == int(
                expected[
                    "evidence_dimension_count_per_assessment"
                ]
            )
        ),
        "current_activation_passed": (
            current_activation_passed == 9
        ),
        "manual_activation_failed": (
            manual_activation_failed == 9
        ),
        "strict_activation_failed": (
            strict_activation_failed
            == int(
                expected["historical_activation_failed_count"]
            )
        ),
        "training_activation_failed": (
            training_activation_failed
            == int(
                expected["historical_activation_failed_count"]
            )
        ),
        "coverage_failed": coverage_failed == 0,
    }
    issues.extend(
        name
        for name, passed in checks.items()
        if not passed
    )

    report = {
        "task_id": "TASK_018D",
        "mode": "OFFLINE_CONTRACT_VALIDATION",
        "gated_service_version": (
            READINESS_GATED_SERVICE_VERSION
        ),
        "dataset_count": len(plan_ids),
        "usage_count": len(usages),
        "planned_assessment_count": (
            len(plan_ids) * len(usages)
        ),
        "evidence_dimension_count": len(ReadinessDimension),
        "current_activation_passed_count": (
            current_activation_passed
        ),
        "manual_activation_failed_count": (
            manual_activation_failed
        ),
        "strict_activation_failed_count": (
            strict_activation_failed
        ),
        "training_activation_failed_count": (
            training_activation_failed
        ),
        "coverage_failed_count": coverage_failed,
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "checks": checks,
        "issues": issues,
        "overall_status": (
            "PASSED" if not issues else "FAILED"
        ),
    }
    print(
        json.dumps(
            report,
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
