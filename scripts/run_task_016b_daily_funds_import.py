"""运行TASK_016B七类日线资金DolphinDB建库与导入。"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from a_stock_quant.daily_funds_ingest import (
    DailyFundsIngestError,
)
from a_stock_quant.daily_funds_dolphindb_writer import (
    DATABASE_URI,
    DailyFundsDolphinDBError,
    DolphinDBWriteSettings,
    build_create_database_script,
    create_database_and_tables,
    probe_dolphindb_environment,
    resolve_password,
    run_daily_funds_import,
    validate_local_contract,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "TASK_016B七类日线资金DolphinDB Raw层工具。"
        )
    )
    parser.add_argument(
        "--mode",
        choices=("contract", "probe", "create", "import"),
        required=True,
    )
    parser.add_argument(
        "--project-root",
        default=".",
    )
    parser.add_argument(
        "--root",
        default=(
            r"D:\Users\Administrator\Desktop"
            r"\数据导入\日线资金\2025\2025\2025"
        ),
    )
    parser.add_argument(
        "--output-dir",
        required=True,
    )
    parser.add_argument(
        "--host",
        default=os.getenv(
            "DOLPHINDB_HOST",
            "127.0.0.1",
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(
            os.getenv("DOLPHINDB_PORT", "8848")
        ),
    )
    parser.add_argument(
        "--username",
        default=os.getenv(
            "DOLPHINDB_USERNAME",
            "admin",
        ),
    )
    parser.add_argument(
        "--database-uri",
        default=DATABASE_URI,
    )
    parser.add_argument(
        "--expected-planned-row-count",
        type=int,
        default=461966,
    )
    return parser


def _print_json(value: Any) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def _write_result(
    output_dir: Path,
    mode: str,
    result: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"task_016b_{mode}_result.json"
    path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir)
    contract_path = (
        project_root
        / "configs"
        / "datasets"
        / "a_stock_daily_funds_raw.yaml"
    )

    try:
        if args.mode == "contract":
            result = validate_local_contract(
                contract_path
            )
            result["ddl_preview"] = (
                build_create_database_script(
                    args.database_uri
                )
            )
        else:
            settings = DolphinDBWriteSettings(
                host=args.host,
                port=args.port,
                username=args.username,
                password=resolve_password(),
                database_uri=args.database_uri,
            )
            if args.mode == "probe":
                result = probe_dolphindb_environment(
                    settings
                )
            elif args.mode == "create":
                result = create_database_and_tables(
                    settings
                )
            else:
                result = run_daily_funds_import(
                    settings=settings,
                    root=Path(args.root),
                    contract_path=contract_path,
                    output_dir=output_dir,
                    expected_planned_row_count=(
                        args.expected_planned_row_count
                    ),
                )
        _write_result(
            output_dir,
            args.mode,
            result,
        )
        _print_json(result)
        return (
            0
            if result.get("overall_status") == "PASSED"
            else 1
        )
    except (
        DailyFundsDolphinDBError,
        DailyFundsIngestError,
        ValueError,
        OSError,
    ) as exc:
        result = {
            "task_id": "TASK_016B",
            "mode": args.mode.upper(),
            "overall_status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_result(
            output_dir,
            args.mode,
            result,
        )
        _print_json(result)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
