from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


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
    return Path(args.project_root).resolve()


def main() -> int:
    project_root = _project_root_from_args()
    src_path = project_root / "src"
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
    if actual_datasets != expected_datasets:
        issues.append(
            "dataset_catalog与预期九个数据集不一致。"
        )

    if not policy.raw_access_forbidden:
        issues.append(
            "政策没有禁止下游直接访问Raw层。"
        )
    if not policy.standard_data_service_required:
        issues.append(
            "政策没有要求通过StandardDataService。"
        )

    selector_counts = {
        "INSTRUMENT_ID": 0,
        "ENTITY_ID": 0,
    }
    canonical_objects: set[str] = set()
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
    if current_result.status is not ReadinessStatus.WARNING:
        issues.append(
            "当前快照研究没有把时点WARNING保留为WARNING。"
        )
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
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
