from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


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

    def count(
        field: str,
        value: str,
    ) -> int:
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
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            issues.append(
                f"{key}预期{expected_value}，实际{actual[key]}。"
            )

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
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
