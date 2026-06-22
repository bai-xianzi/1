"""DolphinDB日K复权字段分层只读核验。

本模块不再尝试用一个全表公式解释所有记录，而是按以下维度分层：

1. deduct_value 是否为零；
2. 公司行为字段是否存在非零值；
3. adj_factor 是否发生变化；
4. 公司行为日与普通交易日。

全部查询只读，不修改 DolphinDB。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
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
_EPSILON = 0.000001
_PRICE_TOLERANCE = 0.01

_FORMULA_FIELDS = {
    "adj_price_equals_close_multiply_factor": (
        "close * adj_factor"
    ),
    "adj_price_equals_close_divide_factor": (
        "close / adj_factor"
    ),
    "adj_price_equals_close_multiply_factor_plus_deduct": (
        "close * adj_factor + deduct_value"
    ),
    "adj_price_equals_close_plus_deduct_multiply_factor": (
        "(close + deduct_value) * adj_factor"
    ),
    "adj_price_equals_close_multiply_factor_minus_deduct": (
        "close * adj_factor - deduct_value"
    ),
    "adj_price_equals_close_minus_deduct_multiply_factor": (
        "(close - deduct_value) * adj_factor"
    ),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    """把数据类、日期、枚举和非有限浮点数转成标准JSON值。"""

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
    if enum_value is not None and not isinstance(
        value,
        (str, bytes),
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


@dataclass(slots=True)
class AdjustmentLayerReport:
    """复权字段分层核验报告。"""

    database_uri: str
    table_name: str
    generated_at: datetime
    latest_trade_date: Any
    calendar_lag_days: int | None
    global_layers: dict[str, Any]
    formula_layers: list[dict[str, Any]]
    factor_change_summary: dict[str, Any]
    factor_change_samples: list[dict[str, Any]]
    conclusions: list[dict[str, Any]] = field(default_factory=list)
    pending_confirmations: list[dict[str, Any]] = field(
        default_factory=list
    )
    overall_status: QualityStatus = (
        QualityStatus.PENDING_CONFIRMATION
    )
    blocks_downstream: bool = True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self)


class DolphinDBAdjustmentLayerProfiler:
    """按字段状态和公司行为分层核验复权关系。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
        factor_chunk_size: int = 100,
    ) -> None:
        adapter._validate_database_uri(database_uri)
        adapter._validate_table_name(table_name)

        if (
            not isinstance(factor_chunk_size, int)
            or not 1 <= factor_chunk_size <= 500
        ):
            raise DataContractError(
                "factor_chunk_size 必须是 1 到 500 之间的整数。"
            )

        self.adapter = adapter
        self.database_uri = database_uri
        self.table_name = table_name
        self.factor_chunk_size = factor_chunk_size
        self._stock_codes_cache: list[str] | None = None
        self.transient_retry_count = 2

    @property
    def _table_ref(self) -> str:
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )

    def _run_readonly_with_retry(self, script: str) -> Any:
        """对偶发文件打开失败执行有限次只读重试。"""

        attempts = self.transient_retry_count + 1

        for attempt in range(attempts):
            try:
                return self.adapter.run_readonly_query(script)
            except DataContractError as exc:
                message = str(exc)

                if (
                    "Can't open file" not in message
                    or attempt >= attempts - 1
                ):
                    raise

                time.sleep(0.5 * (attempt + 1))

        raise DataContractError("只读查询重试流程异常结束。")

    def _query_one(self, script: str) -> dict[str, Any]:
        return _first_record(
            self._run_readonly_with_retry(script)
        )

    def _query_rows(self, script: str) -> list[dict[str, Any]]:
        return _records_from_result(
            self._run_readonly_with_retry(script)
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
        comparable_count = (
            DolphinDBAdjustmentLayerProfiler._as_int(comparable)
        )

        if comparable_count <= 0:
            return None

        return (
            DolphinDBAdjustmentLayerProfiler._as_int(matched)
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

        return (
            datetime.now(timezone.utc).date() - latest_date
        ).days

    @staticmethod
    def _quote_stock_code(stock_code: str) -> str:
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
        return [
            values[index:index + size]
            for index in range(0, len(values), size)
        ]

    @staticmethod
    def _action_expression() -> str:
        """公司行为字段任一非零时返回真。"""

        return (
            f"abs(nullFill(dividend, 0)) > {_EPSILON} "
            f"or abs(nullFill(bonus_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(convert_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(allot_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(allot_price, 0)) > {_EPSILON}"
        )

    def _load_stock_codes(self) -> list[str]:
        if self._stock_codes_cache is not None:
            return list(self._stock_codes_cache)

        rows = self._query_rows(
            f"""
            select distinct stock_code
            from {self._table_ref}
            order by stock_code
            """
        )

        result: list[str] = []

        for row in rows:
            value = row.get("stock_code")

            if value is None:
                continue

            code = str(value).strip()

            if not code:
                continue

            self._quote_stock_code(code)
            result.append(code)

        self._stock_codes_cache = result
        return list(result)

    @staticmethod
    def _layer_specs() -> list[
        tuple[str, bool, bool]
    ]:
        return [
            ("deduct_zero_action_zero", False, False),
            ("deduct_zero_action_nonzero", False, True),
            ("deduct_nonzero_action_zero", True, False),
            ("deduct_nonzero_action_nonzero", True, True),
        ]

    def _layer_condition(
        self,
        *,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> str:
        deduct_condition = (
            f"abs(deduct_value) > {_EPSILON}"
            if deduct_nonzero
            else f"abs(deduct_value) <= {_EPSILON}"
        )
        action_expression = self._action_expression()
        action_condition = (
            f"({action_expression})"
            if action_nonzero
            else f"not ({action_expression})"
        )
        return (
            f"({deduct_condition}) and ({action_condition})"
        )

    @staticmethod
    def _empty_global_layers() -> dict[str, Any]:
        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "row_count": 0,
            "adj_factor_equal_one_count": 0,
            "deduct_zero_count": 0,
            "deduct_nonzero_count": 0,
            "adj_price_equal_close_count": 0,
            "corporate_action_nonzero_count": 0,
        }

    @staticmethod
    def _empty_formula_layer(
        *,
        layer_name: str,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "layer_name": layer_name,
            "deduct_nonzero": deduct_nonzero,
            "action_nonzero": action_nonzero,
            "stock_code_count": 0,
            "chunk_count": 0,
            "comparable_row_count": 0,
        }

        for name in _FORMULA_FIELDS:
            result[f"{name}_match_count"] = 0

        return result

    def _collect_layer_statistics_chunked(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """按股票代码分批完成全局与公式分层统计。"""

        stock_codes = self._load_stock_codes()
        chunks = self._chunked(
            stock_codes,
            self.factor_chunk_size,
        )
        action = self._action_expression()

        global_total = self._empty_global_layers()
        global_total["stock_code_count"] = len(stock_codes)
        global_total["chunk_count"] = len(chunks)

        formula_totals = {
            layer_name: self._empty_formula_layer(
                layer_name=layer_name,
                deduct_nonzero=deduct_nonzero,
                action_nonzero=action_nonzero,
            )
            for (
                layer_name,
                deduct_nonzero,
                action_nonzero,
            ) in self._layer_specs()
        }

        for total in formula_totals.values():
            total["stock_code_count"] = len(stock_codes)
            total["chunk_count"] = len(chunks)

        for chunk in chunks:
            literals = ", ".join(
                self._quote_stock_code(code)
                for code in chunk
            )
            fields: list[str] = [
                "count(*) as row_count",
                (
                    "sum(iif("
                    f"abs(adj_factor - 1) <= {_EPSILON}, "
                    "1, 0)) as adj_factor_equal_one_count"
                ),
                (
                    "sum(iif("
                    f"abs(deduct_value) <= {_EPSILON}, "
                    "1, 0)) as deduct_zero_count"
                ),
                (
                    "sum(iif("
                    f"abs(deduct_value) > {_EPSILON}, "
                    "1, 0)) as deduct_nonzero_count"
                ),
                (
                    "sum(iif("
                    f"abs(adj_price - close) <= {_PRICE_TOLERANCE}, "
                    "1, 0)) as adj_price_equal_close_count"
                ),
                (
                    f"sum(iif({action}, 1, 0)) "
                    "as corporate_action_nonzero_count"
                ),
            ]

            for (
                layer_name,
                deduct_nonzero,
                action_nonzero,
            ) in self._layer_specs():
                condition = self._layer_condition(
                    deduct_nonzero=deduct_nonzero,
                    action_nonzero=action_nonzero,
                )
                fields.append(
                    "sum(iif("
                    f"({condition}) "
                    "and close != 0 "
                    "and adj_factor != 0 "
                    "and adj_price != 0, "
                    "1, 0)) "
                    f"as {layer_name}_comparable_row_count"
                )

                for name, formula in _FORMULA_FIELDS.items():
                    fields.append(
                        "sum(iif("
                        f"({condition}) "
                        "and close != 0 "
                        "and adj_factor != 0 "
                        "and adj_price != 0 "
                        f"and abs(adj_price - ({formula})) "
                        f"<= {_PRICE_TOLERANCE}, "
                        "1, 0)) "
                        f"as {layer_name}_{name}_match_count"
                    )

            result = self._query_one(
                "select\n    "
                + ",\n    ".join(fields)
                + f"""
                from {self._table_ref}
                where stock_code in [{literals}]
                """
            )

            for key in global_total:
                if key in {"stock_code_count", "chunk_count"}:
                    continue

                global_total[key] = (
                    self._as_int(global_total.get(key))
                    + self._as_int(result.get(key))
                )

            for (
                layer_name,
                _,
                _,
            ) in self._layer_specs():
                total = formula_totals[layer_name]
                comparable_key = (
                    f"{layer_name}_comparable_row_count"
                )
                total["comparable_row_count"] = (
                    self._as_int(
                        total.get("comparable_row_count")
                    )
                    + self._as_int(
                        result.get(comparable_key)
                    )
                )

                for name in _FORMULA_FIELDS:
                    source_key = (
                        f"{layer_name}_{name}_match_count"
                    )
                    target_key = f"{name}_match_count"
                    total[target_key] = (
                        self._as_int(total.get(target_key))
                        + self._as_int(
                            result.get(source_key)
                        )
                    )

        formula_layers: list[dict[str, Any]] = []

        for (
            layer_name,
            _,
            _,
        ) in self._layer_specs():
            total = formula_totals[layer_name]
            comparable = total.get("comparable_row_count")
            coverages = {
                name: self._coverage(
                    total.get(f"{name}_match_count"),
                    comparable,
                )
                for name in _FORMULA_FIELDS
            }
            total["candidate_coverages"] = coverages
            (
                total["best_candidate"],
                total["best_coverage"],
            ) = self._best_candidate(coverages)
            formula_layers.append(total)

        return global_total, formula_layers

    def _collect_global_layers(self) -> dict[str, Any]:
        action = self._action_expression()

        return self._query_one(
            f"""
            select
                count(*) as row_count,
                sum(
                    iif(
                        abs(adj_factor - 1) <= {_EPSILON},
                        1,
                        0
                    )
                ) as adj_factor_equal_one_count,
                sum(
                    iif(
                        abs(deduct_value) <= {_EPSILON},
                        1,
                        0
                    )
                ) as deduct_zero_count,
                sum(
                    iif(
                        abs(deduct_value) > {_EPSILON},
                        1,
                        0
                    )
                ) as deduct_nonzero_count,
                sum(
                    iif(
                        abs(adj_price - close)
                            <= {_PRICE_TOLERANCE},
                        1,
                        0
                    )
                ) as adj_price_equal_close_count,
                sum(
                    iif({action}, 1, 0)
                ) as corporate_action_nonzero_count
            from {self._table_ref}
            """
        )

    def _collect_formula_layer(
        self,
        *,
        layer_name: str,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> dict[str, Any]:
        deduct_condition = (
            f"abs(deduct_value) > {_EPSILON}"
            if deduct_nonzero
            else f"abs(deduct_value) <= {_EPSILON}"
        )
        action_expression = self._action_expression()
        action_condition = (
            f"({action_expression})"
            if action_nonzero
            else f"not ({action_expression})"
        )

        match_expressions = ",\n".join(
            (
                "sum(iif("
                f"abs(adj_price - ({formula})) "
                f"<= {_PRICE_TOLERANCE}, 1, 0)) "
                f"as {name}_match_count"
            )
            for name, formula in _FORMULA_FIELDS.items()
        )

        result = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                {match_expressions}
            from {self._table_ref}
            where
                close != 0
                and adj_factor != 0
                and adj_price != 0
                and {deduct_condition}
                and {action_condition}
            """
        )
        result["layer_name"] = layer_name
        result["deduct_nonzero"] = deduct_nonzero
        result["action_nonzero"] = action_nonzero

        comparable = result.get("comparable_row_count")
        coverages: dict[str, float | None] = {}

        for name in _FORMULA_FIELDS:
            coverages[name] = self._coverage(
                result.get(f"{name}_match_count"),
                comparable,
            )

        result["candidate_coverages"] = coverages
        best_name, best_coverage = self._best_candidate(coverages)
        result["best_candidate"] = best_name
        result["best_coverage"] = best_coverage
        return result

    @staticmethod
    def _best_candidate(
        coverages: dict[str, Any],
    ) -> tuple[str | None, float | None]:
        valid = {
            name: float(value)
            for name, value in coverages.items()
            if isinstance(value, (int, float))
            and math.isfinite(float(value))
        }

        if not valid:
            return None, None

        best_name = max(valid, key=valid.get)
        return best_name, valid[best_name]

    @staticmethod
    def _empty_factor_change_summary() -> dict[str, Any]:
        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "factor_change_count": 0,
            "factor_change_deduct_nonzero_count": 0,
            "factor_change_action_nonzero_count": 0,
            "factor_change_adj_price_equal_close_count": 0,
        }

    def _merge_factor_change_summary(
        self,
        total: dict[str, Any],
        part: dict[str, Any],
    ) -> None:
        for key in total:
            if key in {"stock_code_count", "chunk_count"}:
                continue

            total[key] = (
                self._as_int(total.get(key))
                + self._as_int(part.get(key))
            )

    def _collect_factor_changes(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        stock_codes = self._load_stock_codes()
        chunks = self._chunked(
            stock_codes,
            self.factor_chunk_size,
        )
        total = self._empty_factor_change_summary()
        total["stock_code_count"] = len(stock_codes)
        total["chunk_count"] = len(chunks)
        action = self._action_expression()
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
                    adj_price,
                    adj_factor,
                    deduct_value,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price,
                    move(adj_factor, 1) as prev_adj_factor,
                    move(close, 1) as prev_close,
                    move(adj_price, 1) as prev_adj_price
                from {self._table_ref}
                where stock_code in [{literals}]
                context by stock_code
                csort trade_date
            """

            part = self._query_one(
                f"""
                select
                    count(*) as factor_change_count,
                    sum(
                        iif(
                            abs(deduct_value) > {_EPSILON},
                            1,
                            0
                        )
                    ) as factor_change_deduct_nonzero_count,
                    sum(
                        iif({action}, 1, 0)
                    ) as factor_change_action_nonzero_count,
                    sum(
                        iif(
                            abs(adj_price - close)
                                <= {_PRICE_TOLERANCE},
                            1,
                            0
                        )
                    ) as factor_change_adj_price_equal_close_count
                from ({context_query})
                where
                    abs(adj_factor - prev_adj_factor)
                        > {_EPSILON}
                """
            )
            self._merge_factor_change_summary(total, part)

            samples.extend(
                self._query_rows(
                    f"""
                    select top 3
                        stock_code,
                        trade_date,
                        prev_close,
                        close,
                        prev_adj_price,
                        adj_price,
                        prev_adj_factor,
                        adj_factor,
                        deduct_value,
                        dividend,
                        bonus_share,
                        convert_share,
                        allot_share,
                        allot_price
                    from ({context_query})
                    where
                        abs(adj_factor - prev_adj_factor)
                            > {_EPSILON}
                    order by trade_date desc
                    """
                )
            )

        unique_samples: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

        for row in samples:
            key = (
                str(row.get("stock_code") or ""),
                str(row.get("trade_date") or ""),
            )
            unique_samples[key] = row

        ordered = list(unique_samples.values())
        ordered.sort(
            key=lambda row: str(row.get("trade_date") or ""),
            reverse=True,
        )
        return total, ordered[:50]

    def _evaluate(
        self,
        *,
        formula_layers: list[dict[str, Any]],
        factor_change_summary: dict[str, Any],
        calendar_lag_days: int | None,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        conclusions: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []

        nonempty_layers = [
            layer
            for layer in formula_layers
            if self._as_int(
                layer.get("comparable_row_count")
            ) > 0
        ]

        for layer in nonempty_layers:
            coverage = layer.get("best_coverage")
            confirmed = (
                isinstance(coverage, (int, float))
                and float(coverage) >= 0.99
            )
            conclusions.append(
                {
                    "topic": "ADJUSTMENT_LAYER_FORMULA",
                    "layer_name": layer.get("layer_name"),
                    "candidate": layer.get("best_candidate"),
                    "coverage": coverage,
                    "confirmed": confirmed,
                }
            )

            if not confirmed:
                pending.append(
                    {
                        "category": "ADJUSTMENT_LAYER_FORMULA",
                        "layer_name": layer.get("layer_name"),
                        "blocking": True,
                        "description": (
                            "该分层没有候选公式达到99%覆盖率。"
                        ),
                    }
                )

        factor_change_count = self._as_int(
            factor_change_summary.get("factor_change_count")
        )
        action_count = self._as_int(
            factor_change_summary.get(
                "factor_change_action_nonzero_count"
            )
        )
        deduct_count = self._as_int(
            factor_change_summary.get(
                "factor_change_deduct_nonzero_count"
            )
        )

        conclusions.append(
            {
                "topic": "FACTOR_CHANGE_ASSOCIATION",
                "factor_change_count": factor_change_count,
                "action_nonzero_coverage": self._coverage(
                    action_count,
                    factor_change_count,
                ),
                "deduct_nonzero_coverage": self._coverage(
                    deduct_count,
                    factor_change_count,
                ),
                "confirmed": factor_change_count > 0,
            }
        )

        if factor_change_count == 0:
            pending.append(
                {
                    "category": "FACTOR_CHANGE_ASSOCIATION",
                    "blocking": True,
                    "description": "没有取得复权因子变化记录。",
                }
            )

        freshness_confirmed = (
            calendar_lag_days is not None
            and calendar_lag_days <= 7
        )
        conclusions.append(
            {
                "topic": "DATA_FRESHNESS",
                "calendar_lag_days": calendar_lag_days,
                "confirmed": freshness_confirmed,
            }
        )

        if not freshness_confirmed:
            pending.append(
                {
                    "category": "DATA_FRESHNESS",
                    "blocking": True,
                    "description": (
                        "最新交易日期距运行日期超过7个日历日，"
                        "需要检查更新链路。"
                    ),
                }
            )

        return conclusions, pending

    def collect(self) -> AdjustmentLayerReport:
        latest = self._query_one(
            f"""
            select max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )
        latest_trade_date = latest.get("max_trade_date")
        lag_days = self._calendar_lag_days(latest_trade_date)
        (
            global_layers,
            formula_layers,
        ) = self._collect_layer_statistics_chunked()
        (
            factor_change_summary,
            factor_change_samples,
        ) = self._collect_factor_changes()
        conclusions, pending = self._evaluate(
            formula_layers=formula_layers,
            factor_change_summary=factor_change_summary,
            calendar_lag_days=lag_days,
        )

        return AdjustmentLayerReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            latest_trade_date=latest_trade_date,
            calendar_lag_days=lag_days,
            global_layers=global_layers,
            formula_layers=formula_layers,
            factor_change_summary=factor_change_summary,
            factor_change_samples=factor_change_samples,
            conclusions=conclusions,
            pending_confirmations=pending,
            overall_status=(
                QualityStatus.PENDING_CONFIRMATION
                if pending
                else QualityStatus.PASSED
            ),
            blocks_downstream=bool(pending),
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DolphinDB日K复权字段分层只读核验。"
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
        "--factor-chunk-size",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--output",
        default=(
            "reports/task_007_adjustment_layers.json"
        ),
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

        report = DolphinDBAdjustmentLayerProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
            factor_chunk_size=args.factor_chunk_size,
        ).collect()
    except DataContractError as exc:
        print(f"复权分层核验失败：{exc}")
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

    print("=== 日K复权字段分层核验完成 ===")
    print(f"来源：{report.database_uri}/{report.table_name}")
    print(f"最新日期：{report.latest_trade_date}")
    print(f"日历滞后天数：{report.calendar_lag_days}")

    print(
        "复权分层核验批次数："
        f"{report.global_layers.get('chunk_count')}"
    )

    for layer in report.formula_layers:
        print(
            f"{layer.get('layer_name')}："
            f"行数={layer.get('comparable_row_count')} "
            f"最佳公式={layer.get('best_candidate')} "
            f"覆盖率={layer.get('best_coverage')}"
        )

    print(
        "复权因子变化记录数："
        f"{report.factor_change_summary.get('factor_change_count')}"
    )
    print(
        "复权因子变化核验批次数："
        f"{report.factor_change_summary.get('chunk_count')}"
    )
    print(f"整体状态：{report.overall_status.value}")
    print(f"阻断下游：{report.blocks_downstream}")
    print(f"完整报告：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
