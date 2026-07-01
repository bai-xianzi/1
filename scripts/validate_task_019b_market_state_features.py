# 本脚本核心功能：验证任务019b市场状态特征的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
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


# 类 `Gated`：集中封装Gated相关状态和行为。
# - 输入：构造参数、类属性以及基类 `object` 提供的公共能力。
# - 处理：把相关数据、约束和操作聚合在同一对象边界内。
# - 输出：向调用方提供稳定的属性、方法和可测试行为。
# - 为什么这样写：集中管理同一职责，避免脚本流程中出现分散状态和重复约束。
class Gated:
    # 函数 `__init__`：完成init相关处理。
    # - 输入：self、result。
    # - 处理：完成init相关处理，并按现有异常和门禁规则保留失败证据。
    # - 输出：不要求业务返回值，完成校验、输出或状态更新后结束。
    # - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
    def __init__(self, result):
        self.standard_result = result
        self.readiness_snapshot = SimpleNamespace(
            decision=SimpleNamespace(
                status=SimpleNamespace(value="WARNING"),
                warnings=("OFFLINE_VALIDATION_WARNING",),
            )
        )

    # 函数 `assert_usable`：完成assertusable相关处理。
    # - 输入：self。
    # - 处理：完成assertusable相关处理，并按现有异常和门禁规则保留失败证据。
    # - 输出：返回本步骤生成的对象、集合或状态值。
    # - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
    def assert_usable(self):
        # 输出结果：返回 `None` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return None


# 函数 `require`：完成强制校验相关处理。
# - 输入：condition、message。
# - 处理：完成强制校验相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def require(condition: bool, message: str) -> None:
    # 条件分支：检查 `not condition` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not condition:
        # 失败门禁：抛出 `RuntimeError(message)`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise RuntimeError(message)


# 函数 `record`：完成record相关处理。
# - 输入：object_name、key、values。
# - 处理：完成record相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回本步骤生成的对象、集合或状态值。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def record(object_name, key, values):
    # 输出结果：返回 `StandardDataRecord(canonical_object=object_name, primary_key=key, values=values)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return StandardDataRecord(
        canonical_object=object_name,
        primary_key=key,
        values=values,
    )


# 函数 `gated`：完成gated相关处理。
# - 输入：dataset_id、object_name、records、query_id、entity。
# - 处理：完成gated相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回本步骤生成的对象、集合或状态值。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 输出结果：返回 `Gated(StandardQueryResult(query=query, metadata=metadata, records=tuple(records)))` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return Gated(StandardQueryResult(
        query=query,
        metadata=metadata,
        records=tuple(records),
    ))


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
