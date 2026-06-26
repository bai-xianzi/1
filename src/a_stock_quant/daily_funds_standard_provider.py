"""七类日线资金 StandardDataService Provider。

把 TASK_017C 的只读 Canonical 服务注册到统一标准数据入口。
分类节点使用 entity_ids，证券型来源使用 instrument_ids。
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from .data_contracts import DataContractError, QualityStatus
from .daily_funds_canonical_contract import REQUIRED_DATASETS
from .dolphindb_daily_funds_service import (
    DailyFundsReadRequest,
    DolphinDBDailyFundsCanonicalService,
)
from .standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataService,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


PROVIDER_REGISTRY_RELATIVE_PATH = (
    "configs/datasets/a_stock_daily_funds_standard_providers.yaml"
)

_HISTORICAL_BLOCKED_USAGES = frozenset(
    {
        StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
        StandardDataUsage.HISTORICAL_MODEL_TRAINING,
    }
)


def _load_registry(project_root: Path) -> dict[str, Any]:
    path = project_root / PROVIDER_REGISTRY_RELATIVE_PATH
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DataContractError("Provider注册配置根节点必须是映射。")
    return payload


class DailyFundsStandardDataProvider(StandardDatasetProvider):
    """把单个七类来源接入统一 StandardDataService。"""

    def __init__(
        self,
        service: DolphinDBDailyFundsCanonicalService,
        dataset_id: str,
        *,
        project_root: str | Path,
    ) -> None:
        if dataset_id not in REQUIRED_DATASETS:
            raise DataContractError(f"不支持七类来源：{dataset_id}")
        self.service = service
        self.dataset_id = dataset_id
        self.project_root = Path(project_root).resolve()
        self.registry = _load_registry(self.project_root)
        try:
            self.registration = dict(
                self.registry["providers"][dataset_id]
            )
        except KeyError as exc:
            raise DataContractError(
                f"Provider注册表缺少来源：{dataset_id}"
            ) from exc
        self.profile = service.dataset_profile(dataset_id)
        self.canonical_object = str(
            self.registration["canonical_object"]
        )
        profile_object = str(self.profile["canonical_object"])
        if self.canonical_object != profile_object:
            raise DataContractError(
                "Provider对象与Canonical服务不一致："
                f"{dataset_id}/{self.canonical_object}/{profile_object}"
            )

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id=str(self.registration["provider_id"]),
            dataset_id=self.dataset_id,
            supported_objects=(self.canonical_object,),
            coverage_version=self.service.coverage_version,
            mapping_version=self.service.mapping_version,
            dictionary_revision=self.service.dictionary_revision,
            selector_mode=str(self.registration["selector_mode"]),
        )

    def available_fields(self) -> tuple[str, ...]:
        return self.service.available_fields(self.dataset_id)

    def _selected_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        available = self.available_fields()
        if not request.fields:
            return available
        unknown = sorted(set(request.fields) - set(available))
        if unknown:
            raise DataContractError(
                "请求了未登记的七类Canonical字段："
                f"{unknown}"
            )
        return request.fields

    def _selector_ids(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        mode = self.descriptor.selector_mode
        if mode == INSTRUMENT_SELECTOR_MODE:
            return request.instrument_ids
        if mode == ENTITY_SELECTOR_MODE:
            return request.entity_ids
        raise DataContractError(f"未知Provider选择器：{mode}")

    @staticmethod
    def _project_lineage(
        lineage: tuple[dict[str, Any], ...],
        request: StandardDataQuery,
    ) -> tuple[dict[str, Any], ...]:
        if not request.include_lineage:
            return ()
        if not request.fields:
            return tuple(lineage)
        return tuple(
            item
            for item in lineage
            if item.get("canonical_field") in request.fields
        )

    @staticmethod
    def _usage_gate(
        request: StandardDataQuery,
    ) -> tuple[bool, tuple[str, ...]]:
        warnings: list[str] = [
            "DAILY_FUNDS_EXACT_AVAILABLE_AT_UNPROVEN"
        ]
        blocks = False
        if request.usage in _HISTORICAL_BLOCKED_USAGES:
            blocks = True
            warnings.append(
                "DAILY_FUNDS_STRICT_HISTORICAL_USAGE_BLOCKED"
            )
        elif (
            request.usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            and request.decision_time is not None
            and request.decision_time.date() <= request.end_date
        ):
            blocks = True
            warnings.append(
                "DAILY_FUNDS_SAME_DAY_DECISION_TIME_UNPROVEN"
            )
        return blocks, tuple(warnings)

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        if request.dataset_id != self.dataset_id:
            raise DataContractError(
                "查询数据集与七类Provider不一致。"
            )
        if request.canonical_object != self.canonical_object:
            raise DataContractError(
                "查询Canonical对象与七类Provider不一致。"
            )

        selected_fields = self._selected_fields(request)
        selectors = self._selector_ids(request)
        batch = self.service.read(
            DailyFundsReadRequest(
                dataset_id=self.dataset_id,
                entity_ids=selectors,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_entity=request.limit_per_instrument,
            )
        )

        records: list[StandardDataRecord] = []
        quality_counts: Counter[str] = Counter()
        lineage_item_count = 0
        for source_record in batch.records:
            projected_values = {
                field_name: source_record.values.get(field_name)
                for field_name in selected_fields
            }
            quality_flags = tuple(
                source_record.quality_flags
                if request.include_quality_flags
                else ()
            )
            quality_counts.update(quality_flags)
            lineage = self._project_lineage(
                source_record.lineage,
                request,
            )
            lineage_item_count += len(lineage)
            records.append(
                StandardDataRecord(
                    canonical_object=source_record.canonical_object,
                    primary_key=dict(source_record.primary_key),
                    values=projected_values,
                    source_record_id=source_record.source_record_id,
                    source_extensions=(
                        dict(source_record.source_extensions)
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        usage_blocks, usage_warnings = self._usage_gate(request)
        warnings = tuple(
            dict.fromkeys([*batch.warnings, *usage_warnings])
        )
        if usage_blocks:
            status = QualityStatus.FAILED
            blocks_downstream = True
        elif warnings or quality_counts:
            status = QualityStatus.WARNING
            blocks_downstream = False
        else:
            status = QualityStatus.PASSED
            blocks_downstream = False

        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=batch.canonical_object,
            provider_id=self.descriptor.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(records),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=warnings,
            quality_flag_counts=dict(sorted(quality_counts.items())),
            lineage_item_count=lineage_item_count,
        )
        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(records),
        )


def build_daily_funds_standard_providers(
    service: DolphinDBDailyFundsCanonicalService,
    *,
    project_root: str | Path,
) -> tuple[DailyFundsStandardDataProvider, ...]:
    return tuple(
        DailyFundsStandardDataProvider(
            service,
            dataset_id,
            project_root=project_root,
        )
        for dataset_id in REQUIRED_DATASETS
    )


def register_daily_funds_standard_providers(
    standard_service: StandardDataService,
    canonical_service: DolphinDBDailyFundsCanonicalService,
    *,
    project_root: str | Path,
    replace: bool = False,
) -> tuple[ProviderDescriptor, ...]:
    providers = build_daily_funds_standard_providers(
        canonical_service,
        project_root=project_root,
    )
    for provider in providers:
        standard_service.register_provider(
            provider,
            replace=replace,
        )
    return tuple(provider.descriptor for provider in providers)
