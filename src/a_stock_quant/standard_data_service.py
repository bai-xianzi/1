"""统一标准数据服务接口与标准查询结果合同。

本模块位于数据集专属标准化服务和下游业务模块之间。

目标：
1. 下游不直接调用 DolphinDB 或任何来源专属查询接口；
2. 所有数据集通过统一 Provider 接入；
3. 查询请求显式携带数据集、标准对象、证券、日期和时点边界；
4. 查询结果统一携带覆盖版本、映射版本、字典版本、质量和血缘；
5. 日K只是第一个 Provider，后续基本面和七类快照复用同一合同。

本模块不负责写入数据库，也不负责因子、策略和回测。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping
from uuid import uuid4

from .data_contracts import (
    DataContractError,
    MappingStatus,
    QualityStatus,
)
from .dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)


_BLOCKING_DAILY_K_FLAGS = frozenset(
    {
        "SOURCE_PRICE_CHANGE_MISMATCH",
        "SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH",
        "SOURCE_ADJ_FORMULA_MISMATCH",
    }
)


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name} 不能为空。")

    return value.strip()


def _normalise_unique_texts(
    values: Iterable[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalised = tuple(
        _require_text(value, field_name)
        for value in values
    )

    if not allow_empty and not normalised:
        raise DataContractError(
            f"{field_name} 至少包含一个值。"
        )

    if len(set(normalised)) != len(normalised):
        raise DataContractError(
            f"{field_name} 不允许重复。"
        )

    return normalised


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]

    return value


@dataclass(frozen=True, slots=True)
class StandardDataQuery:
    """来源无关的标准数据查询请求。

    as_of_date 是最小的时点安全门禁：
    查询结束日期不得晚于该日期。后续基本面 Provider 仍需基于
    公告日期或 available_at 执行更严格的可见性过滤。
    """

    dataset_id: str
    canonical_object: str
    instrument_ids: tuple[str, ...]
    start_date: date
    end_date: date
    fields: tuple[str, ...] = ()
    as_of_date: date | None = None
    limit_per_instrument: int = 5_000
    include_source_extensions: bool = False
    include_quality_flags: bool = True
    include_lineage: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "canonical_object",
            _require_text(
                self.canonical_object,
                "canonical_object",
            ),
        )
        object.__setattr__(
            self,
            "instrument_ids",
            _normalise_unique_texts(
                self.instrument_ids,
                "instrument_ids",
            ),
        )
        object.__setattr__(
            self,
            "fields",
            _normalise_unique_texts(
                self.fields,
                "fields",
                allow_empty=True,
            ),
        )

        if not isinstance(self.start_date, date):
            raise DataContractError(
                "start_date 必须是 date。"
            )

        if not isinstance(self.end_date, date):
            raise DataContractError(
                "end_date 必须是 date。"
            )

        if self.start_date > self.end_date:
            raise DataContractError(
                "start_date 不能晚于 end_date。"
            )

        resolved_as_of = self.as_of_date or self.end_date

        if not isinstance(resolved_as_of, date):
            raise DataContractError(
                "as_of_date 必须是 date。"
            )

        if self.end_date > resolved_as_of:
            raise DataContractError(
                "end_date 不能晚于 as_of_date，"
                "否则会形成未来数据查询。"
            )

        object.__setattr__(
            self,
            "as_of_date",
            resolved_as_of,
        )

        if (
            not isinstance(self.limit_per_instrument, int)
            or not 1 <= self.limit_per_instrument <= 5_000
        ):
            raise DataContractError(
                "limit_per_instrument 必须是1到5000之间的整数。"
            )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class StandardDataRecord:
    """一个标准对象记录。"""

    canonical_object: str
    primary_key: dict[str, Any]
    values: dict[str, Any]
    source_record_id: str | None = None
    source_extensions: dict[str, Any] = field(
        default_factory=dict
    )
    quality_flags: tuple[str, ...] = ()
    lineage: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_object",
            _require_text(
                self.canonical_object,
                "canonical_object",
            ),
        )

        if not self.primary_key:
            raise DataContractError(
                "标准记录必须包含 primary_key。"
            )

        if not isinstance(self.values, dict):
            raise DataContractError(
                "values 必须是字典。"
            )

        if self.source_record_id is not None:
            object.__setattr__(
                self,
                "source_record_id",
                _require_text(
                    self.source_record_id,
                    "source_record_id",
                ),
            )

        object.__setattr__(
            self,
            "quality_flags",
            _normalise_unique_texts(
                self.quality_flags,
                "quality_flags",
                allow_empty=True,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class StandardQueryMetadata:
    """标准查询结果的版本、质量和血缘摘要。"""

    dataset_id: str
    canonical_object: str
    provider_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    source_row_count: int
    result_count: int
    status: QualityStatus
    blocks_downstream: bool
    warnings: tuple[str, ...] = ()
    quality_flag_counts: dict[str, int] = field(
        default_factory=dict
    )
    lineage_item_count: int = 0
    query_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        for field_name in (
            "dataset_id",
            "canonical_object",
            "provider_id",
            "coverage_version",
            "mapping_version",
            "dictionary_revision",
            "query_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if self.source_row_count < 0:
            raise DataContractError(
                "source_row_count 不能为负数。"
            )

        if self.result_count < 0:
            raise DataContractError(
                "result_count 不能为负数。"
            )

        if self.lineage_item_count < 0:
            raise DataContractError(
                "lineage_item_count 不能为负数。"
            )

        if (
            self.status is QualityStatus.PASSED
            and self.blocks_downstream
        ):
            raise DataContractError(
                "PASSED 查询不能阻断下游。"
            )

        object.__setattr__(
            self,
            "warnings",
            tuple(
                _require_text(item, "warnings")
                for item in self.warnings
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class StandardQueryResult:
    """统一标准查询结果合同。"""

    query: StandardDataQuery
    metadata: StandardQueryMetadata
    records: tuple[StandardDataRecord, ...]

    def __post_init__(self) -> None:
        if self.metadata.dataset_id != self.query.dataset_id:
            raise DataContractError(
                "查询与结果的 dataset_id 不一致。"
            )

        if (
            self.metadata.canonical_object
            != self.query.canonical_object
        ):
            raise DataContractError(
                "查询与结果的 canonical_object 不一致。"
            )

        if self.metadata.result_count != len(self.records):
            raise DataContractError(
                "metadata.result_count 与 records 数量不一致。"
            )

        invalid_objects = sorted(
            {
                record.canonical_object
                for record in self.records
                if record.canonical_object
                != self.query.canonical_object
            }
        )

        if invalid_objects:
            raise DataContractError(
                "结果中存在不匹配的标准对象："
                f"{invalid_objects}"
            )

    def assert_usable(self) -> None:
        if self.metadata.blocks_downstream:
            raise DataContractError(
                "标准查询结果被质量门禁阻断。"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "metadata": self.metadata.to_dict(),
            "records": [
                record.to_dict()
                for record in self.records
            ],
        }


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """标准数据 Provider 的公开描述。"""

    provider_id: str
    dataset_id: str
    supported_objects: tuple[str, ...]
    coverage_version: str
    mapping_version: str
    dictionary_revision: str

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


class StandardDatasetProvider(ABC):
    """数据集专属标准化服务的统一 Provider 接口。"""

    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        raise NotImplementedError


class StandardDataService:
    """面向所有下游模块的统一标准数据入口。"""

    def __init__(self) -> None:
        self._providers: dict[
            str,
            StandardDatasetProvider,
        ] = {}

    def register_provider(
        self,
        provider: StandardDatasetProvider,
        *,
        replace: bool = False,
    ) -> None:
        descriptor = provider.descriptor
        dataset_id = descriptor.dataset_id

        if dataset_id in self._providers and not replace:
            raise DataContractError(
                f"数据集 Provider 已注册：{dataset_id}"
            )

        self._providers[dataset_id] = provider

    def list_datasets(self) -> tuple[ProviderDescriptor, ...]:
        return tuple(
            self._providers[key].descriptor
            for key in sorted(self._providers)
        )

    def get_provider(
        self,
        dataset_id: str,
    ) -> StandardDatasetProvider:
        key = _require_text(dataset_id, "dataset_id")

        try:
            return self._providers[key]
        except KeyError as exc:
            raise DataContractError(
                f"未注册标准数据 Provider：{key}"
            ) from exc

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        provider = self.get_provider(request.dataset_id)

        if (
            request.canonical_object
            not in provider.descriptor.supported_objects
        ):
            raise DataContractError(
                "Provider 不支持标准对象："
                f"{request.canonical_object}"
            )

        result = provider.query(request)

        if result.metadata.dataset_id != request.dataset_id:
            raise DataContractError(
                "Provider 返回了错误的数据集。"
            )

        return result


class DailyKStandardDataProvider(StandardDatasetProvider):
    """把 TASK_010 日K服务接入统一标准数据服务。"""

    provider_id = "dolphindb_daily_k_standard_provider"

    def __init__(
        self,
        service: DolphinDBDailyKStandardizedService,
    ) -> None:
        self.service = service
        self.registration = service.registration
        self._fields_by_object = self._build_field_catalog()

    def _build_field_catalog(
        self,
    ) -> dict[str, tuple[str, ...]]:
        fields: dict[str, list[str]] = {}

        for rule in self.registration.field_mappings:
            if rule.status not in {
                MappingStatus.MAPPED,
                MappingStatus.WARNING,
            }:
                continue

            if (
                rule.target_object is None
                or rule.canonical_field is None
            ):
                continue

            values = fields.setdefault(
                rule.target_object,
                [],
            )

            if rule.canonical_field not in values:
                values.append(rule.canonical_field)

        return {
            object_name: tuple(field_names)
            for object_name, field_names in fields.items()
        }

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id=self.provider_id,
            dataset_id=self.registration.dataset_id,
            supported_objects=tuple(
                sorted(self._fields_by_object)
            ),
            coverage_version=
                self.registration.coverage_version,
            mapping_version=
                self.registration.mapping_version,
            dictionary_revision=
                self.registration.dictionary_revision,
        )

    def available_fields(
        self,
        canonical_object: str,
    ) -> tuple[str, ...]:
        try:
            return self._fields_by_object[
                canonical_object
            ]
        except KeyError as exc:
            raise DataContractError(
                "日K Provider 不支持标准对象："
                f"{canonical_object}"
            ) from exc

    def _validate_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        available = self.available_fields(
            request.canonical_object
        )

        if not request.fields:
            return available

        unknown = sorted(
            set(request.fields) - set(available)
        )

        if unknown:
            raise DataContractError(
                "请求了未登记的标准字段："
                f"{unknown}"
            )

        return request.fields

    @staticmethod
    def _primary_key(
        canonical_object: str,
        values: Mapping[str, Any],
        fallback: Mapping[str, Any],
    ) -> dict[str, Any]:
        if canonical_object == "DailyBar":
            return {
                "instrument_id": values.get(
                    "instrument_id",
                    fallback.get("instrument_id"),
                ),
                "trade_date": values.get(
                    "trade_date",
                    fallback.get("trade_date"),
                ),
            }

        if canonical_object == "OwnershipSnapshot":
            return {
                "instrument_id": values.get(
                    "instrument_id",
                    fallback.get("instrument_id"),
                ),
                "as_of_date": values.get(
                    "as_of_date",
                    fallback.get("trade_date"),
                ),
            }

        return dict(fallback)

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        if request.dataset_id != self.registration.dataset_id:
            raise DataContractError(
                "查询数据集与日K Provider 不一致。"
            )

        selected_fields = self._validate_fields(request)

        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=request.instrument_ids,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_instrument=
                    request.limit_per_instrument,
            )
        )

        rows: list[StandardDataRecord] = []
        warnings = list(batch.warnings)
        quality_counts: Counter[str] = Counter()
        lineage_item_count = 0

        for source_record in batch.records:
            canonical_values = (
                source_record.canonical_objects.get(
                    request.canonical_object
                )
            )

            if canonical_values is None:
                warnings.append(
                    "来源记录缺少标准对象："
                    f"{source_record.source_record_id} "
                    f"{request.canonical_object}"
                )
                continue

            projected_values = {
                field_name: canonical_values.get(field_name)
                for field_name in selected_fields
            }

            quality_flags = tuple(
                source_record.quality_flags
                if request.include_quality_flags
                else ()
            )
            quality_counts.update(quality_flags)

            lineage = tuple(
                item
                for item in source_record.lineage
                if (
                    item.get("target_object")
                    == request.canonical_object
                    and (
                        not request.fields
                        or item.get("canonical_field")
                        in request.fields
                    )
                )
            )
            if not request.include_lineage:
                lineage = ()

            lineage_item_count += len(lineage)

            rows.append(
                StandardDataRecord(
                    canonical_object=
                        request.canonical_object,
                    primary_key=self._primary_key(
                        request.canonical_object,
                        canonical_values,
                        source_record.primary_key,
                    ),
                    values=projected_values,
                    source_record_id=
                        source_record.source_record_id,
                    source_extensions=(
                        dict(
                            source_record.source_extensions
                        )
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        blocking_flag_count = sum(
            count
            for flag, count in quality_counts.items()
            if flag in _BLOCKING_DAILY_K_FLAGS
        )

        if blocking_flag_count:
            status = QualityStatus.FAILED
            blocks_downstream = True
        elif warnings:
            status = QualityStatus.WARNING
            blocks_downstream = False
        else:
            status = QualityStatus.PASSED
            blocks_downstream = False

        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=
                request.canonical_object,
            provider_id=self.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=
                batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(rows),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=tuple(warnings),
            quality_flag_counts=dict(
                sorted(quality_counts.items())
            ),
            lineage_item_count=lineage_item_count,
        )

        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(rows),
        )
