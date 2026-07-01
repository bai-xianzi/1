# 测试模块总览：验证 `test_source_governance` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
import unittest
from datetime import date

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.source_governance import (
    CredentialReference,
    DatasetSourceBinding,
    SourceCapability,
    SourceCatalog,
    SourceDescriptor,
    SourceOperationalStatus,
    SourceProtocol,
    SourceRole,
)


# 测试类 `TestSourceGovernance`：集中验证 `test_source_governance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestSourceGovernance(unittest.TestCase):
    # 测试函数 `_source`：封装 `_source` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：source_id、enabled、capabilities。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _source(
        self,
        source_id: str,
        *,
        enabled: bool,
        capabilities: tuple[
            SourceCapability, ...
        ],
    ) -> SourceDescriptor:
        return SourceDescriptor(
            source_id=source_id,
            vendor_name=source_id,
            protocol=SourceProtocol.HTTP,
            capabilities=capabilities,
            enabled=enabled,
            operational_status=(
                SourceOperationalStatus.AVAILABLE
                if enabled
                else SourceOperationalStatus.DISABLED
            ),
        )

    # 测试函数 `test_disabled_source_must_have_disabled_status`：验证 `disabled、source、must、have、disabled、status` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_disabled_source_must_have_disabled_status(
        self,
    ) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            SourceDescriptor(
                source_id="wind",
                vendor_name="Wind",
                protocol=SourceProtocol.SDK,
                capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
                enabled=False,
                operational_status=(
                    SourceOperationalStatus.CONFIGURED
                ),
            )

    # 测试函数 `test_credentials_are_references_only`：验证 `credentials、are、references、only` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_credentials_are_references_only(
        self,
    ) -> None:
        item = CredentialReference(
            reference_id="ifind_refresh_token",
            environment_variable="IFIND_REFRESH_TOKEN",
        )
        self.assertEqual(
            item.environment_variable,
            "IFIND_REFRESH_TOKEN",
        )

    # 测试函数 `test_binding_requires_registered_source`：验证 `binding、requires、registered、source` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_binding_requires_registered_source(
        self,
    ) -> None:
        catalog = SourceCatalog()
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id="unknown",
                    role=SourceRole.PRIMARY,
                    priority=1,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                )
            )

    # 测试函数 `test_binding_requires_capability`：验证 `binding、requires、capability` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_binding_requires_capability(
        self,
    ) -> None:
        catalog = SourceCatalog()
        catalog.register_source(
            self._source(
                "ifind",
                enabled=True,
                capabilities=(
                    SourceCapability.REALTIME_QUOTES,
                ),
            )
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id="ifind",
                    role=SourceRole.PRIMARY,
                    priority=1,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                    required_capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                    enabled=True,
                )
            )

    # 测试函数 `test_route_order_is_stable`：验证 `route、order、is、stable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_route_order_is_stable(
        self,
    ) -> None:
        catalog = SourceCatalog()
        # 参数化循环：逐项使用 `('primary', 'fallback', 'reconcile')` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for source_id in (
            "primary",
            "fallback",
            "reconcile",
        ):
            catalog.register_source(
                self._source(
                    source_id,
                    enabled=True,
                    capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                )
            )

        # 参数化循环：逐项使用 `(('fallback', SourceRole.FALLBACK, 1), ('primary', SourceRole.PRIMARY, 1), ('reconcile', SourceRole.RECO…` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for source_id, role, priority in (
            ("fallback", SourceRole.FALLBACK, 1),
            ("primary", SourceRole.PRIMARY, 1),
            (
                "reconcile",
                SourceRole.RECONCILIATION,
                1,
            ),
        ):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id=source_id,
                    role=role,
                    priority=priority,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                    required_capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                    enabled=True,
                )
            )

        routes = catalog.routes_for(
            "a_stock_daily_bar",
            required_capabilities=(
                SourceCapability.HISTORICAL_QUOTES,
            ),
        )
        self.assertEqual(
            [route.source.source_id for route in routes],
            ["primary", "fallback", "reconcile"],
        )

    # 测试函数 `test_effective_date_filters_binding`：验证 `effective、date、filters、binding` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_effective_date_filters_binding(
        self,
    ) -> None:
        catalog = SourceCatalog()
        catalog.register_source(
            self._source(
                "primary",
                enabled=True,
                capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
            )
        )
        catalog.register_binding(
            DatasetSourceBinding(
                dataset_id="dataset",
                source_id="primary",
                role=SourceRole.PRIMARY,
                priority=1,
                source_locator={},
                mapping_version="1.0",
                source_schema_version="1.0",
                required_capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
                enabled=True,
                effective_from=date(2026, 1, 1),
            )
        )
        self.assertEqual(
            catalog.routes_for(
                "dataset",
                target_date=date(2025, 12, 31),
            ),
            (),
        )
        self.assertEqual(
            len(
                catalog.routes_for(
                    "dataset",
                    target_date=date(2026, 1, 1),
                )
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
