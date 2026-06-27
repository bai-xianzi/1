"""TASK_019C：真实DolphinDB只读市场状态特征验收。"""
from __future__ import annotations

import argparse
import getpass
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.market_state_features import (
    ExplainableMarketStateFeatureCalculator,
    load_market_state_feature_spec,
)
from a_stock_quant.market_state_inputs import (
    MarketStateInputContractEngine,
    load_market_state_input_contract,
)
from a_stock_quant.market_state_real_acceptance import (
    ReadonlySourceDescriptor,
    assert_readonly_query,
    build_date_presence_query,
    build_feature_acceptance_query,
    build_recent_date_rows_query,
    build_selector_rows_query,
    load_real_feature_acceptance_plan,
    report_to_json_safe,
    unique_dates_from_rows,
    unique_selectors_from_rows,
    validate_real_feature_acceptance_report,
)


def _password() -> str:
    value = os.getenv("DOLPHINDB_PASSWORD")
    if value is None:
        value = getpass.getpass("请输入 DolphinDB 密码：")
    if not value:
        raise DataContractError("DolphinDB密码不能为空。")
    return value


def _load_task_018d_helpers(root: Path) -> Any:
    path = (
        root
        / "scripts"
        / "run_task_018d_real_readiness_gate_acceptance.py"
    )
    if not path.exists():
        raise DataContractError(
            "缺少TASK_018D真实门禁验收脚本，"
            "无法复用已验收的Provider注册和就绪度装配。"
        )
    module_name = "_task_018d_readonly_helpers"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise DataContractError("无法加载TASK_018D验收脚本。")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    required = (
        "_register_services",
        "_build_gated_service",
        "_records_from_result",
    )
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise DataContractError(
            "TASK_018D验收脚本缺少复用入口："
            + ", ".join(missing)
        )
    return module


def _source_descriptor(value: Any) -> ReadonlySourceDescriptor:
    return ReadonlySourceDescriptor(
        dataset_id=str(value.dataset_id),
        database_uri=str(value.database_uri),
        table_name=str(value.table_name),
        entity_field=str(value.entity_field),
        date_field=str(value.date_field),
        dataset_filter=(
            str(value.dataset_filter)
            if value.dataset_filter is not None
            else None
        ),
    )


def _run_rows(
    adapter: DolphinDBDataSourceAdapter,
    helpers: Any,
    script: str,
) -> list[dict[str, Any]]:
    assert_readonly_query(script)
    result = adapter.run_readonly_query(script)
    return helpers._records_from_result(result)


def _find_latest_common_date(
    *,
    adapter: DolphinDBDataSourceAdapter,
    helpers: Any,
    candidate_source: ReadonlySourceDescriptor,
    daily_source: ReadonlySourceDescriptor,
    row_scan_limit: int,
    maximum_candidates: int,
) -> tuple[Any, int]:
    rows = _run_rows(
        adapter,
        helpers,
        build_recent_date_rows_query(
            candidate_source,
            row_scan_limit,
        ),
    )
    candidates = unique_dates_from_rows(
        rows,
        candidate_source.date_field,
        maximum_candidates,
    )
    if not candidates:
        raise DataContractError("hy来源没有可用交易日期候选。")
    checked = 0
    for candidate in candidates:
        checked += 1
        presence_rows = _run_rows(
            adapter,
            helpers,
            build_date_presence_query(
                daily_source,
                candidate,
            ),
        )
        if presence_rows:
            return candidate, checked
    raise DataContractError(
        "在配置的候选日期范围内没有找到日K与hy共同交易日。"
    )


def _selectors(
    *,
    adapter: DolphinDBDataSourceAdapter,
    helpers: Any,
    source: ReadonlySourceDescriptor,
    target_date: Any,
    limit: int,
) -> tuple[str, ...]:
    rows = _run_rows(
        adapter,
        helpers,
        build_selector_rows_query(
            source,
            target_date,
            limit,
        ),
    )
    selectors = unique_selectors_from_rows(
        rows,
        source.entity_field,
        limit,
    )
    if not selectors:
        raise DataContractError(
            f"{source.dataset_id}在共同交易日没有可用选择器。"
        )
    return selectors


