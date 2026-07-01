# 本脚本核心功能：验证任务019c真实特征验收的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
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
    # 循环处理：将 `scripts` 中的元素逐项绑定到 `script`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
