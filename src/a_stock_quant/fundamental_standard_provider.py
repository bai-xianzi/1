"""基本面标准数据Provider与用途级时点门禁。"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from .data_contracts import DataContractError, QualityStatus
from .dolphindb_fundamental_service import (
    DATASET_ID,
    DolphinDBFundamentalStandardizedService,
    FundamentalCanonicalRecord,
    FundamentalReadRequest,
)
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


_HISTORICAL_BLOCKED_USAGES = frozenset(
    {
        StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
        StandardDataUsage.HISTORICAL_MODEL_TRAINING,
    }
)

# 该目录必须与schemas/canonical_fields.yaml revision 0.5完全一致。
_FIELDS_BY_OBJECT: dict[str, tuple[str, ...]] = {
    "FundamentalSnapshot": (
        "instrument_id",
        "company_id",
        "report_period",
        "period_type",
        "fiscal_year",
        "fiscal_quarter",
        "announcement_date",
        "statement_type",
        "consolidation_scope",
        "accounting_standard_code",
        "currency_code",
        "revenue_cny",
        "operating_cost_cny",
        "operating_profit_cny",
        "total_profit_cny",
        "net_profit_cny",
        "net_profit_parent_cny",
        "total_assets_cny",
        "total_equity_cny",
        "inventory_cny",
        "accounts_receivable_cny",
        "operating_cash_flow_cny",
        "basic_eps_cny",
        "book_value_per_share_cny",
    ),
    "OwnershipSnapshot": (
        "instrument_id",
        "as_of_date",
        "total_shares",
        "float_shares",
        "shareholder_count",
    ),
    "Instrument": (
        "instrument_id",
        "symbol",
        "exchange_code",
        "market_code",
        "asset_class",
        "security_type",
        "instrument_name_cn",
        "company_id",
        "currency_code",
        "listing_date",
        "trading_status",
        "is_st",
        "is_new_listing",
        "lot_size_shares",
    ),
    "ClassificationMembership": (
        "classification_system",
        "classification_version",
        "classification_type",
        "node_id",
        "node_code",
        "node_name_cn",
        "node_name_en",
        "node_level",
        "parent_node_id",
        "instrument_id",
        "membership_weight_pct",
        "membership_rank",
        "effective_from",
        "effective_to",
        "membership_reason",
    ),
}


class FundamentalStandardDataProvider(StandardDatasetProvider):
    """把基本面标准化服务接入StandardDataService。"""

    provider_id = "dolphindb_fundamental_standard_provider"

    def __init__(
        self,
        service: DolphinDBFundamentalStandardizedService,
    ) -> None:
        self.service = service

    @property
    def descriptor(self) -> ProviderDescriptor:
        registration = self.service.registration
        return ProviderDescriptor(
            provider_id=self.provider_id,
            dataset_id=registration.dataset_id,
            supported_objects=tuple(sorted(_FIELDS_BY_OBJECT)),
            coverage_version=registration.coverage_version,
            mapping_version=registration.mapping_version,
            dictionary_revision=registration.dictionary_revision,
        )

    def available_fields(
        self,
        canonical_object: str,
    ) -> tuple[str, ...]:
        try:
            return _FIELDS_BY_OBJECT[canonical_object]
        except KeyError as exc:
            raise DataContractError(
                "基本面Provider不支持标准对象："
                f"{canonical_object}"
            ) from exc

    def _selected_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        available = self.available_fields(request.canonical_object)
        if not request.fields:
            return available

        unknown = sorted(set(request.fields) - set(available))
        if unknown:
            raise DataContractError(
                "请求了未登记的基本面标准字段："
                f"{unknown}"
            )
        return request.fields

    @staticmethod
    def _record_is_visible(
        record: FundamentalCanonicalRecord,
        request: StandardDataQuery,
    ) -> tuple[bool, str | None]:
        assert request.as_of_date is not None

        if (
            record.snapshot_date is not None
            and record.snapshot_date > request.as_of_date
        ):
            return False, "SNAPSHOT_AFTER_AS_OF"

        # imported_at是当前唯一可以证明的本地可用时间。缺失时采取安全失败。
        if record.imported_at is None:
            return False, "AVAILABLE_AT_MISSING"

        if record.imported_at.date() > request.as_of_date:
            return False, "IMPORTED_AFTER_AS_OF"

        if request.decision_time is None:
            # 日期级研究查询按as_of_date日终解释，并在结果中保留时区警告。
            return True, None

        decision_time = request.decision_time
        assert isinstance(decision_time, datetime)

        # DolphinDB中的imported_at没有明确时区。为避免伪精确，同日内不能证明
        # imported_at <= decision_time；只有决策日期严格晚于入库日期时才可见。
        if decision_time.date() <= record.imported_at.date():
            return False, "SAME_DAY_TIMEZONE_UNPROVEN"

        return True, None

    @staticmethod
    def _project_lineage(
        record: FundamentalCanonicalRecord,
        request: StandardDataQuery,
    ) -> tuple[dict[str, Any], ...]:
        if not request.include_lineage:
            return ()
        return tuple(
            item
            for item in record.lineage
            if (
                not request.fields
                or item.get("canonical_field") in request.fields
            )
        )

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        if request.dataset_id != DATASET_ID:
            raise DataContractError(
                "查询数据集与基本面Provider不一致。"
            )

        selected_fields = self._selected_fields(request)
        assert request.as_of_date is not None

        pre_coverage = request.as_of_date < self.service.coverage_date
        batch = self.service.read(
            FundamentalReadRequest(
                instrument_ids=request.instrument_ids,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_instrument=request.limit_per_instrument,
            )
        )

        warnings = list(batch.warnings)
        quality_counts: Counter[str] = Counter()
        visibility_counts: Counter[str] = Counter()
        lineage_item_count = 0
        result_records: list[StandardDataRecord] = []
        matching_object_count = 0

        for record in batch.records:
            if record.canonical_object != request.canonical_object:
                continue

            matching_object_count += 1
            visible, reason = self._record_is_visible(record, request)
            if not visible:
                visibility_counts[reason or "UNKNOWN"] += 1
                continue

            values = {
                field_name: record.values.get(field_name)
                for field_name in selected_fields
            }
            quality_flags = tuple(
                record.quality_flags
                if request.include_quality_flags
                else ()
            )
            quality_counts.update(quality_flags)

            lineage = self._project_lineage(record, request)
            lineage_item_count += len(lineage)

            result_records.append(
                StandardDataRecord(
                    canonical_object=record.canonical_object,
                    primary_key=dict(record.primary_key),
                    values=values,
                    source_record_id=record.source_record_id,
                    source_extensions=(
                        dict(record.source_extensions)
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        if pre_coverage:
            warnings.append(
                "查询时点早于当前基本面快照覆盖日2026-06-19，"
                "不得用当前快照回填历史。"
            )

        for reason, count in sorted(visibility_counts.items()):
            warnings.append(
                f"基本面时点门禁过滤{count}条记录：{reason}。"
            )

        historical_blocked = request.usage in _HISTORICAL_BLOCKED_USAGES
        if historical_blocked:
            warnings.append(
                "当前基本面数据只有2026-06-19观察快照，"
                "update_date不能证明是正式公告日期；"
                "严格历史回测和历史模型训练被阻断。"
            )

        if request.usage in {
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            StandardDataUsage.MANUAL_DECISION_SUPPORT,
        }:
            warnings.append(
                "当前快照只允许研究或快照之后的人工辅助决策；"
                "金额与股本单位为经验确认，利润、权益、公告日、"
                "公司身份及分类版本仍保留WARNING。"
            )

        missing_requested_object = (
            batch.source_row_count > 0
            and matching_object_count == 0
        )
        if missing_requested_object:
            warnings.append(
                "来源记录存在，但没有生成请求的标准对象；"
                "空财务载荷不会被补零。"
            )

        all_matching_invisible = (
            matching_object_count > 0
            and not result_records
            and bool(visibility_counts)
        )

        blocks_downstream = any(
            (
                pre_coverage,
                historical_blocked,
                missing_requested_object,
                all_matching_invisible,
            )
        )

        if blocks_downstream:
            status = QualityStatus.FAILED
        elif warnings or quality_counts:
            status = QualityStatus.WARNING
        else:
            status = QualityStatus.PASSED

        combined_quality_counts = Counter(quality_counts)
        combined_quality_counts.update(
            {
                f"VISIBILITY_{key}": value
                for key, value in visibility_counts.items()
            }
        )

        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=request.canonical_object,
            provider_id=self.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(result_records),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=tuple(dict.fromkeys(warnings)),
            quality_flag_counts=dict(
                sorted(combined_quality_counts.items())
            ),
            lineage_item_count=lineage_item_count,
        )

        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(result_records),
        )
