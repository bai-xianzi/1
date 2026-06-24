"""厂商查询清单合同。

具体厂商指标、报表ID、参数和返回路径必须放在版本化清单中，
不得散落在业务代码。Wind代码生成器或iFinD超级命令生成的
调用参数，应先转成VendorQueryManifest，再由未来适配器执行。

本模块不执行HTTP或SDK请求。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from .data_contracts import DataContractError


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name} 不能为空。")
    return value.strip()


class VendorOperation(str, Enum):
    TIME_SERIES = "TIME_SERIES"
    CROSS_SECTION = "CROSS_SECTION"
    HISTORICAL_QUOTES = "HISTORICAL_QUOTES"
    REALTIME_QUOTES = "REALTIME_QUOTES"
    HIGH_FREQUENCY = "HIGH_FREQUENCY"
    SNAPSHOT = "SNAPSHOT"
    BASIC_DATA = "BASIC_DATA"
    DATE_SEQUENCE = "DATE_SEQUENCE"
    DATA_POOL = "DATA_POOL"
    ECONOMIC_DATABASE = "ECONOMIC_DATABASE"
    REPORT_QUERY = "REPORT_QUERY"
    TRADING_CALENDAR = "TRADING_CALENDAR"
    PORTFOLIO_ANALYTICS = "PORTFOLIO_ANALYTICS"
    SMART_QUERY = "SMART_QUERY"


_SECRET_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "access_token",
    "refresh_token",
    "api_key",
    "credential",
)


def _find_secret_paths(
    value: Any,
    path: str = "$",
) -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if any(
                fragment in key_text
                for fragment in _SECRET_FRAGMENTS
            ):
                findings.append(child_path)
            findings.extend(
                _find_secret_paths(item, child_path)
            )
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(
                _find_secret_paths(
                    item,
                    f"{path}[{index}]",
                )
            )
    return findings


@dataclass(frozen=True, slots=True)
class ChunkPolicy:
    max_codes_per_request: int | None = None
    max_days_per_request: int | None = None
    max_rows_hint: int | None = None
    split_strategy: str = "NONE"

    def __post_init__(self) -> None:
        for field_name in (
            "max_codes_per_request",
            "max_days_per_request",
            "max_rows_hint",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, int) or value <= 0
            ):
                raise DataContractError(
                    f"{field_name}必须是正整数或None。"
                )


@dataclass(frozen=True, slots=True)
class VendorQueryManifest:
    manifest_id: str
    source_id: str
    dataset_id: str
    canonical_object: str
    operation: VendorOperation
    request_template: dict[str, Any]
    field_mapping: dict[str, str]
    response_data_path: str
    mapping_version: str
    source_schema_version: str
    generated_by: str
    enabled: bool = False
    chunk_policy: ChunkPolicy = field(
        default_factory=ChunkPolicy
    )
    timeout_seconds: int = 60
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "manifest_id",
            "source_id",
            "dataset_id",
            "canonical_object",
            "response_data_path",
            "mapping_version",
            "source_schema_version",
            "generated_by",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        operation = self.operation
        if isinstance(operation, str):
            try:
                operation = VendorOperation(operation)
            except ValueError as exc:
                raise DataContractError(
                    "operation不是受支持的厂商操作。"
                ) from exc
        object.__setattr__(
            self,
            "operation",
            operation,
        )

        if (
            not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds <= 0
        ):
            raise DataContractError(
                "timeout_seconds必须是正整数。"
            )

        secret_paths = _find_secret_paths(
            self.request_template
        )
        if secret_paths:
            raise DataContractError(
                "request_template不得包含凭据字段："
                + ", ".join(secret_paths)
            )

        if not self.field_mapping:
            raise DataContractError(
                "field_mapping不能为空。"
            )

        if len(set(self.field_mapping)) != len(
            self.field_mapping
        ):
            raise DataContractError(
                "field_mapping来源字段不允许重复。"
            )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operation"] = self.operation.value
        return payload

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "VendorQueryManifest":
        return cls(
            manifest_id=payload["manifest_id"],
            source_id=payload["source_id"],
            dataset_id=payload["dataset_id"],
            canonical_object=payload[
                "canonical_object"
            ],
            operation=VendorOperation(
                payload["operation"]
            ),
            request_template=dict(
                payload.get("request_template", {})
            ),
            field_mapping=dict(
                payload.get("field_mapping", {})
            ),
            response_data_path=payload[
                "response_data_path"
            ],
            mapping_version=payload[
                "mapping_version"
            ],
            source_schema_version=payload[
                "source_schema_version"
            ],
            generated_by=payload["generated_by"],
            enabled=bool(
                payload.get("enabled", False)
            ),
            chunk_policy=ChunkPolicy(
                **payload.get("chunk_policy", {})
            ),
            timeout_seconds=int(
                payload.get("timeout_seconds", 60)
            ),
            notes=tuple(payload.get("notes", [])),
        )


class VendorManifestRegistry:
    def __init__(self) -> None:
        self._items: dict[
            str, VendorQueryManifest
        ] = {}

    def register(
        self,
        manifest: VendorQueryManifest,
    ) -> None:
        if manifest.manifest_id in self._items:
            raise DataContractError(
                f"manifest已注册：{manifest.manifest_id}"
            )
        self._items[manifest.manifest_id] = manifest

    def get(
        self,
        manifest_id: str,
    ) -> VendorQueryManifest:
        try:
            return self._items[manifest_id]
        except KeyError as exc:
            raise DataContractError(
                f"未知manifest：{manifest_id}"
            ) from exc

    def list_for_dataset(
        self,
        dataset_id: str,
        *,
        include_disabled: bool = False,
    ) -> tuple[VendorQueryManifest, ...]:
        items = [
            item
            for item in self._items.values()
            if item.dataset_id == dataset_id
            and (
                include_disabled or item.enabled
            )
        ]
        items.sort(
            key=lambda item: (
                item.source_id,
                item.operation.value,
                item.manifest_id,
            )
        )
        return tuple(items)
