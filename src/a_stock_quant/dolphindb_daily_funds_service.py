"""七类日线资金DolphinDB只读Canonical标准化服务。

本模块只读取TASK_016创建的三张Raw表，根据TASK_017B批准的映射合同
输出Canonical记录、来源扩展、质量标记和字段级血缘。

安全边界：
1. 只通过run_readonly_query执行select查询；
2. 不创建、修改、删除或回写DolphinDB对象；
3. 不读取桌面Excel和导入目录；
4. 不把文件修改时间或入库时间伪装为市场快照时间；
5. 分类节点使用generic entity_ids，不伪装成instrument_ids；
6. 同一Canonical主键存在多个Raw修订时保留最新ingested_at版本。
"""

from __future__ import annotations

import copy
import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

import yaml

from .data_contracts import DataContractError
from .daily_funds_canonical_contract import (
    REQUIRED_DATASETS,
    load_contract,
    validate_contract,
)


SERVICE_CONFIG_RELATIVE_PATH = (
    "configs/datasets/a_stock_daily_funds_standard_service.yaml"
)
MAPPING_CONTRACT_RELATIVE_PATH = (
    "configs/mappings/a_stock_daily_funds_canonical_v0.yaml"
)
DICTIONARY_RELATIVE_PATH = "schemas/canonical_fields.yaml"
ENUM_DEFINITIONS_RELATIVE_PATH = "schemas/enum_definitions.yaml"

_DATABASE_URI_PATTERN = re.compile(r"^dfs://[A-Za-z0-9_.-]+$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DATASET_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_INSTRUMENT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_PROVISIONAL_NODE_ID_PATTERN = re.compile(
    r"^SOURCE_VENDOR:(INDUSTRY|CONCEPT):[A-F0-9]{20}$"
)

SUPPORTED_TRANSFORMS = frozenset(
    {
        "identity",
        "percent_points_identity",
        "multiply_100",
        "divide_100",
        "constant_OPENING_CALL",
        "constant_DATE_ONLY",
        "constant_SOURCE_VENDOR",
        "constant_VENDOR_ORDER_SIZE_BUCKET_V1",
        "normalized_enum",
        "provisional_hash_id",
        "sum_nullable",
        "unavailable",
        "unresolved_from_name_only",
        "no_safe_exact_value",
    }
)

COMMON_RAW_FIELDS = frozenset(
    {
        "dataset_id",
        "snapshot_date",
        "snapshot_month",
        "snapshot_phase",
        "schema_version",
        "entity_key",
        "source_row_number",
        "source_file_name",
        "source_file_relative_path",
        "source_file_size_bytes",
        "source_file_mtime_utc",
        "source_file_sha256",
        "row_sha256",
        "ingest_batch_id",
        "ingested_at_utc",
        "quality_status",
        "raw_row_json",
    }
)
SECURITY_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "instrument_id",
        "market_candidate",
        "instrument_name",
        "last_price",
        "pct_change",
        "price_change",
        "total_volume_lot",
        "current_volume_lot",
        "bid_price",
        "ask_price",
        "speed_pct",
        "turnover_pct",
        "amount_cny",
        "pe_dynamic",
        "industry_name",
        "high_price",
        "low_price",
        "open_price",
        "prev_close",
        "amplitude_pct",
        "volume_ratio",
        "order_imbalance_pct",
        "order_imbalance_lot",
        "avg_price",
        "inner_volume_lot",
        "outer_volume_lot",
        "inner_outer_ratio",
        "bid1_volume_lot",
        "ask1_volume_lot",
        "pb",
        "total_shares",
        "total_market_cap_cny",
        "float_shares",
        "float_market_cap_cny",
        "return_3d_pct",
        "return_6d_pct",
        "turnover_3d_pct",
        "turnover_6d_pct",
        "consecutive_up_days",
        "return_month_pct",
        "return_ytd_pct",
        "return_1m_pct",
        "return_1y_pct",
        "listing_date_raw",
        "speed_5m_pct",
        "return_20d_pct",
        "source_volume_unit",
        "canonical_volume_transform",
        "source_amount_unit",
    }
)
CLASSIFICATION_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "classification_type",
        "node_name_raw",
        "pct_change",
        "return_3d_pct",
        "speed_pct",
        "leading_stock_name",
        "up_count",
        "down_count",
        "breadth_ratio",
        "breadth_status",
        "limit_up_count",
        "turnover_pct",
        "volume_ratio",
        "turnover_3d_pct",
        "return_5d_pct",
        "return_10d_pct",
        "return_20d_pct",
        "volume_lot",
        "amount_cny",
        "total_market_cap_cny",
        "float_market_cap_cny",
        "average_return_pct",
        "average_shares",
        "pe_ratio",
        "source_volume_unit",
        "canonical_volume_transform",
        "source_amount_unit",
    }
)
MONEY_FLOW_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "instrument_id",
        "market_candidate",
        "instrument_name",
        "last_price",
        "pct_change",
        "main_net_inflow_cny",
        "auction_net_inflow_cny",
        "super_large_inflow_cny",
        "super_large_outflow_cny",
        "super_large_net_cny",
        "super_large_net_ratio_pct",
        "large_inflow_cny",
        "large_outflow_cny",
        "large_net_cny",
        "large_net_ratio_pct",
        "medium_inflow_cny",
        "medium_outflow_cny",
        "medium_net_cny",
        "medium_net_ratio_pct",
        "small_inflow_cny",
        "small_outflow_cny",
        "small_net_cny",
        "small_net_ratio_pct",
        "source_amount_unit",
        "outflow_sign_policy",
    }
)
RAW_FIELD_CATALOG = {
    "security_snapshot": SECURITY_RAW_FIELDS,
    "classification_snapshot": CLASSIFICATION_RAW_FIELDS,
    "money_flow_snapshot": MONEY_FLOW_RAW_FIELDS,
}

