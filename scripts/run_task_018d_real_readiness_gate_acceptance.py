"""TASK_018D 九个数据集真实端到端统一就绪度门禁验收。"""
# 本脚本核心功能：执行任务018d真实就绪度门禁验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

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


# 配置常量：集中定义 `PLAN_VERSION`，供后续流程复用。
# - 当前值或构造表达式：`'0.1.0'`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
PLAN_VERSION = "0.1.0"


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


# 函数 `_load_json`：完成加载JSON相关处理。
# - 输入：path。
# - 处理：完成加载JSON相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict[str, Any]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _load_json(path: Path) -> dict[str, Any]:
    # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
    # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
    # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # 失败门禁：抛出 `DataContractError(f'无法加载JSON：{path}')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(f"无法加载JSON：{path}") from exc
    # 条件分支：检查 `not isinstance(payload, dict)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not isinstance(payload, dict):
        # 失败门禁：抛出 `DataContractError(f'JSON根节点必须是对象：{path}')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(f"JSON根节点必须是对象：{path}")
    # 输出结果：返回 `payload` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return payload


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


# 函数 `_records_from_result`：完成records从结果相关处理。
# - 输入：result。
# - 处理：完成records从结果相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `list[dict[str, Any]]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _records_from_result(result: Any) -> list[dict[str, Any]]:
    # 条件分支：检查 `result is None` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if result is None:
        # 输出结果：返回 `[]` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return []
    # 条件分支：检查 `isinstance(result, list)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(result, list):
        # 条件分支：检查 `any((not isinstance(item, Mapping) for item in result))` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if any(not isinstance(item, Mapping) for item in result):
            # 失败门禁：抛出 `DataContractError('DolphinDB列表结果存在非对象记录。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("DolphinDB列表结果存在非对象记录。")
        # 输出结果：返回 `[dict(item) for item in result]` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return [dict(item) for item in result]
    to_dict = getattr(result, "to_dict", None)
    columns = getattr(result, "columns", None)
    # 条件分支：检查 `callable(to_dict) and columns is not None` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if callable(to_dict) and columns is not None:
        # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
        # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
        # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
        try:
            rows = to_dict(orient="records")
        except TypeError:
            rows = to_dict("records")
        # 条件分支：检查 `any((not isinstance(item, Mapping) for item in rows))` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if any(not isinstance(item, Mapping) for item in rows):
            # 失败门禁：抛出 `DataContractError('DolphinDB表格无法转换为对象记录。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("DolphinDB表格无法转换为对象记录。")
        # 输出结果：返回 `[dict(item) for item in rows]` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return [dict(item) for item in rows]
    # 失败门禁：抛出 `DataContractError('不支持当前DolphinDB返回值类型。')`，立即终止当前不可信路径。
    # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
    raise DataContractError("不支持当前DolphinDB返回值类型。")


# 类 `SampleSource`：集中封装SampleSource相关状态和行为。
# - 输入：构造参数、类属性以及基类 `object` 提供的公共能力。
# - 处理：把相关数据、约束和操作聚合在同一对象边界内。
# - 输出：向调用方提供稳定的属性、方法和可测试行为。
# - 为什么这样写：集中管理同一职责，避免脚本流程中出现分散状态和重复约束。
@dataclass(frozen=True, slots=True)
class SampleSource:
    dataset_id: str
    database_uri: str
    table_name: str
    entity_field: str
    date_field: str
    dataset_filter: str | None = None


# 函数 `_sample_selector`：完成sampleselector相关处理。
# - 输入：adapter、source、preferred_selector。
# - 处理：完成sampleselector相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `tuple[str, date]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _sample_selector(
    adapter: DolphinDBDataSourceAdapter,
    source: SampleSource,
    preferred_selector: str | None,
) -> tuple[str, date]:
    where_parts: list[str] = []
    # 条件分支：检查 `source.dataset_filter` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if source.dataset_filter:
        where_parts.append(source.dataset_filter)
    # 条件分支：检查 `preferred_selector` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
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
    # 条件分支：检查 `not rows and preferred_selector` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not rows and preferred_selector:
        # 输出结果：返回 `_sample_selector(adapter, source, None)` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return _sample_selector(adapter, source, None)
    # 条件分支：检查 `not rows` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not rows:
        # 失败门禁：抛出 `DataContractError(f'{source.dataset_id}没有可用于真实验收的来源记录。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(
            f"{source.dataset_id}没有可用于真实验收的来源记录。"
        )
    selector = str(rows[0][source.entity_field]).strip()
    # 条件分支：检查 `not selector` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not selector:
        # 失败门禁：抛出 `DataContractError(f'{source.dataset_id}抽样实体为空。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(
            f"{source.dataset_id}抽样实体为空。"
        )
    # 输出结果：返回 `(selector, _as_date(rows[0][source.date_field]))` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return selector, _as_date(rows[0][source.date_field])