def _evidence_summary(gated_result: Any) -> dict[str, Any]:
    snapshot = gated_result.readiness_snapshot
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
        "# TASK_019C 真实市场状态特征验收",
        "",
        f"- 状态：**{report['overall_status']}**",
        f"- 共同交易日：{report['common_trade_date']}",
        f"- 输入状态：{report['input_assessment_status']}",
        f"- 特征状态：{report['feature_snapshot_status']}",
        f"- 真实特征：{report['generated_feature_count']}",
        f"- 数据库只读：{report['database_readonly_query_mode']}",
        f"- 数据库写操作：{report['write_operation_count']}",
        "",
        "## 查询范围",
        "",
        f"- 范围：`{report['universe_scope']}`",
        "- 本验收不声明全市场全集覆盖。",
        "",
        "| 数据集 | 选择器 | 返回记录 | Provider状态 | 就绪度 | 阻断 |",
        "|---|---:|---:|---|---|---:|",
    ]
    for item in report["query_summaries"]:
        lines.append(
            "| {dataset_id} | {selector_count} | {result_count} | "
            "{provider_status} | {readiness_status} | "
            "{blocks_downstream} |".format(**item)
        )
    lines.extend(
        [
            "",
            "## 15项真实特征",
            "",
            "| 特征 | 特征族 | 数值 | 单位 | 有效观测 | 来源记录 |",
            "|---|---|---:|---|---:|---:|",
        ]
    )
    for item in report["features"]:
        lines.append(
            "| {feature_id} | {family} | {value:.8g} | {unit} | "
            "{valid_observation_count} | {source_record_count} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 仅用于研究特征验收。",
            "- 不输出牛市、熊市或震荡市标签。",
            "- 不输出仓位、选股或交易建议。",
            "- 所有WARNING和来源查询ID均保留在JSON报告中。",
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
            "configs/market_state/"
            "task_019c_real_feature_acceptance_plan_v0.json"
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
    plan = load_real_feature_acceptance_plan(plan_path)

    helpers = _load_task_018d_helpers(root)
    adapter = DolphinDBDataSourceAdapter(
        DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=_password(),
        ),
        source_id="task_019c_real_market_state_feature_acceptance",
    )
    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        raise DataContractError(
            health.description or "DolphinDB健康检查失败。"
        )

    standard, source_objects = helpers._register_services(
        adapter=adapter,
        root=root,
    )
    gated = helpers._build_gated_service(
        root=root,
        standard=standard,
        plan={
            "readiness_policy": plan.readiness_policy,
            "evidence_rules": plan.evidence_rules,
            "external_evidence_config": (
                plan.external_evidence_config
            ),
        },
    )

    descriptors = {
        item.dataset_id: item
        for item in standard.list_datasets()
    }
    for dataset_plan in plan.required_datasets:
        descriptor = descriptors.get(dataset_plan.dataset_id)
        if descriptor is None:
            raise DataContractError(
                f"未注册Provider：{dataset_plan.dataset_id}"
            )
        if (
            dataset_plan.canonical_object
            not in descriptor.supported_objects
        ):
            raise DataContractError(
                f"{dataset_plan.dataset_id}不支持"
                f"{dataset_plan.canonical_object}。"
            )
        if descriptor.selector_mode != dataset_plan.selector_mode:
            raise DataContractError(
                f"{dataset_plan.dataset_id}选择器模式不一致。"
            )

    sources = {
        dataset_id: _source_descriptor(value)
        for dataset_id, value in source_objects.items()
    }
    daily_source = sources["a_stock_daily_k"]
    hy_source = sources["hy"]

    common_date, checked_candidate_count = (
        _find_latest_common_date(
            adapter=adapter,
            helpers=helpers,
            candidate_source=hy_source,
            daily_source=daily_source,
            row_scan_limit=plan.candidate_date_row_scan_limit,
            maximum_candidates=(
                plan.maximum_candidate_dates_to_check
            ),
        )
    )

    selectors_by_dataset = {
        dataset_plan.dataset_id: _selectors(
            adapter=adapter,
            helpers=helpers,
            source=sources[dataset_plan.dataset_id],
            target_date=common_date,
            limit=dataset_plan.selector_limit,
        )
        for dataset_plan in plan.required_datasets
    }

    gated_results: dict[str, Any] = {}
    query_summaries: list[dict[str, Any]] = []
    for dataset_plan in plan.required_datasets:
        selectors = selectors_by_dataset[dataset_plan.dataset_id]
        request = build_feature_acceptance_query(
            dataset_plan,
            selectors,
            common_date,
            plan.as_of_date,
        )
        gated_result = gated.query(request)
        gated_result.assert_usable()
        gated_results[dataset_plan.dataset_id] = gated_result

        standard_result = gated_result.standard_result
        snapshot = gated_result.readiness_snapshot
        query_summaries.append(
            {
                "dataset_id": dataset_plan.dataset_id,
                "canonical_object": (
                    dataset_plan.canonical_object
                ),
                "selector_mode": dataset_plan.selector_mode,
                "selector_count": len(selectors),
                "selectors": list(selectors),
                "query_id": (
                    standard_result.metadata.query_id
                ),
                "provider_id": (
                    standard_result.metadata.provider_id
                ),
                "provider_status": (
                    standard_result.metadata.status.value
                ),
                "provider_warnings": list(
                    standard_result.metadata.warnings
                ),
                "result_count": (
                    standard_result.metadata.result_count
                ),
                "lineage_item_count": (
                    standard_result.metadata.lineage_item_count
                ),
                "readiness_status": (
                    snapshot.decision.status.value
                ),
                "readiness_warnings": list(
                    snapshot.decision.warnings
                ),
                "blocks_downstream": (
                    gated_result.blocks_downstream
                ),
                "evidence": _evidence_summary(gated_result),
            }
        )

    input_contract = load_market_state_input_contract(
        root / plan.market_state_input_contract
    )
    feature_spec = load_market_state_feature_spec(
        root / plan.market_state_feature_spec
    )
    input_engine = MarketStateInputContractEngine(input_contract)
    input_assessment = input_engine.evaluate(gated_results)
    input_assessment.assert_research_usable()

    calculator = ExplainableMarketStateFeatureCalculator(
        input_engine,
        feature_spec,
    )
    feature_snapshot = calculator.calculate(gated_results)
    feature_snapshot.assert_research_usable()

    feature_rows = [
        item
        for item in feature_snapshot.to_dict()["features"]
    ]
    source_query_ids = {
        query_id
        for item in feature_rows
        for query_id in item["source_query_ids"]
    }
    feature_families = {
        item["family"]
        for item in feature_rows
    }
    all_warnings = list(input_assessment.warnings)
    all_warnings.extend(feature_snapshot.warnings)
    for item in feature_rows:
        all_warnings.extend(item.get("warnings", []))
    all_warnings = list(dict.fromkeys(all_warnings))

    report: dict[str, Any] = {
        "task_id": plan.task_id,
        "mode": plan.mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": (
            "PASSED_WITH_WARNINGS"
            if all_warnings
            or feature_snapshot.status.value
            == "READY_WITH_WARNINGS"
            else "PASSED"
        ),
        "as_of_date": plan.as_of_date.isoformat(),
        "common_trade_date": common_date.isoformat(),
        "candidate_dates_checked": checked_candidate_count,
        "required_dataset_count": len(plan.required_datasets),
        "required_feature_family_count": len(
            feature_spec.required_feature_families
        ),
        "feature_definition_count": len(
            feature_spec.feature_definitions
        ),
        "generated_feature_count": len(feature_rows),
        "generated_feature_family_count": len(feature_families),
        "unique_source_query_id_count": len(source_query_ids),
        "source_query_ids": sorted(source_query_ids),
        "input_assessment_status": (
            input_assessment.status.value
        ),
        "feature_snapshot_status": (
            feature_snapshot.status.value
        ),
        "research_feature_build_allowed": (
            feature_snapshot.research_feature_build_allowed
        ),
        "manual_decision_allowed": (
            feature_snapshot.manual_decision_allowed
        ),
        "official_market_state_allowed": (
            feature_snapshot.official_market_state_allowed
        ),
        "regime_label": feature_snapshot.regime_label,
        "universe_scope": plan.universe_scope,
        "claim_full_market_coverage": (
            plan.claim_full_market_coverage
        ),
        "query_summaries": query_summaries,
        "features": feature_rows,
        "warnings": all_warnings,
        "database_connection_attempted": True,
        "database_readonly_query_mode": True,
        "write_operation_count": 0,
        "issues": [],
    }
    issues = validate_real_feature_acceptance_report(report, plan)
    report["issues"] = list(issues)
    if issues:
        report["overall_status"] = "FAILED"

    json_path = (
        output_dir
        / "task_019c_real_market_state_feature_acceptance.json"
    )
    md_path = (
        output_dir
        / "task_019c_real_market_state_feature_acceptance.md"
    )
    json_path.write_text(
        json.dumps(
            report_to_json_safe(report),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        _markdown(report),
        encoding="utf-8",
    )

    print(json.dumps({
        "task_id": report["task_id"],
        "overall_status": report["overall_status"],
        "common_trade_date": report["common_trade_date"],
        "daily_result_count": next(
            item["result_count"]
            for item in query_summaries
            if item["dataset_id"] == "a_stock_daily_k"
        ),
        "industry_result_count": next(
            item["result_count"]
            for item in query_summaries
            if item["dataset_id"] == "hy"
        ),
        "generated_feature_count": (
            report["generated_feature_count"]
        ),
        "input_assessment_status": (
            report["input_assessment_status"]
        ),
        "feature_snapshot_status": (
            report["feature_snapshot_status"]
        ),
        "warning_count": len(report["warnings"]),
        "database_readonly_query_mode": True,
        "write_operation_count": 0,
        "issues": report["issues"],
        "json_report": str(json_path),
        "markdown_report": str(md_path),
    }, ensure_ascii=False, indent=2))

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