SOURCE_EVIDENCE_FIELDS = (
    "dataset_id",
    "snapshot_date",
    "snapshot_phase",
    "schema_version",
    "entity_key",
    "source_row_number",
    "source_file_name",
    "source_file_relative_path",
    "source_file_size_bytes",
    "source_file_mtime_utc",
    "source_file_sha256",
    "row_sha256",
    "ingest_batch_id",
    "ingested_at_utc",
    "quality_status",
    "raw_row_json",
)

PRIMARY_KEY_FIELDS = {
    "DailyBar": ("instrument_id", "trade_date"),
    "AuctionSnapshot": (
        "instrument_id",
        "trade_date",
        "auction_phase",
        "snapshot_time_precision",
    ),
    "ClassificationMarketSnapshot": (
        "classification_system",
        "classification_type",
        "node_id",
        "trade_date",
        "snapshot_phase",
    ),
    "MoneyFlowSnapshot": (
        "instrument_id",
        "trade_date",
        "flow_method_code",
    ),
}


class ReadonlyQueryAdapter(Protocol):
    """服务依赖的最小只读适配器合同。"""

    def run_readonly_query(self, script: str) -> Any:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DailyFundsReadRequest:
    """七类来源统一读取请求；entity_ids不限定为证券。"""

    dataset_id: str
    entity_ids: tuple[str, ...]
    start_date: date
    end_date: date
    limit_per_entity: int = 5_000

    def __post_init__(self) -> None:
        dataset_id = str(self.dataset_id).strip()
        if not _DATASET_ID_PATTERN.fullmatch(dataset_id):
            raise DataContractError("dataset_id格式不合法。")
        object.__setattr__(self, "dataset_id", dataset_id)

        normalized = tuple(str(value).strip() for value in self.entity_ids)
        if not normalized or any(not value for value in normalized):
            raise DataContractError("entity_ids至少包含一个非空实体。")
        if len(set(normalized)) != len(normalized):
            raise DataContractError("entity_ids不允许重复。")
        if any(len(value) > 128 for value in normalized):
            raise DataContractError("entity_id长度不能超过128。")
        if any(any(ord(char) < 32 for char in value) for value in normalized):
            raise DataContractError("entity_id不能包含控制字符。")
        object.__setattr__(self, "entity_ids", normalized)

        if not isinstance(self.start_date, date):
            raise DataContractError("start_date必须是date。")
        if not isinstance(self.end_date, date):
            raise DataContractError("end_date必须是date。")
        if self.start_date > self.end_date:
            raise DataContractError("start_date不能晚于end_date。")
        if (
            not isinstance(self.limit_per_entity, int)
            or not 1 <= self.limit_per_entity <= 5_000
        ):
            raise DataContractError(
                "limit_per_entity必须是1到5000之间的整数。"
            )


@dataclass(frozen=True, slots=True)
class DailyFundsCanonicalRecord:
    dataset_id: str
    canonical_object: str
    primary_key: dict[str, Any]
    values: dict[str, Any]
    source_record_id: str
    source_extensions: dict[str, Any] = field(default_factory=dict)
    quality_flags: tuple[str, ...] = ()
    lineage: tuple[dict[str, Any], ...] = ()
    snapshot_date: date | None = None
    ingested_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class DailyFundsStandardBatch:
    dataset_id: str
    canonical_object: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    scanned_source_row_count: int
    source_row_count: int
    records: tuple[DailyFundsCanonicalRecord, ...]
    warnings: tuple[str, ...] = ()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DataContractError(f"YAML根节点必须是映射：{path}")
    return payload


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        unequal = value != value
        if isinstance(unequal, bool) and unequal:
            return True
    except Exception:
        pass
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def _python_scalar(value: Any) -> Any:
    if _is_missing(value):
        return None
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            pass
    return value