# 函数 `_build_query`：完成构建查询相关处理。
# - 输入：dataset_id、canonical_object、selector_mode、selector、sample_date、as_of_date、usage、manual_decision_time。
# - 处理：完成构建查询相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `StandardDataQuery`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 输出结果：返回 `StandardDataQuery(dataset_id=dataset_id, canonical_object=canonical_object, instrument_...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
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


# 函数 `_register_services`：完成registerservices相关处理。
# - 输入：adapter、root。
# - 处理：完成registerservices相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `tuple[StandardDataService, dict[str, SampleSource]]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 循环处理：将 `standard.list_datasets()` 中的元素逐项绑定到 `descriptor`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for descriptor in standard.list_datasets():
        # 条件分支：检查 `descriptor.dataset_id in sample_sources` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
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

    # 输出结果：返回 `(standard, sample_sources)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return standard, sample_sources


# 函数 `_build_gated_service`：完成构建gated服务相关处理。
# - 输入：root、standard、plan。
# - 处理：完成构建gated服务相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `ReadinessGatedStandardDataService`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 输出结果：返回 `ReadinessGatedStandardDataService(standard, readiness)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return ReadinessGatedStandardDataService(
        standard,
        readiness,
    )


# 函数 `_evidence_summary`：完成证据summary相关处理。
# - 输入：snapshot。
# - 处理：完成证据summary相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict[str, Any]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _evidence_summary(snapshot: Any) -> dict[str, Any]:
    # 输出结果：返回 `{item.dimension.value: {'status': item.status.value, 'code': item.code, 'message': item...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
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


# 函数 `_markdown`：完成markdown相关处理。
# - 输入：report。
# - 处理：完成markdown相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `str`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 循环处理：将 `report['assessments']` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
    # 输出结果：返回 `'\n'.join(lines)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return "\n".join(lines)


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_path = Path(args.plan)
    # 条件分支：检查 `not plan_path.is_absolute()` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    plan = _load_json(plan_path)
    # 条件分支：检查 `str(plan.get('contract_version')) != PLAN_VERSION` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if str(plan.get("contract_version")) != PLAN_VERSION:
        # 失败门禁：抛出 `DataContractError('TASK_018D验收计划版本不兼容。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError("TASK_018D验收计划版本不兼容。")

    as_of_date = date.fromisoformat(str(plan["as_of_date"]))
    manual_decision_time = datetime.fromisoformat(
        str(plan["manual_decision_time"])
    )
    # 条件分支：检查 `manual_decision_time.tzinfo is None` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if manual_decision_time.tzinfo is None:
        # 失败门禁：抛出 `DataContractError('manual_decision_time必须携带时区。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
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
    # 条件分支：检查 `health.status is not QualityStatus.PASSED` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if health.status is not QualityStatus.PASSED:
        # 失败门禁：抛出 `DataContractError(health.description or 'DolphinDB健康检查失败。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
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
    # 条件分支：检查 `len(descriptors) != 9` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(descriptors) != 9:
        # 失败门禁：抛出 `DataContractError(f'预期9个Provider，实际{len(descriptors)}个。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(
            f"预期9个Provider，实际{len(descriptors)}个。"
        )

    assessments: list[dict[str, Any]] = []
    samples: dict[str, dict[str, str]] = {}
    # 循环处理：将 `plan['datasets']` 中的元素逐项绑定到 `dataset`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for dataset in plan["datasets"]:
        dataset_id = str(dataset["dataset_id"])
        canonical_object = str(dataset["canonical_object"])
        descriptor = descriptors.get(dataset_id)
        # 条件分支：检查 `descriptor is None` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if descriptor is None:
            # 失败门禁：抛出 `DataContractError(f'验收计划数据集未注册Provider：{dataset_id}')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(
                f"验收计划数据集未注册Provider：{dataset_id}"
            )
        # 条件分支：检查 `canonical_object not in descriptor.supported_objects` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if canonical_object not in descriptor.supported_objects:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}不支持{canonical_object}。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
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

        # 循环处理：将 `usages` 中的元素逐项绑定到 `usage`。
        # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
        # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
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
            # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
            # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
            # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
            try:
                gated_result.assert_usable()
            except DataContractError:
                assert_failed = True
            else:
                assert_failed = False
            # 条件分支：检查 `usable == assert_failed` 后选择对应处理路径。
            # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
            # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
            if usable == assert_failed:
                # 失败门禁：抛出 `DataContractError(f'{dataset_id}/{usage.value}的blocks_downstream与assert_usable不一致。')`，立即终止当前不可信路径。
                # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
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

    # 函数 `rows`：完成记录相关处理。
    # - 输入：usage。
    # - 处理：完成记录相关处理，并按现有异常和门禁规则保留失败证据。
    # - 输出：返回类型约定为 `list[dict[str, Any]]`。
    # - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
    def rows(usage: StandardDataUsage) -> list[dict[str, Any]]:
        # 输出结果：返回 `[item for item in assessments if item['usage'] == usage.value]` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
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
    # 循环处理：将 `checks` 中的元素逐项绑定到 `(passed, name)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for passed, name in checks:
        # 条件分支：检查 `not passed` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
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
    # 输出结果：返回 `0 if not issues else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if not issues else 1


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
