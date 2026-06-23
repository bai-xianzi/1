"""TASK_014真实DolphinDB基本面标准化抽样验收。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import QualityStatus
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_fundamental_service import (
    DolphinDBFundamentalStandardizedService,
)
from a_stock_quant.dolphindb_probe import resolve_password
from a_stock_quant.fundamental_standard_provider import (
    FundamentalStandardDataProvider,
)
from a_stock_quant.standard_data_service import (
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


SAMPLE_IDS = (
    "000001",
    "002731",
    "600015",
    "001235",
    "001248",
)


@dataclass(frozen=True, slots=True)
class AcceptanceCheck:
    name: str
    passed: bool
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AcceptanceReport:
    checks: tuple[AcceptanceCheck, ...]
    query_results: dict[str, Any]
    overall_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [asdict(item) for item in self.checks],
            "query_results": self.query_results,
            "overall_status": self.overall_status,
        }


def _query(
    service: StandardDataService,
    canonical_object: str,
    *,
    usage: StandardDataUsage = (
        StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
    ),
    decision_time: datetime | None = None,
) -> Any:
    return service.query(
        StandardDataQuery(
            dataset_id="a_stock_fundamental_snapshot",
            canonical_object=canonical_object,
            instrument_ids=SAMPLE_IDS,
            start_date=date(2026, 6, 19),
            end_date=date(2026, 6, 19),
            as_of_date=date(2026, 6, 20),
            usage=usage,
            decision_time=decision_time,
            include_source_extensions=True,
            include_quality_flags=True,
            include_lineage=True,
        )
    )


def _index_records(result: Any) -> dict[str, list[Any]]:
    output: dict[str, list[Any]] = {}
    for record in result.records:
        instrument_id = (
            record.primary_key.get("instrument_id")
            or record.values.get("instrument_id")
        )
        if instrument_id is None:
            continue
        output.setdefault(str(instrument_id), []).append(record)
    return output


def build_report(
    service: StandardDataService,
    raw_service: DolphinDBFundamentalStandardizedService,
) -> AcceptanceReport:
    fundamental = _query(service, "FundamentalSnapshot")
    ownership = _query(service, "OwnershipSnapshot")
    instrument = _query(service, "Instrument")
    classification = _query(service, "ClassificationMembership")
    historical = _query(
        service,
        "FundamentalSnapshot",
        usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
    )
    manual = _query(
        service,
        "FundamentalSnapshot",
        usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
        decision_time=datetime(
            2026, 6, 20, 9, 0, tzinfo=timezone.utc
        ),
    )

    fundamental_by_id = _index_records(fundamental)
    ownership_by_id = _index_records(ownership)
    instrument_by_id = _index_records(instrument)

    checks: list[AcceptanceCheck] = []

    checks.append(
        AcceptanceCheck(
            name="数据集配置保持禁用且验收显式放行",
            passed=(
                raw_service.registration.enabled is False
                and raw_service.registration.mapping_version == "0.2.0-rc2"
                and raw_service.registration.dictionary_revision == "0.5"
            ),
            details={
                "enabled": raw_service.registration.enabled,
                "mapping_version": raw_service.registration.mapping_version,
                "dictionary_revision": raw_service.registration.dictionary_revision,
            },
        )
    )

    record_000001 = (fundamental_by_id.get("000001") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="000001正常一季报金额和报告期标准化",
            passed=(
                record_000001 is not None
                and record_000001.values.get("report_period")
                == date(2026, 3, 31)
                and record_000001.values.get("revenue_cny")
                == 35_277_000_000.0
                and record_000001.source_extensions.get("operating_revenue")
                == 35_277_000.0
                and record_000001.values.get("announcement_date") is None
            ),
            details=(
                record_000001.to_dict()
                if record_000001 is not None
                else {"record": None}
            ),
        )
    )

    ownership_000001 = (ownership_by_id.get("000001") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="000001股本Raw与Canonical分层",
            passed=(
                ownership_000001 is not None
                and ownership_000001.values.get("total_shares")
                == 19_405_918_700
                and isinstance(
                    ownership_000001.values.get("total_shares"), int
                )
                and ownership_000001.source_extensions.get("total_shares")
                == 1_940_591.87
            ),
            details=(
                ownership_000001.to_dict()
                if ownership_000001 is not None
                else {"record": None}
            ),
        )
    )

    record_002731 = (fundamental_by_id.get("002731") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="002731旧三季报日期推导",
            passed=(
                record_002731 is not None
                and record_002731.values.get("report_period")
                == date(2025, 9, 30)
            ),
            details=(
                record_002731.to_dict()
                if record_002731 is not None
                else {"record": None}
            ),
        )
    )

    record_600015 = (fundamental_by_id.get("600015") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="600015年报日期推导",
            passed=(
                record_600015 is not None
                and record_600015.values.get("report_period")
                == date(2025, 12, 31)
            ),
            details=(
                record_600015.to_dict()
                if record_600015 is not None
                else {"record": None}
            ),
        )
    )

    for instrument_id, label in (
        ("001235", "身份和财务不完整"),
        ("001248", "有身份但无财务载荷"),
    ):
        checks.append(
            AcceptanceCheck(
                name=f"{instrument_id}{label}不零填财务",
                passed=(
                    instrument_id not in fundamental_by_id
                    and instrument_id not in ownership_by_id
                    and instrument_id in instrument_by_id
                ),
                details={
                    "fundamental_count": len(
                        fundamental_by_id.get(instrument_id, [])
                    ),
                    "ownership_count": len(
                        ownership_by_id.get(instrument_id, [])
                    ),
                    "instrument_count": len(
                        instrument_by_id.get(instrument_id, [])
                    ),
                },
            )
        )

    classification_fields_are_authoritative = all(
        "node_id" in record.values
        and "node_name_cn" in record.values
        and "classification_node_id" not in record.values
        for record in classification.records
    )
    checks.append(
        AcceptanceCheck(
            name="行业分类使用权威Canonical字段并保持快照警告",
            passed=(
                bool(classification.records)
                and classification_fields_are_authoritative
                and classification.metadata.status is QualityStatus.WARNING
            ),
            details={
                "result_count": len(classification.records),
                "status": classification.metadata.status.value,
                "quality_flag_counts": (
                    classification.metadata.quality_flag_counts
                ),
            },
        )
    )

    checks.append(
        AcceptanceCheck(
            name="当前研究和快照后人工辅助决策允许但带警告",
            passed=(
                fundamental.metadata.status is QualityStatus.WARNING
                and not fundamental.metadata.blocks_downstream
                and manual.metadata.status is QualityStatus.WARNING
                and not manual.metadata.blocks_downstream
            ),
            details={
                "research": fundamental.metadata.to_dict(),
                "manual": manual.metadata.to_dict(),
            },
        )
    )

    checks.append(
        AcceptanceCheck(
            name="严格历史回测继续阻断",
            passed=(
                historical.metadata.status is QualityStatus.FAILED
                and historical.metadata.blocks_downstream
            ),
            details=historical.metadata.to_dict(),
        )
    )

    overall = "PASSED" if all(item.passed for item in checks) else "FAILED"
    return AcceptanceReport(
        checks=tuple(checks),
        query_results={
            "FundamentalSnapshot": fundamental.to_dict(),
            "OwnershipSnapshot": ownership.to_dict(),
            "Instrument": instrument.to_dict(),
            "ClassificationMembership": classification.to_dict(),
            "HistoricalGate": historical.to_dict(),
            "ManualDecisionGate": manual.to_dict(),
        },
        overall_status=overall,
    )


def write_report(
    report: AcceptanceReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# TASK_014 基本面真实标准化验收",
        "",
        f"总体状态：**{report.overall_status}**",
        "",
    ]
    for item in report.checks:
        mark = "PASS" if item.passed else "FAIL"
        lines.append(f"- [{mark}] {item.name}")
    markdown_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument(
        "--registration",
        default=(
            "configs/datasets/"
            "a_stock_fundamental_snapshot.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        default="reports/task_014_fundamental_acceptance.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="reports/task_014_fundamental_acceptance.md",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = resolve_password()

    adapter = DolphinDBDataSourceAdapter(
        settings=DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=password,
        ),
        source_id="dolphindb_fundamental_task_014",
    )

    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        print(f"DolphinDB健康检查失败：{health.description}")
        return 1

    raw_service = (
        DolphinDBFundamentalStandardizedService.from_registry_file(
            adapter,
            args.registration,
            allow_disabled_for_acceptance=True,
        )
    )
    provider = FundamentalStandardDataProvider(raw_service)
    standard_service = StandardDataService()
    standard_service.register_provider(provider)

    report = build_report(standard_service, raw_service)
    write_report(
        report,
        Path(args.json_output),
        Path(args.markdown_output),
    )

    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    print(f"\n验收JSON：{args.json_output}")
    print(f"验收摘要：{args.markdown_output}")
    return 0 if report.overall_status == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
