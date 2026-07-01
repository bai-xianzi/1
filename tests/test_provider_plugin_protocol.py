# 测试模块总览：验证 `test_provider_plugin_protocol` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.provider_capabilities import (
    CapabilityImplementationStatus,
    ProviderCapabilityMatrix,
    ProviderDiscoveryStatus,
    ProviderLifecycle,
    ProviderTarget,
    load_provider_capability_matrix,
)
from a_stock_quant.provider_plugin_protocol import (
    AuthenticationReference,
    AuthenticationReferenceKind,
    BatchPolicy,
    DiscoveryOutcome,
    LicenseBoundary,
    LicenseDecision,
    PaginationMode,
    PaginationPolicy,
    PluginRegistrationStatus,
    PolicyEvidenceStatus,
    ProviderDiscoveryResult,
    ProviderHealthSnapshot,
    ProviderHealthStatus,
    ProviderPluginRegistry,
    ProviderRegistryEntry,
    ProviderRouteRequest,
    RateLimitPolicy,
    RetryPolicy,
    RouteDecision,
    SdkRuntimeDescriptor,
    SubscriptionMode,
    SubscriptionPolicy,
    build_provider_route_candidates,
    load_provider_plugin_protocol_config,
    load_provider_plugin_registry,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    ROOT
    / "configs"
    / "providers"
    / "provider_capability_matrix_v0.json"
)
PROTOCOL_PATH = (
    ROOT
    / "configs"
    / "providers"
    / "provider_plugin_protocol_v0.json"
)
REGISTRY_PATH = (
    ROOT
    / "configs"
    / "providers"
    / "provider_plugin_registry_v0.json"
)


# 测试函数 `complete_discovery`：封装 `complete_discovery` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：provider_id、plugin_id、health、capability、usage、subscription_mode。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def complete_discovery(
    provider_id="test_provider",
    plugin_id="test.plugin",
    *,
    health=ProviderHealthStatus.HEALTHY,
    capability="EOD_MARKET_DATA",
    usage="CURRENT_SNAPSHOT_RESEARCH",
    subscription_mode=SubscriptionMode.NONE,
):
    return ProviderDiscoveryResult(
        discovery_id=f"discovery:{provider_id}:1",
        provider_id=provider_id,
        plugin_id=plugin_id,
        outcome=DiscoveryOutcome.COMPLETE,
        discovered_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
        runtime=SdkRuntimeDescriptor(
            provider_id=provider_id,
            runtime_id=f"runtime:{provider_id}",
            operating_systems=("Windows",),
            python_versions=("3.11",),
            architecture="x86_64",
            client_name="Test Client",
            client_version="1.0",
            sdk_name="test_sdk",
            sdk_version="1.0",
            installed=True,
            installation_probe="importlib.util.find_spec",
            notes="test",
        ),
        authentication_reference=AuthenticationReference(
            reference_id=f"auth:{provider_id}",
            kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
            locator="env://TEST_PROVIDER_TOKEN",
            scopes=("read",),
        ),
        capabilities={
            capability: CapabilityImplementationStatus.VERIFIED,
        },
        rate_limit_policy=RateLimitPolicy(
            requests_per_period=60,
            period_seconds=60,
            burst_size=5,
            maximum_concurrency=2,
            evidence_status=PolicyEvidenceStatus.CONTRACT,
            evidence_refs=("test:rate-limit",),
        ),
        retry_policy=RetryPolicy(
            maximum_attempts=3,
            backoff_seconds=(2, 5),
            retryable_error_codes=("TIMEOUT",),
        ),
        batch_policy=BatchPolicy(
            recommended_entities_per_request=100,
            maximum_entities_per_request=500,
            recommended_rows_per_batch=20000,
            maximum_rows_per_batch=100000,
            supports_date_range=True,
            supports_parallel_requests=True,
        ),
        pagination_policy=PaginationPolicy(
            mode=PaginationMode.CURSOR,
            default_page_size=1000,
            maximum_page_size=5000,
            maximum_pages=100,
            cursor_field="next_cursor",
        ),
        subscription_policy=SubscriptionPolicy(
            mode=subscription_mode,
            maximum_symbols=(
                100 if subscription_mode is not SubscriptionMode.NONE
                else None
            ),
            heartbeat_seconds=(
                30 if subscription_mode is not SubscriptionMode.NONE
                else None
            ),
            reconnect_supported=(
                subscription_mode is not SubscriptionMode.NONE
            ),
            replay_supported=False,
        ),
        license_boundary=LicenseBoundary(
            decision=LicenseDecision.ALLOWED,
            permitted_usages=(usage,),
            cache_allowed=True,
            persistent_storage_allowed=True,
            redistribution_allowed=False,
            maximum_retention_days=365,
            evidence_refs=("test:license",),
        ),
        health=ProviderHealthSnapshot(
            status=health,
            checked_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
            latency_ms=10.0,
            message="ok",
            evidence_refs=("test:health",),
        ),
        warnings=(),
        errors=(),
    )


