"""七类日线资金Canonical接入合同验证。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_DATASETS = (
    "hq",
    "hy",
    "gn",
    "kphq",
    "kphy",
    "kpgn",
    "zj",
)
CLASSIFICATION_DATASETS = frozenset(
    {"hy", "gn", "kphy", "kpgn"}
)
ALLOWED_STATUSES = frozenset(
    {
        "MAPPED",
        "MAPPED_WITH_WARNING",
        "DERIVED",
        "CONSTANT",
        "SOURCE_EXTENSION",
        "BLOCKED_SCHEMA_GAP",
        "NOT_APPLICABLE",
    }
)


class DailyFundsCanonicalContractError(ValueError):
    """Canonical合同无效。"""


@dataclass(frozen=True, slots=True)
class DailyFundsCanonicalContract:
    raw: dict[str, Any]

    @property
    def contract_version(self) -> str:
        return str(self.raw["contract_version"])

    @property
    def dictionary_revision(self) -> str:
        return str(self.raw["dictionary_revision"])

    @property
    def datasets(self) -> dict[str, dict[str, Any]]:
        return dict(self.raw["datasets"])


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DailyFundsCanonicalContractError(
            f"YAML根节点必须是映射：{path}"
        )
    return payload


def load_contract(path: str | Path) -> DailyFundsCanonicalContract:
    return DailyFundsCanonicalContract(raw=_load_yaml(Path(path)))


def _dictionary_objects(
    dictionary_path: Path,
) -> dict[str, set[str]]:
    payload = _load_yaml(dictionary_path)
    objects: dict[str, set[str]] = {}
    for domain in payload.get("domains", []):
        if not isinstance(domain, dict):
            continue
        object_name = str(domain.get("canonical_object", "")).strip()
        fields = {
            str(item.get("canonical_name", "")).strip()
            for item in domain.get("fields", [])
            if isinstance(item, dict)
        }
        if object_name:
            objects.setdefault(object_name, set()).update(
                field for field in fields if field
            )
    return objects


def validate_contract(
    contract_path: str | Path,
    dictionary_path: str | Path,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    dictionary_payload = _load_yaml(Path(dictionary_path))
    dictionary_revision = str(
        dictionary_payload.get("dictionary_revision", "")
    )
    objects = _dictionary_objects(Path(dictionary_path))
    issues: list[dict[str, Any]] = []

    if contract.dictionary_revision != dictionary_revision:
        issues.append(
            {
                "severity": "ERROR",
                "code": "DICTIONARY_REVISION_MISMATCH",
                "expected": dictionary_revision,
                "actual": contract.dictionary_revision,
            }
        )

    dataset_ids = tuple(contract.datasets)
    if (
        len(dataset_ids) != len(REQUIRED_DATASETS)
        or set(dataset_ids) != set(REQUIRED_DATASETS)
    ):
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATASET_SET_MISMATCH",
                "expected": REQUIRED_DATASETS,
                "actual": dataset_ids,
            }
        )

    allowed = set(
        contract.raw.get("allowed_mapping_statuses", [])
    )
    if allowed != ALLOWED_STATUSES:
        issues.append(
            {
                "severity": "ERROR",
                "code": "ALLOWED_STATUS_SET_MISMATCH",
            }
        )

    for dataset_id, dataset in contract.datasets.items():
        canonical_object = str(dataset.get("canonical_object", ""))
        readiness = str(dataset.get("readiness", ""))
        mappings = dataset.get("mappings", [])
        if readiness != "READY_WITH_WARNING":
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "DATASET_NOT_READY_WITH_WARNING",
                    "dataset_id": dataset_id,
                    "readiness": readiness,
                }
            )
        if canonical_object not in objects:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "CANONICAL_OBJECT_MISSING",
                    "dataset_id": dataset_id,
                    "canonical_object": canonical_object,
                }
            )
            continue
        if not isinstance(mappings, list) or not mappings:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "MAPPINGS_MISSING",
                    "dataset_id": dataset_id,
                }
            )
            continue

        for mapping in mappings:
            status = str(mapping.get("status", ""))
            target = str(mapping.get("target", ""))
            if status not in ALLOWED_STATUSES:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNKNOWN_MAPPING_STATUS",
                        "dataset_id": dataset_id,
                        "target": target,
                        "status": status,
                    }
                )
            if target not in objects[canonical_object]:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "TARGET_FIELD_NOT_IN_DICTIONARY",
                        "dataset_id": dataset_id,
                        "canonical_object": canonical_object,
                        "target": target,
                    }
                )

        if dataset_id == "hq" and dataset.get("source_role") != "SUPPLEMENTAL_RECONCILIATION":
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "HQ_ROLE_NOT_SUPPLEMENTAL",
                }
            )

        if dataset_id == "kphq":
            mapping_index = {
                str(item.get("target", "")): item
                for item in mappings
            }
            snapshot_time = mapping_index.get("snapshot_time", {})
            precision = mapping_index.get(
                "snapshot_time_precision", {}
            )
            if snapshot_time.get("status") != "NOT_APPLICABLE":
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_TIME_MUST_REMAIN_NULL",
                    }
                )
            if (
                precision.get("status") != "CONSTANT"
                or precision.get("transform")
                != "constant_DATE_ONLY"
            ):
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_TIME_PRECISION_NOT_DATE_ONLY",
                    }
                )
            serialized = str(dataset)
            for forbidden in (
                "source_file_mtime_utc",
                "ingested_at_utc",
                "midnight",
                "constant_09_25",
            ):
                if forbidden not in serialized:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "AUCTION_FORBIDDEN_FALLBACK_NOT_RECORDED",
                            "fallback": forbidden,
                        }
                    )

        if dataset_id in CLASSIFICATION_DATASETS:
            if canonical_object != "ClassificationMarketSnapshot":
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "CLASSIFICATION_OBJECT_WRONG",
                        "dataset_id": dataset_id,
                    }
                )
            if "average_shares" not in dataset.get(
                "source_extensions", []
            ):
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNCONFIRMED_AVERAGE_SHARES_NOT_EXTENSION",
                        "dataset_id": dataset_id,
                    }
                )

        if dataset_id == "zj" and dataset.get("sign_policy") != "PRESERVE_SOURCE_SIGN":
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "MONEY_FLOW_SIGN_POLICY_INVALID",
                }
            )

    implemented = contract.raw.get(
        "implemented_dictionary_changes", []
    )
    implemented_ids = {
        str(item.get("change_id", ""))
        for item in implemented
        if isinstance(item, dict)
        and item.get("status") == "IMPLEMENTED"
    }
    required_ids = {
        "ADD_CLASSIFICATION_MARKET_SNAPSHOT",
        "AUCTION_TIME_PRECISION_GOVERNANCE",
    }
    if not required_ids.issubset(implemented_ids):
        issues.append(
            {
                "severity": "ERROR",
                "code": "IMPLEMENTED_DICTIONARY_CHANGE_MISSING",
            }
        )

    errors = [
        issue for issue in issues
        if issue["severity"] == "ERROR"
    ]
    ready_count = sum(
        1 for item in contract.datasets.values()
        if item.get("readiness") == "READY_WITH_WARNING"
    )
    blocked_count = sum(
        1 for item in contract.datasets.values()
        if str(item.get("readiness", "")).startswith("BLOCKED_")
    )
    return {
        "task_id": "TASK_017B",
        "contract_version": contract.contract_version,
        "dictionary_revision": dictionary_revision,
        "dataset_count": len(contract.datasets),
        "ready_with_warning_count": ready_count,
        "blocked_count": blocked_count,
        "implemented_dictionary_change_count": len(implemented),
        "overall_status": "PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues": issues,
    }
