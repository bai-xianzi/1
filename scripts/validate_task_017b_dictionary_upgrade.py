"""验证TASK_017B字段字典升级和七类Canonical合同。"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import yaml

from a_stock_quant.daily_funds_canonical_contract import validate_contract
from a_stock_quant.field_dictionary_governance import validate_dictionary_governance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    canonical_path = root / "schemas" / "canonical_fields.yaml"
    canonical = yaml.safe_load(canonical_path.read_text(encoding="utf-8"))
    lifecycle = Counter(
        field["lifecycle_stage"]
        for domain in canonical["domains"]
        for field in domain["fields"]
    )
    governance = validate_dictionary_governance(root)
    mapping = validate_contract(
        root / "configs" / "mappings" / "a_stock_daily_funds_canonical_v0.yaml",
        canonical_path,
    )
    errors = []
    if governance["overall_status"] != "PASSED":
        errors.append({"component":"field_governance","issues":governance["issues"]})
    if mapping["overall_status"] != "PASSED_WITH_WARNINGS":
        errors.append({"component":"canonical_contract","issues":mapping["issues"]})
    expected = {
        "dictionary_revision":"0.6.0",
        "domain_count":46,
        "field_count":1235,
        "core_count":744,
        "near_term_count":50,
        "future_reserved_count":441,
    }
    actual = {
        "dictionary_revision":str(canonical.get("dictionary_revision")),
        "domain_count":len(canonical.get("domains", [])),
        "field_count":sum(lifecycle.values()),
        "core_count":lifecycle.get("core", 0),
        "near_term_count":lifecycle.get("near_term", 0),
        "future_reserved_count":lifecycle.get("future_reserved", 0),
    }
    if actual != expected:
        errors.append({"component":"dictionary_counts","expected":expected,"actual":actual})
    result = {
        "task_id":"TASK_017B",
        **actual,
        "mapping_dataset_count":mapping["dataset_count"],
        "ready_with_warning_count":mapping["ready_with_warning_count"],
        "blocked_count":mapping["blocked_count"],
        "overall_status":"PASSED_WITH_WARNINGS" if not errors else "FAILED",
        "issues":errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
