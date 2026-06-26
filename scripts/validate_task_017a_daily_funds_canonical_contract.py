"""验证TASK_017A Canonical接入合同。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from a_stock_quant.daily_funds_canonical_contract import (
    validate_contract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        default=".",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    result = validate_contract(
        root
        / "configs"
        / "mappings"
        / "a_stock_daily_funds_canonical_v0.yaml",
        root / "schemas" / "canonical_fields.yaml",
    )
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )
    return (
        0
        if result["overall_status"]
        == "PASSED_WITH_REVIEW_ITEMS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