def _clean_text(value: Any) -> str | None:
    if _is_missing(value):
        return None
    text = str(_python_scalar(value)).strip()
    return text or None


def _as_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _as_integral(value: Any) -> int | None:
    number = _as_float(value)
    if number is None:
        return None
    rounded = round(number)
    if abs(number - rounded) > 1e-9:
        return None
    return int(rounded)


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
    text = str(value).strip().replace(".", "-")
    try:
        return date.fromisoformat(text[:10])
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
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def normalise_query_records(result: Any) -> list[dict[str, Any]]:
    """把DolphinDB常见返回值转换为字典行。"""
    if result is None:
        return []
    if isinstance(result, list):
        if any(not isinstance(item, dict) for item in result):
            raise DataContractError("DolphinDB列表结果包含非字典行。")
        return [dict(item) for item in result]
    to_dict = getattr(result, "to_dict", None)
    columns = getattr(result, "columns", None)
    if callable(to_dict) and columns is not None:
        try:
            rows = to_dict(orient="records")
        except TypeError:
            rows = to_dict("records")
        if any(not isinstance(item, dict) for item in rows):
            raise DataContractError("DolphinDB表格结果无法转换为字典行。")
        return [dict(item) for item in rows]
    raise DataContractError("不支持当前DolphinDB查询返回值类型。")


def provisional_node_id(
    classification_type: Any,
    node_name: Any,
) -> str | None:
    type_text = _clean_text(classification_type)
    name_text = _clean_text(node_name)
    if type_text is None or name_text is None:
        return None
    normalized_type = type_text.upper()
    normalized_name = unicodedata.normalize("NFKC", name_text).strip()
    digest = hashlib.sha256(
        f"{normalized_type}|{normalized_name}".encode("utf-8")
    ).hexdigest()[:20].upper()
    return f"SOURCE_VENDOR:{normalized_type}:{digest}"


