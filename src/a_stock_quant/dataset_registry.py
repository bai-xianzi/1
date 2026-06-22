"""通用数据集注册表与标准字段映射引擎。

目标：
1. 数据源表不直接决定系统核心结构；
2. 每个来源数据集必须显式登记；
3. 每个来源字段必须被映射、待确认或明确保留；
4. 映射规则可以随新数据集持续扩展；
5. 映射执行同时输出质量提示、来源扩展和字段血缘。

本模块不负责连接 DolphinDB，也不写入数据库。
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .data_contracts import (
    DataContractError,
    MappingStatus,
    SourceType,
)


TransformFunction = Callable[
    [
        list[Any],
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
    Any,
]


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name} 不能为空。")

    return value.strip()


def _require_unique(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(
        _require_text(value, field_name)
        for value in values
    )

    duplicates = [
        value
        for value, count in Counter(normalized).items()
        if count > 1
    ]

    if duplicates:
        raise DataContractError(
            f"{field_name} 存在重复值：{duplicates}"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class FieldMappingRule:
    """一个来源字段到标准字段的映射规则。"""

    source_fields: tuple[str, ...]
    status: MappingStatus
    transform_id: str = "identity"
    target_object: str | None = None
    canonical_field: str | None = None
    transform_params: dict[str, Any] = field(default_factory=dict)
    required: bool = False
    source_unit: str | None = None
    canonical_unit: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        source_fields = _require_unique(
            self.source_fields,
            "source_fields",
        )
        object.__setattr__(self, "source_fields", source_fields)
        object.__setattr__(
            self,
            "transform_id",
            _require_text(self.transform_id, "transform_id"),
        )

        if self.status in {
            MappingStatus.MAPPED,
            MappingStatus.WARNING,
        }:
            if self.target_object is None:
                raise DataContractError(
                    "已映射规则必须提供 target_object。"
                )
            if self.canonical_field is None:
                raise DataContractError(
                    "已映射规则必须提供 canonical_field。"
                )

        if self.target_object is not None:
            object.__setattr__(
                self,
                "target_object",
                _require_text(
                    self.target_object,
                    "target_object",
                ),
            )

        if self.canonical_field is not None:
            object.__setattr__(
                self,
                "canonical_field",
                _require_text(
                    self.canonical_field,
                    "canonical_field",
                ),
            )

    @property
    def canonical_target(self) -> str | None:
        if (
            self.target_object is None
            or self.canonical_field is None
        ):
            return None

        return (
            f"{self.target_object}.{self.canonical_field}"
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["source_fields"] = list(self.source_fields)
        return result

    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
    ) -> "FieldMappingRule":
        return cls(
            source_fields=tuple(value["source_fields"]),
            status=MappingStatus(value["status"]),
            transform_id=value.get("transform_id", "identity"),
            target_object=value.get("target_object"),
            canonical_field=value.get("canonical_field"),
            transform_params=dict(
                value.get("transform_params", {})
            ),
            required=bool(value.get("required", False)),
            source_unit=value.get("source_unit"),
            canonical_unit=value.get("canonical_unit"),
            notes=value.get("notes"),
        )


@dataclass(frozen=True, slots=True)
class DatasetRegistration:
    """一个来源数据集的注册信息和映射合同。"""

    dataset_id: str
    source_type: SourceType
    source_locator: dict[str, Any]
    dataset_mode: str
    coverage_version: str
    schema_version: str
    mapping_version: str
    dictionary_revision: str
    date_field: str | None
    entity_field: str | None
    primary_key_fields: tuple[str, ...]
    source_fields: tuple[str, ...]
    canonical_objects: tuple[str, ...]
    field_mappings: tuple[FieldMappingRule, ...]
    enabled: bool = True
    tags: tuple[str, ...] = ()
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "dataset_mode",
            _require_text(
                self.dataset_mode,
                "dataset_mode",
            ),
        )
        object.__setattr__(
            self,
            "coverage_version",
            _require_text(
                self.coverage_version,
                "coverage_version",
            ),
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_text(
                self.schema_version,
                "schema_version",
            ),
        )
        object.__setattr__(
            self,
            "mapping_version",
            _require_text(
                self.mapping_version,
                "mapping_version",
            ),
        )
        object.__setattr__(
            self,
            "dictionary_revision",
            _require_text(
                self.dictionary_revision,
                "dictionary_revision",
            ),
        )

        source_fields = _require_unique(
            self.source_fields,
            "source_fields",
        )
        primary_keys = _require_unique(
            self.primary_key_fields,
            "primary_key_fields",
        )
        canonical_objects = _require_unique(
            self.canonical_objects,
            "canonical_objects",
        )
        tags = _require_unique(self.tags, "tags")

        object.__setattr__(self, "source_fields", source_fields)
        object.__setattr__(
            self,
            "primary_key_fields",
            primary_keys,
        )
        object.__setattr__(
            self,
            "canonical_objects",
            canonical_objects,
        )
        object.__setattr__(self, "tags", tags)

        unknown_keys = sorted(
            set(primary_keys) - set(source_fields)
        )
        if unknown_keys:
            raise DataContractError(
                "主键字段未出现在 source_fields 中："
                f"{unknown_keys}"
            )

        mapping_sources = {
            source_field
            for rule in self.field_mappings
            for source_field in rule.source_fields
        }
        unknown_mapping_sources = sorted(
            mapping_sources - set(source_fields)
        )
        if unknown_mapping_sources:
            raise DataContractError(
                "映射规则引用了未知来源字段："
                f"{unknown_mapping_sources}"
            )

        undeclared_objects = sorted(
            {
                rule.target_object
                for rule in self.field_mappings
                if rule.target_object is not None
            }
            - set(canonical_objects)
        )
        if undeclared_objects:
            raise DataContractError(
                "映射规则使用了未声明的标准对象："
                f"{undeclared_objects}"
            )

    def mapping_coverage(self) -> dict[str, Any]:
        """统计全部来源字段是否被明确处理。"""

        rules_by_source: dict[
            str,
            list[FieldMappingRule],
        ] = {
            field_name: []
            for field_name in self.source_fields
        }

        for rule in self.field_mappings:
            for field_name in rule.source_fields:
                rules_by_source[field_name].append(rule)

        unaccounted_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if not rules
        )
        mapped_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if any(
                rule.status in {
                    MappingStatus.MAPPED,
                    MappingStatus.WARNING,
                }
                and rule.canonical_target is not None
                for rule in rules
            )
        )
        pending_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if rules
            and field_name not in mapped_fields
            and any(
                rule.status
                is MappingStatus.PENDING_CONFIRMATION
                for rule in rules
            )
        )
        unmapped_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if rules
            and field_name not in mapped_fields
            and field_name not in pending_fields
        )

        return {
            "source_field_count": len(self.source_fields),
            "mapped_source_field_count": len(mapped_fields),
            "pending_source_field_count": len(pending_fields),
            "unmapped_source_field_count": len(unmapped_fields),
            "unaccounted_source_field_count": len(
                unaccounted_fields
            ),
            "mapped_fields": mapped_fields,
            "pending_fields": pending_fields,
            "unmapped_fields": unmapped_fields,
            "unaccounted_fields": unaccounted_fields,
            "all_source_fields_accounted":
                not unaccounted_fields,
            "canonical_target_count": len(
                {
                    rule.canonical_target
                    for rule in self.field_mappings
                    if rule.canonical_target is not None
                }
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_type": self.source_type.value,
            "source_locator": dict(self.source_locator),
            "dataset_mode": self.dataset_mode,
            "coverage_version": self.coverage_version,
            "schema_version": self.schema_version,
            "mapping_version": self.mapping_version,
            "dictionary_revision": self.dictionary_revision,
            "date_field": self.date_field,
            "entity_field": self.entity_field,
            "primary_key_fields": list(
                self.primary_key_fields
            ),
            "source_fields": list(self.source_fields),
            "canonical_objects": list(
                self.canonical_objects
            ),
            "field_mappings": [
                rule.to_dict()
                for rule in self.field_mappings
            ],
            "enabled": self.enabled,
            "tags": list(self.tags),
            "description": self.description,
        }

    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
    ) -> "DatasetRegistration":
        return cls(
            dataset_id=value["dataset_id"],
            source_type=SourceType(value["source_type"]),
            source_locator=dict(value["source_locator"]),
            dataset_mode=value["dataset_mode"],
            coverage_version=value["coverage_version"],
            schema_version=value["schema_version"],
            mapping_version=value["mapping_version"],
            dictionary_revision=value["dictionary_revision"],
            date_field=value.get("date_field"),
            entity_field=value.get("entity_field"),
            primary_key_fields=tuple(
                value.get("primary_key_fields", [])
            ),
            source_fields=tuple(value["source_fields"]),
            canonical_objects=tuple(
                value.get("canonical_objects", [])
            ),
            field_mappings=tuple(
                FieldMappingRule.from_dict(item)
                for item in value.get(
                    "field_mappings",
                    [],
                )
            ),
            enabled=bool(value.get("enabled", True)),
            tags=tuple(value.get("tags", [])),
            description=value.get("description"),
        )


class CanonicalFieldCatalog:
    """用于校验标准对象和 canonical 字段名称。"""

    def __init__(
        self,
        fields_by_object: Mapping[
            str,
            Iterable[str],
        ],
    ) -> None:
        self._fields = {
            _require_text(object_name, "canonical_object"):
                frozenset(
                    _require_text(field_name, "canonical_field")
                    for field_name in field_names
                )
            for object_name, field_names
            in fields_by_object.items()
        }

    def contains(
        self,
        object_name: str,
        field_name: str,
    ) -> bool:
        return field_name in self._fields.get(
            object_name,
            frozenset(),
        )

    def validate_registration(
        self,
        registration: DatasetRegistration,
    ) -> list[str]:
        errors: list[str] = []

        for rule in registration.field_mappings:
            if rule.canonical_target is None:
                continue

            assert rule.target_object is not None
            assert rule.canonical_field is not None

            if not self.contains(
                rule.target_object,
                rule.canonical_field,
            ):
                errors.append(
                    "标准字段不存在："
                    f"{rule.canonical_target}"
                )

        return errors

    def assert_valid(
        self,
        registration: DatasetRegistration,
    ) -> None:
        errors = self.validate_registration(registration)

        if errors:
            raise DataContractError(
                "标准字段目录校验失败："
                + "; ".join(errors)
            )


class DatasetRegistry:
    """可持续扩展的数据集注册中心。"""

    def __init__(self) -> None:
        self._registrations: dict[
            str,
            DatasetRegistration,
        ] = {}

    def register(
        self,
        registration: DatasetRegistration,
        *,
        replace: bool = False,
    ) -> None:
        if (
            registration.dataset_id
            in self._registrations
            and not replace
        ):
            raise DataContractError(
                "数据集已注册："
                f"{registration.dataset_id}"
            )

        self._registrations[
            registration.dataset_id
        ] = registration

    def get(
        self,
        dataset_id: str,
    ) -> DatasetRegistration:
        key = _require_text(dataset_id, "dataset_id")

        try:
            return self._registrations[key]
        except KeyError as exc:
            raise DataContractError(
                f"数据集未注册：{key}"
            ) from exc

    def list(
        self,
        *,
        enabled_only: bool = False,
        source_type: SourceType | None = None,
        canonical_object: str | None = None,
    ) -> list[DatasetRegistration]:
        result = list(self._registrations.values())

        if enabled_only:
            result = [
                item
                for item in result
                if item.enabled
            ]

        if source_type is not None:
            result = [
                item
                for item in result
                if item.source_type is source_type
            ]

        if canonical_object is not None:
            result = [
                item
                for item in result
                if canonical_object
                in item.canonical_objects
            ]

        return sorted(
            result,
            key=lambda item: item.dataset_id,
        )

    def load_json(
        self,
        path: str | Path,
        *,
        replace: bool = False,
    ) -> DatasetRegistration:
        file_path = Path(path)
        value = json.loads(
            file_path.read_text(encoding="utf-8")
        )
        registration = DatasetRegistration.from_dict(value)
        self.register(registration, replace=replace)
        return registration

    def load_directory(
        self,
        directory: str | Path,
        *,
        replace: bool = False,
    ) -> list[DatasetRegistration]:
        root = Path(directory)

        if not root.exists():
            raise DataContractError(
                f"注册目录不存在：{root}"
            )

        loaded = [
            self.load_json(path, replace=replace)
            for path in sorted(root.glob("*.json"))
        ]
        return loaded

    def to_dict(self) -> dict[str, Any]:
        return {
            "datasets": [
                item.to_dict()
                for item in self.list()
            ]
        }


class TransformRegistry:
    """标准化转换函数注册中心。"""

    def __init__(self) -> None:
        self._transforms: dict[
            str,
            TransformFunction,
        ] = {}
        self.register("identity", self._identity)
        self.register("multiply", self._multiply)
        self.register("divide", self._divide)
        self.register("negate", self._negate)
        self.register(
            "price_change_from_prev_close",
            self._price_change_from_prev_close,
        )
        self.register(
            "pct_change_from_prev_close",
            self._pct_change_from_prev_close,
        )

    def register(
        self,
        transform_id: str,
        function: TransformFunction,
        *,
        replace: bool = False,
    ) -> None:
        key = _require_text(
            transform_id,
            "transform_id",
        )

        if key in self._transforms and not replace:
            raise DataContractError(
                f"转换函数已注册：{key}"
            )

        if not callable(function):
            raise DataContractError(
                f"转换函数不可调用：{key}"
            )

        self._transforms[key] = function

    def apply(
        self,
        transform_id: str,
        values: list[Any],
        *,
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        try:
            function = self._transforms[transform_id]
        except KeyError as exc:
            raise DataContractError(
                f"转换函数未注册：{transform_id}"
            ) from exc

        return function(values, params, record, context)

    @staticmethod
    def _require_one(values: list[Any]) -> Any:
        if len(values) != 1:
            raise DataContractError(
                "该转换要求恰好一个来源值。"
            )

        return values[0]

    @classmethod
    def _identity(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        return cls._require_one(values)

    @classmethod
    def _multiply(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        value = cls._require_one(values)

        if value is None:
            return None

        factor = params.get("factor")
        if not isinstance(factor, (int, float)):
            raise DataContractError(
                "multiply 转换缺少数值 factor。"
            )

        return value * factor

    @classmethod
    def _divide(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        value = cls._require_one(values)

        if value is None:
            return None

        divisor = params.get("divisor")
        if (
            not isinstance(divisor, (int, float))
            or divisor == 0
        ):
            raise DataContractError(
                "divide 转换需要非零 divisor。"
            )

        return value / divisor

    @classmethod
    def _negate(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        value = cls._require_one(values)
        return None if value is None else -value

    @staticmethod
    def _price_change_from_prev_close(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        if len(values) != 1:
            raise DataContractError(
                "价格变动转换要求一个 close 来源值。"
            )

        close = values[0]
        prev_close = context.get("prev_close")

        if close is None or prev_close is None:
            return None

        return close - prev_close

    @staticmethod
    def _pct_change_from_prev_close(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        if len(values) != 1:
            raise DataContractError(
                "涨跌幅转换要求一个 close 来源值。"
            )

        close = values[0]
        prev_close = context.get("prev_close")

        if (
            close is None
            or prev_close is None
            or prev_close == 0
        ):
            return None

        precision = int(params.get("precision", 6))
        return round(
            (close / prev_close - 1) * 100,
            precision,
        )


@dataclass(slots=True)
class MappingExecutionResult:
    dataset_id: str
    outputs: dict[str, dict[str, Any]]
    source_extensions: dict[str, Any]
    warnings: list[str]
    lineage: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CanonicalMappingEngine:
    """把一个来源记录映射为一个或多个标准对象片段。"""

    def __init__(
        self,
        transforms: TransformRegistry | None = None,
    ) -> None:
        self.transforms = transforms or TransformRegistry()

    def map_record(
        self,
        registration: DatasetRegistration,
        record: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> MappingExecutionResult:
        context_values = context or {}
        outputs: dict[str, dict[str, Any]] = {}
        warnings: list[str] = []
        lineage: list[dict[str, Any]] = []
        mapped_source_fields: set[str] = set()

        for rule in registration.field_mappings:
            if rule.status not in {
                MappingStatus.MAPPED,
                MappingStatus.WARNING,
            }:
                continue

            missing = [
                field_name
                for field_name in rule.source_fields
                if field_name not in record
            ]

            if missing:
                message = (
                    f"映射 {rule.canonical_target} "
                    f"缺少来源字段：{missing}"
                )

                if rule.required:
                    raise DataContractError(message)

                warnings.append(message)
                continue

            values = [
                record[field_name]
                for field_name in rule.source_fields
            ]
            value = self.transforms.apply(
                rule.transform_id,
                values,
                params=rule.transform_params,
                record=record,
                context=context_values,
            )

            assert rule.target_object is not None
            assert rule.canonical_field is not None

            target = outputs.setdefault(
                rule.target_object,
                {},
            )

            if rule.canonical_field in target:
                raise DataContractError(
                    "同一记录重复写入标准字段："
                    f"{rule.canonical_target}"
                )

            target[rule.canonical_field] = value
            mapped_source_fields.update(rule.source_fields)
            lineage.append(
                {
                    "target_object": rule.target_object,
                    "canonical_field":
                        rule.canonical_field,
                    "source_fields":
                        list(rule.source_fields),
                    "transform_id":
                        rule.transform_id,
                    "transform_params":
                        dict(rule.transform_params),
                    "mapping_version":
                        registration.mapping_version,
                    "dictionary_revision":
                        registration.dictionary_revision,
                }
            )

            if rule.status is MappingStatus.WARNING:
                warnings.append(
                    "映射规则带警告："
                    f"{rule.canonical_target}"
                )

        source_extensions = {
            field_name: value
            for field_name, value in record.items()
            if field_name not in mapped_source_fields
        }

        return MappingExecutionResult(
            dataset_id=registration.dataset_id,
            outputs=outputs,
            source_extensions=source_extensions,
            warnings=warnings,
            lineage=lineage,
        )
