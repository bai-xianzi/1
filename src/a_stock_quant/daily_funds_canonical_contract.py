"""TASK_017A七类日线资金Canonical接入合同验证。"""

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
    payload = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise DailyFundsCanonicalContractError(
            f"YAML根节点必须是映射：{path}"
        )
    return payload


def load_contract(
    path: str | Path,
) -> DailyFundsCanonicalContract:
    return DailyFundsCanonicalContract(
        raw=_load_yaml(Path(path))
    )


def _dictionary_objects(
    dictionary_path: Path,
) -> dict[str, set[str]]:
    payload = _load_yaml(dictionary_path)
    objects: dict[str, set[str]] = {}
    for domain in payload.get("domains", []):
        if not isinstance(domain, dict):
            continue
        object_name = str(
            domain.get("canonical_object", "")
        ).strip()
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
        contract.raw.get(
            "allowed_mapping_statuses",
            [],
        )
    )
    if allowed != ALLOWED_STATUSES:
        issues.append(
            {
                "severity": "ERROR",
                "code": "ALLOWED_STATUS_SET_MISMATCH",
            }
        )

    for dataset_id, dataset in contract.datasets.items():
        canonical_object = str(
            dataset.get("canonical_object", "")
        )
        readiness = str(
            dataset.get("readiness", "")
        )
        mappings = dataset.get("mappings", [])
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
            if (
                canonical_object in objects
                and status != "BLOCKED_SCHEMA_GAP"
                and target not in objects[canonical_object]
            ):
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "TARGET_FIELD_NOT_IN_DICTIONARY",
                        "dataset_id": dataset_id,
                        "canonical_object": canonical_object,
                        "target": target,
                    }
                )

        if dataset_id == "hq":
            if (
                dataset.get("source_role")
                != "SUPPLEMENTAL_RECONCILIATION"
            ):
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "HQ_ROLE_NOT_SUPPLEMENTAL",
                    }
                )

        if dataset_id == "kphq":
            gap_targets = {
                str(item.get("target", ""))
                for item in mappings
                if item.get("status")
                == "BLOCKED_SCHEMA_GAP"
            }
            if "snapshot_time" not in gap_targets:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_TIME_GAP_NOT_BLOCKING",
                    }
                )
            serialized = str(dataset)
            forbidden = (
                "constant_09_25",
                "source_file_mtime_utc",
                "ingested_at_utc",
                "midnight",
            )
            if not all(item in serialized for item in forbidden):
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "AUCTION_FORBIDDEN_FALLBACKS_MISSING",
                    }
                )
            if readiness != "BLOCKED_SCHEMA_GAP":
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "KPHQ_READINESS_TOO_PERMISSIVE",
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
            if readiness != "BLOCKED_DICTIONARY_GAP":
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "CLASSIFICATION_GAP_NOT_BLOCKING",
                        "dataset_id": dataset_id,
                    }
                )
            if canonical_object in objects:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "PROPOSED_OBJECT_ALREADY_EXISTS_REVIEW_CONTRACT",
                        "dataset_id": dataset_id,
                    }
                )

        if dataset_id == "zj":
            if dataset.get("sign_policy") != "PRESERVE_SOURCE_SIGN":
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "MONEY_FLOW_SIGN_POLICY_INVALID",
                    }
                )

    proposals = contract.raw.get(
        "proposed_dictionary_changes",
        [],
    )
    proposal_ids = {
        str(item.get("change_id", ""))
        for item in proposals
        if isinstance(item, dict)
    }
    required_proposals = {
        "ADD_CLASSIFICATION_MARKET_SNAPSHOT",
        "AUCTION_TIME_PRECISION_GOVERNANCE",
    }
    if not required_proposals.issubset(proposal_ids):
        issues.append(
            {
                "severity": "ERROR",
                "code": "REQUIRED_DICTIONARY_PROPOSAL_MISSING",
            }
        )

    errors = [
        issue
        for issue in issues
        if issue["severity"] == "ERROR"
    ]
    return {
        "task_id": "TASK_017A",
        "contract_version": contract.contract_version,
        "dictionary_revision": dictionary_revision,
        "dataset_count": len(contract.datasets),
        "existing_ready_with_warning_count": sum(
            1
            for item in contract.datasets.values()
            if item.get("readiness")
            == "READY_WITH_WARNING"
        ),
        "blocked_schema_gap_count": sum(
            1
            for item in contract.datasets.values()
            if str(item.get("readiness", "")).startswith(
                "BLOCKED_"
            )
        ),
        "proposed_dictionary_change_count": len(proposals),
        "overall_status": (
            "PASSED_WITH_REVIEW_ITEMS"
            if not errors
            else "FAILED"
        ),
        "issues": issues,
    }
