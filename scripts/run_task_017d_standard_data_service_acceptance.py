"""TASK_017D 统一 StandardDataService 真实只读验收。"""
# 本脚本核心功能：执行任务017d标准化数据服务验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import argparse
import getpass
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.daily_funds_canonical_contract import REQUIRED_DATASETS
from a_stock_quant.daily_funds_standard_provider import (
    register_daily_funds_standard_providers,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DolphinDBDailyFundsCanonicalService,
    normalise_query_records,
)
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


# 函数 `_password`：完成password相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成password相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `str`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _password() -> str:
    value = os.getenv("DOLPHINDB_PASSWORD")
    # 条件分支：检查 `value is None` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if value is None:
        value = getpass.getpass("请输入 DolphinDB 密码：")
    # 条件分支：检查 `not value` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not value:
        # 失败门禁：抛出 `DataContractError('DolphinDB密码不能为空。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError("DolphinDB密码不能为空。")
    # 输出结果：返回 `value` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return value


# 函数 `_as_date`：完成asdate相关处理。
# - 输入：value。
# - 处理：完成asdate相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `date`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _as_date(value: Any) -> date:
    # 条件分支：检查 `isinstance(value, datetime)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(value, datetime):
        # 输出结果：返回 `value.date()` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return value.date()
    # 条件分支：检查 `isinstance(value, date)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(value, date):
        # 输出结果：返回 `value` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return value
    converted = getattr(value, "to_pydatetime", lambda: None)()
    # 条件分支：检查 `isinstance(converted, datetime)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(converted, datetime):
        # 输出结果：返回 `converted.date()` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return converted.date()
    # 条件分支：检查 `isinstance(converted, date)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(converted, date):
        # 输出结果：返回 `converted` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return converted
    # 输出结果：返回 `date.fromisoformat(str(value).replace('.', '-')[:10])` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return date.fromisoformat(str(value).replace(".", "-")[:10])


# 函数 `_sample_selector`：完成sampleselector相关处理。
# - 输入：adapter、service、dataset_id。
# - 处理：完成sampleselector相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `tuple[str, date]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _sample_selector(adapter: Any, service: Any, dataset_id: str) -> tuple[str, date]:
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
    # 条件分支：检查 `not rows` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not rows:
        # 失败门禁：抛出 `DataContractError(f'{dataset_id}没有可验收的Raw记录。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(f"{dataset_id}没有可验收的Raw记录。")
    # 输出结果：返回 `(str(rows[0][raw_field]).strip(), _as_date(rows[0]['snapshot_date']))` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return str(rows[0][raw_field]).strip(), _as_date(rows[0]["snapshot_date"])


