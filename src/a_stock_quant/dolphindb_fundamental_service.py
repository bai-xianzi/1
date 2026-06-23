"""DolphinDB基本面快照标准化读取服务。

本模块属于数据集专属插件层，只负责从DolphinDB只读获取Raw记录，
并根据数据集注册合同输出Canonical候选对象。它不读取Excel目录、不调用
外部导入脚本，也不修改数据库。
"""

from __future__ import annotations

import calendar
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Mapping, Protocol

from .data_contracts import DataContractError, SourceType
from .dataset_registry import DatasetRegistration, DatasetRegistry


DATASET_ID = "a_stock_fundamental_snapshot"
DEFAULT_DATABASE_URI = "dfs://A_STOCK_FUNDAMENTAL_DB"
DEFAULT_TABLE_NAME = "stock_fundamental_snapshot"

_MONEY_FACTOR = 1_000.0
_SHARE_FACTOR = 10_000
_STOCK_CODE_PATTERN = re.compile(r"^[0-9]{6}$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DATABASE_URI_PATTERN = re.compile(r"^dfs://[A-Za-z0-9_.-]+$")

_EXCHANGE_CODE_MAP = {
    "sh": "SSE",
    "sz": "SZSE",
    "bj": "BSE",
}
_MARKET_CODE_MAP = {
    "sh": "SH",
    "sz": "SZ",
    "bj": "BJ",
}

# 这里只列入canonical_fields.yaml revision 0.5中真实存在的宽表字段。
# 其他来源指标继续保存在source_extensions，避免制造伪Canonical字段。
_FUNDAMENTAL_MONEY_FIELDS = {
    "revenue_cny": "operating_revenue",
    "operating_cost_cny": "operating_cost",
    "operating_profit_cny": "operating_profit",
    "total_profit_cny": "total_profit",
    "net_profit_cny": "after_tax_profit",
    "net_profit_parent_cny": "net_profit",
    "total_assets_cny": "total_assets",
    "total_equity_cny": "net_assets",
    "accounts_receivable_cny": "accounts_receivable",
    "inventory_cny": "inventory",
    "operating_cash_flow_cny": "operating_cash_flow",
}

_FUNDAMENTAL_DIRECT_FIELDS = {
    "basic_eps_cny": "eps",
    "book_value_per_share_cny": "adjusted_nav_per_share",
}

_FUNDAMENTAL_PAYLOAD_FIELDS = tuple(
    dict.fromkeys(
        [
            *_FUNDAMENTAL_MONEY_FIELDS.values(),
            *_FUNDAMENTAL_DIRECT_FIELDS.values(),
        ]
    )
)

_OWNERSHIP_PAYLOAD_FIELDS = (
    "total_shares",
    "circulating_a_shares",
    "shareholder_count",
)

_SOURCE_EXTENSION_FIELDS = (
    "snapshot_date",
    "update_date",
    "report_period",
    "source_file",
    "imported_at",
    "total_shares",
    "b_shares",
    "h_shares",
    "circulating_a_shares",
    "shareholder_count",
    "eps",
    "adjusted_nav_per_share",
    "zpg",
    "total_assets",
    "current_assets",
    "fixed_assets",
    "intangible_assets",
    "current_liabilities",
    "long_term_liabilities",
    "capital_reserve",
    "net_assets",
    "operating_revenue",
    "operating_cost",
    "accounts_receivable",
    "operating_profit",
    "investment_income",
    "operating_cash_flow",
    "total_cash_flow",
    "inventory",
    "total_profit",
    "after_tax_profit",
    "net_profit",
    "undistributed_profit",
    "region_code",
    "source_industry_code",
    "pinyin",
    "tdx_industry_code",
)


class ReadonlyQueryAdapter(Protocol):
    """标准化服务需要的最小只读适配器合同。"""

    def run_readonly_query(self, script: str) -> Any:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class FundamentalReadRequest:
    instrument_ids: tuple[str, ...]
    start_date: date
    end_date: date
    limit_per_instrument: int = 5_000

    def __post_init__(self) -> None:
        if not self.instrument_ids:
            raise DataContractError("instrument_ids 至少包含一个证券。")

        normalized = tuple(str(value).strip() for value in self.instrument_ids)
        if any(not _STOCK_CODE_PATTERN.fullmatch(value) for value in normalized):
            raise DataContractError("基本面证券代码必须是6位数字。")
        if len(set(normalized)) != len(normalized):
            raise DataContractError("instrument_ids 不允许重复。")
        if len(normalized) > 100:
            raise DataContractError("一次最多读取100只证券。")

        object.__setattr__(self, "instrument_ids", normalized)

        if not isinstance(self.start_date, date):
            raise DataContractError("start_date 必须是date。")
        if not isinstance(self.end_date, date):
            raise DataContractError("end_date 必须是date。")
        if self.start_date > self.end_date:
            raise DataContractError("start_date 不能晚于end_date。")
        if (
            not isinstance(self.limit_per_instrument, int)
            or not 1 <= self.limit_per_instrument <= 5_000
        ):
            raise DataContractError(
                "limit_per_instrument必须是1到5000之间的整数。"
            )


@dataclass(frozen=True, slots=True)
class FundamentalCanonicalRecord:
    canonical_object: str
    primary_key: dict[str, Any]
    values: dict[str, Any]
    source_record_id: str
    source_extensions: dict[str, Any] = field(default_factory=dict)
    quality_flags: tuple[str, ...] = ()
    lineage: tuple[dict[str, Any], ...] = ()
    snapshot_date: date | None = None
    imported_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class FundamentalStandardBatch:
    dataset_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    source_row_count: int
    records: tuple[FundamentalCanonicalRecord, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DerivedReportPeriod:
    report_period: date
    period_type: str
    fiscal_year: int
    fiscal_quarter: int


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def _clean_text(value: Any) -> str | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    return text or None


def _as_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _as_int(value: Any) -> int | None:
    number = _as_float(value)
    return None if number is None else int(number)


def _as_date(value: Any) -> date | None:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted = to_pydatetime()
        if isinstance(converted, datetime):
            return converted.date()
        if isinstance(converted, date):
            return converted
    text_value = str(value).strip().replace(".", "-")
    try:
        return date.fromisoformat(text_value[:10])
    except ValueError:
        return None


def _as_datetime(value: Any) -> datetime | None:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):
        converted = to_pydatetime()
        if isinstance(converted, datetime):
            return converted
    text_value = str(value).strip().replace(".", "-")
    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        return None


def _records_from_result(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        if any(not isinstance(item, dict) for item in result):
            raise DataContractError("基本面查询结果列表中存在非字典记录。")
        return [dict(item) for item in result]
    if isinstance(result, dict):
        return [dict(result)]
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        try:
            records = to_dict(orient="records")
        except TypeError:
            records = to_dict("records")
        if any(not isinstance(item, dict) for item in records):
            raise DataContractError("基本面表格结果无法转换为字典记录。")
        return [dict(item) for item in records]
    raise DataContractError("暂不支持当前基本面查询结果类型。")


def derive_report_period(
    update_date: date | None,
    report_period_month: Any,
) -> DerivedReportPeriod | None:
    """根据供应商更新日和报告月份码推导报告期结束日。"""

    month = _as_int(report_period_month)
    if update_date is None or month not in {3, 6, 9, 12}:
        return None

    year = update_date.year - (1 if month > update_date.month else 0)
    last_day = calendar.monthrange(year, month)[1]
    return DerivedReportPeriod(
        report_period=date(year, month, last_day),
        period_type="ANNUAL" if month == 12 else "QUARTERLY",
        fiscal_year=year,
        fiscal_quarter=month // 3,
    )


def _scale_money(value: Any) -> float | None:
    number = _as_float(value)
    return None if number is None else number * _MONEY_FACTOR


def _scale_shares(value: Any) -> int | None:
    number = _as_float(value)
    return None if number is None else int(round(number * _SHARE_FACTOR))


def _has_payload(row: Mapping[str, Any], fields: tuple[str, ...]) -> bool:
    return any(not _is_missing(row.get(field_name)) for field_name in fields)


def _source_extensions(row: Mapping[str, Any]) -> dict[str, Any]:
    values = {
        field_name: row.get(field_name)
        for field_name in _SOURCE_EXTENSION_FIELDS
        if field_name in row
    }
    values["raw_unit_contract"] = {
        "share_fields": {
            "unit": "10k_shares",
            "canonical_factor": 10_000,
        },
        "money_fields": {
            "unit": "CNY_thousand",
            "canonical_factor": 1_000,
        },
        "per_share_fields": {
            "unit": "CNY_per_share",
            "canonical_factor": 1,
        },
        "evidence_status": "CONFIRMED_EMPIRICALLY",
    }
    values["raw_classification"] = {
        key: row.get(key)
        for key in (
            "sw_code",
            "source_detail_code",
            "source_industry_level2_code",
            "source_industry_level1_code",
            "source_sector",
            "source_industry",
            "source_subindustry",
            "sw_subindustry_code",
            "sw_industry_code",
            "sw_sector_code",
            "sw_sector",
            "sw_industry",
            "sw_subindustry",
        )
    }
    return values


class DolphinDBFundamentalStandardizedService:
    """根据数据集注册合同读取并标准化基本面快照。"""

    def __init__(
        self,
        adapter: ReadonlyQueryAdapter,
        registration: DatasetRegistration,
        *,
        allow_disabled_for_acceptance: bool = False,
    ) -> None:
        if registration.dataset_id != DATASET_ID:
            raise DataContractError(
                f"基本面服务收到错误数据集：{registration.dataset_id}"
            )
        if registration.source_type is not SourceType.DOLPHINDB:
            raise DataContractError("基本面服务只接受DolphinDB数据集。")
        if not registration.enabled and not allow_disabled_for_acceptance:
            raise DataContractError(
                "基本面数据集仍处于禁用状态；真实验收必须显式允许。"
            )

        locator = registration.source_locator
        database_uri = locator.get("database_uri")
        table_name = locator.get("table_name")
        if not isinstance(database_uri, str) or not _DATABASE_URI_PATTERN.fullmatch(
            database_uri
        ):
            raise DataContractError("注册配置中的database_uri不合法。")
        if not isinstance(table_name, str) or not _IDENTIFIER_PATTERN.fullmatch(
            table_name
        ):
            raise DataContractError("注册配置中的table_name不合法。")
        if registration.date_field != "snapshot_date":
            raise DataContractError("基本面date_field必须是snapshot_date。")
        if registration.entity_field != "stock_code":
            raise DataContractError("基本面entity_field必须是stock_code。")

        required_objects = {
            "FundamentalSnapshot",
            "OwnershipSnapshot",
            "Instrument",
            "ClassificationMembership",
        }
        missing_objects = sorted(
            required_objects - set(registration.canonical_objects)
        )
        if missing_objects:
            raise DataContractError(
                f"基本面注册缺少标准对象：{missing_objects}"
            )

        self.adapter = adapter
        self.registration = registration
        self.database_uri = database_uri
        self.table_name = table_name
        self.coverage_date = self._coverage_date(registration.coverage_version)

    @classmethod
    def from_registry_file(
        cls,
        adapter: ReadonlyQueryAdapter,
        registration_path: str | Path,
        *,
        allow_disabled_for_acceptance: bool = False,
    ) -> "DolphinDBFundamentalStandardizedService":
        registration = DatasetRegistry().load_json(registration_path)
        return cls(
            adapter,
            registration,
            allow_disabled_for_acceptance=allow_disabled_for_acceptance,
        )

    @staticmethod
    def _coverage_date(value: str) -> date:
        if "@" not in value:
            raise DataContractError("coverage_version必须包含@YYYY-MM-DD。")
        parsed = _as_date(value.rsplit("@", 1)[1])
        if parsed is None:
            raise DataContractError("coverage_version截止日期不合法。")
        return parsed

    @property
    def table_ref(self) -> str:
        return f'loadTable("{self.database_uri}", `{self.table_name})'

    @staticmethod
    def _date_literal(value: date) -> str:
        return value.strftime("%Y.%m.%d")

    @staticmethod
    def _symbol_vector(values: tuple[str, ...]) -> str:
        return "symbol([" + ",".join(f'"{value}"' for value in values) + "])"

    def _lineage(
        self,
        *,
        target_object: str,
        canonical_field: str,
        source_fields: tuple[str, ...],
        transform_id: str,
        transform_params: Mapping[str, Any] | None = None,
        semantic_status: str = "MAPPED",
    ) -> dict[str, Any]:
        return {
            "target_object": target_object,
            "canonical_field": canonical_field,
            "source_fields": list(source_fields),
            "transform_id": transform_id,
            "transform_params": dict(transform_params or {}),
            "mapping_version": self.registration.mapping_version,
            "dictionary_revision": self.registration.dictionary_revision,
            "semantic_status": semantic_status,
        }

    def _build_query(self, request: FundamentalReadRequest) -> str:
        fields = ", ".join(self.registration.source_fields)
        return (
            f"select {fields} "
            f"from {self.table_ref} "
            "where stock_code in "
            f"{self._symbol_vector(request.instrument_ids)} "
            "and snapshot_date >= "
            f"{self._date_literal(request.start_date)} "
            "and snapshot_date <= "
            f"{self._date_literal(request.end_date)} "
            "order by stock_code, snapshot_date"
        )

    def _read_rows(self, request: FundamentalReadRequest) -> list[dict[str, Any]]:
        raw_rows = _records_from_result(
            self.adapter.run_readonly_query(self._build_query(request))
        )
        counts: defaultdict[str, int] = defaultdict(int)
        selected: list[dict[str, Any]] = []
        for row in raw_rows:
            stock_code = _clean_text(row.get("stock_code"))
            if stock_code is None or counts[stock_code] >= request.limit_per_instrument:
                continue
            counts[stock_code] += 1
            selected.append(row)
        return selected

    def _fundamental_record(
        self,
        row: Mapping[str, Any],
    ) -> FundamentalCanonicalRecord | None:
        if not _has_payload(row, _FUNDAMENTAL_PAYLOAD_FIELDS):
            return None

        instrument_id = _clean_text(row.get("stock_code"))
        snapshot_date = _as_date(row.get("snapshot_date"))
        update_date = _as_date(row.get("update_date"))
        imported_at = _as_datetime(row.get("imported_at"))
        derived_period = derive_report_period(update_date, row.get("report_period"))
        if instrument_id is None or snapshot_date is None or derived_period is None:
            return None

        company_id = f"CN-A-COMPANY:{instrument_id}"
        values: dict[str, Any] = {
            "instrument_id": instrument_id,
            "company_id": company_id,
            "report_period": derived_period.report_period,
            "period_type": derived_period.period_type,
            "fiscal_year": derived_period.fiscal_year,
            "fiscal_quarter": derived_period.fiscal_quarter,
            "announcement_date": None,
            "statement_type": None,
            "consolidation_scope": None,
            "accounting_standard_code": None,
            "currency_code": "CNY",
        }
        for canonical_field, source_field in _FUNDAMENTAL_MONEY_FIELDS.items():
            values[canonical_field] = _scale_money(row.get(source_field))
        for canonical_field, source_field in _FUNDAMENTAL_DIRECT_FIELDS.items():
            values[canonical_field] = _as_float(row.get(source_field))

        extensions = _source_extensions(row)
        extensions.update(
            {
                "source_report_period_month": _as_int(row.get("report_period")),
                "source_update_date": update_date,
                "derived_report_period": derived_period.report_period,
                "derived_report_period_status": "DERIVED_WARNING",
            }
        )

        lineage = [
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="instrument_id",
                source_fields=("stock_code",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="company_id",
                source_fields=("stock_code",),
                transform_id="provisional_company_id",
                transform_params={"prefix": "CN-A-COMPANY:"},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="report_period",
                source_fields=("update_date", "report_period"),
                transform_id="derive_report_period_end",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="period_type",
                source_fields=("report_period",),
                transform_id="derive_period_type",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="fiscal_year",
                source_fields=("update_date", "report_period"),
                transform_id="derive_fiscal_year",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="fiscal_quarter",
                source_fields=("report_period",),
                transform_id="divide_integer",
                transform_params={"divisor": 3},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="FundamentalSnapshot",
                canonical_field="currency_code",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": "CNY"},
            ),
        ]
        for canonical_field, source_field in _FUNDAMENTAL_MONEY_FIELDS.items():
            lineage.append(
                self._lineage(
                    target_object="FundamentalSnapshot",
                    canonical_field=canonical_field,
                    source_fields=(source_field,),
                    transform_id="multiply",
                    transform_params={"factor": 1_000},
                    semantic_status="WARNING",
                )
            )
        for canonical_field, source_field in _FUNDAMENTAL_DIRECT_FIELDS.items():
            lineage.append(
                self._lineage(
                    target_object="FundamentalSnapshot",
                    canonical_field=canonical_field,
                    source_fields=(source_field,),
                    transform_id="identity",
                    semantic_status="WARNING",
                )
            )

        return FundamentalCanonicalRecord(
            canonical_object="FundamentalSnapshot",
            primary_key={
                "instrument_id": instrument_id,
                "report_period": derived_period.report_period,
                "snapshot_date": snapshot_date,
            },
            values=values,
            source_record_id=f"{instrument_id}|{snapshot_date.isoformat()}",
            source_extensions=extensions,
            quality_flags=(
                "EMPIRICAL_MONEY_UNIT_CNY_THOUSAND",
                "PROVISIONAL_COMPANY_ID_FROM_INSTRUMENT",
                "PROFIT_SCOPE_UNCONFIRMED",
                "EQUITY_SCOPE_UNCONFIRMED",
                "REPORT_PERIOD_DERIVED",
                "SOURCE_UPDATE_DATE_NOT_ANNOUNCEMENT_DATE",
                "AVAILABLE_AT_TIMEZONE_UNKNOWN",
            ),
            lineage=tuple(lineage),
            snapshot_date=snapshot_date,
            imported_at=imported_at,
        )

    def _ownership_record(
        self,
        row: Mapping[str, Any],
    ) -> FundamentalCanonicalRecord | None:
        if not _has_payload(row, _OWNERSHIP_PAYLOAD_FIELDS):
            return None
        instrument_id = _clean_text(row.get("stock_code"))
        snapshot_date = _as_date(row.get("snapshot_date"))
        imported_at = _as_datetime(row.get("imported_at"))
        if instrument_id is None or snapshot_date is None:
            return None

        values = {
            "instrument_id": instrument_id,
            "as_of_date": snapshot_date,
            "total_shares": _scale_shares(row.get("total_shares")),
            "float_shares": _scale_shares(row.get("circulating_a_shares")),
            "shareholder_count": _as_int(row.get("shareholder_count")),
        }
        lineage = (
            self._lineage(
                target_object="OwnershipSnapshot",
                canonical_field="instrument_id",
                source_fields=("stock_code",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="OwnershipSnapshot",
                canonical_field="as_of_date",
                source_fields=("snapshot_date",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="OwnershipSnapshot",
                canonical_field="total_shares",
                source_fields=("total_shares",),
                transform_id="multiply_and_round",
                transform_params={"factor": 10_000},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="OwnershipSnapshot",
                canonical_field="float_shares",
                source_fields=("circulating_a_shares",),
                transform_id="multiply_and_round",
                transform_params={"factor": 10_000},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="OwnershipSnapshot",
                canonical_field="shareholder_count",
                source_fields=("shareholder_count",),
                transform_id="identity",
            ),
        )
        return FundamentalCanonicalRecord(
            canonical_object="OwnershipSnapshot",
            primary_key={"instrument_id": instrument_id, "as_of_date": snapshot_date},
            values=values,
            source_record_id=f"{instrument_id}|{snapshot_date.isoformat()}",
            source_extensions=_source_extensions(row),
            quality_flags=(
                "EMPIRICAL_SHARE_UNIT_10K",
                "AVAILABLE_AT_TIMEZONE_UNKNOWN",
            ),
            lineage=lineage,
            snapshot_date=snapshot_date,
            imported_at=imported_at,
        )

    def _instrument_record(
        self,
        row: Mapping[str, Any],
    ) -> FundamentalCanonicalRecord | None:
        instrument_id = _clean_text(row.get("stock_code"))
        snapshot_date = _as_date(row.get("snapshot_date"))
        imported_at = _as_datetime(row.get("imported_at"))
        if instrument_id is None or snapshot_date is None:
            return None

        market = _clean_text(row.get("market"))
        market_key = market.lower() if market else None
        name = _clean_text(row.get("stock_name"))
        company_id = f"CN-A-COMPANY:{instrument_id}"
        exchange_code = _EXCHANGE_CODE_MAP.get(market_key or "")

        flags = [
            "INSTRUMENT_ID_LEGACY_SIX_DIGIT",
            "PROVISIONAL_COMPANY_ID_FROM_INSTRUMENT",
            "TRADING_STATUS_UNKNOWN",
            "IS_NEW_LISTING_UNKNOWN",
            "A_SHARE_DEFAULT_LOT_SIZE",
        ]
        if exchange_code is None or name is None:
            flags.append("INCOMPLETE_INSTRUMENT_IDENTITY")

        values = {
            "instrument_id": instrument_id,
            "symbol": instrument_id,
            "exchange_code": exchange_code,
            "market_code": _MARKET_CODE_MAP.get(market_key or ""),
            "asset_class": "EQUITY",
            "security_type": "COMMON_STOCK",
            "instrument_name_cn": name,
            "company_id": company_id,
            "currency_code": "CNY",
            "listing_date": _as_date(row.get("listing_date")),
            "trading_status": "UNKNOWN",
            "is_st": ("ST" in name.upper()) if name is not None else None,
            "is_new_listing": None,
            "lot_size_shares": 100,
        }
        lineage = (
            self._lineage(
                target_object="Instrument",
                canonical_field="instrument_id",
                source_fields=("stock_code",),
                transform_id="identity",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="symbol",
                source_fields=("stock_code",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="exchange_code",
                source_fields=("market",),
                transform_id="map_market_to_exchange",
                transform_params=dict(_EXCHANGE_CODE_MAP),
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="market_code",
                source_fields=("market",),
                transform_id="map_market_code",
                transform_params=dict(_MARKET_CODE_MAP),
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="asset_class",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": "EQUITY"},
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="security_type",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": "COMMON_STOCK"},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="instrument_name_cn",
                source_fields=("stock_name",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="company_id",
                source_fields=("stock_code",),
                transform_id="provisional_company_id",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="currency_code",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": "CNY"},
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="listing_date",
                source_fields=("listing_date",),
                transform_id="identity",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="trading_status",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": "UNKNOWN"},
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="is_st",
                source_fields=("stock_name",),
                transform_id="derive_st_from_name",
                semantic_status="WARNING",
            ),
            self._lineage(
                target_object="Instrument",
                canonical_field="lot_size_shares",
                source_fields=(),
                transform_id="constant",
                transform_params={"value": 100},
                semantic_status="WARNING",
            ),
        )
        return FundamentalCanonicalRecord(
            canonical_object="Instrument",
            primary_key={"instrument_id": instrument_id},
            values=values,
            source_record_id=f"{instrument_id}|{snapshot_date.isoformat()}",
            source_extensions=_source_extensions(row),
            quality_flags=tuple(flags),
            lineage=lineage,
            snapshot_date=snapshot_date,
            imported_at=imported_at,
        )

    def _classification_records(
        self,
        row: Mapping[str, Any],
    ) -> list[FundamentalCanonicalRecord]:
        instrument_id = _clean_text(row.get("stock_code"))
        snapshot_date = _as_date(row.get("snapshot_date"))
        imported_at = _as_datetime(row.get("imported_at"))
        if instrument_id is None or snapshot_date is None:
            return []

        definitions = (
            ("SOURCE_VENDOR", 1, "source_industry_level1_code", "source_sector", None),
            (
                "SOURCE_VENDOR",
                2,
                "source_industry_level2_code",
                "source_industry",
                "source_industry_level1_code",
            ),
            (
                "SOURCE_VENDOR",
                3,
                "source_detail_code",
                "source_subindustry",
                "source_industry_level2_code",
            ),
            ("SW", 1, "sw_sector_code", "sw_sector", None),
            ("SW", 2, "sw_industry_code", "sw_industry", "sw_sector_code"),
            (
                "SW",
                3,
                "sw_subindustry_code",
                "sw_subindustry",
                "sw_industry_code",
            ),
        )
        output: list[FundamentalCanonicalRecord] = []
        effective_from = datetime.combine(snapshot_date, time.min)

        for system, level, code_field, name_field, parent_field in definitions:
            node_code = _clean_text(row.get(code_field))
            node_name = _clean_text(row.get(name_field))
            if node_name is None:
                continue
            node_id = f"{system}:{node_code or node_name}"
            parent_code = _clean_text(row.get(parent_field)) if parent_field else None
            parent_node_id = f"{system}:{parent_code}" if parent_code else None
            values = {
                "classification_system": system,
                "classification_version": f"UNKNOWN@{snapshot_date.isoformat()}",
                "classification_type": "INDUSTRY",
                "node_id": node_id,
                "node_code": node_code,
                "node_name_cn": node_name,
                "node_level": level,
                "parent_node_id": parent_node_id,
                "instrument_id": instrument_id,
                "membership_weight_pct": None,
                "membership_rank": None,
                "effective_from": effective_from,
                "effective_to": None,
                "membership_reason": "SNAPSHOT_OBSERVED",
            }
            output.append(
                FundamentalCanonicalRecord(
                    canonical_object="ClassificationMembership",
                    primary_key={
                        "classification_system": system,
                        "node_id": node_id,
                        "instrument_id": instrument_id,
                        "effective_from": effective_from,
                    },
                    values=values,
                    source_record_id=(
                        f"{instrument_id}|{snapshot_date.isoformat()}|{node_id}"
                    ),
                    source_extensions=_source_extensions(row),
                    quality_flags=(
                        "CLASSIFICATION_VERSION_UNKNOWN",
                        "CLASSIFICATION_INTERVAL_SNAPSHOT_ONLY",
                        "CLASSIFICATION_EFFECTIVE_TIME_DATE_ONLY",
                    ),
                    lineage=(
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="classification_system",
                            source_fields=(code_field, name_field),
                            transform_id="constant_by_source_family",
                            transform_params={"value": system},
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="classification_version",
                            source_fields=("snapshot_date",),
                            transform_id="unknown_version_at_snapshot",
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="classification_type",
                            source_fields=(),
                            transform_id="constant",
                            transform_params={"value": "INDUSTRY"},
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="node_id",
                            source_fields=(code_field, name_field),
                            transform_id="compose_node_id",
                            transform_params={"system": system},
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="node_code",
                            source_fields=(code_field,),
                            transform_id="identity",
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="node_name_cn",
                            source_fields=(name_field,),
                            transform_id="identity",
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="node_level",
                            source_fields=(),
                            transform_id="constant",
                            transform_params={"value": level},
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="parent_node_id",
                            source_fields=((parent_field,) if parent_field else ()),
                            transform_id="compose_parent_node_id",
                            transform_params={"system": system},
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="instrument_id",
                            source_fields=("stock_code",),
                            transform_id="identity",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="effective_from",
                            source_fields=("snapshot_date",),
                            transform_id="snapshot_date_to_midnight_timestamp",
                            semantic_status="WARNING",
                        ),
                        self._lineage(
                            target_object="ClassificationMembership",
                            canonical_field="membership_reason",
                            source_fields=("snapshot_date",),
                            transform_id="constant",
                            transform_params={"value": "SNAPSHOT_OBSERVED"},
                            semantic_status="WARNING",
                        ),
                    ),
                    snapshot_date=snapshot_date,
                    imported_at=imported_at,
                )
            )
        return output

    def read(self, request: FundamentalReadRequest) -> FundamentalStandardBatch:
        rows = self._read_rows(request)
        records: list[FundamentalCanonicalRecord] = []
        warnings: list[str] = []
        seen_instruments: set[str] = set()

        for row in rows:
            instrument_id = _clean_text(row.get("stock_code"))
            if instrument_id:
                seen_instruments.add(instrument_id)

            instrument = self._instrument_record(row)
            if instrument is not None:
                records.append(instrument)

            has_financial_payload = _has_payload(row, _FUNDAMENTAL_PAYLOAD_FIELDS)
            fundamental = self._fundamental_record(row)
            if fundamental is not None:
                records.append(fundamental)
            elif instrument_id and has_financial_payload:
                warnings.append(
                    f"{instrument_id} 有财务载荷但报告期无法安全推导，未生成FundamentalSnapshot。"
                )
            elif instrument_id:
                warnings.append(f"{instrument_id} 没有可用财务载荷。")

            ownership = self._ownership_record(row)
            if ownership is not None:
                records.append(ownership)
            records.extend(self._classification_records(row))

        for instrument_id in request.instrument_ids:
            if instrument_id not in seen_instruments:
                warnings.append(f"{instrument_id} 在请求范围内没有数据。")

        return FundamentalStandardBatch(
            dataset_id=self.registration.dataset_id,
            coverage_version=self.registration.coverage_version,
            mapping_version=self.registration.mapping_version,
            dictionary_revision=self.registration.dictionary_revision,
            source_row_count=len(rows),
            records=tuple(records),
            warnings=tuple(dict.fromkeys(warnings)),
        )
