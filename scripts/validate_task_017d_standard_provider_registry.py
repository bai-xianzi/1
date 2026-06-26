"""验证 TASK_017D 七类 StandardDataService Provider 注册合同。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import yaml

from a_stock_quant.daily_funds_canonical_contract import REQUIRED_DATASETS
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    STANDARD_QUERY_CONTRACT_VERSION,
)


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"YAML根节点必须是映射：{path}")
    return payload


def validate(project_root: Path) -> dict[str, Any]:
    registry = _load(
        project_root
        / "configs/datasets/a_stock_daily_funds_standard_providers.yaml"
    )
    service = _load(
        project_root
        / "configs/datasets/a_stock_daily_funds_standard_service.yaml"
    )
    providers = dict(registry.get("providers", {}))
    issues: list[dict[str, Any]] = []

    if registry.get("standard_query_contract_version") != STANDARD_QUERY_CONTRACT_VERSION:
        issues.append({"severity": "ERROR", "code": "QUERY_CONTRACT_VERSION_MISMATCH"})
    if tuple(providers) != REQUIRED_DATASETS:
        issues.append({"severity": "ERROR", "code": "PROVIDER_DATASET_SET_OR_ORDER_MISMATCH"})

    provider_ids = [str(item.get("provider_id", "")) for item in providers.values()]
    if len(provider_ids) != len(set(provider_ids)):
        issues.append({"severity": "ERROR", "code": "PROVIDER_ID_DUPLICATE"})

    service_profiles = dict(service.get("dataset_profiles", {}))
    instrument_count = 0
    entity_count = 0
    for dataset_id, item in providers.items():
        mode = item.get("selector_mode")
        if mode == INSTRUMENT_SELECTOR_MODE:
            instrument_count += 1
        elif mode == ENTITY_SELECTOR_MODE:
            entity_count += 1
        else:
            issues.append({"severity": "ERROR", "code": "SELECTOR_MODE_INVALID", "dataset_id": dataset_id})
        profile = service_profiles.get(dataset_id, {})
        if item.get("canonical_object") != profile.get("canonical_object"):
            issues.append({"severity": "ERROR", "code": "CANONICAL_OBJECT_MISMATCH", "dataset_id": dataset_id})
        raw_mode = profile.get("selector_mode")
        expected_mode = (
            INSTRUMENT_SELECTOR_MODE
            if raw_mode == "INSTRUMENT_ID"
            else ENTITY_SELECTOR_MODE
        )
        if mode != expected_mode:
            issues.append({"severity": "ERROR", "code": "SELECTOR_SEMANTIC_MISMATCH", "dataset_id": dataset_id})

    errors = [item for item in issues if item["severity"] == "ERROR"]
    return {
        "task_id": "TASK_017D",
        "registry_version": str(registry.get("registry_version", "")),
        "standard_query_contract_version": STANDARD_QUERY_CONTRACT_VERSION,
        "provider_count": len(providers),
        "instrument_selector_provider_count": instrument_count,
        "entity_selector_provider_count": entity_count,
        "canonical_object_count": len({item.get("canonical_object") for item in providers.values()}),
        "overall_status": "PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues": issues,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args(argv)
    result = validate(Path(args.project_root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall_status"] == "PASSED_WITH_WARNINGS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
