"""运行 TASK_016A 七类日线资金只读预导入。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.daily_funds_ingest import (  # noqa: E402
    load_daily_funds_contract,
    run_daily_funds_preflight,
    validate_daily_funds_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "TASK_016A 七类日线资金只读预导入；"
            "不会连接或修改DolphinDB。"
        )
    )
    parser.add_argument(
        "--root",
        help="日线资金根目录，下一层必须是YYYYMMDD目录。",
    )
    parser.add_argument(
        "--output-dir",
        help="预导入报告输出目录。",
    )
    parser.add_argument(
        "--contract",
        default=str(
            PROJECT_ROOT
            / "configs"
            / "datasets"
            / "a_stock_daily_funds_raw.yaml"
        ),
        help="来源合同YAML路径。",
    )
    parser.add_argument(
        "--validate-contract-only",
        action="store_true",
        help="只验证合同，不扫描源文件。",
    )
    args = parser.parse_args()

    contract_path = Path(args.contract)
    contract = load_daily_funds_contract(contract_path)
    contract_report = validate_daily_funds_contract(contract)

    if args.validate_contract_only:
        print(
            json.dumps(
                contract_report,
                ensure_ascii=False,
                indent=2,
            )
        )
        return (
            0
            if contract_report["overall_status"] == "PASSED"
            else 1
        )

    if not args.root or not args.output_dir:
        parser.error(
            "扫描模式必须同时提供 --root 和 --output-dir。"
        )

    summary = run_daily_funds_preflight(
        root=Path(args.root),
        contract_path=contract_path,
        output_dir=Path(args.output_dir),
    )
    print("TASK_016A 七类日线资金只读预导入完成")
    print(f"总体状态：{summary['overall_status']}")
    print(
        f"快照目录：{summary['snapshot_directory_count']}"
    )
    print(f"画像文件：{summary['profiled_file_count']}")
    print(f"可写入文件：{summary['ready_file_count']}")
    print(
        f"隔离文件：{summary['quarantined_file_count']}"
    )
    print(f"阻断文件：{summary['blocked_file_count']}")
    print(f"解析行：{summary['parsed_row_count']}")
    print(
        f"计划写入行：{summary['planned_insert_row_count']}"
    )
    print(f"输出目录：{args.output_dir}")
    print("本任务没有连接或修改DolphinDB。")
    return 0 if summary["overall_status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
