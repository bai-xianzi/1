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


class TestProviderPluginProtocol(unittest.TestCase):
    def setUp(self):
        self.matrix = load_provider_capability_matrix(MATRIX_PATH)
        self.protocol = load_provider_plugin_protocol_config(
            PROTOCOL_PATH
        )
        self.registry = load_provider_plugin_registry(REGISTRY_PATH)

    def test_protocol_is_provider_neutral(self):
        self.assertTrue(self.protocol.provider_neutral)

    def test_protocol_forbids_secrets_and_activation(self):
        self.assertFalse(self.protocol.secret_material_allowed)
        self.assertFalse(
            self.protocol.automatic_plugin_activation_allowed
        )

    def test_validation_forbids_network_and_database(self):
        self.assertFalse(
            self.protocol.network_probe_during_validation_allowed
        )
        self.assertFalse(
            self.protocol.database_probe_during_validation_allowed
        )

    def test_protocol_has_nine_required_methods(self):
        self.assertEqual(len(self.protocol.required_plugin_methods), 9)

    def test_seed_registry_covers_matrix(self):
        self.assertEqual(
            {entry.provider_id for entry in self.registry.entries},
            {
                target.provider_id
                for target in self.matrix.provider_targets
            },
        )

    def test_seed_registry_has_no_enabled_routes(self):
        self.assertTrue(
            all(
                not entry.enabled_for_routing
                for entry in self.registry.entries
            )
        )

    def test_commercial_targets_are_pending(self):
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

    def test_auth_reference_accepts_environment_reference(self):
        ref = AuthenticationReference(
            reference_id="auth:test",
            kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
            locator="env://TEST_TOKEN",
        )
        self.assertEqual(ref.locator, "env://TEST_TOKEN")

    def test_auth_reference_rejects_raw_value(self):
        with self.assertRaises(DataContractError):
            AuthenticationReference(
                reference_id="auth:test",
                kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
                locator="abcdef0123456789abcdef0123456789",
            )

    def test_auth_reference_rejects_prefix_mismatch(self):
        with self.assertRaises(DataContractError):
            AuthenticationReference(
                reference_id="auth:test",
                kind=AuthenticationReferenceKind.OS_KEYRING,
                locator="env://TEST_TOKEN",
            )

    def test_complete_discovery_requires_installed_runtime(self):
        result = complete_discovery()
        raw = {
            **result.__dict__
        } if hasattr(result, "__dict__") else None
        self.assertTrue(result.runtime.installed)

    def test_complete_discovery_has_capability(self):
        result = complete_discovery()
        self.assertEqual(
            result.capabilities["EOD_MARKET_DATA"],
            CapabilityImplementationStatus.VERIFIED,
        )

    def test_failed_discovery_requires_error(self):
        result = complete_discovery()
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

    def test_license_allowed_requires_evidence(self):
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

    def test_cursor_pagination_requires_field(self):
        with self.assertRaises(DataContractError):
            PaginationPolicy(
                mode=PaginationMode.CURSOR,
                default_page_size=100,
                maximum_page_size=1000,
                maximum_pages=10,
                cursor_field=None,
            )

    def test_retry_backoff_count_is_enforced(self):
        with self.assertRaises(DataContractError):
            RetryPolicy(
                maximum_attempts=3,
                backoff_seconds=(1,),
                retryable_error_codes=(),
            )

    def test_enabled_entry_requires_entrypoint(self):
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

    def test_seed_registry_rejects_manual_enable_without_discovery(self):
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        raw["entries"][1]["enabled_for_routing"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_provider_plugin_registry(path)

    def test_protocol_weights_sum_to_one_hundred(self):
        self.assertAlmostEqual(
            sum(self.protocol.route_score_weights.values()),
            100.0,
        )

    def test_registry_auth_references_contain_no_secret_material(self):
        for entry in self.registry.entries:
            value = entry.authentication_reference_ref
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
