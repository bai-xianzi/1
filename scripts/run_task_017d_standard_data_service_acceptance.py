"""TASK_017D 统一 StandardDataService 真实只读验收。"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.daily_funds_canonical_contract import REQUIRED_DATASETS
from a_stock_quant.daily_funds_standard_provider import (
    register_daily_funds_standard_providers,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DolphinDBDailyFundsCanonicalService,
    normalise_query_records,
)
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


def _password() -> str:
    value = os.getenv("DOLPHINDB_PASSWORD")
    if value is None:
        value = getpass.getpass("请输入 DolphinDB 密码：")
    if not value:
        raise DataContractError("DolphinDB密码不能为空。")
    return value


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    converted = getattr(value, "to_pydatetime", lambda: None)()
    if isinstance(converted, datetime):
        return converted.date()
    if isinstance(converted, date):
        return converted
    return date.fromisoformat(str(value).replace(".", "-")[:10])


def _sample_selector(adapter: Any, service: Any, dataset_id: str) -> tuple[str, date]:
    profile = service.dataset_profile(dataset_id)
    raw_field = profile["raw_entity_field"]
    table_name = profile["source_table"]
    script = (
        f"select top 1 {raw_field}, snapshot_date "
        f'from loadTable("{service.database_uri}", `{table_name}) '
        f"where dataset_id=`{dataset_id} "
        "order by snapshot_date, source_row_number"
    )
    rows = normalise_query_records(adapter.run_readonly_query(script))
    if not rows:
        raise DataContractError(f"{dataset_id}没有可验收的Raw记录。")
    return str(rows[0][raw_field]).strip(), _as_date(rows[0]["snapshot_date"])


def _query(dataset_id: str, selector_mode: str, selector: str, snapshot_date: date, canonical_object: str, usage: StandardDataUsage = StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH) -> StandardDataQuery:
    return StandardDataQuery(
        dataset_id=dataset_id,
        canonical_object=canonical_object,
        instrument_ids=(selector,) if selector_mode == INSTRUMENT_SELECTOR_MODE else (),
        entity_ids=(selector,) if selector_mode == ENTITY_SELECTOR_MODE else (),
        start_date=snapshot_date,
        end_date=snapshot_date,
        as_of_date=snapshot_date,
        usage=usage,
        include_source_extensions=True,
        include_quality_flags=True,
        include_lineage=True,
        limit_per_instrument=10,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    adapter = DolphinDBDataSourceAdapter(
        DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=_password(),
        ),
        source_id="daily_funds_task_017d_acceptance",
    )
    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        raise DataContractError(health.description or "健康检查失败。")

    canonical_service = DolphinDBDailyFundsCanonicalService(
        adapter,
        project_root=root,
    )
    standard_service = StandardDataService()
    descriptors = register_daily_funds_standard_providers(
        standard_service,
        canonical_service,
        project_root=root,
    )
    if len(descriptors) != 7 or len(standard_service.list_datasets()) != 7:
        raise DataContractError("七个Provider没有完整注册。")

    results: list[dict[str, Any]] = []
    historical_blocks = 0
    for dataset_id in REQUIRED_DATASETS:
        descriptor = standard_service.get_provider(dataset_id).descriptor
        selector, snapshot_date = _sample_selector(
            adapter,
            canonical_service,
            dataset_id,
        )
        request = _query(
            dataset_id,
            descriptor.selector_mode,
            selector,
            snapshot_date,
            descriptor.supported_objects[0],
        )
        result = standard_service.query(request)
        if not result.records:
            raise DataContractError(f"{dataset_id}统一入口没有返回记录。")
        if result.metadata.blocks_downstream:
            raise DataContractError(f"{dataset_id}研究用途被意外阻断。")
        result.assert_usable()

        strict_result = standard_service.query(
            _query(
                dataset_id,
                descriptor.selector_mode,
                selector,
                snapshot_date,
                descriptor.supported_objects[0],
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            )
        )
        if not strict_result.metadata.blocks_downstream:
            raise DataContractError(f"{dataset_id}严格历史用途没有阻断。")
        try:
            strict_result.assert_usable()
        except DataContractError:
            historical_blocks += 1
        else:
            raise DataContractError(f"{dataset_id}阻断结果仍可用。")

        record = result.records[0]
        results.append(
            {
                "dataset_id": dataset_id,
                "provider_id": descriptor.provider_id,
                "selector_mode": descriptor.selector_mode,
                "selector": selector,
                "snapshot_date": snapshot_date.isoformat(),
                "canonical_object": record.canonical_object,
                "result_count": result.metadata.result_count,
                "status": result.metadata.status.value,
                "blocks_downstream": result.metadata.blocks_downstream,
                "strict_historical_blocks": strict_result.metadata.blocks_downstream,
                "lineage_item_count": result.metadata.lineage_item_count,
                "primary_key": record.primary_key,
            }
        )

    report = {
        "task_id": "TASK_017D",
        "mode": "REAL_STANDARD_DATA_SERVICE_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_uri": canonical_service.database_uri,
        "provider_count": len(descriptors),
        "unified_query_count": len(results),
        "historical_gate_block_count": historical_blocks,
        "write_operation_count": 0,
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": results,
    }
    (output_dir / "task_017d_real_acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    lines = [
        "# TASK_017D统一标准数据入口真实验收",
        "",
        "- 状态：**PASSED_WITH_WARNINGS**",
        f"- Provider：{len(descriptors)}",
        f"- 统一查询：{len(results)}",
        f"- 严格历史门禁阻断：{historical_blocks}",
        "- 写操作：0",
        "",
        "| 来源 | 选择器 | Canonical对象 | 状态 |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {item['dataset_id']} | {item['selector_mode']} | {item['canonical_object']} | {item['status']} |"
        for item in results
    )
    (output_dir / "task_017d_real_acceptance.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
