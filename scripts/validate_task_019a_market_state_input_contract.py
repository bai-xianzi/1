# 本脚本核心功能：验证任务019a市场状态输入合同的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
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
