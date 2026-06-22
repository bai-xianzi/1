"""DolphinDB日K数据只读画像与质量验收。"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .data_contracts import DataContractError, QualityStatus
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from .dolphindb_probe import resolve_password


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

REQUIRED_FIELDS = (
    "stock_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "amount",
    "volume",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    """将日期、枚举、NaN和数据类转换为标准JSON值。"""

    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    enum_value = getattr(value, "value", None)
    if enum_value is not None and not isinstance(value, (str, bytes)):
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


def _records_from_result(result: Any) -> list[dict[str, Any]]:
    """把常见DolphinDB表格返回值转换为记录列表。"""

    if result is None:
        return []

    if isinstance(result, list):
        if any(not isinstance(item, dict) for item in result):
            raise DataContractError("画像结果列表中存在非字典记录。")
        return list(result)

    if isinstance(result, dict):
        return [dict(result)]

    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        try:
            records = to_dict(orient="records")
        except TypeError:
            records = to_dict("records")

        if any(not isinstance(item, dict) for item in records):
            raise DataContractError("画像结果无法转换为字典记录。")
        return list(records)

    raise DataContractError("暂不支持当前画像结果类型。")


def _first_record(result: Any) -> dict[str, Any]:
    records = _records_from_result(result)
    return records[0] if records else {}


@dataclass(slots=True)
class DailyKProfileReport:
    """日K表只读画像报告。"""

    database_uri: str
    table_name: str
    generated_at: datetime
    raw_fields: list[str]
    summary: dict[str, Any]
    null_counts: dict[str, Any]
    duplicate_summary: dict[str, Any]
    duplicate_samples: list[dict[str, Any]]
    ohlc_summary: dict[str, Any]
    change_formula_summary: dict[str, Any]
    change_formula_samples: list[dict[str, Any]]
    amount_volume_summary: dict[str, Any]
    adjustment_summary: dict[str, Any]
    checks: list[dict[str, Any]] = field(default_factory=list)
    pending_confirmations: list[dict[str, Any]] = field(default_factory=list)
    overall_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    blocks_downstream: bool = True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self)


class DolphinDBDailyKProfiler:
    """对DolphinDB日K表执行只读聚合画像。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
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

    def _query_one(self, script: str) -> dict[str, Any]:
        return _first_record(self.adapter.run_readonly_query(script))

    def _query_rows(self, script: str) -> list[dict[str, Any]]:
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

    @staticmethod
    def _as_int(value: Any) -> int:
        if value is None:
            return 0

        if isinstance(value, float) and math.isnan(value):
            return 0

        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return 0

    def collect(self) -> DailyKProfileReport:
        """执行画像并返回结构化报告。"""

        raw_fields = self._discover_fields()
        valid_fields = [
            name
            for name in raw_fields
            if _IDENTIFIER_PATTERN.fullmatch(name)
        ]
        available = set(valid_fields)

        summary = self._query_one(
            f"""
            select
                count(*) as row_count,
                nunique(stock_code, true) as stock_count,
                min(trade_date) as min_trade_date,
                max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )

        null_expressions = ",\n".join(
            f"sum(isNull({name})) as {name}_null_count"
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

        duplicate_summary: dict[str, Any] = {}
        duplicate_samples: list[dict[str, Any]] = []

        if {"stock_code", "trade_date"}.issubset(available):
            duplicate_summary = self._query_one(
                f"""
                select
                    count(*) as duplicate_group_count,
                    sum(duplicate_count - 1)
                        as duplicate_extra_row_count
                from (
                    select count(*) as duplicate_count
                    from {self._table_ref}
                    group by stock_code, trade_date
                    having count(*) > 1
                )
                """
            )
            duplicate_samples = self._query_rows(
                f"""
                select top 20
                    stock_code,
                    trade_date,
                    count(*) as duplicate_count
                from {self._table_ref}
                group by stock_code, trade_date
                having count(*) > 1
                order by duplicate_count desc
                """
            )
            duplicate_summary["duplicate_group_count"] = self._as_int(
                duplicate_summary.get("duplicate_group_count")
            )
            duplicate_summary["duplicate_extra_row_count"] = self._as_int(
                duplicate_summary.get("duplicate_extra_row_count")
            )

        ohlc_summary: dict[str, Any] = {}
        if {"open", "high", "low", "close"}.issubset(available):
            ohlc_summary = self._query_one(
                f"""
                select
                    count(*) as checked_row_count,
                    sum(isNull(open)) as open_null_count,
                    sum(isNull(high)) as high_null_count,
                    sum(isNull(low)) as low_null_count,
                    sum(isNull(close)) as close_null_count,
                    sum(iif(open <= 0, 1, 0)) as open_nonpositive_count,
                    sum(iif(high <= 0, 1, 0)) as high_nonpositive_count,
                    sum(iif(low <= 0, 1, 0)) as low_nonpositive_count,
                    sum(iif(close <= 0, 1, 0)) as close_nonpositive_count,
                    sum(iif(high < low, 1, 0)) as high_below_low_count,
                    sum(iif(high < open, 1, 0)) as high_below_open_count,
                    sum(iif(high < close, 1, 0)) as high_below_close_count,
                    sum(iif(low > open, 1, 0)) as low_above_open_count,
                    sum(iif(low > close, 1, 0)) as low_above_close_count
                from {self._table_ref}
                """
            )

            missing_keys = (
                "open_null_count",
                "high_null_count",
                "low_null_count",
                "close_null_count",
            )
            anomaly_keys = (
                "open_nonpositive_count",
                "high_nonpositive_count",
                "low_nonpositive_count",
                "close_nonpositive_count",
                "high_below_low_count",
                "high_below_open_count",
                "high_below_close_count",
                "low_above_open_count",
                "low_above_close_count",
            )
            ohlc_summary["missing_ohlc_count"] = sum(
                self._as_int(ohlc_summary.get(key))
                for key in missing_keys
            )
            ohlc_summary["ohlc_logic_anomaly_count"] = sum(
                self._as_int(ohlc_summary.get(key))
                for key in anomaly_keys
            )

        change_formula_summary: dict[str, Any] = {}
        change_formula_samples: list[dict[str, Any]] = []
        formula_fields = {
            "stock_code",
            "trade_date",
            "close",
            "price_change",
            "pct_change",
        }

        if formula_fields.issubset(available):
            context_query = f"""
                select
                    stock_code,
                    trade_date,
                    close,
                    price_change,
                    pct_change,
                    move(close, 1) as prev_close
                from {self._table_ref}
                context by stock_code
                csort trade_date
            """
            change_formula_summary = self._query_one(
                f"""
                select
                    count(*) as comparable_row_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001,
                            1,
                            0
                        )
                    ) as price_change_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (close / prev_close - 1)
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_standard_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (prev_close / close - 1)
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_inverse_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (prev_close - close)
                                    / prev_close
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_negated_standard_mismatch_count
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and prev_close != 0
                    and close != 0
                    and not isNull(price_change)
                    and not isNull(pct_change)
                """
            )
            change_formula_samples = self._query_rows(
                f"""
                select top 20
                    stock_code,
                    trade_date,
                    prev_close,
                    close,
                    price_change,
                    close - prev_close
                        as expected_price_change,
                    pct_change,
                    (close / prev_close - 1) * 100
                        as expected_standard_pct_change,
                    (prev_close / close - 1) * 100
                        as expected_inverse_pct_change,
                    (prev_close - close) / prev_close * 100
                        as expected_negated_standard_pct_change
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and prev_close != 0
                    and close != 0
                    and not isNull(price_change)
                    and not isNull(pct_change)
                    and (
                        abs(
                            price_change
                            - (close - prev_close)
                        ) > 0.0001
                        or abs(
                            pct_change
                            - (
                                (close / prev_close - 1)
                                * 100
                            )
                        ) > 0.01
                    )
                """
            )

        amount_volume_summary: dict[str, Any] = {}
        if {"amount", "volume"}.issubset(available):
            amount_volume_summary = self._query_one(
                f"""
                select
                    count(*) as comparable_row_count,
                    min(amount / volume)
                        as min_amount_per_volume,
                    avg(amount / volume)
                        as avg_amount_per_volume,
                    max(amount / volume)
                        as max_amount_per_volume
                from {self._table_ref}
                where
                    not isNull(amount)
                    and not isNull(volume)
                    and amount > 0
                    and volume > 0
                """
            )

        adjustment_summary: dict[str, Any] = {}
        if {"adj_factor", "adj_price"}.issubset(available):
            adjustment_summary = self._query_one(
                f"""
                select
                    count(*) as row_count,
                    sum(isNull(adj_factor))
                        as adj_factor_null_count,
                    sum(
                        iif(
                            isNull(adj_factor),
                            0,
                            iif(adj_factor == 1, 1, 0)
                        )
                    ) as adj_factor_equal_one_count,
                    sum(
                        iif(
                            isNull(adj_factor),
                            0,
                            iif(adj_factor != 1, 1, 0)
                        )
                    ) as adj_factor_non_one_count,
                    sum(isNull(adj_price))
                        as adj_price_null_count,
                    sum(
                        iif(
                            isNull(adj_price),
                            0,
                            iif(
                                isNull(close),
                                0,
                                iif(
                                    abs(adj_price - close) <= 0.0001,
                                    1,
                                    0
                                )
                            )
                        )
                    ) as adj_price_equal_close_count,
                    sum(
                        iif(
                            isNull(adj_price),
                            0,
                            iif(
                                isNull(close),
                                0,
                                iif(
                                    abs(adj_price - close) > 0.0001,
                                    1,
                                    0
                                )
                            )
                        )
                    ) as adj_price_close_difference_count
                from {self._table_ref}
                """
            )

        checks, pending, overall, blocks = self._evaluate(
            raw_fields=raw_fields,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            ohlc_summary=ohlc_summary,
            change_formula_summary=change_formula_summary,
        )

        return DailyKProfileReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            raw_fields=raw_fields,
            summary=summary,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            duplicate_samples=duplicate_samples,
            ohlc_summary=ohlc_summary,
            change_formula_summary=change_formula_summary,
            change_formula_samples=change_formula_samples,
            amount_volume_summary=amount_volume_summary,
            adjustment_summary=adjustment_summary,
            checks=checks,
            pending_confirmations=pending,
            overall_status=overall,
            blocks_downstream=blocks,
        )

    def _evaluate(
        self,
        *,
        raw_fields: list[str],
        null_counts: dict[str, Any],
        duplicate_summary: dict[str, Any],
        ohlc_summary: dict[str, Any],
        change_formula_summary: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        QualityStatus,
        bool,
    ]:
        """把画像指标转换成质量检查和待确认事项。"""

        checks: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []
        blocking_failure = False
        has_warning = False

        missing_fields = sorted(set(REQUIRED_FIELDS) - set(raw_fields))
        checks.append(
            {
                "check_name": "必需字段完整性",
                "status": (
                    QualityStatus.PASSED.value
                    if not missing_fields
                    else QualityStatus.FAILED.value
                ),
                "blocking": bool(missing_fields),
                "details": {"missing_fields": missing_fields},
            }
        )
        blocking_failure = blocking_failure or bool(missing_fields)

        key_null_count = (
            self._as_int(
                null_counts.get("stock_code_null_count")
            )
            + self._as_int(
                null_counts.get("trade_date_null_count")
            )
        )
        checks.append(
            {
                "check_name": "主键字段空值",
                "status": (
                    QualityStatus.PASSED.value
                    if key_null_count == 0
                    else QualityStatus.FAILED.value
                ),
                "blocking": key_null_count > 0,
                "details": {"null_count": key_null_count},
            }
        )
        blocking_failure = blocking_failure or key_null_count > 0

        duplicate_extra = self._as_int(
            duplicate_summary.get("duplicate_extra_row_count")
        )
        checks.append(
            {
                "check_name": "股票代码与交易日期重复",
                "status": (
                    QualityStatus.PASSED.value
                    if duplicate_extra == 0
                    else QualityStatus.FAILED.value
                ),
                "blocking": duplicate_extra > 0,
                "details": {
                    "duplicate_extra_row_count": duplicate_extra
                },
            }
        )
        blocking_failure = blocking_failure or duplicate_extra > 0

        ohlc_anomaly = self._as_int(
            ohlc_summary.get("ohlc_logic_anomaly_count")
        )
        checks.append(
            {
                "check_name": "OHLC逻辑关系",
                "status": (
                    QualityStatus.PASSED.value
                    if ohlc_anomaly == 0
                    else QualityStatus.WARNING.value
                ),
                "blocking": False,
                "details": {
                    "ohlc_logic_anomaly_count": ohlc_anomaly
                },
            }
        )
        has_warning = has_warning or ohlc_anomaly > 0

        comparable = self._as_int(
            change_formula_summary.get("comparable_row_count")
        )
        standard_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_standard_mismatch_count"
            )
        )
        inverse_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_inverse_mismatch_count"
            )
        )
        negated_standard_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_negated_standard_mismatch_count"
            )
        )
        formula_pending = comparable == 0 or standard_mismatch > 0

        checks.append(
            {
                "check_name": "涨跌幅公式一致性",
                "status": (
                    QualityStatus.PENDING_CONFIRMATION.value
                    if formula_pending
                    else QualityStatus.PASSED.value
                ),
                "blocking": formula_pending,
                "details": {
                    "comparable_row_count": comparable,
                    "standard_mismatch_count": standard_mismatch,
                    "inverse_mismatch_count": inverse_mismatch,
                    "negated_standard_mismatch_count": (
                        negated_standard_mismatch
                    ),
                },
            }
        )

        if formula_pending:
            pending.append(
                {
                    "category": "PCT_CHANGE_FORMULA",
                    "field": "pct_change",
                    "blocking": True,
                    "description": (
                        "需要确认pct_change采用常规涨跌幅、"
                        "反向分母公式、常规涨跌幅取反或其他公式。"
                    ),
                }
            )

        pending.extend(
            [
                {
                    "category": "ADJUSTMENT_METHOD",
                    "field": "open/high/low/close/adj_price",
                    "blocking": True,
                    "description": "价格复权口径尚未确认。",
                },
                {
                    "category": "VOLUME_UNIT",
                    "field": "volume",
                    "blocking": True,
                    "description": "成交量单位尚未确认。",
                },
                {
                    "category": "AMOUNT_UNIT",
                    "field": "amount",
                    "blocking": True,
                    "description": "成交额单位尚未确认。",
                },
                {
                    "category": "SHARE_UNIT",
                    "field": "float_shares/total_shares",
                    "blocking": True,
                    "description": "股本字段单位尚未确认。",
                },
                {
                    "category": "TRADE_DATE_SEMANTICS",
                    "field": "trade_date",
                    "blocking": False,
                    "description": "日期时区和时间语义尚未固化。",
                },
            ]
        )

        blocks = blocking_failure or any(
            bool(item.get("blocking")) for item in pending
        )

        if blocking_failure:
            overall = QualityStatus.FAILED
        elif pending:
            overall = QualityStatus.PENDING_CONFIRMATION
        elif has_warning:
            overall = QualityStatus.WARNING
        else:
            overall = QualityStatus.PASSED

        return checks, pending, overall, blocks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DolphinDB日K表只读画像与质量验收。"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_DAILY_K_DB",
    )
    parser.add_argument("--table", default="stock_daily_k")
    parser.add_argument(
        "--output",
        default="reports/task_005_daily_k_profile.json",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        settings = DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=resolve_password(),
        )
        adapter = DolphinDBDataSourceAdapter(settings=settings)
        health = adapter.health_check()

        if health.blocks_downstream:
            print(f"健康检查失败：{health.description}")
            return 1

        report = DolphinDBDailyKProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
        ).collect()
    except DataContractError as exc:
        print(f"画像失败：{exc}")
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    print("=== 日K数据只读画像完成 ===")
    print(f"来源：{report.database_uri}/{report.table_name}")
    print(f"总行数：{report.summary.get('row_count')}")
    print(f"股票数量：{report.summary.get('stock_count')}")
    print(f"最早日期：{report.summary.get('min_trade_date')}")
    print(f"最晚日期：{report.summary.get('max_trade_date')}")
    print(
        "重复额外行数："
        f"{report.duplicate_summary.get('duplicate_extra_row_count')}"
    )
    print(
        "OHLC逻辑异常计数："
        f"{report.ohlc_summary.get('ohlc_logic_anomaly_count')}"
    )
    print(
        "涨跌幅常规公式不匹配数："
        f"{report.change_formula_summary.get('pct_change_standard_mismatch_count')}"
    )
    print(
        "涨跌幅反向分母公式不匹配数："
        f"{report.change_formula_summary.get('pct_change_inverse_mismatch_count')}"
    )
    print(
        "涨跌幅常规公式取反不匹配数："
        f"{report.change_formula_summary.get('pct_change_negated_standard_mismatch_count')}"
    )
    print(
        "复权因子等于1行数："
        f"{report.adjustment_summary.get('adj_factor_equal_one_count')}"
    )
    print(
        "复权价等于收盘价行数："
        f"{report.adjustment_summary.get('adj_price_equal_close_count')}"
    )
    print(f"整体状态：{report.overall_status.value}")
    print(f"阻断下游：{report.blocks_downstream}")
    print(f"完整报告：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