# 测试函数 `route_ready_matrix`：封装 `route_ready_matrix` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：provider_id、execution。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def route_ready_matrix(provider_id="test_provider", execution=False):
    return ProviderCapabilityMatrix(
        task_id="TASK_020A",
        matrix_version="0.1.0",
        matrix_status="test",
        provider_neutral=True,
        automatic_activation_allowed=False,
        secret_storage_allowed=False,
        core_system_may_import_vendor_sdk=False,
        upper_layers_may_depend_on_vendor_fields=False,
        required_adapter_contracts=("health_check",),
        capability_catalog=(
            "EOD_MARKET_DATA",
            "REALTIME_SUBSCRIPTION",
            "ORDER_SUBMIT",
        ),
        provider_targets=(
            ProviderTarget(
                provider_id=provider_id,
                display_name="Test",
                provider_kind="TEST",
                lifecycle=ProviderLifecycle.REAL_ACCEPTED,
                integration_mode="SDK",
                authentication_mode="REFERENCE",
                discovery_status=(
                    ProviderDiscoveryStatus.DISCOVERY_COMPLETE
                ),
                capabilities={
                    "EOD_MARKET_DATA": (
                        CapabilityImplementationStatus.VERIFIED
                    )
                },
                license_review_required=True,
                execution_capability=execution,
                notes="test",
            ),
            ProviderTarget(
                provider_id="local_dolphindb",
                display_name="DDB",
                provider_kind="TEST",
                lifecycle=ProviderLifecycle.IMPLEMENTED_FOUNDATION,
                integration_mode="NATIVE",
                authentication_mode="REFERENCE",
                discovery_status=(
                    ProviderDiscoveryStatus.VERIFIED_IN_PROJECT
                ),
                capabilities={},
                license_review_required=False,
                execution_capability=False,
                notes="required target",
            ),
            ProviderTarget(
                provider_id="wind",
                display_name="Wind",
                provider_kind="TEST",
                lifecycle=ProviderLifecycle.REGISTERED_TARGET,
                integration_mode="SDK",
                authentication_mode="REFERENCE",
                discovery_status=(
                    ProviderDiscoveryStatus.DISCOVERY_REQUIRED
                ),
                capabilities={},
                license_review_required=True,
                execution_capability=False,
                notes="required target",
            ),
            ProviderTarget(
                provider_id="ifind",
                display_name="iFinD",
                provider_kind="TEST",
                lifecycle=ProviderLifecycle.REGISTERED_TARGET,
                integration_mode="SDK",
                authentication_mode="REFERENCE",
                discovery_status=(
                    ProviderDiscoveryStatus.DISCOVERY_REQUIRED
                ),
                capabilities={},
                license_review_required=True,
                execution_capability=False,
                notes="required target",
            ),
            ProviderTarget(
                provider_id="galaxy_xingyao",
                display_name="Galaxy",
                provider_kind="TEST",
                lifecycle=ProviderLifecycle.REGISTERED_TARGET,
                integration_mode="SDK",
                authentication_mode="REFERENCE",
                discovery_status=(
                    ProviderDiscoveryStatus.DISCOVERY_REQUIRED
                ),
                capabilities={},
                license_review_required=True,
                execution_capability=False,
                notes="required target",
            ),
        ),
        routing_rules=("test",),
    )


