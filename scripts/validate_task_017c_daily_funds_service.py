"""验证TASK_017C只读Canonical服务合同。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from a_stock_quant.dolphindb_daily_funds_service import (
    validate_daily_funds_service_contract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_daily_funds_service_contract(
        Path(args.project_root)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall_status"] == "PASSED_WITH_WARNINGS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
