"""TASK_014真实DolphinDB基本面标准化抽样验收。"""
# 本脚本核心功能：执行任务014基本面验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# 配置常量：集中定义 `PROJECT_ROOT`，供后续流程复用。
# - 当前值或构造表达式：`Path(__file__).resolve().parents[1]`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 配置常量：集中定义 `SRC_DIR`，供后续流程复用。
# - 当前值或构造表达式：`PROJECT_ROOT / 'src'`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
SRC_DIR = PROJECT_ROOT / "src"
# 条件分支：检查 `str(SRC_DIR) not in sys.path` 后选择对应处理路径。
# - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
# - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import QualityStatus
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_fundamental_service import (
    DolphinDBFundamentalStandardizedService,
)
from a_stock_quant.dolphindb_probe import resolve_password
from a_stock_quant.fundamental_standard_provider import (
    FundamentalStandardDataProvider,
)
from a_stock_quant.standard_data_service import (
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


# 配置常量：集中定义 `SAMPLE_IDS`，供后续流程复用。
# - 当前值或构造表达式：`('000001', '002731', '600015', '001235', '001248')`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
SAMPLE_IDS = (
    "000001",
    "002731",
    "600015",
    "001235",
    "001248",
)


# 类 `AcceptanceCheck`：集中封装AcceptanceCheck相关状态和行为。
# - 输入：构造参数、类属性以及基类 `object` 提供的公共能力。
# - 处理：把相关数据、约束和操作聚合在同一对象边界内。
# - 输出：向调用方提供稳定的属性、方法和可测试行为。
# - 为什么这样写：集中管理同一职责，避免脚本流程中出现分散状态和重复约束。
@dataclass(frozen=True, slots=True)
class AcceptanceCheck:
    name: str
    passed: bool
    details: dict[str, Any]


# 类 `AcceptanceReport`：集中封装AcceptanceReport相关状态和行为。
# - 输入：构造参数、类属性以及基类 `object` 提供的公共能力。
# - 处理：把相关数据、约束和操作聚合在同一对象边界内。
# - 输出：向调用方提供稳定的属性、方法和可测试行为。
# - 为什么这样写：集中管理同一职责，避免脚本流程中出现分散状态和重复约束。
@dataclass(frozen=True, slots=True)
class AcceptanceReport:
    checks: tuple[AcceptanceCheck, ...]
    query_results: dict[str, Any]
    overall_status: str

    # 函数 `to_dict`：完成到dict相关处理。
    # - 输入：self。
    # - 处理：完成到dict相关处理，并按现有异常和门禁规则保留失败证据。
    # - 输出：返回类型约定为 `dict[str, Any]`。
    # - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
    def to_dict(self) -> dict[str, Any]:
        # 输出结果：返回 `{'checks': [asdict(item) for item in self.checks], 'query_results': self.query_results,...` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return {
            "checks": [asdict(item) for item in self.checks],
            "query_results": self.query_results,
            "overall_status": self.overall_status,
        }


# 函数 `_query`：完成查询相关处理。
# - 输入：service、canonical_object、usage、decision_time。
# - 处理：完成查询相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `Any`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _query(
    service: StandardDataService,
    canonical_object: str,
    *,
    usage: StandardDataUsage = (
        StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
    ),
    decision_time: datetime | None = None,
) -> Any:
    # 输出结果：返回 `service.query(StandardDataQuery(dataset_id='a_stock_fundamental_snapshot', canonical_ob...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return service.query(
        StandardDataQuery(
            dataset_id="a_stock_fundamental_snapshot",
            canonical_object=canonical_object,
            instrument_ids=SAMPLE_IDS,
            start_date=date(2026, 6, 19),
            end_date=date(2026, 6, 19),
            as_of_date=date(2026, 6, 20),
            usage=usage,
            decision_time=decision_time,
            include_source_extensions=True,
            include_quality_flags=True,
            include_lineage=True,
        )
    )