# 测试函数 `route_ready_registry`：封装 `route_ready_registry` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：provider_id、plugin_id。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def route_ready_registry(provider_id="test_provider", plugin_id="test.plugin"):
    return ProviderPluginRegistry(
        task_id="TASK_020B",
        registry_version="0.1.0",
        registry_status="test",
        automatic_activation_allowed=False,
        entries=(
            ProviderRegistryEntry(
                provider_id=provider_id,
                plugin_id=plugin_id,
                registration_status=(
                    PluginRegistrationStatus.AVAILABLE
                ),
                entrypoint="test.module:Plugin",
                priority=10,
                enabled_for_routing=True,
                discovery_result_ref=f"discovery:{provider_id}:1",
                authentication_reference_ref=(
                    "env://TEST_PROVIDER_TOKEN"
                ),
                notes="test",
            ),
        ),
        hard_rules=("test",),
    )


# 测试类 `TestProviderPluginProtocol`：集中验证 `test_provider_plugin_protocol` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestProviderPluginProtocol(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self):
        self.matrix = load_provider_capability_matrix(MATRIX_PATH)
        self.protocol = load_provider_plugin_protocol_config(
            PROTOCOL_PATH
        )
        self.registry = load_provider_plugin_registry(REGISTRY_PATH)

    # 测试函数 `test_protocol_is_provider_neutral`：验证 `protocol、is、provider、neutral` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_protocol_is_provider_neutral(self):
        self.assertTrue(self.protocol.provider_neutral)

    # 测试函数 `test_protocol_forbids_secrets_and_activation`：验证 `protocol、forbids、secrets、and、activation` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_protocol_forbids_secrets_and_activation(self):
        self.assertFalse(self.protocol.secret_material_allowed)
        self.assertFalse(
            self.protocol.automatic_plugin_activation_allowed
        )

    # 测试函数 `test_validation_forbids_network_and_database`：验证 `validation、forbids、network、and、database` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_validation_forbids_network_and_database(self):
        self.assertFalse(
            self.protocol.network_probe_during_validation_allowed
        )
        self.assertFalse(
            self.protocol.database_probe_during_validation_allowed
        )

    # 测试函数 `test_protocol_has_nine_required_methods`：验证 `protocol、has、nine、required、methods` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_protocol_has_nine_required_methods(self):
        self.assertEqual(len(self.protocol.required_plugin_methods), 9)

    # 测试函数 `test_seed_registry_covers_matrix`：验证 `seed、registry、covers、matrix` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_seed_registry_covers_matrix(self):
        self.assertEqual(
            {entry.provider_id for entry in self.registry.entries},
            {
                target.provider_id
                for target in self.matrix.provider_targets
            },
        )

    # 测试函数 `test_seed_registry_has_no_enabled_routes`：验证 `seed、registry、has、no、enabled、routes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_seed_registry_has_no_enabled_routes(self):
        self.assertTrue(
            all(
                not entry.enabled_for_routing
                for entry in self.registry.entries
            )
        )

    # 测试函数 `test_commercial_targets_are_pending`：验证 `commercial、targets、are、pending` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_commercial_targets_are_pending(self):
        # 参数化循环：逐项使用 `('wind', 'ifind', 'galaxy_xingyao', 'qmt', 'ptrade')` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for provider_id in (
            "wind",
            "ifind",
            "galaxy_xingyao",
            "qmt",
            "ptrade",
        ):
            entry = self.registry.entry(provider_id)
            self.assertIsNone(entry.entrypoint)
            self.assertIs(
                entry.registration_status,
                PluginRegistrationStatus.REGISTERED_TARGET,
            )

    # 测试函数 `test_auth_reference_accepts_environment_reference`：验证 `auth、reference、accepts、environment、reference` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_auth_reference_accepts_environment_reference(self):
        ref = AuthenticationReference(
            reference_id="auth:test",
            kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
            locator="env://TEST_TOKEN",
        )
        self.assertEqual(ref.locator, "env://TEST_TOKEN")

    # 测试函数 `test_auth_reference_rejects_raw_value`：验证 `auth、reference、rejects、raw、value` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_auth_reference_rejects_raw_value(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            AuthenticationReference(
                reference_id="auth:test",
                kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
                locator="abcdef0123456789abcdef0123456789",
            )

    # 测试函数 `test_auth_reference_rejects_prefix_mismatch`：验证 `auth、reference、rejects、prefix、mismatch` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_auth_reference_rejects_prefix_mismatch(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            AuthenticationReference(
                reference_id="auth:test",
                kind=AuthenticationReferenceKind.OS_KEYRING,
                locator="env://TEST_TOKEN",
            )

    # 测试函数 `test_complete_discovery_requires_installed_runtime`：验证 `complete、discovery、requires、installed、runtime` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_complete_discovery_requires_installed_runtime(self):
        result = complete_discovery()
        raw = {
            **result.__dict__
        } if hasattr(result, "__dict__") else None
        self.assertTrue(result.runtime.installed)

    # 测试函数 `test_complete_discovery_has_capability`：验证 `complete、discovery、has、capability` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_complete_discovery_has_capability(self):
        result = complete_discovery()
        self.assertEqual(
            result.capabilities["EOD_MARKET_DATA"],
            CapabilityImplementationStatus.VERIFIED,
        )

    # 测试函数 `test_failed_discovery_requires_error`：验证 `failed、discovery、requires、error` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_failed_discovery_requires_error(self):
        result = complete_discovery()
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ProviderDiscoveryResult(
                discovery_id="failed",
                provider_id=result.provider_id,
                plugin_id=result.plugin_id,
                outcome=DiscoveryOutcome.FAILED,
                discovered_at=result.discovered_at,
                runtime=result.runtime,
                authentication_reference=(
                    result.authentication_reference
                ),
                capabilities={},
                rate_limit_policy=result.rate_limit_policy,
                retry_policy=result.retry_policy,
                batch_policy=result.batch_policy,
                pagination_policy=result.pagination_policy,
                subscription_policy=result.subscription_policy,
                license_boundary=result.license_boundary,
                health=result.health,
                warnings=(),
                errors=(),
            )

    # 测试函数 `test_license_allowed_requires_evidence`：验证 `license、allowed、requires、evidence` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_license_allowed_requires_evidence(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            LicenseBoundary(
                decision=LicenseDecision.ALLOWED,
                permitted_usages=("RESEARCH",),
                cache_allowed=True,
                persistent_storage_allowed=True,
                redistribution_allowed=False,
                maximum_retention_days=30,
                evidence_refs=(),
            )

    # 测试函数 `test_cursor_pagination_requires_field`：验证 `cursor、pagination、requires、field` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_cursor_pagination_requires_field(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            PaginationPolicy(
                mode=PaginationMode.CURSOR,
                default_page_size=100,
                maximum_page_size=1000,
                maximum_pages=10,
                cursor_field=None,
            )

    # 测试函数 `test_retry_backoff_count_is_enforced`：验证 `retry、backoff、count、is、enforced` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_retry_backoff_count_is_enforced(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            RetryPolicy(
                maximum_attempts=3,
                backoff_seconds=(1,),
                retryable_error_codes=(),
            )

    # 测试函数 `test_enabled_entry_requires_entrypoint`：验证 `enabled、entry、requires、entrypoint` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_enabled_entry_requires_entrypoint(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ProviderRegistryEntry(
                provider_id="x",
                plugin_id="x.plugin",
                registration_status=(
                    PluginRegistrationStatus.AVAILABLE
                ),
                entrypoint=None,
                priority=1,
                enabled_for_routing=True,
                discovery_result_ref="d",
                authentication_reference_ref=None,
                notes="x",
            )

    # 测试函数 `test_route_candidate_is_eligible`：验证 `route、candidate、is、eligible` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_route_candidate_is_eligible(self):
        matrix = route_ready_matrix()
        registry = route_ready_registry()
        discovery = complete_discovery()
        candidates = build_provider_route_candidates(
            matrix=matrix,
            registry=registry,
            protocol=self.protocol,
            discovery_results={"test_provider": discovery},
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        self.assertEqual(len(candidates), 1)
        self.assertIs(candidates[0].decision, RouteDecision.ELIGIBLE)
        self.assertGreater(candidates[0].score, 90)

    # 测试函数 `test_route_rejects_missing_discovery`：验证 `route、rejects、missing、discovery` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_route_rejects_missing_discovery(self):
        candidates = build_provider_route_candidates(
            matrix=route_ready_matrix(),
            registry=route_ready_registry(),
            protocol=self.protocol,
            discovery_results={},
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        self.assertIs(
            candidates[0].decision,
            RouteDecision.INELIGIBLE,
        )
        self.assertIn(
            "DISCOVERY_RESULT_MISSING",
            candidates[0].reasons,
        )

    # 测试函数 `test_route_rejects_unlicensed_usage`：验证 `route、rejects、unlicensed、usage` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_route_rejects_unlicensed_usage(self):
        discovery = complete_discovery(usage="OTHER_USAGE")
        candidates = build_provider_route_candidates(
            matrix=route_ready_matrix(),
            registry=route_ready_registry(),
            protocol=self.protocol,
            discovery_results={"test_provider": discovery},
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        self.assertIn("USAGE_NOT_LICENSED", candidates[0].reasons)

    # 测试函数 `test_route_rejects_realtime_without_subscription`：验证 `route、rejects、realtime、without、subscription` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_route_rejects_realtime_without_subscription(self):
        discovery = complete_discovery(
            capability="REALTIME_SUBSCRIPTION",
        )
        matrix = route_ready_matrix()
        target = matrix.provider("test_provider")
        updated_target = ProviderTarget(
            provider_id=target.provider_id,
            display_name=target.display_name,
            provider_kind=target.provider_kind,
            lifecycle=target.lifecycle,
            integration_mode=target.integration_mode,
            authentication_mode=target.authentication_mode,
            discovery_status=target.discovery_status,
            capabilities={
                "REALTIME_SUBSCRIPTION": (
                    CapabilityImplementationStatus.VERIFIED
                )
            },
            license_review_required=True,
            execution_capability=False,
            notes=target.notes,
        )
        matrix = ProviderCapabilityMatrix(
            task_id=matrix.task_id,
            matrix_version=matrix.matrix_version,
            matrix_status=matrix.matrix_status,
            provider_neutral=matrix.provider_neutral,
            automatic_activation_allowed=False,
            secret_storage_allowed=False,
            core_system_may_import_vendor_sdk=False,
            upper_layers_may_depend_on_vendor_fields=False,
            required_adapter_contracts=matrix.required_adapter_contracts,
            capability_catalog=matrix.capability_catalog,
            provider_targets=(
                updated_target,
                *matrix.provider_targets[1:],
            ),
            routing_rules=matrix.routing_rules,
        )
        candidates = build_provider_route_candidates(
            matrix=matrix,
            registry=route_ready_registry(),
            protocol=self.protocol,
            discovery_results={"test_provider": discovery},
            request=ProviderRouteRequest(
                capability="REALTIME_SUBSCRIPTION",
                usage="CURRENT_SNAPSHOT_RESEARCH",
                requires_realtime=True,
            ),
        )
        self.assertIn(
            "REALTIME_SUBSCRIPTION_NOT_SUPPORTED",
            candidates[0].reasons,
        )

    # 测试函数 `test_degraded_health_is_eligible_with_warning`：验证 `degraded、health、is、eligible、with、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_degraded_health_is_eligible_with_warning(self):
        discovery = complete_discovery(
            health=ProviderHealthStatus.DEGRADED,
        )
        candidates = build_provider_route_candidates(
            matrix=route_ready_matrix(),
            registry=route_ready_registry(),
            protocol=self.protocol,
            discovery_results={"test_provider": discovery},
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        self.assertIs(candidates[0].decision, RouteDecision.ELIGIBLE)
        self.assertIn(
            "PROVIDER_HEALTH_DEGRADED",
            candidates[0].warnings,
        )

    # 测试函数 `test_seed_registry_rejects_manual_enable_without_discovery`：验证 `seed、registry、rejects、manual、enable、without、discovery` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_seed_registry_rejects_manual_enable_without_discovery(self):
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        raw["entries"][1]["enabled_for_routing"] = True
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.assertRaises(DataContractError):
                load_provider_plugin_registry(path)

    # 测试函数 `test_protocol_weights_sum_to_one_hundred`：验证 `protocol、weights、sum、to、one、hundred` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_protocol_weights_sum_to_one_hundred(self):
        self.assertAlmostEqual(
            sum(self.protocol.route_score_weights.values()),
            100.0,
        )

    # 测试函数 `test_registry_auth_references_contain_no_secret_material`：验证 `registry、auth、references、contain、no、secret、material` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_registry_auth_references_contain_no_secret_material(self):
        # 参数化循环：逐项使用 `self.registry.entries` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for entry in self.registry.entries:
            value = entry.authentication_reference_ref
            # 测试分支：根据 `value is not None` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if value is not None:
                self.assertTrue(
                    value.startswith(
                        (
                            "none://",
                            "env://",
                            "keyring://",
                            "secret-manager://",
                            "interactive://",
                        )
                    )
                )


if __name__ == "__main__":
    unittest.main()
