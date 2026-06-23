"""DolphinDB基本面快照只读发现与语义画像。

本模块属于TASK_013的数据发现阶段。

它只执行只读查询，目标是确认：
1. 实际字段结构和覆盖范围；
2. (stock_code, snapshot_date)主键质量；
3. 快照、更新、报告期和导入时间的语义；
4. 股本和金额单位候选；
5. FundamentalSnapshot、OwnershipSnapshot和Instrument映射风险；
6. 严格历史回测是否需要阻断。

本模块不会读取桌面Excel目录，不会调用外部导入脚本，
也不会创建、删除或修改DolphinDB数据库和表。
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .data_contracts import DataContractError, QualityStatus
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from .dolphindb_probe import resolve_password


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)

EXPECTED_FIELD_TYPES: dict[str, str] = {
    "stock_code": "SYMBOL",
    "snapshot_date": "DATE",
    "update_date": "DATE",
    "total_shares": "DOUBLE",
    "b_shares": "DOUBLE",
    "h_shares": "DOUBLE",
    "circulating_a_shares": "DOUBLE",
    "eps": "DOUBLE",
    "zpg": "DOUBLE",
    "total_assets": "DOUBLE",
    "current_assets": "DOUBLE",
    "fixed_assets": "DOUBLE",
    "intangible_assets": "DOUBLE",
    "shareholder_count": "LONG",
    "current_liabilities": "DOUBLE",
    "long_term_liabilities": "DOUBLE",
    "capital_reserve": "DOUBLE",
    "net_assets": "DOUBLE",
    "operating_revenue": "DOUBLE",
    "operating_cost": "DOUBLE",
    "accounts_receivable": "DOUBLE",
    "operating_profit": "DOUBLE",
    "investment_income": "DOUBLE",
    "operating_cash_flow": "DOUBLE",
    "total_cash_flow": "DOUBLE",
    "inventory": "DOUBLE",
    "total_profit": "DOUBLE",
    "after_tax_profit": "DOUBLE",
    "net_profit": "DOUBLE",
    "undistributed_profit": "DOUBLE",
    "adjusted_nav_per_share": "DOUBLE",
    "region_code": "INT",
    "source_industry_code": "INT",
    "report_period": "INT",
    "listing_date": "DATE",
    "sw_code": "SYMBOL",
    "source_detail_code": "SYMBOL",
    "source_industry_level2_code": "SYMBOL",
    "source_industry_level1_code": "SYMBOL",
    "source_sector": "STRING",
    "source_industry": "STRING",
    "source_subindustry": "STRING",
    "tdx_industry_code": "SYMBOL",
    "sw_subindustry_code": "SYMBOL",
    "sw_industry_code": "SYMBOL",
    "sw_sector_code": "SYMBOL",
    "sw_sector": "STRING",
    "sw_industry": "STRING",
    "sw_subindustry": "STRING",
    "market": "SYMBOL",
    "stock_name": "STRING",
    "pinyin": "STRING",
    "source_file": "STRING",
    "imported_at": "TIMESTAMP",
}

EXPECTED_FIELDS = tuple(EXPECTED_FIELD_TYPES)

REQUIRED_FIELDS = (
    "stock_code",
    "snapshot_date",
    "update_date",
    "total_shares",
    "circulating_a_shares",
    "eps",
    "total_assets",
    "net_assets",
    "operating_revenue",
    "operating_cost",
    "operating_profit",
    "total_profit",
    "after_tax_profit",
    "net_profit",
    "report_period",
    "listing_date",
    "market",
    "stock_name",
    "source_file",
    "imported_at",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    enum_value = getattr(value, "value", None)
    if (
        enum_value is not None
        and not isinstance(value, (str, bytes))
    ):
        return _json_safe(enum_value)

    if isinstance(value, float) and (
        math.isnan(value) or math.isinf(value)
    ):
        return None

    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            return _json_safe(item_method())
        except (TypeError, ValueError):
            pass

    return value


def _records_from_result(
    result: Any,
) -> list[dict[str, Any]]:
    if result is None:
        return []

    if isinstance(result, list):
        if any(
            not isinstance(item, dict)
            for item in result
        ):
            raise DataContractError(
                "基本面画像结果列表中存在非字典记录。"
            )
        return list(result)

    if isinstance(result, dict):
        return [dict(result)]

    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        try:
            records = to_dict(orient="records")
        except TypeError:
            records = to_dict("records")

        if any(
            not isinstance(item, dict)
            for item in records
        ):
            raise DataContractError(
                "基本面画像结果无法转换为字典记录。"
            )
        return list(records)

    raise DataContractError(
        "暂不支持当前基本面画像结果类型。"
    )


def _first_record(result: Any) -> dict[str, Any]:
    records = _records_from_result(result)
    return records[0] if records else {}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def _as_int(value: Any) -> int:
    if _is_missing(value):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def _ratio(
    numerator: int,
    denominator: int,
) -> float | None:
    if denominator <= 0:
        return None

    return round(numerator / denominator, 6)


@dataclass(slots=True)
class FundamentalProfileReport:
    database_uri: str
    table_name: str
    generated_at: datetime
    expected_schema: dict[str, str]
    raw_fields: list[str]
    schema_comparison: dict[str, Any]
    summary: dict[str, Any]
    snapshot_counts: list[dict[str, Any]]
    report_period_counts: list[dict[str, Any]]
    market_counts: list[dict[str, Any]]
    source_file_counts: list[dict[str, Any]]
    null_counts: dict[str, Any]
    duplicate_summary: dict[str, Any]
    duplicate_samples: list[dict[str, Any]]
    anomaly_counts: dict[str, Any]
    unit_candidate_summary: dict[str, Any]
    sample_rows: list[dict[str, Any]]
    checks: list[dict[str, Any]] = field(
        default_factory=list
    )
    pending_confirmations: list[dict[str, Any]] = field(
        default_factory=list
    )
    overall_status: QualityStatus = (
        QualityStatus.PENDING_CONFIRMATION
    )
    blocks_downstream: bool = True
    blocks_strict_historical_backtest: bool = True
    allows_current_snapshot_research: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self)


class DolphinDBFundamentalProfiler:
    """对基本面快照表执行只读聚合画像。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = (
            "dfs://A_STOCK_FUNDAMENTAL_DB"
        ),
        table_name: str = (
            "stock_fundamental_snapshot"
        ),
    ) -> None:
        adapter._validate_database_uri(database_uri)
        adapter._validate_table_name(table_name)

        self.adapter = adapter
        self.database_uri = database_uri
        self.table_name = table_name

    @property
    def _table_ref(self) -> str:
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )

    def _query_one(
        self,
        script: str,
    ) -> dict[str, Any]:
        return _first_record(
            self.adapter.run_readonly_query(script)
        )

    def _query_rows(
        self,
        script: str,
    ) -> list[dict[str, Any]]:
        return _records_from_result(
            self.adapter.run_readonly_query(script)
        )

    def _discover_fields(self) -> list[str]:
        batch = self.adapter.read_raw(
            self.table_name,
            database_uri=self.database_uri,
            limit=1,
        )
        return batch.raw_fields

    def _count_where(
        self,
        condition: str,
    ) -> int:
        normalized_condition = re.sub(
            r"\bnot\s+isNull\(([A-Za-z_][A-Za-z0-9_]*)\)",
            r"not(isNull(\1))",
            condition,
        )

        result = self._query_one(
            f"""
            select count(*) as row_count
            from {self._table_ref}
            where {normalized_condition}
            """
        )
        return _as_int(result.get("row_count"))

    def collect(self) -> FundamentalProfileReport:
        raw_fields = self._discover_fields()
        valid_fields = [
            name
            for name in raw_fields
            if _IDENTIFIER_PATTERN.fullmatch(name)
        ]
        available = set(valid_fields)

        missing_fields = sorted(
            set(EXPECTED_FIELDS) - available
        )
        unexpected_fields = sorted(
            available - set(EXPECTED_FIELDS)
        )
        schema_comparison = {
            "expected_field_count": len(EXPECTED_FIELDS),
            "actual_field_count": len(raw_fields),
            "missing_fields": missing_fields,
            "unexpected_fields": unexpected_fields,
            "field_order_matches": (
                tuple(raw_fields) == EXPECTED_FIELDS
            ),
            "declared_type_source": (
                "DolphinDB schema export supplied "
                "during TASK_013 discovery"
            ),
        }

        summary = self._query_one(
            f"""
            select
                count(*) as row_count,
                nunique(stock_code, true)
                    as stock_count,
                min(snapshot_date)
                    as min_snapshot_date,
                max(snapshot_date)
                    as max_snapshot_date,
                min(update_date)
                    as min_update_date,
                max(update_date)
                    as max_update_date,
                min(listing_date)
                    as min_listing_date,
                max(listing_date)
                    as max_listing_date,
                min(imported_at)
                    as first_imported_at,
                max(imported_at)
                    as last_imported_at
            from {self._table_ref}
            """
        )

        snapshot_counts = self._query_rows(
            f"""
            select
                snapshot_date,
                count(*) as row_count
            from {self._table_ref}
            group by snapshot_date
            order by snapshot_date
            """
        )

        report_period_counts = self._query_rows(
            f"""
            select
                report_period,
                count(*) as row_count
            from {self._table_ref}
            group by report_period
            order by report_period
            """
        )

        market_counts = self._query_rows(
            f"""
            select
                market,
                count(*) as row_count
            from {self._table_ref}
            group by market
            order by market
            """
        )

        source_file_counts = self._query_rows(
            f"""
            select
                source_file,
                count(*) as row_count,
                min(snapshot_date)
                    as min_snapshot_date,
                max(snapshot_date)
                    as max_snapshot_date,
                min(imported_at)
                    as first_imported_at,
                max(imported_at)
                    as last_imported_at
            from {self._table_ref}
            group by source_file
            order by source_file
            """
        )

        null_expressions = ",\n".join(
            f"sum(isNull({name})) "
            f"as {name}_null_count"
            for name in valid_fields
        )
        null_counts = (
            self._query_one(
                f"""
                select
                    {null_expressions}
                from {self._table_ref}
                """
            )
            if null_expressions
            else {}
        )

        duplicate_summary = self._query_one(
            f"""
            select
                count(*) as duplicate_group_count,
                sum(duplicate_count - 1)
                    as duplicate_extra_row_count
            from (
                select count(*) as duplicate_count
                from {self._table_ref}
                group by stock_code, snapshot_date
                having count(*) > 1
            )
            """
        )
        duplicate_summary[
            "duplicate_group_count"
        ] = _as_int(
            duplicate_summary.get(
                "duplicate_group_count"
            )
        )
        duplicate_summary[
            "duplicate_extra_row_count"
        ] = _as_int(
            duplicate_summary.get(
                "duplicate_extra_row_count"
            )
        )

        duplicate_samples = self._query_rows(
            f"""
            select top 20
                stock_code,
                snapshot_date,
                count(*) as duplicate_count
            from {self._table_ref}
            group by stock_code, snapshot_date
            having count(*) > 1
            order by duplicate_count desc
            """
        )

        anomaly_counts = {
            "key_null_count": self._count_where(
                "isNull(stock_code) "
                "or isNull(snapshot_date)"
            ),
            "update_after_snapshot_count":
                self._count_where(
                    "not isNull(update_date) "
                    "and not isNull(snapshot_date) "
                    "and update_date > snapshot_date"
                ),
            "listing_after_snapshot_count":
                self._count_where(
                    "not isNull(listing_date) "
                    "and not isNull(snapshot_date) "
                    "and listing_date > snapshot_date"
                ),
            "negative_total_shares_count":
                self._count_where(
                    "not isNull(total_shares) "
                    "and total_shares < 0"
                ),
            "negative_circulating_shares_count":
                self._count_where(
                    "not isNull("
                    "circulating_a_shares) "
                    "and circulating_a_shares < 0"
                ),
            "circulating_above_total_count":
                self._count_where(
                    "not isNull(total_shares) "
                    "and not isNull("
                    "circulating_a_shares) "
                    "and circulating_a_shares "
                    "> total_shares"
                ),
            "nonpositive_total_assets_count":
                self._count_where(
                    "not isNull(total_assets) "
                    "and total_assets <= 0"
                ),
            "source_file_null_count":
                self._count_where(
                    "isNull(source_file)"
                ),
            "imported_at_null_count":
                self._count_where(
                    "isNull(imported_at)"
                ),
        }

        nav_checked_count = self._count_where(
            "not isNull(net_assets) "
            "and not isNull(total_shares) "
            "and total_shares > 0 "
            "and not isNull("
            "adjusted_nav_per_share)"
        )
        nav_match_thousand_cny_10k_shares = (
            self._count_where(
                "not isNull(net_assets) "
                "and not isNull(total_shares) "
                "and total_shares > 0 "
                "and not isNull("
                "adjusted_nav_per_share) "
                "and abs("
                "net_assets / "
                "(total_shares * 10.0) "
                "- adjusted_nav_per_share"
                ") <= 0.05"
            )
        )
        nav_match_10k_cny_10k_shares = (
            self._count_where(
                "not isNull(net_assets) "
                "and not isNull(total_shares) "
                "and total_shares > 0 "
                "and not isNull("
                "adjusted_nav_per_share) "
                "and abs("
                "net_assets / total_shares "
                "- adjusted_nav_per_share"
                ") <= 0.05"
            )
        )
        profit_comparable_count = self._count_where(
            "not isNull(after_tax_profit) "
            "and not isNull(net_profit)"
        )
        profit_equal_count = self._count_where(
            "not isNull(after_tax_profit) "
            "and not isNull(net_profit) "
            "and abs(after_tax_profit "
            "- net_profit) <= 0.000001"
        )

        unit_candidate_summary = {
            "nav_formula_checked_count":
                nav_checked_count,
            "money_thousand_cny_and_shares_10k_match_count":
                nav_match_thousand_cny_10k_shares,
            "money_10k_cny_and_shares_10k_match_count":
                nav_match_10k_cny_10k_shares,
            "money_thousand_cny_and_shares_10k_match_ratio":
                _ratio(
                    nav_match_thousand_cny_10k_shares,
                    nav_checked_count,
                ),
            "money_10k_cny_and_shares_10k_match_ratio":
                _ratio(
                    nav_match_10k_cny_10k_shares,
                    nav_checked_count,
                ),
            "after_tax_and_net_profit_comparable_count":
                profit_comparable_count,
            "after_tax_and_net_profit_equal_count":
                profit_equal_count,
            "after_tax_and_net_profit_equal_ratio":
                _ratio(
                    profit_equal_count,
                    profit_comparable_count,
                ),
            "interpretation": (
                "该结果仅用于单位和利润口径候选判断，"
                "不能替代供应商说明或人工确认。"
            ),
        }

        sample_rows = self._query_rows(
            f"""
            select top 20
                stock_code,
                stock_name,
                market,
                snapshot_date,
                update_date,
                report_period,
                total_shares,
                circulating_a_shares,
                shareholder_count,
                eps,
                adjusted_nav_per_share,
                total_assets,
                net_assets,
                operating_revenue,
                operating_cost,
                operating_profit,
                total_profit,
                after_tax_profit,
                net_profit,
                source_file,
                imported_at
            from {self._table_ref}
            order by stock_code
            """
        )

        checks: list[dict[str, Any]] = []

        missing_required = sorted(
            set(REQUIRED_FIELDS) - available
        )
        checks.append({
            "check_name": "必需字段完整性",
            "status": (
                "PASSED"
                if not missing_required
                else "FAILED"
            ),
            "blocking": bool(missing_required),
            "details": {
                "missing_fields": missing_required,
            },
        })

        checks.append({
            "check_name": "54列物理结构一致性",
            "status": (
                "PASSED"
                if (
                    not missing_fields
                    and not unexpected_fields
                    and len(raw_fields)
                    == len(EXPECTED_FIELDS)
                )
                else "FAILED"
            ),
            "blocking": bool(
                missing_fields or unexpected_fields
            ),
            "details": schema_comparison,
        })

        duplicate_count = duplicate_summary[
            "duplicate_extra_row_count"
        ]
        checks.append({
            "check_name": "基本面快照主键重复",
            "status": (
                "PASSED"
                if duplicate_count == 0
                else "FAILED"
            ),
            "blocking": duplicate_count > 0,
            "details": duplicate_summary,
        })

        key_null_count = anomaly_counts[
            "key_null_count"
        ]
        checks.append({
            "check_name": "基本面快照主键空值",
            "status": (
                "PASSED"
                if key_null_count == 0
                else "FAILED"
            ),
            "blocking": key_null_count > 0,
            "details": {
                "key_null_count": key_null_count,
            },
        })

        structural_failures = [
            check
            for check in checks
            if (
                check["status"] == "FAILED"
                and check["blocking"]
            )
        ]

        period_values = {
            _as_int(item.get("report_period"))
            for item in report_period_counts
            if not _is_missing(
                item.get("report_period")
            )
        }
        period_month_candidate = (
            bool(period_values)
            and period_values.issubset(
                {3, 6, 9, 12}
            )
        )

        pending_confirmations = [
            {
                "category":
                    "FUNDAMENTAL_REPORT_PERIOD",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "来源report_period是3/6/9/12月码、"
                    "季度码还是其他枚举？"
                ),
                "evidence": {
                    "observed_values":
                        sorted(period_values),
                    "period_month_candidate":
                        period_month_candidate,
                    "canonical_requirement":
                        "FundamentalSnapshot."
                        "report_period必须为DATE，"
                        "period_type必须明确。",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_AVAILABLE_AT",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "update_date是否等于正式公告日期，"
                    "还是供应商内部更新日期？"
                ),
                "evidence": {
                    "snapshot_date_semantics":
                        "文件观测快照日期",
                    "required_rule":
                        "available_at <= decision_time",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_MONEY_UNIT",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "资产、收入、利润和现金流字段"
                    "是否以千元人民币计量？"
                ),
                "evidence": unit_candidate_summary,
            },
            {
                "category":
                    "FUNDAMENTAL_SHARE_UNIT",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "total_shares、b_shares、h_shares"
                    "和circulating_a_shares"
                    "是否以万股计量？"
                ),
                "evidence": {
                    "candidate_transform":
                        "multiply by 10000",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_PROFIT_SCOPE",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "after_tax_profit是否为公司整体净利润，"
                    "net_profit是否为归母净利润？"
                ),
                "evidence": unit_candidate_summary,
            },
            {
                "category":
                    "FUNDAMENTAL_EQUITY_SCOPE",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "net_assets是所有者权益合计，"
                    "还是归母所有者权益？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_TOTAL_CASH_FLOW",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "total_cash_flow的准确会计含义是什么？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_ZPG",
                "blocking_for":
                    "field_mapping",
                "question": (
                    "zpg字段的全称、单位和口径是什么？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_COMPANY_ID",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "FundamentalSnapshot要求company_id，"
                    "当前来源只有stock_code；"
                    "需要统一公司身份解析规则。"
                ),
            },
            {
                "category":
                    "CLASSIFICATION_HISTORY",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "来源行业和申万行业字段缺少"
                    "分类版本与有效起止时间，"
                    "当前只能视为snapshot_date观察到的分类。"
                ),
            },
            {
                "category":
                    "INSTRUMENT_ID_FORMAT",
                "blocking_for":
                    "identity_governance",
                "question": (
                    "当前日K使用6位stock_code作为"
                    "instrument_id；基本面必须保持一致，"
                    "未来如升级为000001.SZ需统一迁移。"
                ),
            },
        ]

        if structural_failures:
            overall_status = QualityStatus.FAILED
            blocks_downstream = True
            allows_current_snapshot_research = False
        else:
            overall_status = (
                QualityStatus.PENDING_CONFIRMATION
            )
            blocks_downstream = True
            allows_current_snapshot_research = True

        return FundamentalProfileReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            expected_schema=dict(EXPECTED_FIELD_TYPES),
            raw_fields=raw_fields,
            schema_comparison=schema_comparison,
            summary=summary,
            snapshot_counts=snapshot_counts,
            report_period_counts=
                report_period_counts,
            market_counts=market_counts,
            source_file_counts=source_file_counts,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            duplicate_samples=duplicate_samples,
            anomaly_counts=anomaly_counts,
            unit_candidate_summary=
                unit_candidate_summary,
            sample_rows=sample_rows,
            checks=checks,
            pending_confirmations=
                pending_confirmations,
            overall_status=overall_status,
            blocks_downstream=blocks_downstream,
            blocks_strict_historical_backtest=True,
            allows_current_snapshot_research=
                allows_current_snapshot_research,
        )


