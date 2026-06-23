"""日K标准数据Provider。

本模块属于日K数据集插件层，不属于通用标准数据服务核心。

职责：
1. 把DolphinDBDailyKStandardizedService接入StandardDataService；
2. 传播日K覆盖、映射、字典、质量和血缘信息；
3. 保持通用核心不依赖DolphinDB和日K专属规则。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from .data_contracts import (
    DataContractError,
    MappingStatus,
    QualityStatus,
)
from .dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


_BLOCKING_DAILY_K_FLAGS = frozenset(
    {
        "SOURCE_PRICE_CHANGE_MISMATCH",
        "SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH",
        "SOURCE_ADJ_FORMULA_MISMATCH",
    }
)


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
