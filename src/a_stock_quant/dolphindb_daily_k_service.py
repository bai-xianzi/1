"""A股日K标准映射插件与批量标准化读取服务。

职责：
1. 从数据集注册配置加载当前日K映射合同；
2. 通过 DolphinDB 只读适配器按股票和日期范围读取原始记录；
3. 为每只股票补充上一交易日收盘价上下文；
4. 使用通用 CanonicalMappingEngine 输出标准对象；
5. 生成质量标记、来源扩展和字段级血缘；
6. 严格限制请求不得超过快照覆盖截止日期。

本模块不会写入、更新或删除 DolphinDB 数据。
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from .data_contracts import DataContractError, SourceType
from .dataset_registry import (
    CanonicalMappingEngine,
    DatasetRegistration,
    DatasetRegistry,
    MappingExecutionResult,
    TransformRegistry,
)
from .dolphindb_adapter import DolphinDBDataSourceAdapter


_INSTRUMENT_PATTERN = re.compile(r"^[0-9A-Za-z._-]+$")
_MAX_INSTRUMENTS = 100
_MAX_ROWS_PER_INSTRUMENT = 5_000
_PRICE_TOLERANCE = 0.0001
_ADJ_TOLERANCE = 0.01


def _as_date(value: Any, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if value is None:
        raise DataContractError(f"{field_name} 不能为空。")

    text = str(value).strip()

    if not text:
        raise DataContractError(f"{field_name} 不能为空。")

    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError as exc:
            raise DataContractError(
                f"{field_name} 不是合法日期：{value!r}"
            ) from exc


def _ddb_date_literal(value: date) -> str:
    return value.strftime("%Y.%m.%d")


def _quote_instrument(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError("instrument_id 不能为空。")

    normalized = value.strip()

    if not _INSTRUMENT_PATTERN.fullmatch(normalized):
        raise DataContractError(
            f"instrument_id 包含不安全字符：{value!r}"
        )

    return f'"{normalized}"'


def _records_from_result(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []

    if isinstance(result, list):
        if any(not isinstance(item, dict) for item in result):
            raise DataContractError(
                "DolphinDB 返回列表中存在非字典记录。"
            )

        return [dict(item) for item in result]

    to_dict = getattr(result, "to_dict", None)
    columns = getattr(result, "columns", None)

    if callable(to_dict) and columns is not None:
        try:
            records = to_dict(orient="records")
        except TypeError:
            records = to_dict("records")

        if any(not isinstance(item, dict) for item in records):
            raise DataContractError(
                "DolphinDB 表格结果无法转换为字典记录。"
            )

        return [dict(item) for item in records]

    raise DataContractError(
        "暂不支持当前 DolphinDB 返回值类型。"
    )


@dataclass(frozen=True, slots=True)
class DailyKReadRequest:
    """标准化日K读取请求。"""

    instrument_ids: tuple[str, ...]
    start_date: date
    end_date: date
    limit_per_instrument: int = 5_000

    def __post_init__(self) -> None:
        if not self.instrument_ids:
            raise DataContractError(
                "instrument_ids 至少包含一个证券代码。"
            )

        if len(self.instrument_ids) > _MAX_INSTRUMENTS:
            raise DataContractError(
                f"一次最多读取 {_MAX_INSTRUMENTS} 只证券。"
            )

        normalized: list[str] = []

        for value in self.instrument_ids:
            _quote_instrument(value)
            normalized.append(value.strip())

        if len(set(normalized)) != len(normalized):
            raise DataContractError(
                "instrument_ids 不允许重复。"
            )

        object.__setattr__(
            self,
            "instrument_ids",
            tuple(normalized),
        )

        if self.start_date > self.end_date:
            raise DataContractError(
                "start_date 不能晚于 end_date。"
            )

        if (
            not isinstance(self.limit_per_instrument, int)
            or not 1
            <= self.limit_per_instrument
            <= _MAX_ROWS_PER_INSTRUMENT
        ):
            raise DataContractError(
                "limit_per_instrument 必须是1到5000之间的整数。"
            )


@dataclass(slots=True)
class StandardizedDailyKRecord:
    """一条来源日K记录对应的标准化输出。"""

    source_record_id: str
    primary_key: dict[str, Any]
    canonical_objects: dict[str, dict[str, Any]]
    source_extensions: dict[str, Any]
    quality_flags: list[str]
    lineage: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StandardizedDailyKBatch:
    """一次标准化读取的输出批次。"""

    dataset_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    request: dict[str, Any]
    source_row_count: int
    standardized_record_count: int
    records: list[StandardizedDailyKRecord]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["request"] = {
            key: (
                value.isoformat()
                if isinstance(value, date)
                else value
            )
            for key, value in self.request.items()
        }
        return result


class DailyKTransformRegistry(TransformRegistry):
    """日K插件专用转换函数集合。"""

    def __init__(self) -> None:
        super().__init__()
        self.register(
            "previous_close_from_context",
            self._previous_close_from_context,
        )
        self.register(
            "vwap_from_amount_volume",
            self._vwap_from_amount_volume,
        )
        self.register(
            "market_cap_from_close_shares_10k",
            self._market_cap_from_close_shares_10k,
        )

    @staticmethod
    def _previous_close_from_context(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        if len(values) != 1:
            raise DataContractError(
                "前收盘转换要求一个 close 来源值。"
            )

        return context.get("prev_close")

    @staticmethod
    def _vwap_from_amount_volume(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        if len(values) != 2:
            raise DataContractError(
                "VWAP转换要求 amount 和 volume 两个来源值。"
            )

        amount, volume = values

        if amount is None or volume in {None, 0}:
            return None

        return amount / volume

    @staticmethod
    def _market_cap_from_close_shares_10k(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        if len(values) != 2:
            raise DataContractError(
                "市值转换要求 close 和股本两个来源值。"
            )

        close, shares_10k = values

        if close is None or shares_10k is None:
            return None

        return close * shares_10k * 10_000


class DolphinDBDailyKStandardizedService:
    """从 DolphinDB 读取并输出标准日K对象。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        registration: DatasetRegistration,
        *,
        mapping_engine: CanonicalMappingEngine | None = None,
    ) -> None:
        if registration.source_type is not SourceType.DOLPHINDB:
            raise DataContractError(
                "日K标准化服务只接受 DolphinDB 数据集注册。"
            )

        if not registration.enabled:
            raise DataContractError(
                f"数据集已禁用：{registration.dataset_id}"
            )

        locator = registration.source_locator
        database_uri = locator.get("database_uri")
        table_name = locator.get("table_name")

        if not isinstance(database_uri, str):
            raise DataContractError(
                "注册配置缺少 database_uri。"
            )

        if not isinstance(table_name, str):
            raise DataContractError(
                "注册配置缺少 table_name。"
            )

        adapter._validate_database_uri(database_uri)
        adapter._validate_table_name(table_name)

        if (
            registration.date_field is None
            or registration.entity_field is None
        ):
            raise DataContractError(
                "日K注册配置必须提供 date_field 和 entity_field。"
            )

        self.adapter = adapter
        self.registration = registration
        self.database_uri = database_uri
        self.table_name = table_name
        self.date_field = registration.date_field
        self.entity_field = registration.entity_field
        self.mapping_engine = mapping_engine or CanonicalMappingEngine(
            DailyKTransformRegistry()
        )
        self.coverage_end_date = self._parse_coverage_end_date(
            registration.coverage_version
        )

    @classmethod
    def from_registry_file(
        cls,
        adapter: DolphinDBDataSourceAdapter,
        registration_path: str | Path,
    ) -> "DolphinDBDailyKStandardizedService":
        registry = DatasetRegistry()
        registration = registry.load_json(registration_path)
        return cls(adapter, registration)

    @staticmethod
    def _parse_coverage_end_date(
        coverage_version: str,
    ) -> date:
        if "@" not in coverage_version:
            raise DataContractError(
                "coverage_version 必须包含 @YYYY-MM-DD。"
            )

        _, date_text = coverage_version.rsplit("@", 1)
        return _as_date(
            date_text,
            "coverage_version 截止日期",
        )

    @property
    def _table_ref(self) -> str:
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )

    def _validate_request(
        self,
        request: DailyKReadRequest,
    ) -> None:
        if request.end_date > self.coverage_end_date:
            raise DataContractError(
                "请求结束日期超出数据集覆盖范围："
                f"{request.end_date} > {self.coverage_end_date}"
            )

    def _read_previous_close(
        self,
        instrument_id: str,
        start_date: date,
    ) -> float | None:
        quoted = _quote_instrument(instrument_id)
        script = f"""
            select top 1 close
            from {self._table_ref}
            where
                {self.entity_field} = {quoted}
                and {self.date_field}
                    < {_ddb_date_literal(start_date)}
            order by {self.date_field} desc
        """
        records = _records_from_result(
            self.adapter.run_readonly_query(script)
        )

        if not records:
            return None

        value = records[0].get("close")
        return None if value is None else float(value)

    def _read_source_rows(
        self,
        instrument_id: str,
        request: DailyKReadRequest,
    ) -> list[dict[str, Any]]:
        quoted = _quote_instrument(instrument_id)
        fields = ", ".join(
            self.registration.source_fields
        )
        script = f"""
            select top {request.limit_per_instrument}
                {fields}
            from {self._table_ref}
            where
                {self.entity_field} = {quoted}
                and {self.date_field}
                    >= {_ddb_date_literal(request.start_date)}
                and {self.date_field}
                    <= {_ddb_date_literal(request.end_date)}
            order by {self.date_field}
        """
        return _records_from_result(
            self.adapter.run_readonly_query(script)
        )

    @staticmethod
    def _normalise_date_fields(
        mapping_result: MappingExecutionResult,
    ) -> None:
        daily_bar = mapping_result.outputs.get("DailyBar")

        if daily_bar is not None and "trade_date" in daily_bar:
            daily_bar["trade_date"] = _as_date(
                daily_bar["trade_date"],
                "DailyBar.trade_date",
            )

        ownership = mapping_result.outputs.get(
            "OwnershipSnapshot"
        )

        if ownership is not None and "as_of_date" in ownership:
            ownership["as_of_date"] = _as_date(
                ownership["as_of_date"],
                "OwnershipSnapshot.as_of_date",
            )

    @staticmethod
    def _quality_flags(
        row: Mapping[str, Any],
        prev_close: float | None,
    ) -> list[str]:
        flags: list[str] = []

        close = row.get("close")
        source_price_change = row.get("price_change")
        source_pct_change = row.get("pct_change")
        adj_factor = row.get("adj_factor")
        deduct_value = row.get("deduct_value")
        adj_price = row.get("adj_price")

        if prev_close is None:
            flags.append("MISSING_PRE_CLOSE")
        elif close is not None:
            expected_change = float(close) - prev_close

            if (
                source_price_change is not None
                and abs(
                    float(source_price_change)
                    - expected_change
                ) > _PRICE_TOLERANCE
            ):
                flags.append(
                    "SOURCE_PRICE_CHANGE_MISMATCH"
                )

            if (
                source_pct_change is not None
                and prev_close != 0
            ):
                expected_standard = (
                    (float(close) / prev_close - 1) * 100
                )
                expected_source = round(
                    -expected_standard,
                    2,
                )

                if abs(
                    float(source_pct_change)
                    - expected_source
                ) > 0.000001:
                    flags.append(
                        "SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH"
                    )
                else:
                    flags.append(
                        "SOURCE_PCT_CHANGE_SIGN_INVERTED"
                    )

        if all(
            value is not None
            for value in (
                close,
                adj_factor,
                deduct_value,
                adj_price,
            )
        ):
            expected_adj_price = (
                float(close)
                * float(adj_factor)
                + float(deduct_value)
            )

            if abs(
                float(adj_price) - expected_adj_price
            ) > _ADJ_TOLERANCE:
                flags.append(
                    "SOURCE_ADJ_FORMULA_MISMATCH"
                )

        return sorted(set(flags))

    @staticmethod
    def _source_record_id(
        row: Mapping[str, Any],
    ) -> str:
        instrument_id = str(row.get("stock_code") or "")
        trade_date = _as_date(
            row.get("trade_date"),
            "trade_date",
        )
        return f"{instrument_id}|{trade_date.isoformat()}"

    def _map_one(
        self,
        row: Mapping[str, Any],
        prev_close: float | None,
    ) -> StandardizedDailyKRecord:
        result = self.mapping_engine.map_record(
            self.registration,
            row,
            context={"prev_close": prev_close},
        )
        self._normalise_date_fields(result)

        instrument_id = str(row.get("stock_code") or "")
        trade_date = _as_date(
            row.get("trade_date"),
            "trade_date",
        )

        return StandardizedDailyKRecord(
            source_record_id=self._source_record_id(row),
            primary_key={
                "instrument_id": instrument_id,
                "trade_date": trade_date,
            },
            canonical_objects=result.outputs,
            source_extensions=result.source_extensions,
            quality_flags=self._quality_flags(
                row,
                prev_close,
            ),
            lineage=result.lineage,
        )

    def read(
        self,
        request: DailyKReadRequest,
    ) -> StandardizedDailyKBatch:
        """执行多证券、有限行数、只读标准化读取。"""

        self._validate_request(request)
        records: list[StandardizedDailyKRecord] = []
        warnings: list[str] = []
        source_row_count = 0

        for instrument_id in request.instrument_ids:
            prev_close = self._read_previous_close(
                instrument_id,
                request.start_date,
            )
            rows = self._read_source_rows(
                instrument_id,
                request,
            )
            source_row_count += len(rows)

            if not rows:
                warnings.append(
                    f"{instrument_id} 在请求范围内没有数据。"
                )
                continue

            for row in rows:
                standardized = self._map_one(
                    row,
                    prev_close,
                )
                records.append(standardized)

                close = row.get("close")
                if close is not None:
                    prev_close = float(close)

        records.sort(
            key=lambda item: (
                str(item.primary_key["instrument_id"]),
                item.primary_key["trade_date"],
            )
        )

        return StandardizedDailyKBatch(
            dataset_id=self.registration.dataset_id,
            coverage_version=
                self.registration.coverage_version,
            mapping_version=
                self.registration.mapping_version,
            dictionary_revision=
                self.registration.dictionary_revision,
            request={
                "instrument_ids":
                    list(request.instrument_ids),
                "start_date": request.start_date,
                "end_date": request.end_date,
                "limit_per_instrument":
                    request.limit_per_instrument,
            },
            source_row_count=source_row_count,
            standardized_record_count=len(records),
            records=records,
            warnings=warnings,
        )