def render_markdown(
    report: FundamentalProfileReport,
) -> str:
    value = report.to_dict()
    summary = value["summary"]
    duplicate_summary = value[
        "duplicate_summary"
    ]
    anomalies = value["anomaly_counts"]
    unit_candidates = value[
        "unit_candidate_summary"
    ]

    lines = [
        "# TASK_013 基本面快照画像检查",
        "",
        f"- 数据库：`{report.database_uri}`",
        f"- 表：`{report.table_name}`",
        f"- 生成时间：`{value['generated_at']}`",
        (
            "- 状态："
            f"`{value['overall_status']}`"
        ),
        (
            "- 阻断严格历史回测："
            f"`{value['blocks_strict_historical_backtest']}`"
        ),
        (
            "- 允许当前快照研究："
            f"`{value['allows_current_snapshot_research']}`"
        ),
        "",
        "## 结构与覆盖",
        "",
        (
            f"- 实际字段数："
            f"{value['schema_comparison']['actual_field_count']}"
        ),
        (
            f"- 总行数："
            f"{summary.get('row_count')}"
        ),
        (
            f"- 股票数："
            f"{summary.get('stock_count')}"
        ),
        (
            "- 快照范围："
            f"{summary.get('min_snapshot_date')} "
            f"至 {summary.get('max_snapshot_date')}"
        ),
        (
            "- 重复额外行数："
            f"{duplicate_summary.get('duplicate_extra_row_count')}"
        ),
        "",
        "## 关键异常",
        "",
    ]

    for name, count in anomalies.items():
        lines.append(f"- `{name}`：{count}")

    lines.extend([
        "",
        "## 单位候选",
        "",
        (
            "- 千元人民币 + 万股公式匹配率："
            f"{unit_candidates.get('money_thousand_cny_and_shares_10k_match_ratio')}"
        ),
        (
            "- 万元人民币 + 万股公式匹配率："
            f"{unit_candidates.get('money_10k_cny_and_shares_10k_match_ratio')}"
        ),
        "",
        "## 待确认事项",
        "",
    ])

    for item in value["pending_confirmations"]:
        lines.append(
            f"- **{item['category']}**："
            f"{item['question']}"
        )

    lines.extend([
        "",
        "## 结论",
        "",
        (
            "该数据集可以继续完成标准映射和Provider开发，"
            "但在公告日期、报告期、单位和利润口径确认前，"
            "不得用于严格历史点时回测。"
        ),
        "",
    ])

    return "\n".join(lines)


