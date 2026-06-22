"""A股量化项目的最小数据接入契约。

本模块只定义不同数据来源和下游模块之间交换数据时必须遵守的
标准接口、状态和数据结构。

当前版本不连接 DolphinDB，不读取真实数据，也不执行具体 ETL 逻辑。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class SourceType(str, Enum):
    """数据来源类型。"""

    DOLPHINDB = "DOLPHINDB"
    DATABASE = "DATABASE"
    FILE = "FILE"
    API = "API"
    MANUAL = "MANUAL"
    OTHER = "OTHER"


class MappingStatus(str, Enum):
    """来源字段映射到标准字段时的状态。"""

    MAPPED = "MAPPED"
    UNMAPPED = "UNMAPPED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


class QualityStatus(str, Enum):
    """数据质量检查状态。"""

    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


class QualityLevel(str, Enum):
    """数据质量问题严重级别。"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ConfirmationStatus(str, Enum):
    """待人工确认事项的处理状态。"""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class BlockingLevel(str, Enum):
    """待确认事项对下游流程的阻断程度。"""

    NONE = "NONE"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class DataContractError(ValueError):
    """数据契约违反约定时抛出的基础异常。"""


def _new_id() -> str:
    """生成字符串形式的唯一标识。"""

    return str(uuid4())


def _utc_now() -> datetime:
    """生成带 UTC 时区的当前时间。"""

    return datetime.now(timezone.utc)


def _require_non_empty(value: str, field_name: str) -> None:
    """检查必填字符串是否为空。"""

    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name} 不能为空。")


@dataclass(slots=True)
class RawDataBatch:
    """从数据来源读取后、尚未修改语义的原始数据批次。"""

    source_id: str
    source_type: SourceType
    source_object_name: str
    raw_fields: list[str]
    records: list[dict[str, Any]]
    source_location: str | None = None
    data_version: str | None = None
    data_start: datetime | None = None
    data_end: datetime | None = None
    notes: str | None = None
    batch_id: str = field(default_factory=_new_id)
    read_at: datetime = field(default_factory=_utc_now)
    row_count: int = field(init=False)

    def __post_init__(self) -> None:
        """创建对象后执行最小一致性检查。"""

        _require_non_empty(self.source_id, "source_id")
        _require_non_empty(self.source_object_name, "source_object_name")
        _require_non_empty(self.batch_id, "batch_id")

        if not isinstance(self.source_type, SourceType):
            raise DataContractError("source_type 必须是 SourceType。")

        if any(not isinstance(name, str) or not name.strip() for name in self.raw_fields):
            raise DataContractError("raw_fields 中的每个字段名都必须是非空字符串。")

        if len(self.raw_fields) != len(set(self.raw_fields)):
            raise DataContractError("raw_fields 不能包含重复字段名。")

        if any(not isinstance(record, dict) for record in self.records):
            raise DataContractError("records 中的每一行都必须是字典。")

        if self.data_start and self.data_end and self.data_start > self.data_end:
            raise DataContractError("data_start 不能晚于 data_end。")

        self.row_count = len(self.records)


@dataclass(slots=True)
class FieldMappingResult:
    """一个来源字段映射到标准字段后的结果。"""

    source_field: str
    canonical_field_ref: str | None
    status: MappingStatus
    source_data_type: str | None = None
    target_data_type: str | None = None
    source_unit: str | None = None
    target_unit: str | None = None
    transform_rule: str | None = None
    requires_confirmation: bool = False
    message: str | None = None

    def __post_init__(self) -> None:
        """检查字段映射结果是否符合最小约定。"""

        _require_non_empty(self.source_field, "source_field")

        if not isinstance(self.status, MappingStatus):
            raise DataContractError("status 必须是 MappingStatus。")

        if self.status is MappingStatus.MAPPED and not self.canonical_field_ref:
            raise DataContractError(
                "状态为 MAPPED 时，canonical_field_ref 不能为空。"
            )

        if self.canonical_field_ref is not None:
            field_ref = self.canonical_field_ref.strip()
            if not field_ref:
                raise DataContractError("canonical_field_ref 不能是空字符串。")
            if "." not in field_ref:
                raise DataContractError(
                    "canonical_field_ref 必须使用 domain.field 格式。"
                )

        if (
            self.status is MappingStatus.PENDING_CONFIRMATION
            and not self.requires_confirmation
        ):
            raise DataContractError(
                "状态为 PENDING_CONFIRMATION 时，requires_confirmation 必须为 True。"
            )


