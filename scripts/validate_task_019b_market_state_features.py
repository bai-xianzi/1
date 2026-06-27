from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from a_stock_quant.data_contracts import QualityStatus
from a_stock_quant.market_state_features import (
    ExplainableMarketStateFeatureCalculator,
    load_market_state_feature_spec,
)
from a_stock_quant.market_state_inputs import (
    MarketStateInputContractEngine,
    load_market_state_input_contract,
)
from a_stock_quant.standard_data_service import (
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryMetadata,
    StandardQueryResult,
)


class Gated:
    def __init__(self, result):
        self.standard_result = result
        self.readiness_snapshot = SimpleNamespace(
            decision=SimpleNamespace(
                status=SimpleNamespace(value="WARNING"),
                warnings=("OFFLINE_VALIDATION_WARNING",),
            )
        )

    def assert_usable(self):
        return None


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def record(object_name, key, values):
    return StandardDataRecord(
        canonical_object=object_name,
        primary_key=key,
        values=values,
    )


def gated(dataset_id, object_name, records, query_id, entity=False):
    day = date(2025, 12, 31)
    query = StandardDataQuery(
        dataset_id=dataset_id,
        canonical_object=object_name,
        instrument_ids=() if entity else ("a", "b", "c"),
        entity_ids=("x", "y") if entity else (),
        start_date=day,
        end_date=day,
        usage=StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
    )
    metadata = StandardQueryMetadata(
        dataset_id=dataset_id,
        canonical_object=object_name,
        provider_id=f"{dataset_id}-provider",
        coverage_version="offline",
        mapping_version="offline",
        dictionary_revision="offline",
        source_row_count=len(records),
        result_count=len(records),
        status=QualityStatus.WARNING,
        blocks_downstream=False,
        warnings=("OFFLINE_SOURCE_WARNING",),
        query_id=query_id,
    )
    return Gated(StandardQueryResult(
        query=query,
        metadata=metadata,
        records=tuple(records),
    ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    input_contract = load_market_state_input_contract(
        root
        / "configs"
        / "market_state"
        / "market_state_input_contract_v0.json"
    )
    spec = load_market_state_feature_spec(
        root
        / "configs"
        / "market_state"
        / "market_state_feature_spec_v0.json"
    )
    calculator = ExplainableMarketStateFeatureCalculator(
        MarketStateInputContractEngine(input_contract),
        spec,
    )

    day = date(2025, 12, 31)
    daily = [
        record("DailyBar", {"instrument_id": code, "trade_date": day}, {
            "trade_date": day,
            "pct_change_pct": pct,
            "amount_cny": amount,
            "turnover_rate_pct": turnover,
            "high_raw_cny": close * 1.05,
            "low_raw_cny": close * 0.95,
            "close_raw_cny": close,
        })
        for code, pct, amount, turnover, close in (
            ("a", -1.0, 100.0, 1.0, 10.0),
            ("b", 2.0, 200.0, 2.0, 20.0),
            ("c", 3.0, 300.0, 3.0, 30.0),
        )
    ]
    industry = [
        record(
            "ClassificationMarketSnapshot",
            {"node_id": node, "trade_date": day},
            {
                "trade_date": day,
                "pct_change_pct": pct,
                "up_count": up,
                "down_count": down,
                "limit_up_count": limit_up,
                "breadth_ratio": breadth,
                "average_return_pct": average_return,
                "amount_cny": 100.0,
            },
        )
        for node, pct, up, down, limit_up, breadth, average_return in (
            ("x", 1.0, 60, 40, 3, 1.5, 0.8),
            ("y", -0.5, 30, 70, 1, 0.6, -0.2),
        )
    ]
    snapshot = calculator.calculate({
        "a_stock_daily_k": gated(
            "a_stock_daily_k",
            "DailyBar",
            daily,
            "daily-offline",
        ),
        "hy": gated(
            "hy",
            "ClassificationMarketSnapshot",
            industry,
            "hy-offline",
            entity=True,
        ),
    })

    require(spec.task_id == "TASK_019B", "task_id异常")
    require(spec.spec_version == "0.1.0", "spec_version异常")
    require(len(spec.feature_definitions) == 15, "特征数量异常")
    require(
        snapshot.status.value == "READY_WITH_WARNINGS",
        "离线特征快照状态异常",
    )
    require(len(snapshot.features) == 15, "生成特征数量异常")
    require(snapshot.as_of_date == day, "共同交易日异常")
    require(
        not snapshot.manual_decision_allowed,
        "不得启用人工决策",
    )
    require(
        not snapshot.official_market_state_allowed,
        "不得启用正式市场状态",
    )
    require(snapshot.regime_label is None, "不得生成市场状态标签")

    output = {
        "task_id": spec.task_id,
        "overall_status": "PASSED",
        "spec_version": spec.spec_version,
        "input_contract_version": spec.input_contract_version,
        "feature_definition_count": len(spec.feature_definitions),
        "required_feature_family_count": len(
            spec.required_feature_families
        ),
        "required_source_dataset_count": len(
            spec.required_source_datasets
        ),
        "offline_generated_feature_count": len(snapshot.features),
        "offline_snapshot_status": snapshot.status.value,
        "offline_as_of_date": snapshot.as_of_date.isoformat(),
        "date_alignment_policy": spec.date_alignment_policy,
        "manual_decision_allowed": snapshot.manual_decision_allowed,
        "official_market_state_allowed": (
            snapshot.official_market_state_allowed
        ),
        "regime_label": snapshot.regime_label,
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