# 函数 `_index_records`：完成indexrecords相关处理。
# - 输入：result。
# - 处理：完成indexrecords相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `dict[str, list[Any]]`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _index_records(result: Any) -> dict[str, list[Any]]:
    output: dict[str, list[Any]] = {}
    # 循环处理：将 `result.records` 中的元素逐项绑定到 `record`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for record in result.records:
        instrument_id = (
            record.primary_key.get("instrument_id")
            or record.values.get("instrument_id")
        )
        # 条件分支：检查 `instrument_id is None` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if instrument_id is None:
            continue
        output.setdefault(str(instrument_id), []).append(record)
    # 输出结果：返回 `output` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return output


# 函数 `build_report`：完成构建报告相关处理。
# - 输入：service、raw_service。
# - 处理：完成构建报告相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `AcceptanceReport`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_report(
    service: StandardDataService,
    raw_service: DolphinDBFundamentalStandardizedService,
) -> AcceptanceReport:
    fundamental = _query(service, "FundamentalSnapshot")
    ownership = _query(service, "OwnershipSnapshot")
    instrument = _query(service, "Instrument")
    classification = _query(service, "ClassificationMembership")
    historical = _query(
        service,
        "FundamentalSnapshot",
        usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
    )
    manual = _query(
        service,
        "FundamentalSnapshot",
        usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
        decision_time=datetime(
            2026, 6, 20, 9, 0, tzinfo=timezone.utc
        ),
    )

    fundamental_by_id = _index_records(fundamental)
    ownership_by_id = _index_records(ownership)
    instrument_by_id = _index_records(instrument)

    checks: list[AcceptanceCheck] = []

    checks.append(
        AcceptanceCheck(
            name="数据集配置保持禁用且验收显式放行",
            passed=(
                raw_service.registration.enabled is False
                and raw_service.registration.mapping_version == "0.2.0-rc2"
                and raw_service.registration.dictionary_revision == "0.5"
            ),
            details={
                "enabled": raw_service.registration.enabled,
                "mapping_version": raw_service.registration.mapping_version,
                "dictionary_revision": raw_service.registration.dictionary_revision,
            },
        )
    )

    record_000001 = (fundamental_by_id.get("000001") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="000001正常一季报金额和报告期标准化",
            passed=(
                record_000001 is not None
                and record_000001.values.get("report_period")
                == date(2026, 3, 31)
                and record_000001.values.get("revenue_cny")
                == 35_277_000_000.0
                and record_000001.source_extensions.get("operating_revenue")
                == 35_277_000.0
                and record_000001.values.get("announcement_date") is None
            ),
            details=(
                record_000001.to_dict()
                if record_000001 is not None
                else {"record": None}
            ),
        )
    )

    ownership_000001 = (ownership_by_id.get("000001") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="000001股本Raw与Canonical分层",
            passed=(
                ownership_000001 is not None
                and ownership_000001.values.get("total_shares")
                == 19_405_918_700
                and isinstance(
                    ownership_000001.values.get("total_shares"), int
                )
                and ownership_000001.source_extensions.get("total_shares")
                == 1_940_591.87
            ),
            details=(
                ownership_000001.to_dict()
                if ownership_000001 is not None
                else {"record": None}
            ),
        )
    )

    record_002731 = (fundamental_by_id.get("002731") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="002731旧三季报日期推导",
            passed=(
                record_002731 is not None
                and record_002731.values.get("report_period")
                == date(2025, 9, 30)
            ),
            details=(
                record_002731.to_dict()
                if record_002731 is not None
                else {"record": None}
            ),
        )
    )

    record_600015 = (fundamental_by_id.get("600015") or [None])[0]
    checks.append(
        AcceptanceCheck(
            name="600015年报日期推导",
            passed=(
                record_600015 is not None
                and record_600015.values.get("report_period")
                == date(2025, 12, 31)
            ),
            details=(
                record_600015.to_dict()
                if record_600015 is not None
                else {"record": None}
            ),
        )
    )

    # 循环处理：将 `(('001235', '身份和财务不完整'), ('001248', '有身份但无财务载荷'))` 中的元素逐项绑定到 `(instrument_id, label)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for instrument_id, label in (
        ("001235", "身份和财务不完整"),
        ("001248", "有身份但无财务载荷"),
    ):
        checks.append(
            AcceptanceCheck(
                name=f"{instrument_id}{label}不零填财务",
                passed=(
                    instrument_id not in fundamental_by_id
                    and instrument_id not in ownership_by_id
                    and instrument_id in instrument_by_id
                ),
                details={
                    "fundamental_count": len(
                        fundamental_by_id.get(instrument_id, [])
                    ),
                    "ownership_count": len(
                        ownership_by_id.get(instrument_id, [])
                    ),
                    "instrument_count": len(
                        instrument_by_id.get(instrument_id, [])
                    ),
                },
            )
        )

    classification_fields_are_authoritative = all(
        "node_id" in record.values
        and "node_name_cn" in record.values
        and "classification_node_id" not in record.values
        for record in classification.records
    )
    checks.append(
        AcceptanceCheck(
            name="行业分类使用权威Canonical字段并保持快照警告",
            passed=(
                bool(classification.records)
                and classification_fields_are_authoritative
                and classification.metadata.status is QualityStatus.WARNING
            ),
            details={
                "result_count": len(classification.records),
                "status": classification.metadata.status.value,
                "quality_flag_counts": (
                    classification.metadata.quality_flag_counts
                ),
            },
        )
    )

    checks.append(
        AcceptanceCheck(
            name="当前研究和快照后人工辅助决策允许但带警告",
            passed=(
                fundamental.metadata.status is QualityStatus.WARNING
                and not fundamental.metadata.blocks_downstream
                and manual.metadata.status is QualityStatus.WARNING
                and not manual.metadata.blocks_downstream
            ),
            details={
                "research": fundamental.metadata.to_dict(),
                "manual": manual.metadata.to_dict(),
            },
        )
    )

    checks.append(
        AcceptanceCheck(
            name="严格历史回测继续阻断",
            passed=(
                historical.metadata.status is QualityStatus.FAILED
                and historical.metadata.blocks_downstream
            ),
            details=historical.metadata.to_dict(),
        )
    )

    overall = "PASSED" if all(item.passed for item in checks) else "FAILED"
    # 输出结果：返回 `AcceptanceReport(checks=tuple(checks), query_results={'FundamentalSnapshot': fundamenta...` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return AcceptanceReport(
        checks=tuple(checks),
        query_results={
            "FundamentalSnapshot": fundamental.to_dict(),
            "OwnershipSnapshot": ownership.to_dict(),
            "Instrument": instrument.to_dict(),
            "ClassificationMembership": classification.to_dict(),
            "HistoricalGate": historical.to_dict(),
            "ManualDecisionGate": manual.to_dict(),
        },
        overall_status=overall,
    )