@dataclass(slots=True)
class DataQualityResult:
    """一次数据质量检查的结构化结果。"""

    check_name: str
    level: QualityLevel
    status: QualityStatus
    checked_row_count: int
    failed_row_count: int
    blocking: bool
    sample_failures: list[dict[str, Any]] = field(default_factory=list)
    description: str | None = None
    check_id: str = field(default_factory=_new_id)
    checked_at: datetime = field(default_factory=_utc_now)
    failure_rate: float = field(init=False)

    def __post_init__(self) -> None:
        """检查行数、状态和唯一标识是否符合约定。"""

        _require_non_empty(self.check_name, "check_name")
        _require_non_empty(self.check_id, "check_id")

        if not isinstance(self.level, QualityLevel):
            raise DataContractError("level 必须是 QualityLevel。")
        if not isinstance(self.status, QualityStatus):
            raise DataContractError("status 必须是 QualityStatus。")
        if self.checked_row_count < 0:
            raise DataContractError("checked_row_count 不能小于 0。")
        if self.failed_row_count < 0:
            raise DataContractError("failed_row_count 不能小于 0。")
        if self.failed_row_count > self.checked_row_count:
            raise DataContractError(
                "failed_row_count 不能大于 checked_row_count。"
            )
        if self.status is QualityStatus.PASSED and self.failed_row_count > 0:
            raise DataContractError(
                "状态为 PASSED 时，failed_row_count 必须为 0。"
            )
        if any(not isinstance(item, dict) for item in self.sample_failures):
            raise DataContractError("sample_failures 中的每一项都必须是字典。")

        self.failure_rate = (
            0.0
            if self.checked_row_count == 0
            else self.failed_row_count / self.checked_row_count
        )

    @property
    def blocks_downstream(self) -> bool:
        """返回本次质量结果是否阻止下游继续运行。"""

        return self.blocking


@dataclass(slots=True)
class PendingConfirmation:
    """需要人工确认的数据语义或来源问题。"""

    category: str
    source_object: str
    issue_description: str
    field_or_object_name: str | None = None
    possible_options: list[str] = field(default_factory=list)
    status: ConfirmationStatus = ConfirmationStatus.OPEN
    blocking_level: BlockingLevel = BlockingLevel.WARNING
    resolution_text: str | None = None
    resolved_at: datetime | None = None
    confirmation_id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """检查待确认事项的基本完整性。"""

        _require_non_empty(self.category, "category")
        _require_non_empty(self.source_object, "source_object")
        _require_non_empty(self.issue_description, "issue_description")
        _require_non_empty(self.confirmation_id, "confirmation_id")

        if not isinstance(self.status, ConfirmationStatus):
            raise DataContractError("status 必须是 ConfirmationStatus。")
        if not isinstance(self.blocking_level, BlockingLevel):
            raise DataContractError("blocking_level 必须是 BlockingLevel。")
        if any(not isinstance(option, str) or not option.strip() for option in self.possible_options):
            raise DataContractError(
                "possible_options 中的每个选项都必须是非空字符串。"
            )
        if self.status is ConfirmationStatus.RESOLVED:
            if self.resolved_at is None:
                raise DataContractError(
                    "状态为 RESOLVED 时，resolved_at 不能为空。"
                )
            if not self.resolution_text or not self.resolution_text.strip():
                raise DataContractError(
                    "状态为 RESOLVED 时，resolution_text 不能为空。"
                )

    @property
    def blocks_downstream(self) -> bool:
        """判断当前事项是否仍阻断下游流程。"""

        return (
            self.status is ConfirmationStatus.OPEN
            and self.blocking_level is BlockingLevel.BLOCKING
        )


