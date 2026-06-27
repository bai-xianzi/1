"""统一数据就绪度门禁后的标准数据服务。

本模块把 StandardDataService 与 StandardQueryReadinessService 组合成
下游唯一允许调用的数据入口。它不会绕过 Provider，也不会修改原始数据。

调用链：

    StandardDataService.query
        -> StandardQueryResult
        -> 八维 ReadinessEvidence
        -> DatasetReadinessDecision
        -> ReadinessGatedQueryResult

只有标准查询本身和统一就绪度决策都未阻断时，assert_usable 才会通过。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .data_contracts import DataContractError
from .data_readiness_evidence import (
    DatasetReadinessSnapshot,
    EvidenceBuildContext,
    StandardQueryReadinessService,
)
from .standard_data_service import (
    StandardDataQuery,
    StandardDataService,
    StandardQueryResult,
)

READINESS_GATED_SERVICE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class ReadinessGatedQueryResult:
    """标准查询结果与统一数据就绪度快照的不可分割组合。"""

    standard_result: StandardQueryResult
    readiness_snapshot: DatasetReadinessSnapshot
    service_version: str = READINESS_GATED_SERVICE_VERSION

    def __post_init__(self) -> None:
        result = self.standard_result
        snapshot = self.readiness_snapshot

        if result.query.dataset_id != snapshot.dataset_id:
            raise DataContractError(
                "标准查询结果与就绪度快照dataset_id不一致。"
            )
        if result.query.canonical_object != snapshot.canonical_object:
            raise DataContractError(
                "标准查询结果与就绪度快照canonical_object不一致。"
            )
        if result.metadata.provider_id != snapshot.provider_id:
            raise DataContractError(
                "标准查询结果与就绪度快照provider_id不一致。"
            )
        if result.metadata.query_id != snapshot.query_id:
            raise DataContractError(
                "标准查询结果与就绪度快照query_id不一致。"
            )
        if result.query.usage is not snapshot.usage:
            raise DataContractError(
                "标准查询结果与就绪度快照usage不一致。"
            )
        if not isinstance(self.service_version, str) or not self.service_version:
            raise DataContractError("service_version不能为空。")

    @property
    def blocks_downstream(self) -> bool:
        return bool(
            self.standard_result.metadata.blocks_downstream
            or self.readiness_snapshot.decision.blocks_downstream
        )

    def assert_usable(self) -> None:
        """同时执行Provider门禁与统一八维就绪度门禁。"""

        self.standard_result.assert_usable()
        self.readiness_snapshot.assert_usable()

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_version": self.service_version,
            "blocks_downstream": self.blocks_downstream,
            "standard_result": self.standard_result.to_dict(),
            "readiness_snapshot": self.readiness_snapshot.to_dict(),
        }


class ReadinessGatedStandardDataService:
    """面向市场状态、因子、风控和交易模块的唯一标准数据入口。"""

    def __init__(
        self,
        standard_service: StandardDataService,
        readiness_service: StandardQueryReadinessService,
    ) -> None:
        if not isinstance(standard_service, StandardDataService):
            raise DataContractError(
                "standard_service必须是StandardDataService。"
            )
        if not isinstance(
            readiness_service,
            StandardQueryReadinessService,
        ):
            raise DataContractError(
                "readiness_service必须是StandardQueryReadinessService。"
            )
        self.standard_service = standard_service
        self.readiness_service = readiness_service

    def query(
        self,
        request: StandardDataQuery,
        context: EvidenceBuildContext | None = None,
    ) -> ReadinessGatedQueryResult:
        provider = self.standard_service.get_provider(request.dataset_id)
        descriptor = provider.descriptor
        standard_result = self.standard_service.query(request)
        readiness_snapshot = self.readiness_service.assess(
            standard_result,
            descriptor,
            context,
        )
        return ReadinessGatedQueryResult(
            standard_result=standard_result,
            readiness_snapshot=readiness_snapshot,
        )
