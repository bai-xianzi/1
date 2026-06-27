"""离线验证TASK_018D验收计划与统一门禁合同。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.project_root).resolve()
    src = root / "src"
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

    if len(plan_ids) != len(set(plan_ids)):
        issues.append("验收计划dataset_id重复。")
    if set(plan_ids) != set(policy_ids):
        issues.append("验收计划与就绪度政策数据集不一致。")
    if set(plan_ids) != set(external_ids):
        issues.append("验收计划与外部证据配置数据集不一致。")

    for item in plan["datasets"]:
        dataset = policy.dataset(str(item["dataset_id"]))
        if str(item["canonical_object"]) not in dataset.canonical_objects:
            issues.append(
                f"{dataset.dataset_id}的canonical_object未登记。"
            )

    usages = tuple(
        StandardDataUsage(value)
        for value in plan["usages"]
    )
    if set(usages) != set(StandardDataUsage):
        issues.append("验收计划没有完整覆盖四种数据用途。")

    as_of_date = resolver.config.as_of_date
    current_activation_passed = 0
    manual_activation_failed = 0
    strict_activation_failed = 0
    training_activation_failed = 0
    coverage_failed = 0

    for dataset_id in plan_ids:
        coverage = resolver.coverage_evidence(dataset_id)
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
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