@dataclass(slots=True)
class CanonicalDataBatch:
    """完成字段映射后的标准化数据批次。"""

    raw_batch_id: str
    domain_code: str
    canonical_object_name: str
    field_dictionary_version: str
    mapping_version: str
    records: list[dict[str, Any]]
    quality_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    pending_confirmations: list[PendingConfirmation] = field(default_factory=list)
    notes: str | None = None
    batch_id: str = field(default_factory=_new_id)
    transformed_at: datetime = field(default_factory=_utc_now)
    row_count: int = field(init=False)

    def __post_init__(self) -> None:
        """检查标准化批次的基本完整性。"""

        _require_non_empty(self.raw_batch_id, "raw_batch_id")
        _require_non_empty(self.domain_code, "domain_code")
        _require_non_empty(self.canonical_object_name, "canonical_object_name")
        _require_non_empty(self.field_dictionary_version, "field_dictionary_version")
        _require_non_empty(self.mapping_version, "mapping_version")
        _require_non_empty(self.batch_id, "batch_id")

        if not isinstance(self.quality_status, QualityStatus):
            raise DataContractError("quality_status 必须是 QualityStatus。")
        if any(not isinstance(record, dict) for record in self.records):
            raise DataContractError("records 中的每一行都必须是字典。")
        if any(
            not isinstance(item, PendingConfirmation)
            for item in self.pending_confirmations
        ):
            raise DataContractError(
                "pending_confirmations 中的每一项都必须是 PendingConfirmation。"
            )

        self.row_count = len(self.records)

    @property
    def blocks_downstream(self) -> bool:
        """判断该标准化批次是否应阻止下游使用。"""

        if self.quality_status in {
            QualityStatus.FAILED,
            QualityStatus.PENDING_CONFIRMATION,
        }:
            return True
        return any(item.blocks_downstream for item in self.pending_confirmations)


@dataclass(slots=True)
class DataLineageRecord:
    """记录原始批次到标准批次之间的转换血缘。"""

    source_batch_id: str
    target_batch_id: str
    source_location: str
    target_object: str
    mapping_version: str
    transformation_version: str
    code_version: str | None = None
    configuration_version: str | None = None
    description: str | None = None
    lineage_id: str = field(default_factory=_new_id)
    transformed_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """检查血缘记录的关键标识和版本是否完整。"""

        required_values = {
            "source_batch_id": self.source_batch_id,
            "target_batch_id": self.target_batch_id,
            "source_location": self.source_location,
            "target_object": self.target_object,
            "mapping_version": self.mapping_version,
            "transformation_version": self.transformation_version,
            "lineage_id": self.lineage_id,
        }
        for field_name, value in required_values.items():
            _require_non_empty(value, field_name)

        if self.source_batch_id == self.target_batch_id:
            raise DataContractError(
                "source_batch_id 和 target_batch_id 不能相同。"
            )


class DataSourceAdapter(ABC):
    """所有数据来源适配器必须遵守的最小接口。"""

    def __init__(self, source_id: str, source_type: SourceType) -> None:
        """保存数据来源的唯一标识和来源类型。"""

        _require_non_empty(source_id, "source_id")
        if not isinstance(source_type, SourceType):
            raise DataContractError("source_type 必须是 SourceType。")
        self.source_id = source_id
        self.source_type = source_type

    @abstractmethod
    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        """从来源读取一批原始数据。"""

        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> DataQualityResult:
        """检查当前数据来源是否可用。"""

        raise NotImplementedError
