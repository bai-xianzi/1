"""TASK_017C真实DolphinDB只读Canonical抽样验收。"""
# 本脚本核心功能：执行任务017c日频资金数据验收的真实运行或验收流程。
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
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DailyFundsReadRequest,
    DolphinDBDailyFundsCanonicalService,
    normalise_query_records,
)


# 配置常量：集中定义 `DATASETS`，供后续流程复用。
# - 当前值或构造表达式：`('hq', 'kphq', 'hy', 'gn', 'kphy', 'kpgn', 'zj')`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
DATASETS = ("hq", "kphq", "hy", "gn", "kphy", "kpgn", "zj")


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
def _sample_selector(
    adapter: DolphinDBDataSourceAdapter,
    service: DolphinDBDailyFundsCanonicalService,
    dataset_id: str,
) -> tuple[str, date]:
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
    selector = str(rows[0][raw_field]).strip()
    # 输出结果：返回 `(selector, _as_date(rows[0]['snapshot_date']))` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return selector, _as_date(rows[0]["snapshot_date"])


# 函数 `_assert_semantics`：完成assert语义相关处理。
# - 输入：dataset_id、record。
# - 处理：完成assert语义相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `list[str]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _assert_semantics(dataset_id: str, record: Any) -> list[str]:
    checks: list[str] = []
    values = record.values
    # 条件分支：检查 `dataset_id == 'hq'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if dataset_id == "hq":
        lots = values.get("volume_lots")
        shares = values.get("volume_shares")
        # 条件分支：检查 `lots is not None and shares != round(lots * 100)` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if lots is not None and shares != round(lots * 100):
            # 失败门禁：抛出 `DataContractError('hq手到股转换验收失败。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("hq手到股转换验收失败。")
        checks.append("VOLUME_LOT_TO_SHARE")
    # 条件分支：检查 `dataset_id == 'kphq'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    elif dataset_id == "kphq":
        # 条件分支：检查 `values.get('snapshot_time') is not None` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if values.get("snapshot_time") is not None:
            # 失败门禁：抛出 `DataContractError('kphq伪造了精确snapshot_time。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("kphq伪造了精确snapshot_time。")
        # 条件分支：检查 `values.get('snapshot_time_precision') != 'DATE_ONLY'` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if values.get("snapshot_time_precision") != "DATE_ONLY":
            # 失败门禁：抛出 `DataContractError('kphq时间精度不是DATE_ONLY。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("kphq时间精度不是DATE_ONLY。")
        checks.append("DATE_ONLY_NO_FABRICATED_TIME")
    # 条件分支：检查 `dataset_id in {'hy', 'gn', 'kphy', 'kpgn'}` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    elif dataset_id in {"hy", "gn", "kphy", "kpgn"}:
        # 条件分支：检查 `record.canonical_object != 'ClassificationMarketSnapshot'` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if record.canonical_object != "ClassificationMarketSnapshot":
            # 失败门禁：抛出 `DataContractError('分类来源映射成了错误对象。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("分类来源映射成了错误对象。")
        # 条件分支：检查 `not values.get('node_id')` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not values.get("node_id"):
            # 失败门禁：抛出 `DataContractError('分类节点缺少稳定临时node_id。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("分类节点缺少稳定临时node_id。")
        checks.append("CLASSIFICATION_NODE_NOT_MEMBERSHIP")
    # 条件分支：检查 `dataset_id == 'zj'` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    elif dataset_id == "zj":
        buckets = [
            values.get("net_inflow_super_large_cny"),
            values.get("net_inflow_large_cny"),
            values.get("net_inflow_medium_cny"),
            values.get("net_inflow_small_cny"),
        ]
        present = [value for value in buckets if value is not None]
        expected = None if not present else sum(present)
        # 条件分支：检查 `values.get('net_inflow_total_cny') != expected` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if values.get("net_inflow_total_cny") != expected:
            # 失败门禁：抛出 `DataContractError('zj总净流入派生验收失败。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError("zj总净流入派生验收失败。")
        checks.append("MONEY_FLOW_BUCKET_SUM")
    # 输出结果：返回 `checks` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return checks


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
        source_id="daily_funds_task_017c_acceptance",
    )
    health = adapter.health_check()
    # 条件分支：检查 `health.status is not QualityStatus.PASSED` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if health.status is not QualityStatus.PASSED:
        # 失败门禁：抛出 `DataContractError(health.description or '健康检查失败。')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise DataContractError(health.description or "健康检查失败。")
    service = DolphinDBDailyFundsCanonicalService(
        adapter,
        project_root=root,
    )

    dataset_results: list[dict[str, Any]] = []
    # 循环处理：将 `DATASETS` 中的元素逐项绑定到 `dataset_id`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for dataset_id in DATASETS:
        selector, snapshot_date = _sample_selector(
            adapter,
            service,
            dataset_id,
        )
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id=dataset_id,
                entity_ids=(selector,),
                start_date=snapshot_date,
                end_date=snapshot_date,
                limit_per_entity=10,
            )
        )
        # 条件分支：检查 `not batch.records` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not batch.records:
            # 失败门禁：抛出 `DataContractError(f'{dataset_id}抽样没有生成Canonical记录。')`，立即终止当前不可信路径。
            # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
            raise DataContractError(
                f"{dataset_id}抽样没有生成Canonical记录。"
            )
        record = batch.records[0]
        checks = _assert_semantics(dataset_id, record)
        dataset_results.append(
            {
                "dataset_id": dataset_id,
                "selector": selector,
                "snapshot_date": snapshot_date.isoformat(),
                "canonical_object": batch.canonical_object,
                "source_row_count": batch.source_row_count,
                "result_count": len(batch.records),
                "quality_flags": list(record.quality_flags),
                "warnings": list(batch.warnings),
                "semantic_checks": checks,
                "primary_key": record.primary_key,
                "source_record_id": record.source_record_id,
            }
        )

    report = {
        "task_id": "TASK_017C",
        "mode": "REAL_READONLY_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_uri": service.database_uri,
        "service_id": service.service_id,
        "service_version": service.service_version,
        "coverage_version": service.coverage_version,
        "mapping_version": service.mapping_version,
        "dictionary_revision": service.dictionary_revision,
        "dataset_count": len(dataset_results),
        "write_operation_count": 0,
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": dataset_results,
    }
    json_path = output_dir / "task_017c_real_acceptance.json"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    md_lines = [
        "# TASK_017C真实只读验收",
        "",
        "- 状态：**PASSED_WITH_WARNINGS**",
        f"- 数据库：`{service.database_uri}`",
        f"- 来源：{len(dataset_results)}",
        "- 写操作：0",
        "",
        "| 来源 | Canonical对象 | 记录数 |",
        "|---|---|---:|",
    ]
    md_lines.extend(
        f"| {item['dataset_id']} | {item['canonical_object']} | {item['result_count']} |"
        for item in dataset_results
    )
    (output_dir / "task_017c_real_acceptance.md").write_text(
        "\n".join(md_lines) + "\n",
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
