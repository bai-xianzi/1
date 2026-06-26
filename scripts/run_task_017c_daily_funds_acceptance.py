"""TASK_017C真实DolphinDB只读Canonical抽样验收。"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DailyFundsReadRequest,
    DolphinDBDailyFundsCanonicalService,
    normalise_query_records,
)


DATASETS = ("hq", "kphq", "hy", "gn", "kphy", "kpgn", "zj")


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


def _sample_selector(
    adapter: DolphinDBDataSourceAdapter,
    service: DolphinDBDailyFundsCanonicalService,
    dataset_id: str,
) -> tuple[str, date]:
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
    selector = str(rows[0][raw_field]).strip()
    return selector, _as_date(rows[0]["snapshot_date"])


def _assert_semantics(dataset_id: str, record: Any) -> list[str]:
    checks: list[str] = []
    values = record.values
    if dataset_id == "hq":
        lots = values.get("volume_lots")
        shares = values.get("volume_shares")
        if lots is not None and shares != round(lots * 100):
            raise DataContractError("hq手到股转换验收失败。")
        checks.append("VOLUME_LOT_TO_SHARE")
    elif dataset_id == "kphq":
        if values.get("snapshot_time") is not None:
            raise DataContractError("kphq伪造了精确snapshot_time。")
        if values.get("snapshot_time_precision") != "DATE_ONLY":
            raise DataContractError("kphq时间精度不是DATE_ONLY。")
        checks.append("DATE_ONLY_NO_FABRICATED_TIME")
    elif dataset_id in {"hy", "gn", "kphy", "kpgn"}:
        if record.canonical_object != "ClassificationMarketSnapshot":
            raise DataContractError("分类来源映射成了错误对象。")
        if not values.get("node_id"):
            raise DataContractError("分类节点缺少稳定临时node_id。")
        checks.append("CLASSIFICATION_NODE_NOT_MEMBERSHIP")
    elif dataset_id == "zj":
        buckets = [
            values.get("net_inflow_super_large_cny"),
            values.get("net_inflow_large_cny"),
            values.get("net_inflow_medium_cny"),
            values.get("net_inflow_small_cny"),
        ]
        present = [value for value in buckets if value is not None]
        expected = None if not present else sum(present)
        if values.get("net_inflow_total_cny") != expected:
            raise DataContractError("zj总净流入派生验收失败。")
        checks.append("MONEY_FLOW_BUCKET_SUM")
    return checks


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
        source_id="daily_funds_task_017c_acceptance",
    )
    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        raise DataContractError(health.description or "健康检查失败。")
    service = DolphinDBDailyFundsCanonicalService(
        adapter,
        project_root=root,
    )

    dataset_results: list[dict[str, Any]] = []
    for dataset_id in DATASETS:
        selector, snapshot_date = _sample_selector(
            adapter,
            service,
            dataset_id,
        )
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id=dataset_id,
                entity_ids=(selector,),
                start_date=snapshot_date,
                end_date=snapshot_date,
                limit_per_entity=10,
            )
        )
        if not batch.records:
            raise DataContractError(
                f"{dataset_id}抽样没有生成Canonical记录。"
            )
        record = batch.records[0]
        checks = _assert_semantics(dataset_id, record)
        dataset_results.append(
            {
                "dataset_id": dataset_id,
                "selector": selector,
                "snapshot_date": snapshot_date.isoformat(),
                "canonical_object": batch.canonical_object,
                "source_row_count": batch.source_row_count,
                "result_count": len(batch.records),
                "quality_flags": list(record.quality_flags),
                "warnings": list(batch.warnings),
                "semantic_checks": checks,
                "primary_key": record.primary_key,
                "source_record_id": record.source_record_id,
            }
        )

    report = {
        "task_id": "TASK_017C",
        "mode": "REAL_READONLY_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_uri": service.database_uri,
        "service_id": service.service_id,
        "service_version": service.service_version,
        "coverage_version": service.coverage_version,
        "mapping_version": service.mapping_version,
        "dictionary_revision": service.dictionary_revision,
        "dataset_count": len(dataset_results),
        "write_operation_count": 0,
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": dataset_results,
    }
    json_path = output_dir / "task_017c_real_acceptance.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    md_lines = [
        "# TASK_017C真实只读验收",
        "",
        "- 状态：**PASSED_WITH_WARNINGS**",
        f"- 数据库：`{service.database_uri}`",
        f"- 来源：{len(dataset_results)}",
        "- 写操作：0",
        "",
        "| 来源 | Canonical对象 | 记录数 |",
        "|---|---|---:|",
    ]
    md_lines.extend(
        f"| {item['dataset_id']} | {item['canonical_object']} | {item['result_count']} |"
        for item in dataset_results
    )
    (output_dir / "task_017c_real_acceptance.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