def write_reports(
    report: FundamentalProfileReport,
    json_path: str | Path,
    markdown_path: str | Path,
) -> None:
    json_file = Path(json_path)
    markdown_file = Path(markdown_path)

    json_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    markdown_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_file.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown_file.write_text(
        render_markdown(report),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "对DolphinDB基本面快照表执行只读画像。"
        )
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8848,
    )
    parser.add_argument(
        "--username",
        default="admin",
    )
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_FUNDAMENTAL_DB",
    )
    parser.add_argument(
        "--table-name",
        default="stock_fundamental_snapshot",
    )
    parser.add_argument(
        "--output",
        default=(
            "reports/"
            "task_013_fundamental_profile.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        default=(
            "reports/"
            "task_013_fundamental_profile_final_check.md"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = resolve_password()

    settings = DolphinDBConnectionSettings(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
    )
    adapter = DolphinDBDataSourceAdapter(
        settings=settings,
        source_id="dolphindb_fundamental",
    )

    health = adapter.health_check()
    if health.status is not QualityStatus.PASSED:
        print(
            "DolphinDB健康检查失败："
            f"{health.description}"
        )
        return 1

    report = DolphinDBFundamentalProfiler(
        adapter=adapter,
        database_uri=args.database_uri,
        table_name=args.table_name,
    ).collect()

    write_reports(
        report,
        args.output,
        args.markdown_output,
    )

    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    )
    print(
        "\n画像报告已写入："
        f"{args.output}"
    )
    print(
        "检查摘要已写入："
        f"{args.markdown_output}"
    )
    return (
        0
        if report.overall_status
        is not QualityStatus.FAILED
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