def _dictionary_objects(
    dictionary: Mapping[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    objects: dict[str, dict[str, dict[str, Any]]] = {}
    for domain in dictionary.get("domains", []):
        if not isinstance(domain, dict):
            continue
        object_name = _clean_text(domain.get("canonical_object"))
        if object_name is None:
            continue
        catalog = objects.setdefault(object_name, {})
        for item in domain.get("fields", []):
            if not isinstance(item, dict):
                continue
            field_name = _clean_text(item.get("canonical_name"))
            if field_name:
                catalog[field_name] = dict(item)
    return objects


def _mapping_source_fields(mapping: Mapping[str, Any]) -> tuple[str, ...]:
    source = mapping.get("source")
    if source is None:
        return ()
    if isinstance(source, list):
        return tuple(str(item) for item in source)
    return (str(source),)


def validate_daily_funds_service_contract(
    project_root: str | Path,
) -> dict[str, Any]:
    root = str(Path(project_root).resolve())
    return copy.deepcopy(_validate_daily_funds_service_contract_cached(root))


@lru_cache(maxsize=16)
def _validate_daily_funds_service_contract_cached(
    project_root: str,
) -> dict[str, Any]:
    root = Path(project_root)
    config = _load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)
    mapping_path = root / str(config.get("mapping_contract_path", ""))
    dictionary_path = root / str(config.get("dictionary_path", ""))
    enum_path = root / str(config.get("enum_definitions_path", ""))
    mapping_validation = validate_contract(mapping_path, dictionary_path)
    mapping_contract = load_contract(mapping_path)
    dictionary = _load_yaml(dictionary_path)
    enum_definitions = _load_yaml(enum_path)
    objects = _dictionary_objects(dictionary)
    issues: list[dict[str, Any]] = []

    if mapping_validation["overall_status"] != "PASSED_WITH_WARNINGS":
        issues.append(
            {
                "severity": "ERROR",
                "code": "MAPPING_CONTRACT_NOT_APPROVED",
                "detail": mapping_validation,
            }
        )
    if config.get("mapping_version") != mapping_contract.contract_version:
        issues.append(
            {
                "severity": "ERROR",
                "code": "MAPPING_VERSION_MISMATCH",
            }
        )
    if str(config.get("dictionary_revision")) != str(
        dictionary.get("dictionary_revision")
    ):
        issues.append(
            {
                "severity": "ERROR",
                "code": "DICTIONARY_REVISION_MISMATCH",
            }
        )
    database_uri = str(config.get("database_uri", ""))
    if not _DATABASE_URI_PATTERN.fullmatch(database_uri):
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATABASE_URI_INVALID",
            }
        )

    coverage = config.get("coverage", {})
    coverage_start = _as_date(coverage.get("start_date"))
    coverage_end = _as_date(coverage.get("end_date"))
    if (
        coverage_start is None
        or coverage_end is None
        or coverage_start > coverage_end
    ):
        issues.append(
            {
                "severity": "ERROR",
                "code": "COVERAGE_RANGE_INVALID",
            }
        )

    profiles = config.get("dataset_profiles", {})
    if set(profiles) != set(REQUIRED_DATASETS):
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATASET_PROFILE_SET_MISMATCH",
            }
        )

    used_transforms: set[str] = set()
    for dataset_id, dataset in mapping_contract.datasets.items():
        profile = profiles.get(dataset_id, {})
        family = str(dataset.get("family", ""))
        canonical_object = str(dataset.get("canonical_object", ""))
        source_table = str(dataset.get("source_table", ""))
        if profile.get("family") != family:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_FAMILY_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        if profile.get("canonical_object") != canonical_object:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_OBJECT_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        if profile.get("source_table") != source_table:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_TABLE_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        if not _IDENTIFIER_PATTERN.fullmatch(source_table):
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "SOURCE_TABLE_INVALID",
                    "dataset_id": dataset_id,
                }
            )
        raw_fields = RAW_FIELD_CATALOG.get(family, frozenset())
        for mapping in dataset.get("mappings", []):
            transform = str(mapping.get("transform", ""))
            used_transforms.add(transform)
            if transform not in SUPPORTED_TRANSFORMS:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNSUPPORTED_TRANSFORM",
                        "dataset_id": dataset_id,
                        "transform": transform,
                    }
                )
            for source_field in _mapping_source_fields(mapping):
                if source_field not in raw_fields:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "MAPPING_SOURCE_FIELD_NOT_IN_RAW_SCHEMA",
                            "dataset_id": dataset_id,
                            "source_field": source_field,
                        }
                    )
        for field_name in dataset.get("source_extensions", []):
            if field_name not in raw_fields:
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "SOURCE_EXTENSION_NOT_IN_RAW_SCHEMA",
                        "dataset_id": dataset_id,
                        "source_field": field_name,
                    }
                )
        if canonical_object not in objects:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "CANONICAL_OBJECT_MISSING",
                    "dataset_id": dataset_id,
                }
            )
        else:
            for mapping in dataset.get("mappings", []):
                target = str(mapping.get("target", ""))
                if target not in objects[canonical_object]:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "TARGET_FIELD_MISSING",
                            "dataset_id": dataset_id,
                            "target": target,
                        }
                    )
                field_def = objects[canonical_object].get(target, {})
                enum_ref = field_def.get("enum_ref")
                if enum_ref and enum_ref not in enum_definitions:
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "ENUM_REFERENCE_MISSING",
                            "dataset_id": dataset_id,
                            "target": target,
                            "enum_ref": enum_ref,
                        }
                    )

    query_policy = config.get("query_policy", {})
    for name, minimum, maximum in (
        ("max_entity_ids", 1, 1000),
        ("max_limit_per_entity", 1, 5000),
        ("max_raw_rows_per_request", 1, 1_000_000),
    ):
        value = query_policy.get(name)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "QUERY_POLICY_INVALID",
                    "field": name,
                }
            )

    errors = [item for item in issues if item["severity"] == "ERROR"]
    return {
        "task_id": "TASK_017C",
        "service_id": config.get("service_id"),
        "service_version": str(config.get("service_version")),
        "coverage_version": coverage.get("coverage_version"),
        "coverage_start": str(coverage_start),
        "coverage_end": str(coverage_end),
        "dataset_count": len(profiles),
        "raw_table_count": len(
            {item.get("source_table") for item in profiles.values()}
        ),
        "canonical_object_count": len(
            {item.get("canonical_object") for item in profiles.values()}
        ),
        "supported_transform_count": len(used_transforms),
        "known_quarantine_count": len(config.get("known_quarantines", [])),
        "overall_status": (
            "PASSED_WITH_WARNINGS" if not errors else "FAILED"
        ),
        "issues": issues,
    }


