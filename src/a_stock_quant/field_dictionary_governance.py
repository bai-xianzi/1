from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


EXPECTED_DICTIONARY_REVISION = "0.6.0"
EXPECTED_VALUE_DOMAIN_KINDS = {
    "CLOSED_ENUM",
    "CONTROLLED_CODESET",
    "OPEN_CODE",
    "IDENTIFIER",
    "FREE_TEXT",
}


@dataclass(frozen=True)
class GovernanceIssue:
    severity: str
    code: str
    message: str
    evidence: dict[str, Any] | None = None


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"YAML根节点必须是字典：{path}")
    return payload


def field_index(
    canonical: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for domain in canonical.get("domains", []):
        domain_code = str(domain.get("domain_code", ""))
        for field in domain.get("fields", []):
            key = (domain_code, str(field.get("canonical_name", "")))
            if key in result:
                raise ValueError(f"字段重复：{key}")
            result[key] = field
    return result


def occurrences_by_name(
    canonical: dict[str, Any],
) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    result: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for domain in canonical.get("domains", []):
        domain_code = str(domain.get("domain_code", ""))
        for field in domain.get("fields", []):
            result[str(field.get("canonical_name", ""))].append(
                (domain_code, field)
            )
    return result


def signature(field: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(field.get("data_type", "")).upper(),
        str(field.get("unit", "")).lower(),
        str(field.get("time_semantics", "")),
    )


def validate_dictionary_governance(
    project_root: Path,
) -> dict[str, Any]:
    schema_dir = project_root / "schemas"
    canonical = load_yaml(schema_dir / "canonical_fields.yaml")
    contract = load_yaml(schema_dir / "field_governance_contract.yaml")
    enums = load_yaml(schema_dir / "enum_definitions.yaml")

    issues: list[GovernanceIssue] = []
    index = field_index(canonical)

    canonical_revision = str(canonical.get("dictionary_revision", ""))
    contract_revision = str(contract.get("dictionary_revision", ""))
    if canonical_revision != EXPECTED_DICTIONARY_REVISION:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "DICTIONARY_REVISION_MISMATCH",
                "canonical_fields.yaml修订号不符合当前治理合同。",
                {"actual": canonical_revision},
            )
        )
    if contract_revision != canonical_revision:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "CONTRACT_REVISION_MISMATCH",
                "治理合同与字段字典修订号不一致。",
                {
                    "canonical": canonical_revision,
                    "contract": contract_revision,
                },
            )
        )

    actual_kinds = set(contract.get("value_domain_kinds", {}))
    if actual_kinds != EXPECTED_VALUE_DOMAIN_KINDS:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "VALUE_DOMAIN_KINDS_INVALID",
                "value_domain_kinds不完整。",
                {
                    "expected": sorted(EXPECTED_VALUE_DOMAIN_KINDS),
                    "actual": sorted(actual_kinds),
                },
            )
        )

    for requirement in contract.get("required_metadata", []):
        key = (
            str(requirement.get("domain_code", "")),
            str(requirement.get("canonical_name", "")),
        )
        field = index.get(key)
        if field is None:
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "REQUIRED_FIELD_MISSING",
                    "治理合同引用的字段不存在。",
                    {"field": key},
                )
            )
            continue
        metadata_key = str(requirement.get("key", ""))
        expected_value = requirement.get("value")
        actual_value = field.get(metadata_key)
        if actual_value != expected_value:
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "REQUIRED_METADATA_MISMATCH",
                    "字段治理元数据不符合合同。",
                    {
                        "field": key,
                        "key": metadata_key,
                        "expected": expected_value,
                        "actual": actual_value,
                    },
                )
            )

    contracts = {
        str(item.get("canonical_name", "")): item
        for item in contract.get("shared_field_contracts", [])
    }
    accepted_drift_names = set(contracts)

    ungoverned_drift: dict[str, list[dict[str, Any]]] = {}
    for name, occurrences in occurrences_by_name(canonical).items():
        signatures = {signature(field) for _, field in occurrences}
        if len(signatures) <= 1:
            continue
        if name not in accepted_drift_names:
            ungoverned_drift[name] = [
                {
                    "domain_code": domain_code,
                    "signature": signature(field),
                }
                for domain_code, field in occurrences
            ]

    if ungoverned_drift:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "UNGOVERNED_CROSS_DOMAIN_DRIFT",
                "仍有未登记的跨Domain同名字段签名漂移。",
                ungoverned_drift,
            )
        )

    trade_contract = contracts.get("trade_count", {})
    if (
        trade_contract.get("resolution")
        != "SEMANTIC_COLLISION_MIGRATION_REQUIRED"
    ):
        issues.append(
            GovernanceIssue(
                "ERROR",
                "TRADE_COUNT_MIGRATION_MISSING",
                "trade_count语义冲突未进入迁移计划。",
            )
        )
    migration = trade_contract.get("migration", {})
    if migration.get("breaking_change_allowed") is not False:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "BREAKING_CHANGE_GUARD_MISSING",
                "trade_count迁移必须禁止直接破坏性修改。",
            )
        )
    if ("backtest", "executed_trade_count") in index:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "PREMATURE_TRADE_COUNT_RENAME",
                "TASK_015C-1仅登记迁移计划，不应直接新增或替换字段。",
            )
        )

    value_contract = contracts.get("value_numeric", {})
    if (
        value_contract.get("resolution")
        != "CONTEXTUAL_TYPE_VARIANT_ALLOWED"
    ):
        issues.append(
            GovernanceIssue(
                "ERROR",
                "VALUE_NUMERIC_EXCEPTION_MISSING",
                "value_numeric上下文类型差异未登记。",
            )
        )


    expected_precision_values = {
        "EXACT_TIMESTAMP",
        "SECOND",
        "MINUTE",
        "DATE_ONLY",
        "UNKNOWN",
    }
    actual_precision_values = set(
        enums.get("snapshot_time_precision", [])
    )
    if actual_precision_values != expected_precision_values:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "SNAPSHOT_TIME_PRECISION_ENUM_INVALID",
                "snapshot_time_precision枚举不完整。",
                {
                    "expected": sorted(expected_precision_values),
                    "actual": sorted(actual_precision_values),
                },
            )
        )

    auction_time = index.get(("auction", "snapshot_time"))
    auction_precision = index.get(
        ("auction", "snapshot_time_precision")
    )
    if auction_time is None or auction_time.get("nullable") is not True:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_NULLABILITY_INVALID",
                "日期级竞价来源要求snapshot_time可空。",
            )
        )
    if (
        auction_time is not None
        and auction_time.get("time_semantics")
        != "observation_time"
    ):
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_SEMANTICS_INVALID",
                "snapshot_time必须声明observation_time。",
            )
        )
    if (
        auction_precision is None
        or auction_precision.get("nullable") is not False
        or auction_precision.get("enum_ref")
        != "snapshot_time_precision"
    ):
        issues.append(
            GovernanceIssue(
                "ERROR",
                "AUCTION_TIME_PRECISION_FIELD_INVALID",
                "snapshot_time_precision必须非空并绑定枚举。",
            )
        )

    object_domains = {
        str(domain.get("canonical_object", "")): domain
        for domain in canonical.get("domains", [])
    }
    classification_market = object_domains.get(
        "ClassificationMarketSnapshot"
    )
    required_classification_fields = {
        "classification_system",
        "classification_type",
        "node_id",
        "node_name_cn",
        "trade_date",
        "snapshot_phase",
        "pct_change_pct",
        "up_count",
        "down_count",
        "breadth_ratio",
        "breadth_status",
        "volume_lots",
        "volume_shares",
        "amount_cny",
    }
    if classification_market is None:
        issues.append(
            GovernanceIssue(
                "ERROR",
                "CLASSIFICATION_MARKET_OBJECT_MISSING",
                "缺少ClassificationMarketSnapshot对象。",
            )
        )
    else:
        actual_fields = {
            str(field.get("canonical_name", ""))
            for field in classification_market.get("fields", [])
        }
        missing_fields = sorted(
            required_classification_fields - actual_fields
        )
        if missing_fields:
            issues.append(
                GovernanceIssue(
                    "ERROR",
                    "CLASSIFICATION_MARKET_FIELDS_MISSING",
                    "ClassificationMarketSnapshot缺少核心字段。",
                    {"missing": missing_fields},
                )
            )

    issue_rows = [
        {
            "severity": item.severity,
            "code": item.code,
            "message": item.message,
            "evidence": item.evidence,
        }
        for item in issues
    ]
    errors = [item for item in issue_rows if item["severity"] == "ERROR"]

    return {
        "task_id": "FIELD_DICTIONARY_GOVERNANCE",
        "overall_status": "PASSED" if not errors else "FAILED",
        "dictionary_revision": canonical_revision,
        "contract_revision": contract.get("contract_revision"),
        "required_metadata_count": len(
            contract.get("required_metadata", [])
        ),
        "shared_field_contract_count": len(
            contract.get("shared_field_contracts", [])
        ),
        "value_domain_kind_count": len(actual_kinds),
        "issues": issue_rows,
    }
