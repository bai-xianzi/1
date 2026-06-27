from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.market_state_inputs import (
    MarketStateFeatureFamily,
    MarketStateInputContractEngine,
    load_market_state_input_contract,
)
from a_stock_quant.standard_data_service import StandardDataUsage


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    config_path = (
        root
        / "configs"
        / "market_state"
        / "market_state_input_contract_v0.json"
    )
    contract = load_market_state_input_contract(config_path)
    engine = MarketStateInputContractEngine(contract)

    require(contract.task_id == "TASK_019A", "task_id异常")
    require(contract.contract_version == "0.1.0", "合同版本异常")
    require(
        contract.allowed_usage
        is StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        "用途必须为CURRENT_SNAPSHOT_RESEARCH",
    )
    require(len(contract.dataset_requirements) == 9, "数据集必须为9个")
    required_ids = {
        item.dataset_id
        for item in contract.dataset_requirements
        if item.required
    }
    require(
        required_ids == {"a_stock_daily_k", "hy"},
        "必需数据集必须是日K和行业快照",
    )
    require(not contract.manual_decision_allowed, "不得启用人工决策")
    require(
        not contract.official_market_state_allowed,
        "不得启用正式市场状态",
    )
    require(
        set(contract.required_feature_families)
        == {
            MarketStateFeatureFamily.TREND,
            MarketStateFeatureFamily.BREADTH,
            MarketStateFeatureFamily.LIQUIDITY,
            MarketStateFeatureFamily.VOLATILITY,
            MarketStateFeatureFamily.SECTOR_DIFFUSION,
        },
        "必需特征族异常",
    )

    empty_assessment = engine.evaluate({})
    require(empty_assessment.blocks_downstream, "空输入必须阻断")
    require(
        set(empty_assessment.missing_required_datasets)
        == {"a_stock_daily_k", "hy"},
        "空输入缺失数据集异常",
    )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    field_count = sum(
        len(item["required_fields"])
        for item in raw["dataset_requirements"]
    )
    output = {
        "task_id": contract.task_id,
        "overall_status": "PASSED",
        "contract_version": contract.contract_version,
        "dataset_count": len(contract.dataset_requirements),
        "required_dataset_count": len(required_ids),
        "optional_or_context_dataset_count": (
            len(contract.dataset_requirements) - len(required_ids)
        ),
        "required_feature_family_count": len(
            contract.required_feature_families
        ),
        "registered_field_reference_count": field_count,
        "allowed_usage": contract.allowed_usage.value,
        "output_scope": contract.output_scope,
        "manual_decision_allowed": contract.manual_decision_allowed,
        "official_market_state_allowed": (
            contract.official_market_state_allowed
        ),
        "empty_input_blocks_downstream": (
            empty_assessment.blocks_downstream
        ),
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
