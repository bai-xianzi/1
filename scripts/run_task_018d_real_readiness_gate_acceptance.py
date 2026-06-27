"""TASK_018D 九个数据集真实端到端统一就绪度门禁验收。"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    ReadinessDimension,
    load_data_readiness_policy,
)
from a_stock_quant.data_readiness_evidence import (
    StandardQueryReadinessService,
    load_evidence_rule_config,
)
from a_stock_quant.data_readiness_external_evidence import (
    ExternalEvidenceOverlayBuilder,
    ReportBackedEvidenceResolver,
)
from a_stock_quant.daily_funds_standard_provider import (
    register_daily_funds_standard_providers,
)
from a_stock_quant.daily_k_standard_provider import (
    DailyKStandardDataProvider,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DolphinDBDailyFundsCanonicalService,
)
from a_stock_quant.dolphindb_daily_k_service import (
    DolphinDBDailyKStandardizedService,
)
from a_stock_quant.dolphindb_fundamental_service import (
    DolphinDBFundamentalStandardizedService,
)
from a_stock_quant.fundamental_standard_provider import (
    FundamentalStandardDataProvider,
)
from a_stock_quant.readiness_gated_data_service import (
    ReadinessGatedStandardDataService,
)
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


PLAN_VERSION = "0.1.0"


def _password() -> str:
    value = os.getenv("DOLPHINDB_PASSWORD")
    if value is None:
        value = getpass.getpass("请输入 DolphinDB 密码：")
    if not value:
        raise DataContractError("DolphinDB密码不能为空。")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(f"无法加载JSON：{path}") from exc
    if not isinstance(payload, dict):
        raise DataContractError(f"JSON根节点必须是对象：{path}")
    return payload


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


def _records_from_result(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        if any(not isinstance(item, Mapping) for item in result):
            raise DataContractError("DolphinDB列表结果存在非对象记录。")
        return [dict(item) for item in result]
    to_dict = getattr(result, "to_dict", None)
    columns = getattr(result, "columns", None)
    if callable(to_dict) and columns is not None:
        try:
            rows = to_dict(orient="records")
        except TypeError:
            rows = to_dict("records")
        if any(not isinstance(item, Mapping) for item in rows):
            raise DataContractError("DolphinDB表格无法转换为对象记录。")
        return [dict(item) for item in rows]
    raise DataContractError("不支持当前DolphinDB返回值类型。")


@dataclass(frozen=True, slots=True)
class SampleSource:
    dataset_id: str
    database_uri: str
    table_name: str
    entity_field: str
    date_field: str
    dataset_filter: str | None = None


def _sample_selector(
    adapter: DolphinDBDataSourceAdapter,
    source: SampleSource,
    preferred_selector: str | None,
) -> tuple[str, date]:
    where_parts: list[str] = []
    if source.dataset_filter:
        where_parts.append(source.dataset_filter)
    if preferred_selector:
        safe = preferred_selector.replace('"', "")
        where_parts.append(
            f'{source.entity_field} = "{safe}"'
        )
    where_clause = (
        " where " + " and ".join(where_parts)
        if where_parts
        else ""
    )
    script = (
        f"select top 1 {source.entity_field}, {source.date_field} "
        f'from loadTable("{source.database_uri}", `{source.table_name})'
        f"{where_clause} "
        f"order by {source.date_field} desc"
    )
    rows = _records_from_result(adapter.run_readonly_query(script))
    if not rows and preferred_selector:
        return _sample_selector(adapter, source, None)
    if not rows:
        raise DataContractError(
            f"{source.dataset_id}没有可用于真实验收的来源记录。"
        )
    selector = str(rows[0][source.entity_field]).strip()
    if not selector:
        raise DataContractError(
            f"{source.dataset_id}抽样实体为空。"
        )
    return selector, _as_date(rows[0][source.date_field])


def _build_query(
    *,
    dataset_id: str,
    canonical_object: str,
    selector_mode: str,
    selector: str,
    sample_date: date,
    as_of_date: date,
    usage: StandardDataUsage,
    manual_decision_time: datetime,
) -> StandardDataQuery:
    return StandardDataQuery(
        dataset_id=dataset_id,
        canonical_object=canonical_object,
        instrument_ids=(
            (selector,)
            if selector_mode == INSTRUMENT_SELECTOR_MODE
            else ()
        ),
        entity_ids=(
            (selector,)
            if selector_mode == ENTITY_SELECTOR_MODE
            else ()
        ),
        start_date=sample_date,
        end_date=sample_date,
        as_of_date=as_of_date,
        usage=usage,
        decision_time=(
            manual_decision_time
            if usage is StandardDataUsage.MANUAL_DECISION_SUPPORT
            else None
        ),
        include_source_extensions=True,
        include_quality_flags=True,
        include_lineage=True,
        limit_per_instrument=10,
    )


def _register_services(
    *,
    adapter: DolphinDBDataSourceAdapter,
    root: Path,
) -> tuple[
    StandardDataService,
    dict[str, SampleSource],
]:
    standard = StandardDataService()
    sample_sources: dict[str, SampleSource] = {}

    daily_k = DolphinDBDailyKStandardizedService.from_registry_file(
        adapter,
        root / "configs/datasets/a_stock_daily_k.json",
    )
    standard.register_provider(
        DailyKStandardDataProvider(daily_k)
    )
    sample_sources[daily_k.registration.dataset_id] = SampleSource(
        dataset_id=daily_k.registration.dataset_id,
        database_uri=daily_k.database_uri,
        table_name=daily_k.table_name,
        entity_field=daily_k.entity_field,
        date_field=daily_k.date_field,
    )

    fundamental = (
        DolphinDBFundamentalStandardizedService.from_registry_file(
            adapter,
            root
            / "configs/datasets/a_stock_fundamental_snapshot.json",
            allow_disabled_for_acceptance=True,
        )
    )
    standard.register_provider(
        FundamentalStandardDataProvider(fundamental)
    )
    sample_sources[
        fundamental.registration.dataset_id
    ] = SampleSource(
        dataset_id=fundamental.registration.dataset_id,
        database_uri=fundamental.database_uri,
        table_name=fundamental.table_name,
        entity_field=fundamental.registration.entity_field or "stock_code",
        date_field=fundamental.registration.date_field or "snapshot_date",
    )

    daily_funds = DolphinDBDailyFundsCanonicalService(
        adapter,
        project_root=root,
    )
    register_daily_funds_standard_providers(
        standard,
        daily_funds,
        project_root=root,
    )
    for descriptor in standard.list_datasets():
        if descriptor.dataset_id in sample_sources:
            continue
        profile = daily_funds.dataset_profile(
            descriptor.dataset_id
        )
        sample_sources[descriptor.dataset_id] = SampleSource(
            dataset_id=descriptor.dataset_id,
            database_uri=daily_funds.database_uri,
            table_name=str(profile["source_table"]),
            entity_field=str(profile["raw_entity_field"]),
            date_field="snapshot_date",
            dataset_filter=(
                f"dataset_id=`{descriptor.dataset_id}"
            ),
        )

    return standard, sample_sources


def _build_gated_service(
    *,
    root: Path,
    standard: StandardDataService,
    plan: Mapping[str, Any],
) -> ReadinessGatedStandardDataService:
    policy = load_data_readiness_policy(
        root / str(plan["readiness_policy"])
    )
    rules = load_evidence_rule_config(
        root / str(plan["evidence_rules"])
    )
    resolver = ReportBackedEvidenceResolver.from_project(
        project_root=root,
        config_path=str(plan["external_evidence_config"]),
    )
    builder = ExternalEvidenceOverlayBuilder(
        base_rules=rules,
        resolver=resolver,
    )
    readiness = StandardQueryReadinessService(
        DataReadinessEngine(policy),
        builder,
    )
    return ReadinessGatedStandardDataService(
        standard,
        readiness,
    )


def _evidence_summary(snapshot: Any) -> dict[str, Any]:
    return {
        item.dimension.value: {
            "status": item.status.value,
            "code": item.code,
            "message": item.message,
            "metrics": item.metrics,
            "evidence_refs": list(item.evidence_refs),
        }
        for item in snapshot.evidence
    }


def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# TASK_018D 九个数据集真实端到端就绪度门禁验收",
        "",
        f"- 状态：**{report['overall_status']}**",
        f"- Provider：{report['provider_count']}",
        f"- 数据集：{report['dataset_count']}",
        f"- 用途：{report['usage_count']}",
        f"- 真实门禁评估：{report['assessment_count']}",
        f"- 当前研究可用：{report['current_research_usable_count']}",
        f"- 人工决策阻断：{report['manual_decision_block_count']}",
        f"- 严格历史回测阻断：{report['strict_historical_block_count']}",
        f"- 历史模型训练阻断：{report['historical_training_block_count']}",
        "- 数据库写操作：0",
        "",
        "| 数据集 | 用途 | Provider状态 | 就绪度决策 | 阻断 | 记录数 |",
        "|---|---|---|---|---:|---:|",
    ]
    for item in report["assessments"]:
        lines.append(
            "| {dataset_id} | {usage} | {provider_status} | "
            "{readiness_status} | {blocks_downstream} | "
            "{result_count} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- 当前快照研究必须通过统一门禁，但允许保留WARNING。",
            "- 人工辅助决策当前全部阻断，因为尚未激活。",
            "- 基本面和七类快照的严格历史用途由启用、覆盖、时点或语义证据阻断。",
            "- 日K是否通过严格历史用途，以真实八维证据结果为准。",
            "- 本验收仅执行只读查询，不修改DolphinDB。",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--plan",
        default=(
            "configs/quality/"
            "task_018d_acceptance_plan_v0.json"
        ),
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_path = Path(args.plan)
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    plan = _load_json(plan_path)
    if str(plan.get("contract_version")) != PLAN_VERSION:
        raise DataContractError("TASK_018D验收计划版本不兼容。")

    as_of_date = date.fromisoformat(str(plan["as_of_date"]))
    manual_decision_time = datetime.fromisoformat(
        str(plan["manual_decision_time"])
    )
    if manual_decision_time.tzinfo is None:
        raise DataContractError(
            "manual_decision_time必须携带时区。"
        )
    usages = tuple(
        StandardDataUsage(value)
        for value in plan["usages"]
    )

    adapter = DolphinDBDataSourceAdapter(
        DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=_password(),
        ),
        source_id="task_018d_real_readiness_acceptance",
    )
    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        raise DataContractError(
            health.description or "DolphinDB健康检查失败。"
        )

    standard, sample_sources = _register_services(
        adapter=adapter,
        root=root,
    )
    gated = _build_gated_service(
        root=root,
        standard=standard,
        plan=plan,
    )

    descriptors = {
        item.dataset_id: item
        for item in standard.list_datasets()
    }
    if len(descriptors) != 9:
        raise DataContractError(
            f"预期9个Provider，实际{len(descriptors)}个。"
        )

    assessments: list[dict[str, Any]] = []
    samples: dict[str, dict[str, str]] = {}
    for dataset in plan["datasets"]:
        dataset_id = str(dataset["dataset_id"])
        canonical_object = str(dataset["canonical_object"])
        descriptor = descriptors.get(dataset_id)
        if descriptor is None:
            raise DataContractError(
                f"验收计划数据集未注册Provider：{dataset_id}"
            )
        if canonical_object not in descriptor.supported_objects:
            raise DataContractError(
                f"{dataset_id}不支持{canonical_object}。"
            )
        selector, sample_date = _sample_selector(
            adapter,
            sample_sources[dataset_id],
            (
                str(dataset["preferred_selector"])
                if dataset.get("preferred_selector")
                else None
            ),
        )
        samples[dataset_id] = {
            "selector_mode": descriptor.selector_mode,
            "selector": selector,
            "sample_date": sample_date.isoformat(),
            "canonical_object": canonical_object,
        }

        for usage in usages:
            request = _build_query(
                dataset_id=dataset_id,
                canonical_object=canonical_object,
                selector_mode=descriptor.selector_mode,
                selector=selector,
                sample_date=sample_date,
                as_of_date=as_of_date,
                usage=usage,
                manual_decision_time=manual_decision_time,
            )
            gated_result = gated.query(request)
            snapshot = gated_result.readiness_snapshot
            evidence = _evidence_summary(snapshot)
            usable = not gated_result.blocks_downstream
            try:
                gated_result.assert_usable()
            except DataContractError:
                assert_failed = True
            else:
                assert_failed = False
            if usable == assert_failed:
                raise DataContractError(
                    f"{dataset_id}/{usage.value}"
                    "的blocks_downstream与assert_usable不一致。"
                )

            assessments.append(
                {
                    "dataset_id": dataset_id,
                    "provider_id": descriptor.provider_id,
                    "selector_mode": descriptor.selector_mode,
                    "selector": selector,
                    "sample_date": sample_date.isoformat(),
                    "canonical_object": canonical_object,
                    "usage": usage.value,
                    "query_id": (
                        gated_result.standard_result.metadata.query_id
                    ),
                    "provider_status": (
                        gated_result.standard_result.metadata.status.value
                    ),
                    "provider_blocks_downstream": (
                        gated_result.standard_result.metadata.blocks_downstream
                    ),
                    "result_count": (
                        gated_result.standard_result.metadata.result_count
                    ),
                    "lineage_item_count": (
                        gated_result.standard_result.metadata.lineage_item_count
                    ),
                    "readiness_status": snapshot.decision.status.value,
                    "blocks_downstream": gated_result.blocks_downstream,
                    "blocking_reasons": list(
                        snapshot.decision.blocking_reasons
                    ),
                    "warnings": list(snapshot.decision.warnings),
                    "evidence": evidence,
                }
            )

    def rows(usage: StandardDataUsage) -> list[dict[str, Any]]:
        return [
            item
            for item in assessments
            if item["usage"] == usage.value
        ]

    current_rows = rows(
        StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
    )
    manual_rows = rows(
        StandardDataUsage.MANUAL_DECISION_SUPPORT
    )
    strict_rows = rows(
        StandardDataUsage.STRICT_HISTORICAL_BACKTEST
    )
    training_rows = rows(
        StandardDataUsage.HISTORICAL_MODEL_TRAINING
    )

    current_usable = sum(
        not item["blocks_downstream"]
        for item in current_rows
    )
    manual_blocks = sum(
        item["blocks_downstream"]
        for item in manual_rows
    )
    strict_blocks = sum(
        item["blocks_downstream"]
        for item in strict_rows
    )
    training_blocks = sum(
        item["blocks_downstream"]
        for item in training_rows
    )
    strict_activation_failed = sum(
        item["evidence"]["ACTIVATION"]["status"] == "FAILED"
        for item in strict_rows
    )
    training_activation_failed = sum(
        item["evidence"]["ACTIVATION"]["status"] == "FAILED"
        for item in training_rows
    )

    invariants = plan["acceptance_invariants"]
    issues: list[str] = []
    checks = (
        (
            len(descriptors) == int(invariants["provider_count"]),
            "provider_count",
        ),
        (
            len(plan["datasets"]) == 9,
            "dataset_count",
        ),
        (
            len(usages) == int(invariants["usage_count"]),
            "usage_count",
        ),
        (
            len(assessments)
            == int(invariants["assessment_count"]),
            "assessment_count",
        ),
        (
            all(
                len(item["evidence"])
                == int(
                    invariants[
                        "evidence_dimension_count_per_assessment"
                    ]
                )
                for item in assessments
            ),
            "evidence_dimension_count",
        ),
        (
            current_usable
            == int(invariants["current_research_usable_count"]),
            "current_research_usable_count",
        ),
        (
            manual_blocks
            == int(invariants["manual_decision_block_count"]),
            "manual_decision_block_count",
        ),
        (
            strict_blocks
            >= int(invariants["historical_minimum_block_count"]),
            "strict_historical_block_count",
        ),
        (
            training_blocks
            >= int(invariants["historical_minimum_block_count"]),
            "historical_training_block_count",
        ),
        (
            strict_activation_failed
            == int(
                invariants["historical_activation_failed_count"]
            ),
            "strict_activation_failed_count",
        ),
        (
            training_activation_failed
            == int(
                invariants["historical_activation_failed_count"]
            ),
            "training_activation_failed_count",
        ),
    )
    for passed, name in checks:
        if not passed:
            issues.append(name)

    report = {
        "task_id": "TASK_018D",
        "mode": str(plan["mode"]),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of_date": as_of_date.isoformat(),
        "provider_count": len(descriptors),
        "dataset_count": len(plan["datasets"]),
        "usage_count": len(usages),
        "assessment_count": len(assessments),
        "evidence_dimension_count": len(ReadinessDimension),
        "current_research_usable_count": current_usable,
        "current_research_warning_count": sum(
            item["readiness_status"] == "WARNING"
            for item in current_rows
        ),
        "manual_decision_block_count": manual_blocks,
        "strict_historical_block_count": strict_blocks,
        "historical_training_block_count": training_blocks,
        "strict_activation_failed_count": (
            strict_activation_failed
        ),
        "training_activation_failed_count": (
            training_activation_failed
        ),
        "database_connection_attempted": True,
        "database_readonly_query_mode": True,
        "write_operation_count": 0,
        "samples": samples,
        "assessments": assessments,
        "issues": issues,
        "overall_status": (
            "PASSED_WITH_WARNINGS"
            if not issues
            else "FAILED"
        ),
    }

    json_path = (
        output_dir
        / "task_018d_real_readiness_gate_acceptance.json"
    )
    md_path = (
        output_dir
        / "task_018d_real_readiness_gate_acceptance.md"
    )
    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    md_path.write_text(
        _markdown(report),
        encoding="utf-8",
    )
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
