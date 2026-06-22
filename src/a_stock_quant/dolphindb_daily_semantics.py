"""DolphinDB日K字段语义只读核验。

本模块核验：
1. turnover_rate、volume、float_shares 的候选单位关系；
2. amount 与 volume、价格字段的候选尺度关系；
3. adj_price 与 close、adj_factor 的候选公式；
4. price_change 与 pct_change 的820条例外记录；
5. 数据最新日期的日历滞后。

所有查询均为只读聚合或有限样例查询。
"""

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
from .dolphindb_daily_profile import (
    _first_record,
    _records_from_result,
)
from .dolphindb_probe import resolve_password


_STOCK_CODE_PATTERN = re.compile(r"^[0-9A-Za-z._-]+$")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
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


@dataclass(slots=True)
class DailyKSemanticReport:
    """日K字段语义核验报告。"""

    database_uri: str
    table_name: str
    generated_at: datetime
    latest_trade_date: Any
    calendar_lag_days: int | None
    turnover_unit_analysis: dict[str, Any]
    amount_volume_analysis: dict[str, Any]
    adjustment_relation_analysis: dict[str, Any]
    price_change_anomaly_summary: dict[str, Any]
    price_change_anomaly_samples: list[dict[str, Any]]
    conclusions: list[dict[str, Any]] = field(default_factory=list)
    pending_confirmations: list[dict[str, Any]] = field(default_factory=list)
    overall_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    blocks_downstream: bool = True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self)