@lru_cache(maxsize=16)
def _load_service_assets(project_root: str) -> tuple[Any, ...]:
    root = Path(project_root)
    config = _load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)
    mapping_path = root / str(config["mapping_contract_path"])
    dictionary_path = root / str(config["dictionary_path"])
    enum_path = root / str(config["enum_definitions_path"])
    mapping_contract = load_contract(mapping_path)
    dictionary = _load_yaml(dictionary_path)
    enum_definitions = _load_yaml(enum_path)
    object_fields = _dictionary_objects(dictionary)
    return (
        config,
        mapping_path,
        dictionary_path,
        enum_path,
        mapping_contract,
        dictionary,
        enum_definitions,
        object_fields,
    )


class DolphinDBDailyFundsCanonicalService:
    """三张Raw表到四类Canonical对象的只读标准化服务。"""

    def __init__(
        self,
        adapter: ReadonlyQueryAdapter,
        *,
        project_root: str | Path,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        validation = validate_daily_funds_service_contract(self.project_root)
        if validation["overall_status"] != "PASSED_WITH_WARNINGS":
            raise DataContractError(
                f"TASK_017C服务合同无效：{validation['issues']}"
            )
        self.adapter = adapter
        (
            self.config,
            self.mapping_path,
            self.dictionary_path,
            self.enum_path,
            self.mapping_contract,
            self.dictionary,
            self.enum_definitions,
            self.object_fields,
        ) = _load_service_assets(str(self.project_root))
        self.database_uri = str(self.config["database_uri"])
        coverage = self.config["coverage"]
        self.coverage_version = str(coverage["coverage_version"])
        self.coverage_start = _as_date(coverage["start_date"])
        self.coverage_end = _as_date(coverage["end_date"])
        assert self.coverage_start is not None
        assert self.coverage_end is not None
        self.query_policy = dict(self.config["query_policy"])
        self.profiles = dict(self.config["dataset_profiles"])
        self.known_quarantines = tuple(
            dict(item) for item in self.config.get("known_quarantines", [])
        )

    @property
    def service_id(self) -> str:
        return str(self.config["service_id"])

    @property
    def service_version(self) -> str:
        return str(self.config["service_version"])

    @property
    def mapping_version(self) -> str:
        return self.mapping_contract.contract_version

    @property
    def dictionary_revision(self) -> str:
        return str(self.dictionary["dictionary_revision"])

    def dataset_profile(self, dataset_id: str) -> dict[str, Any]:
        try:
            return dict(self.profiles[dataset_id])
        except KeyError as exc:
            raise DataContractError(f"不支持七类来源：{dataset_id}") from exc

    def available_fields(self, dataset_id: str) -> tuple[str, ...]:
        dataset = self.mapping_contract.datasets.get(dataset_id)
        if dataset is None:
            raise DataContractError(f"不支持七类来源：{dataset_id}")
        return tuple(str(item["target"]) for item in dataset["mappings"])

    @staticmethod
    def _date_literal(value: date) -> str:
        return value.strftime("%Y.%m.%d")

    @staticmethod
    def _symbol_vector(values: Sequence[str]) -> str:
        return "symbol([" + ",".join(f'"{value}"' for value in values) + "])"

    @staticmethod
    def _symbol_literal(value: str) -> str:
        if not _DATASET_ID_PATTERN.fullmatch(value):
            raise DataContractError("不安全的dataset_id。")
        return f"`{value}"

    def _validate_request(self, request: DailyFundsReadRequest) -> None:
        profile = self.dataset_profile(request.dataset_id)
        if len(request.entity_ids) > int(self.query_policy["max_entity_ids"]):
            raise DataContractError("一次查询实体数超过服务上限。")
        if request.limit_per_entity > int(
            self.query_policy["max_limit_per_entity"]
        ):
            raise DataContractError("limit_per_entity超过服务上限。")
        if request.start_date < self.coverage_start:
            raise DataContractError(
                "请求开始日期早于七类Raw覆盖起点："
                f"{request.start_date} < {self.coverage_start}"
            )
        if request.end_date > self.coverage_end:
            raise DataContractError(
                "请求结束日期晚于七类Raw覆盖终点："
                f"{request.end_date} > {self.coverage_end}"
            )
        if profile["selector_mode"] == "INSTRUMENT_ID":
            invalid = [
                value
                for value in request.entity_ids
                if not _INSTRUMENT_ID_PATTERN.fullmatch(value)
            ]
            if invalid:
                raise DataContractError(
                    f"证券型来源只接受6位代码：{invalid}"
                )

    def _selected_raw_fields(self, dataset_id: str) -> tuple[str, ...]:
        dataset = self.mapping_contract.datasets[dataset_id]
        fields: set[str] = set(SOURCE_EVIDENCE_FIELDS)
        profile = self.profiles[dataset_id]
        fields.add(str(profile["raw_entity_field"]))
        for mapping in dataset["mappings"]:
            fields.update(_mapping_source_fields(mapping))
        fields.update(str(item) for item in dataset.get("source_extensions", []))
        raw_catalog = RAW_FIELD_CATALOG[str(dataset["family"])]
        unknown = sorted(fields - raw_catalog)
        if unknown:
            raise DataContractError(
                f"服务请求了Raw表不存在的字段：{dataset_id} {unknown}"
            )
        return tuple(sorted(fields))

    def _build_query(self, request: DailyFundsReadRequest) -> str:
        profile = self.profiles[request.dataset_id]
        table_name = str(profile["source_table"])
        if not _IDENTIFIER_PATTERN.fullmatch(table_name):
            raise DataContractError("source_table格式不合法。")
        fields = ", ".join(self._selected_raw_fields(request.dataset_id))
        where_parts = [
            f"dataset_id={self._symbol_literal(request.dataset_id)}",
            f"snapshot_date>={self._date_literal(request.start_date)}",
            f"snapshot_date<={self._date_literal(request.end_date)}",
        ]
        if profile["selector_mode"] == "INSTRUMENT_ID":
            where_parts.append(
                "instrument_id in "
                + self._symbol_vector(request.entity_ids)
            )
        max_rows = int(self.query_policy["max_raw_rows_per_request"])
        return (
            f"select top {max_rows} {fields} "
            f'from loadTable("{self.database_uri}", `{table_name}) '
            "where "
            + " and ".join(where_parts)
            + " order by snapshot_date, source_row_number"
        )

    def _raw_entity_identity(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> tuple[str | None, str | None]:
        profile = self.profiles[dataset_id]
        if profile["selector_mode"] == "INSTRUMENT_ID":
            instrument_id = _clean_text(row.get("instrument_id"))
            return instrument_id, instrument_id
        node_name = _clean_text(row.get("node_name_raw"))
        node_id = provisional_node_id(
            row.get("classification_type"),
            node_name,
        )
        return node_name, node_id

    def _filter_entity_rows(
        self,
        request: DailyFundsReadRequest,
        rows: Sequence[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], set[str]]:
        requested = set(request.entity_ids)
        selected: list[dict[str, Any]] = []
        matched: set[str] = set()
        for row in rows:
            name_or_id, provisional_id = self._raw_entity_identity(
                request.dataset_id,
                row,
            )
            candidates = {value for value in (name_or_id, provisional_id) if value}
            intersection = requested & candidates
            if not intersection:
                continue
            matched.update(intersection)
            selected.append(row)
        return selected, matched

    def _apply_transform(
        self,
        *,
        transform: str,
        source_fields: tuple[str, ...],
        row: Mapping[str, Any],
        target_field: str,
    ) -> Any:
        values = [row.get(field_name) for field_name in source_fields]
        if transform in {"identity", "percent_points_identity"}:
            return values[0] if values else None
        if transform == "multiply_100":
            number = _as_float(values[0] if values else None)
            return None if number is None else number * 100.0
        if transform == "divide_100":
            number = _as_float(values[0] if values else None)
            return None if number is None else number / 100.0
        if transform == "normalized_enum":
            text = _clean_text(values[0] if values else None)
            return None if text is None else text.upper()
        if transform == "provisional_hash_id":
            return provisional_node_id(
                row.get("classification_type"),
                values[0] if values else None,
            )
        if transform == "sum_nullable":
            numbers = [_as_float(value) for value in values]
            present = [value for value in numbers if value is not None]
            return None if not present else sum(present)
        if transform.startswith("constant_"):
            return transform[len("constant_") :]
        if transform in {
            "unavailable",
            "unresolved_from_name_only",
            "no_safe_exact_value",
        }:
            return None
        raise DataContractError(
            f"未实现的Canonical转换：{target_field}/{transform}"
        )

    def _coerce_value(
        self,
        value: Any,
        field_definition: Mapping[str, Any],
    ) -> Any:
        if _is_missing(value):
            return None
        data_type = str(field_definition.get("data_type", ""))
        if data_type == "DATE":
            return _as_date(value)
        if data_type == "TIMESTAMP":
            return _as_datetime(value)
        if data_type in {"INT", "LONG"}:
            return _as_integral(value)
        if data_type in {"DOUBLE", "DECIMAL"}:
            return _as_float(value)
        if data_type == "BOOL":
            if isinstance(value, bool):
                return value
            text = str(value).strip().lower()
            if text in {"true", "1", "yes"}:
                return True
            if text in {"false", "0", "no"}:
                return False
            return None
        if data_type == "STRING":
            return _clean_text(value)
        return _python_scalar(value)

    def _source_record_id(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> str:
        source_hash = _clean_text(row.get("source_file_sha256")) or "NOHASH"
        row_number = _as_integral(row.get("source_row_number"))
        return f"{dataset_id}:{source_hash}:{row_number or 0}"

    def _lineage(
        self,
        *,
        dataset_id: str,
        source_record_id: str,
        canonical_object: str,
        mapping: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "dataset_id": dataset_id,
            "source_table": self.profiles[dataset_id]["source_table"],
            "source_record_id": source_record_id,
            "target_object": canonical_object,
            "canonical_field": str(mapping["target"]),
            "source_fields": list(_mapping_source_fields(mapping)),
            "transform_id": str(mapping["transform"]),
            "semantic_status": str(mapping["status"]),
            "mapping_version": self.mapping_version,
            "dictionary_revision": self.dictionary_revision,
        }

    def _source_extensions(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> dict[str, Any]:
        dataset = self.mapping_contract.datasets[dataset_id]
        fields = tuple(
            dict.fromkeys(
                [
                    *SOURCE_EVIDENCE_FIELDS,
                    *dataset.get("source_extensions", []),
                ]
            )
        )
        return {
            field_name: _python_scalar(row.get(field_name))
            for field_name in fields
        }

    def _build_record(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> tuple[DailyFundsCanonicalRecord | None, tuple[str, ...]]:
        dataset = self.mapping_contract.datasets[dataset_id]
        canonical_object = str(dataset["canonical_object"])
        field_catalog = self.object_fields[canonical_object]
        source_record_id = self._source_record_id(dataset_id, row)
        values: dict[str, Any] = {}
        quality_flags = list(dataset.get("quality_flags", []))
        lineage: list[dict[str, Any]] = []

        for mapping in dataset["mappings"]:
            target = str(mapping["target"])
            source_fields = _mapping_source_fields(mapping)
            transformed = self._apply_transform(
                transform=str(mapping["transform"]),
                source_fields=source_fields,
                row=row,
                target_field=target,
            )
            coerced = self._coerce_value(transformed, field_catalog[target])
            enum_ref = field_catalog[target].get("enum_ref")
            if (
                coerced is not None
                and enum_ref
                and coerced not in self.enum_definitions[enum_ref]
            ):
                quality_flags.append(
                    f"CANONICAL_ENUM_INVALID_{target.upper()}"
                )
                coerced = None
            if (
                transformed is not None
                and coerced is None
                and str(field_catalog[target].get("data_type"))
                in {"INT", "LONG"}
            ):
                quality_flags.append(
                    f"NON_INTEGRAL_CANONICAL_{target.upper()}"
                )
            values[target] = coerced
            if mapping.get("status") == "MAPPED_WITH_WARNING":
                quality_flags.append(f"MAPPING_WARNING_{target.upper()}")
            lineage.append(
                self._lineage(
                    dataset_id=dataset_id,
                    source_record_id=source_record_id,
                    canonical_object=canonical_object,
                    mapping=mapping,
                )
            )

        source_quality = _clean_text(row.get("quality_status"))
        if source_quality and source_quality != "PASSED":
            quality_flags.append(f"SOURCE_QUALITY_{source_quality.upper()}")

        primary_fields = PRIMARY_KEY_FIELDS[canonical_object]
        primary_key = {field_name: values.get(field_name) for field_name in primary_fields}
        missing_primary = [
            field_name
            for field_name, value in primary_key.items()
            if value is None
        ]
        if missing_primary:
            return None, tuple(
                f"RECORD_SKIPPED_PRIMARY_KEY_MISSING_{field_name.upper()}"
                for field_name in missing_primary
            )

        snapshot_date = _as_date(row.get("snapshot_date"))
        return (
            DailyFundsCanonicalRecord(
                dataset_id=dataset_id,
                canonical_object=canonical_object,
                primary_key=primary_key,
                values=values,
                source_record_id=source_record_id,
                source_extensions=self._source_extensions(dataset_id, row),
                quality_flags=tuple(dict.fromkeys(quality_flags)),
                lineage=tuple(lineage),
                snapshot_date=snapshot_date,
                ingested_at=_as_datetime(row.get("ingested_at_utc")),
            ),
            (),
        )

    @staticmethod
    def _revision_key(record: DailyFundsCanonicalRecord) -> tuple[str, str]:
        value = record.ingested_at
        if value is None:
            timestamp = ""
        elif value.tzinfo is None:
            timestamp = value.isoformat(timespec="microseconds")
        else:
            timestamp = (
                value.astimezone(timezone.utc)
                .replace(tzinfo=None)
                .isoformat(timespec="microseconds")
            )
        return timestamp, record.source_record_id

    @staticmethod
    def _primary_key_tuple(
        record: DailyFundsCanonicalRecord,
    ) -> tuple[tuple[str, str], ...]:
        return tuple(
            (key, str(value))
            for key, value in record.primary_key.items()
        )

    def _deduplicate_revisions(
        self,
        records: Sequence[DailyFundsCanonicalRecord],
    ) -> tuple[list[DailyFundsCanonicalRecord], int]:
        selected: dict[
            tuple[tuple[str, str], ...],
            DailyFundsCanonicalRecord,
        ] = {}
        collapsed = 0
        for record in records:
            key = self._primary_key_tuple(record)
            existing = selected.get(key)
            if existing is None:
                selected[key] = record
                continue
            collapsed += 1
            if self._revision_key(record) >= self._revision_key(existing):
                selected[key] = record
        return list(selected.values()), collapsed

    @staticmethod
    def _canonical_entity_key(record: DailyFundsCanonicalRecord) -> str:
        if "instrument_id" in record.primary_key:
            return str(record.primary_key["instrument_id"])
        return str(record.primary_key.get("node_id", ""))

    def _limit_records(
        self,
        records: Sequence[DailyFundsCanonicalRecord],
        limit_per_entity: int,
    ) -> list[DailyFundsCanonicalRecord]:
        counts: defaultdict[str, int] = defaultdict(int)
        selected: list[DailyFundsCanonicalRecord] = []
        ordered = sorted(
            records,
            key=lambda record: (
                self._canonical_entity_key(record),
                str(record.snapshot_date or ""),
                str(record.primary_key),
            ),
        )
        for record in ordered:
            entity_key = self._canonical_entity_key(record)
            if counts[entity_key] >= limit_per_entity:
                continue
            counts[entity_key] += 1
            selected.append(record)
        return selected

    def _known_quarantine_warnings(
        self,
        request: DailyFundsReadRequest,
    ) -> list[str]:
        warnings: list[str] = []
        for item in self.known_quarantines:
            quarantine_date = _as_date(item.get("snapshot_date"))
            if (
                item.get("dataset_id") == request.dataset_id
                and quarantine_date is not None
                and request.start_date <= quarantine_date <= request.end_date
            ):
                warnings.append(
                    "KNOWN_QUARANTINED_SOURCE_DATE:"
                    f"{request.dataset_id}:{quarantine_date}:"
                    f"{item.get('reason_code')}"
                )
        return warnings

    def read(
        self,
        request: DailyFundsReadRequest,
    ) -> DailyFundsStandardBatch:
        self._validate_request(request)
        raw_rows = normalise_query_records(
            self.adapter.run_readonly_query(self._build_query(request))
        )
        selected_rows, matched_selectors = self._filter_entity_rows(
            request,
            raw_rows,
        )
        records: list[DailyFundsCanonicalRecord] = []
        warnings = self._known_quarantine_warnings(request)
        skipped_flags: Counter[str] = Counter()

        for row in selected_rows:
            if _clean_text(row.get("dataset_id")) != request.dataset_id:
                skipped_flags["RECORD_SKIPPED_DATASET_MISMATCH"] += 1
                continue
            record, skip_reasons = self._build_record(request.dataset_id, row)
            if record is None:
                skipped_flags.update(skip_reasons)
                continue
            records.append(record)

        deduplicated, collapsed = self._deduplicate_revisions(records)
        limited = self._limit_records(deduplicated, request.limit_per_entity)
        for selector in request.entity_ids:
            if selector not in matched_selectors:
                warnings.append(f"NO_DATA_FOR_ENTITY:{selector}")
        if collapsed:
            warnings.append(f"COLLAPSED_RAW_REVISIONS:{collapsed}")
        if len(raw_rows) >= int(self.query_policy["max_raw_rows_per_request"]):
            warnings.append("QUERY_REACHED_RAW_ROW_CAP")
        for flag, count in sorted(skipped_flags.items()):
            warnings.append(f"{flag}:{count}")

        return DailyFundsStandardBatch(
            dataset_id=request.dataset_id,
            canonical_object=str(
                self.mapping_contract.datasets[request.dataset_id][
                    "canonical_object"
                ]
            ),
            coverage_version=self.coverage_version,
            mapping_version=self.mapping_version,
            dictionary_revision=self.dictionary_revision,
            scanned_source_row_count=len(raw_rows),
            source_row_count=len(selected_rows),
            records=tuple(limited),
            warnings=tuple(dict.fromkeys(warnings)),
        )
