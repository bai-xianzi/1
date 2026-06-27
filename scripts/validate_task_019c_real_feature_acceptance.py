from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from a_stock_quant.market_state_features import (
    load_market_state_feature_spec,
)
from a_stock_quant.market_state_inputs import (
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
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    plan = load_real_feature_acceptance_plan(
        root
        / "configs"
        / "market_state"
        / "task_019c_real_feature_acceptance_plan_v0.json"
    )
    input_contract = load_market_state_input_contract(
        root / plan.market_state_input_contract
    )
    feature_spec = load_market_state_feature_spec(
        root / plan.market_state_feature_spec
    )

    require(
        input_contract.contract_version
        == feature_spec.input_contract_version,
        "输入合同与特征规范版本不一致",
    )
    require(
        len(feature_spec.feature_definitions) == 15,
        "特征定义数量异常",
    )
    require(
        len(feature_spec.required_feature_families) == 5,
        "必需特征族数量异常",
    )
    require(
        set(plan.required_datasets[i].dataset_id for i in range(2))
        == {"a_stock_daily_k", "hy"},
        "必需数据集异常",
    )

    daily_source = ReadonlySourceDescriptor(
        dataset_id="a_stock_daily_k",
        database_uri="dfs://A_STOCK_DAILY_K_DB",
        table_name="stock_daily_k",
        entity_field="stock_code",
        date_field="trade_date",
    )
    hy_source = ReadonlySourceDescriptor(
        dataset_id="hy",
        database_uri="dfs://A_STOCK_DAILY_FUNDS_DB",
        table_name="classification_snapshot",
        entity_field="node_name",
        date_field="snapshot_date",
        dataset_filter="dataset_id=`hy",
    )
    scripts = (
        build_recent_date_rows_query(
            hy_source,
            plan.candidate_date_row_scan_limit,
        ),
        build_date_presence_query(
            daily_source,
            date(2025, 12, 31),
        ),
        build_selector_rows_query(
            daily_source,
            date(2025, 12, 31),
            plan.dataset("a_stock_daily_k").selector_limit,
        ),
        build_selector_rows_query(
            hy_source,
            date(2025, 12, 31),
            plan.dataset("hy").selector_limit,
        ),
    )
    for script in scripts:
        assert_readonly_query(script)

    daily_query = build_feature_acceptance_query(
        plan.dataset("a_stock_daily_k"),
        ("000001", "000002", "000003"),
        date(2025, 12, 31),
        plan.as_of_date,
    )
    hy_query = build_feature_acceptance_query(
        plan.dataset("hy"),
        ("industry-a", "industry-b"),
        date(2025, 12, 31),
        plan.as_of_date,
    )

    output = {
        "task_id": plan.task_id,
        "overall_status": "PASSED",
        "plan_version": plan.contract_version,
        "mode": plan.mode,
        "required_dataset_count": len(plan.required_datasets),
        "required_feature_family_count": len(
            feature_spec.required_feature_families
        ),
        "feature_definition_count": len(
            feature_spec.feature_definitions
        ),
        "date_alignment_policy": plan.common_date_policy,
        "universe_scope": plan.universe_scope,
        "claim_full_market_coverage": (
            plan.claim_full_market_coverage
        ),
        "daily_selector_limit": (
            plan.dataset("a_stock_daily_k").selector_limit
        ),
        "industry_selector_limit": plan.dataset("hy").selector_limit,
        "daily_query_usage": daily_query.usage.value,
        "industry_query_usage": hy_query.usage.value,
        "readonly_script_count": len(scripts),
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