# 函数 `write_report`：完成写入报告相关处理。
# - 输入：report、json_path、markdown_path。
# - 处理：完成写入报告相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def write_report(
    report: AcceptanceReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# TASK_014 基本面真实标准化验收",
        "",
        f"总体状态：**{report.overall_status}**",
        "",
    ]
    # 循环处理：将 `report.checks` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in report.checks:
        mark = "PASS" if item.passed else "FAIL"
        lines.append(f"- [{mark}] {item.name}")
    markdown_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument(
        "--registration",
        default=(
            "configs/datasets/"
            "a_stock_fundamental_snapshot.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        default="reports/task_014_fundamental_acceptance.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="reports/task_014_fundamental_acceptance.md",
    )
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    args = build_parser().parse_args()
    password = resolve_password()

    adapter = DolphinDBDataSourceAdapter(
        settings=DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=password,
        ),
        source_id="dolphindb_fundamental_task_014",
    )

    health = adapter.health_check()
    # 条件分支：检查 `health.status is not QualityStatus.PASSED` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if health.status is not QualityStatus.PASSED:
        print(f"DolphinDB健康检查失败：{health.description}")
        # 输出结果：返回 `1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 1

    raw_service = (
        DolphinDBFundamentalStandardizedService.from_registry_file(
            adapter,
            args.registration,
            allow_disabled_for_acceptance=True,
        )
    )
    provider = FundamentalStandardDataProvider(raw_service)
    standard_service = StandardDataService()
    standard_service.register_provider(provider)

    report = build_report(standard_service, raw_service)
    write_report(
        report,
        Path(args.json_output),
        Path(args.markdown_output),
    )

    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    print(f"\n验收JSON：{args.json_output}")
    print(f"验收摘要：{args.markdown_output}")
    # 输出结果：返回 `0 if report.overall_status == 'PASSED' else 2` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if report.overall_status == "PASSED" else 2


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