class DolphinDBDailyKSemanticProfiler:
    """日K字段候选语义关系的只读核验器。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
        anomaly_chunk_size: int = 100,
    ) -> None:
        adapter._validate_database_uri(database_uri)
        adapter._validate_table_name(table_name)

        if (
            not isinstance(anomaly_chunk_size, int)
            or not 1 <= anomaly_chunk_size <= 500
        ):
            raise DataContractError(
                "anomaly_chunk_size 必须是 1 到 500 之间的整数。"
            )

        self.adapter = adapter
        self.database_uri = database_uri
        self.table_name = table_name
        self.anomaly_chunk_size = anomaly_chunk_size

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

    @staticmethod
    def _coverage(
        matched: Any,
        comparable: Any,
    ) -> float | None:
        comparable_count = DolphinDBDailyKSemanticProfiler._as_int(
            comparable
        )

        if comparable_count <= 0:
            return None

        return (
            DolphinDBDailyKSemanticProfiler._as_int(matched)
            / comparable_count
        )

    @staticmethod
    def _calendar_lag_days(value: Any) -> int | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            latest_date = value.date()
        elif isinstance(value, date):
            latest_date = value
        else:
            text = str(value).strip()

            try:
                latest_date = datetime.fromisoformat(text).date()
            except ValueError:
                try:
                    latest_date = date.fromisoformat(text[:10])
                except ValueError:
                    return None

        return (datetime.now(timezone.utc).date() - latest_date).days

    @staticmethod
    def _quote_stock_code(stock_code: str) -> str:
        """生成安全的DolphinDB字符串字面量。"""

        if not _STOCK_CODE_PATTERN.fullmatch(stock_code):
            raise DataContractError(
                f"发现不安全的股票代码：{stock_code!r}"
            )

        return f'"{stock_code}"'

    @staticmethod
    def _chunked(
        values: list[str],
        size: int,
    ) -> list[list[str]]:
        """把股票代码拆成固定大小的小批次。"""

        return [
            values[index:index + size]
            for index in range(0, len(values), size)
        ]

    def _load_stock_codes(self) -> list[str]:
        """只读取股票代码列表，不加载日K全表。"""

        rows = self._query_rows(
            f"""
            select distinct stock_code
            from {self._table_ref}
            order by stock_code
            """
        )

        stock_codes: list[str] = []

        for row in rows:
            value = row.get("stock_code")

            if value is None:
                continue

            code = str(value).strip()

            if not code:
                continue

            self._quote_stock_code(code)
            stock_codes.append(code)

        return stock_codes

    @staticmethod
    def _empty_anomaly_summary() -> dict[str, Any]:
        """生成分批异常统计的初始累计值。"""

        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "total_context_row_count": 0,
            "comparable_row_count": 0,
            "anomaly_row_count": 0,
            "anomaly_adj_factor_changed_count": 0,
            "anomaly_dividend_present_count": 0,
            "anomaly_dividend_nonzero_count": 0,
            "anomaly_bonus_share_present_count": 0,
            "anomaly_bonus_share_nonzero_count": 0,
            "anomaly_convert_share_present_count": 0,
            "anomaly_convert_share_nonzero_count": 0,
            "anomaly_allot_share_present_count": 0,
            "anomaly_allot_share_nonzero_count": 0,
            "anomaly_allot_price_present_count": 0,
            "anomaly_allot_price_nonzero_count": 0,
            "pct_change_negated_formula_exception_count": 0,
        }

    def _merge_anomaly_summary(
        self,
        total: dict[str, Any],
        part: dict[str, Any],
    ) -> None:
        """把一个股票批次的统计合并到总计。"""

        for key in total:
            if key in {"stock_code_count", "chunk_count"}:
                continue

            total[key] = (
                self._as_int(total.get(key))
                + self._as_int(part.get(key))
            )

    def _collect_anomalies_chunked(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """按股票代码分批核验异常，避免全表宽查询导致内存溢出。"""

        stock_codes = self._load_stock_codes()
        chunks = self._chunked(
            stock_codes,
            self.anomaly_chunk_size,
        )
        total = self._empty_anomaly_summary()
        total["stock_code_count"] = len(stock_codes)
        total["chunk_count"] = len(chunks)

        samples: list[dict[str, Any]] = []

        for chunk in chunks:
            literals = ", ".join(
                self._quote_stock_code(code)
                for code in chunk
            )

            context_query = f"""
                select
                    stock_code,
                    trade_date,
                    close,
                    price_change,
                    pct_change,
                    adj_factor,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price,
                    move(close, 1) as prev_close,
                    move(adj_factor, 1) as prev_adj_factor
                from {self._table_ref}
                where stock_code in [{literals}]
                context by stock_code
                csort trade_date
            """

            part = self._query_one(
                f"""
                select
                    count(*) as total_context_row_count,
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
                    ) as anomaly_row_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(prev_adj_factor)
                            and not isNull(adj_factor)
                            and abs(
                                adj_factor - prev_adj_factor
                            ) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_adj_factor_changed_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(dividend),
                            1,
                            0
                        )
                    ) as anomaly_dividend_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(dividend)
                            and abs(dividend) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_dividend_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(bonus_share),
                            1,
                            0
                        )
                    ) as anomaly_bonus_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(bonus_share)
                            and abs(bonus_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_bonus_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(convert_share),
                            1,
                            0
                        )
                    ) as anomaly_convert_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(convert_share)
                            and abs(convert_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_convert_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_share),
                            1,
                            0
                        )
                    ) as anomaly_allot_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_share)
                            and abs(allot_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_allot_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_price),
                            1,
                            0
                        )
                    ) as anomaly_allot_price_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_price)
                            and abs(allot_price) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_allot_price_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and prev_close != 0
                            and not isNull(pct_change)
                            and abs(
                                pct_change
                                - round(
                                    (prev_close - close)
                                    / prev_close
                                    * 100,
                                    2
                                )
                            ) > 0.000001,
                            1,
                            0
                        )
                    ) as pct_change_negated_formula_exception_count
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and not isNull(price_change)
                """
            )
            self._merge_anomaly_summary(total, part)

            part_samples = self._query_rows(
                f"""
                select top 5
                    stock_code,
                    trade_date,
                    prev_close,
                    close,
                    price_change,
                    close - prev_close
                        as expected_price_change,
                    abs(
                        price_change
                        - (close - prev_close)
                    ) as price_change_error,
                    pct_change,
                    round(
                        (prev_close - close)
                        / prev_close
                        * 100,
                        2
                    ) as expected_negated_pct_change,
                    prev_adj_factor,
                    adj_factor,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and not isNull(price_change)
                    and abs(
                        price_change
                        - (close - prev_close)
                    ) > 0.0001
                order by
                    price_change_error desc,
                    trade_date desc
                """
            )
            samples.extend(part_samples)

        unique_samples: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

        for row in samples:
            key = (
                str(row.get("stock_code") or ""),
                str(row.get("trade_date") or ""),
            )
            existing = unique_samples.get(key)
            current_error = float(
                row.get("price_change_error") or 0
            )
            existing_error = float(
                existing.get("price_change_error") or 0
            ) if existing is not None else -1.0

            if existing is None or current_error > existing_error:
                unique_samples[key] = row

        ordered_samples = list(unique_samples.values())
        ordered_samples.sort(
            key=lambda row: (
                float(row.get("price_change_error") or 0),
                str(row.get("trade_date") or ""),
            ),
            reverse=True,
        )

        return total, ordered_samples[:50]

    def collect(self) -> DailyKSemanticReport:
        """执行字段语义候选关系核验。"""

        latest = self._query_one(
            f"""
            select
                max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )
        latest_trade_date = latest.get("max_trade_date")

        turnover = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares
                                / 100.0,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as volume_share_float_10k_percent_match_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as volume_lot_float_10k_percent_match_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares
                                * 100.0,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as same_unit_percent_match_count
            from {self._table_ref}
            where
                not isNull(turnover_rate)
                and not isNull(volume)
                and not isNull(float_shares)
                and float_shares > 0
            """
        )
        turnover_comparable = turnover.get("comparable_row_count")
        turnover["candidate_coverages"] = {
            "volume_share_float_10k_turnover_percent": self._coverage(
                turnover.get(
                    "volume_share_float_10k_percent_match_count"
                ),
                turnover_comparable,
            ),
            "volume_lot_float_10k_turnover_percent": self._coverage(
                turnover.get(
                    "volume_lot_float_10k_percent_match_count"
                ),
                turnover_comparable,
            ),
            "same_unit_turnover_percent": self._coverage(
                turnover.get("same_unit_percent_match_count"),
                turnover_comparable,
            ),
        }

        amount_volume = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            amount / volume / close - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_1_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            / (volume * 100.0)
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_1_100_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 100.0
                            / volume
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_100_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 10000.0
                            / volume
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_10000_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 100.0
                            / volume
                            / adj_price
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_100_1_adj_price_match_count
            from {self._table_ref}
            where
                not isNull(amount)
                and not isNull(volume)
                and not isNull(close)
                and not isNull(adj_price)
                and amount > 0
                and volume > 0
                and close > 0
                and adj_price > 0
            """
        )
        amount_comparable = amount_volume.get("comparable_row_count")
        amount_volume["candidate_coverages"] = {
            "amount_scale_1_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_1_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_1_volume_scale_100_close": self._coverage(
                amount_volume.get("scale_1_100_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_100_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_100_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_10000_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_10000_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_100_volume_scale_1_adj_price": self._coverage(
                amount_volume.get(
                    "scale_100_1_adj_price_match_count"
                ),
                amount_comparable,
            ),
        }

        adjustment = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (close * adj_factor)
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (close / adj_factor)
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_divide_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                close * adj_factor
                                - deduct_value
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_minus_deduct_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                (close - deduct_value)
                                * adj_factor
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_minus_deduct_multiply_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                close * adj_factor
                                + deduct_value
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_plus_deduct_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                (close + deduct_value)
                                * adj_factor
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_plus_deduct_multiply_factor_match_count,
                sum(
                    iif(
                        not isNull(deduct_value)
                        and abs(deduct_value) > 0.000001,
                        1,
                        0
                    )
                ) as deduct_value_nonzero_count
            from {self._table_ref}
            where
                not isNull(close)
                and not isNull(adj_factor)
                and not isNull(adj_price)
                and not isNull(deduct_value)
                and close != 0
                and adj_factor != 0
                and adj_price != 0
                and close * adj_factor != deduct_value
                and close != deduct_value
            """
        )
        adjustment_comparable = adjustment.get("comparable_row_count")
        adjustment["candidate_coverages"] = {
            "adj_price_equals_close_multiply_adj_factor": self._coverage(
                adjustment.get(
                    "close_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_divide_adj_factor": self._coverage(
                adjustment.get(
                    "close_divide_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_multiply_factor_minus_deduct": self._coverage(
                adjustment.get(
                    "close_multiply_factor_minus_deduct_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_minus_deduct_multiply_factor": self._coverage(
                adjustment.get(
                    "close_minus_deduct_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_multiply_factor_plus_deduct": self._coverage(
                adjustment.get(
                    "close_multiply_factor_plus_deduct_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_plus_deduct_multiply_factor": self._coverage(
                adjustment.get(
                    "close_plus_deduct_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
        }

        (
            anomaly_summary,
            anomaly_samples,
        ) = self._collect_anomalies_chunked()

        conclusions, pending = self._evaluate(
            turnover=turnover,
            amount_volume=amount_volume,
            adjustment=adjustment,
            anomaly_summary=anomaly_summary,
        )

        return DailyKSemanticReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            latest_trade_date=latest_trade_date,
            calendar_lag_days=self._calendar_lag_days(
                latest_trade_date
            ),
            turnover_unit_analysis=turnover,
            amount_volume_analysis=amount_volume,
            adjustment_relation_analysis=adjustment,
            price_change_anomaly_summary=anomaly_summary,
            price_change_anomaly_samples=anomaly_samples,
            conclusions=conclusions,
            pending_confirmations=pending,
            overall_status=(
                QualityStatus.PENDING_CONFIRMATION
                if pending
                else QualityStatus.PASSED
            ),
            blocks_downstream=bool(pending),
        )

    @staticmethod
    def _best_candidate(
        coverages: dict[str, Any],
    ) -> tuple[str | None, float | None]:
        valid = {
            key: value
            for key, value in coverages.items()
            if isinstance(value, (int, float))
            and not (
                isinstance(value, float)
                and math.isnan(value)
            )
        }

        if not valid:
            return None, None

        name = max(valid, key=valid.get)
        return name, float(valid[name])

    def _evaluate(
        self,
        *,
        turnover: dict[str, Any],
        amount_volume: dict[str, Any],
        adjustment: dict[str, Any],
        anomaly_summary: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        conclusions: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []

        turnover_name, turnover_coverage = self._best_candidate(
            turnover.get("candidate_coverages", {})
        )
        turnover_confirmed = (
            turnover_coverage is not None
            and turnover_coverage >= 0.99
        )
        conclusions.append(
            {
                "topic": "TURNOVER_AND_SHARE_UNIT",
                "candidate": turnover_name,
                "coverage": turnover_coverage,
                "confirmed": turnover_confirmed,
            }
        )

        if not turnover_confirmed:
            pending.append(
                {
                    "category": "TURNOVER_AND_SHARE_UNIT",
                    "blocking": True,
                    "description": (
                        "换手率、成交量和流通股本的候选关系"
                        "未达到99%覆盖率。"
                    ),
                }
            )

        amount_name, amount_coverage = self._best_candidate(
            amount_volume.get("candidate_coverages", {})
        )
        amount_confirmed = (
            amount_coverage is not None
            and amount_coverage >= 0.95
        )
        conclusions.append(
            {
                "topic": "AMOUNT_VOLUME_SCALE",
                "candidate": amount_name,
                "coverage": amount_coverage,
                "confirmed": amount_confirmed,
            }
        )

        if not amount_confirmed:
            pending.append(
                {
                    "category": "AMOUNT_VOLUME_SCALE",
                    "blocking": True,
                    "description": (
                        "成交额、成交量和价格的候选尺度关系"
                        "未达到95%覆盖率。"
                    ),
                }
            )

        adjustment_name, adjustment_coverage = self._best_candidate(
            adjustment.get("candidate_coverages", {})
        )
        adjustment_confirmed = (
            adjustment_coverage is not None
            and adjustment_coverage >= 0.999
        )
        conclusions.append(
            {
                "topic": "ADJUSTMENT_FORMULA",
                "candidate": adjustment_name,
                "coverage": adjustment_coverage,
                "confirmed": adjustment_confirmed,
            }
        )

        if not adjustment_confirmed:
            pending.append(
                {
                    "category": "ADJUSTMENT_FORMULA",
                    "blocking": True,
                    "description": (
                        "adj_price与close、adj_factor的候选公式"
                        "未达到99.9%覆盖率。"
                    ),
                }
            )

        anomaly_count = self._as_int(
            anomaly_summary.get("anomaly_row_count")
        )
        pct_exception_count = self._as_int(
            anomaly_summary.get(
                "pct_change_negated_formula_exception_count"
            )
        )
        conclusions.append(
            {
                "topic": "PRICE_CHANGE_EXCEPTION",
                "anomaly_row_count": anomaly_count,
                "pct_change_exception_count": pct_exception_count,
                "confirmed": anomaly_count == pct_exception_count,
            }
        )

        if anomaly_count > 0:
            pending.append(
                {
                    "category": "PRICE_CHANGE_EXCEPTION",
                    "blocking": True,
                    "description": (
                        f"仍有{anomaly_count}条price_change例外记录"
                        "需要分类核验。"
                    ),
                }
            )

        return conclusions, pending


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DolphinDB日K字段语义只读核验。"
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
        "--anomaly-chunk-size",
        type=int,
        default=100,
        help="异常核验每批股票数量，默认100，范围1到500。",
    )
    parser.add_argument(
        "--output",
        default="reports/task_006_daily_k_semantics.json",
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

        report = DolphinDBDailyKSemanticProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
            anomaly_chunk_size=args.anomaly_chunk_size,
        ).collect()
    except DataContractError as exc:
        print(f"语义核验失败：{exc}")
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

    print("=== 日K字段语义只读核验完成 ===")
    print(f"来源：{report.database_uri}/{report.table_name}")
    print(f"最新日期：{report.latest_trade_date}")
    print(f"日历滞后天数：{report.calendar_lag_days}")

    for conclusion in report.conclusions:
        print(
            f"{conclusion.get('topic')}："
            f"{conclusion.get('candidate', '')} "
            f"覆盖率={conclusion.get('coverage', '')} "
            f"确认={conclusion.get('confirmed')}"
        )

    print(
        "price_change例外数："
        f"{report.price_change_anomaly_summary.get('anomaly_row_count')}"
    )
    print(
        "异常核验批次数："
        f"{report.price_change_anomaly_summary.get('chunk_count')}"
    )
    print(f"整体状态：{report.overall_status.value}")
    print(f"阻断下游：{report.blocks_downstream}")
    print(f"完整报告：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