# 函数 `_query`：完成查询相关处理。
# - 输入：dataset_id、selector_mode、selector、snapshot_date、canonical_object、usage。
# - 处理：完成查询相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `StandardDataQuery`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _query(dataset_id: str, selector_mode: str, selector: str, snapshot_date: date, canonical_object: str, usage: StandardDataUsage = StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH) -> StandardDataQuery:
    # 输出结果：返回 `StandardDataQuery(dataset_id=dataset_id, canonical_object=canonical_object, instrument_...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return StandardDataQuery(
        dataset_id=dataset_id,
        canonical_object=canonical_object,
        instrument_ids=(selector,) if selector_mode == INSTRUMENT_SELECTOR_MODE else (),
        entity_ids=(selector,) if selector_mode == ENTITY_SELECTOR_MODE else (),
        start_date=snapshot_date,
        end_date=snapshot_date,
        as_of_date=snapshot_date,
        usage=usage,
        include_source_extensions=True,
        include_quality_flags=True,
        include_lineage=True,
        limit_per_instrument=10,
    )


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：argv。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
        source_id="daily_funds_task_017d_acceptance",
    )
    health = adapter.health_check()
    # 条件分支：检查 `health.status is not QualityStatus.PASSED` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if health.status is not QualityStatus.PASSED:
        # 失败门禁：抛出 `DataContractError(health.description or '健康检查失败。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(health.description or "健康检查失败。")

    canonical_service = DolphinDBDailyFundsCanonicalService(
        adapter,
        project_root=root,
    )
    standard_service = StandardDataService()
    descriptors = register_daily_funds_standard_providers(
        standard_service,
        canonical_service,
        project_root=root,
    )
    # 条件分支：检查 `len(descriptors) != 7 or len(standard_service.list_datasets()) != 7` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(descriptors) != 7 or len(standard_service.list_datasets()) != 7:
        # 失败门禁：抛出 `DataContractError('七个Provider没有完整注册。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError("七个Provider没有完整注册。")

    results: list[dict[str, Any]] = []
    historical_blocks = 0
    # 循环处理：将 `REQUIRED_DATASETS` 中的元素逐项绑定到 `dataset_id`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for dataset_id in REQUIRED_DATASETS:
        descriptor = standard_service.get_provider(dataset_id).descriptor
        selector, snapshot_date = _sample_selector(
            adapter,
            canonical_service,
            dataset_id,
        )
        request = _query(
            dataset_id,
            descriptor.selector_mode,
            selector,
            snapshot_date,
            descriptor.supported_objects[0],
        )
        result = standard_service.query(request)
        # 条件分支：检查 `not result.records` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not result.records:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}统一入口没有返回记录。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(f"{dataset_id}统一入口没有返回记录。")
        # 条件分支：检查 `result.metadata.blocks_downstream` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if result.metadata.blocks_downstream:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}研究用途被意外阻断。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(f"{dataset_id}研究用途被意外阻断。")
        result.assert_usable()

        strict_result = standard_service.query(
            _query(
                dataset_id,
                descriptor.selector_mode,
                selector,
                snapshot_date,
                descriptor.supported_objects[0],
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            )
        )
        # 条件分支：检查 `not strict_result.metadata.blocks_downstream` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not strict_result.metadata.blocks_downstream:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}严格历史用途没有阻断。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(f"{dataset_id}严格历史用途没有阻断。")
        # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
        # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
        # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
        try:
            strict_result.assert_usable()
        except DataContractError:
            historical_blocks += 1
        else:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}阻断结果仍可用。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(f"{dataset_id}阻断结果仍可用。")

        record = result.records[0]
        results.append(
            {
                "dataset_id": dataset_id,
                "provider_id": descriptor.provider_id,
                "selector_mode": descriptor.selector_mode,
                "selector": selector,
                "snapshot_date": snapshot_date.isoformat(),
                "canonical_object": record.canonical_object,
                "result_count": result.metadata.result_count,
                "status": result.metadata.status.value,
                "blocks_downstream": result.metadata.blocks_downstream,
                "strict_historical_blocks": strict_result.metadata.blocks_downstream,
                "lineage_item_count": result.metadata.lineage_item_count,
                "primary_key": record.primary_key,
            }
        )

    report = {
        "task_id": "TASK_017D",
        "mode": "REAL_STANDARD_DATA_SERVICE_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_uri": canonical_service.database_uri,
        "provider_count": len(descriptors),
        "unified_query_count": len(results),
        "historical_gate_block_count": historical_blocks,
        "write_operation_count": 0,
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": results,
    }
    (output_dir / "task_017d_real_acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    lines = [
        "# TASK_017D统一标准数据入口真实验收",
        "",
        "- 状态：**PASSED_WITH_WARNINGS**",
        f"- Provider：{len(descriptors)}",
        f"- 统一查询：{len(results)}",
        f"- 严格历史门禁阻断：{historical_blocks}",
        "- 写操作：0",
        "",
        "| 来源 | 选择器 | Canonical对象 | 状态 |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {item['dataset_id']} | {item['selector_mode']} | {item['canonical_object']} | {item['status']} |"
        for item in results
    )
    (output_dir / "task_017d_real_acceptance.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
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
