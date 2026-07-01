from __future__ import annotations

import json
import os
import tempfile
import unittest
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dolphindb_provider_plugin import (
    DolphinDBProviderPluginBridge,
    load_dolphindb_provider_plugin_bridge_config,
)
from a_stock_quant.provider_plugin_protocol import (
    AuthenticationReference,
    AuthenticationReferenceKind,
    DiscoveryOutcome,
    PluginRegistrationStatus,
    ProviderHealthStatus,
    ProviderPlugin,
    ProviderQueryRequest,
    ProviderSubscriptionRequest,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = (
    ROOT
    / "configs"
    / "providers"
    / "dolphindb_provider_plugin_bridge_v0.json"
)


class FakeStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class FakeAdapter:
    def __init__(
        self,
        *,
        health_status=FakeStatus.PASSED,
        blocking=False,
    ):
        self.health_status = health_status
        self.blocking = blocking
        self.health_calls = 0
        self.read_calls = []
        self.query_calls = []
        self.closed = False

    def health_check(self):
        self.health_calls += 1
        return SimpleNamespace(
            status=self.health_status,
            blocking=self.blocking,
            description="fake health",
        )

    def read_raw(self, source_object_name, **kwargs):
        self.read_calls.append((source_object_name, kwargs))
        return SimpleNamespace(
            records=[
                {"instrument_id": "000001", "close": 10.0},
                {"instrument_id": "000002", "close": 11.0},
            ]
        )

    def run_readonly_query(self, script):
        self.query_calls.append(script)
        return [{"value": 1}]

    @staticmethod
    def _normalise_records(result):
        return (
            list(result[0]) if result else [],
            [dict(item) for item in result],
        )

    def close(self):
        self.closed = True


def runtime_probe(installed=True):
    return {
        "installed": installed,
        "sdk_version": "3.0.0" if installed else None,
        "python_version": "3.11",
        "operating_system": "Windows",
        "architecture": "AMD64",
        "probe": "fake",
    }


class TestDolphinDBProviderPluginBridge(unittest.TestCase):
    def setUp(self):
        self.config = (
            load_dolphindb_provider_plugin_bridge_config(
                CONFIG_PATH
            )
        )
        self.adapter = FakeAdapter()
        self.bridge = DolphinDBProviderPluginBridge(
            adapter=self.adapter,
            config=self.config,
            runtime_probe=lambda: runtime_probe(True),
        )
        self.old_password = os.environ.get("DOLPHINDB_PASSWORD")
        os.environ["DOLPHINDB_PASSWORD"] = "test-only-secret"

    def tearDown(self):
        if self.old_password is None:
            os.environ.pop("DOLPHINDB_PASSWORD", None)
        else:
            os.environ["DOLPHINDB_PASSWORD"] = self.old_password

    def open(self):
        self.bridge.open_session(
            self.config.authentication_reference
        )

    def test_config_reuses_legacy_adapter(self):
        self.assertEqual(
            self.config.reuse_strategy,
            "WRAP_WITH_THIN_ADAPTER",
        )
        self.assertFalse(
            self.config.custom_query_engine_implemented
        )
        self.assertFalse(
            self.config.custom_session_engine_implemented
        )

    def test_config_has_no_secret_value(self):
        locator = self.config.authentication_reference.locator
        self.assertEqual(locator, "env://DOLPHINDB_PASSWORD")
        self.assertNotIn("test-only-secret", locator)

    def test_bridge_satisfies_runtime_protocol(self):
        self.assertIsInstance(self.bridge, ProviderPlugin)

    def test_describe_is_not_route_enabled(self):
        descriptor = self.bridge.describe()
        self.assertIs(
            descriptor.registration_status,
            PluginRegistrationStatus.DISCOVERY_PENDING,
        )
        self.assertFalse(descriptor.enabled_for_routing)

    def test_describe_has_new_entrypoint(self):
        descriptor = self.bridge.describe()
        self.assertIn(
            "DolphinDBProviderPluginBridge",
            descriptor.entrypoint,
        )

    def test_health_passed_maps_to_healthy(self):
        result = self.bridge.health_check()
        self.assertIs(result.status, ProviderHealthStatus.HEALTHY)

    def test_health_warning_maps_to_degraded(self):
        bridge = DolphinDBProviderPluginBridge(
            adapter=FakeAdapter(
                health_status=FakeStatus.WARNING,
                blocking=False,
            ),
            config=self.config,
            runtime_probe=lambda: runtime_probe(True),
        )
        self.assertIs(
            bridge.health_check().status,
            ProviderHealthStatus.DEGRADED,
        )

    def test_health_failure_maps_to_unavailable(self):
        bridge = DolphinDBProviderPluginBridge(
            adapter=FakeAdapter(
                health_status=FakeStatus.FAILED,
                blocking=True,
            ),
            config=self.config,
            runtime_probe=lambda: runtime_probe(True),
        )
        self.assertIs(
            bridge.health_check().status,
            ProviderHealthStatus.UNAVAILABLE,
        )

    def test_discovery_complete_when_installed_and_healthy(self):
        result = self.bridge.discover()
        self.assertIs(result.outcome, DiscoveryOutcome.COMPLETE)
        self.assertTrue(result.runtime.installed)
        self.assertEqual(result.errors, ())

    def test_discovery_fails_when_client_missing(self):
        bridge = DolphinDBProviderPluginBridge(
            adapter=FakeAdapter(),
            config=self.config,
            runtime_probe=lambda: runtime_probe(False),
        )
        result = bridge.discover()
        self.assertIs(result.outcome, DiscoveryOutcome.FAILED)
        self.assertIn(
            "DOLPHINDB_PYTHON_CLIENT_NOT_INSTALLED",
            result.errors,
        )

    def test_discovery_fails_when_health_unavailable(self):
        bridge = DolphinDBProviderPluginBridge(
            adapter=FakeAdapter(
                health_status=FakeStatus.FAILED,
                blocking=True,
            ),
            config=self.config,
            runtime_probe=lambda: runtime_probe(True),
        )
        result = bridge.discover()
        self.assertIs(result.outcome, DiscoveryOutcome.FAILED)
        self.assertIn(
            "DOLPHINDB_HEALTH_UNAVAILABLE",
            result.errors,
        )

    def test_open_requires_matching_reference(self):
        bad = AuthenticationReference(
            reference_id="auth:other",
            kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
            locator="env://DOLPHINDB_PASSWORD",
        )
        with self.assertRaises(DataContractError):
            self.bridge.open_session(bad)

    def test_open_requires_environment_value(self):
        os.environ.pop("DOLPHINDB_PASSWORD", None)
        with self.assertRaises(DataContractError):
            self.open()

    def test_query_requires_open_session(self):
        request = ProviderQueryRequest(
            request_id="r1",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=5,
        )
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    def test_read_raw_delegates_to_existing_adapter(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r1",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=5,
        )
        result = self.bridge.query_batch(request)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(
            self.adapter.read_calls,
            [
                (
                    "a_stock_daily_k",
                    {
                        "database_uri": "dfs://a_stock_daily_k",
                        "limit": 5,
                    },
                )
            ],
        )

    def test_readonly_query_delegates_and_normalises(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r2",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="RUN_READONLY_QUERY",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={"script": "select top 1 * from t"},
            maximum_rows=1,
        )
        result = self.bridge.query_batch(request)
        self.assertEqual(result.records, ({"value": 1},))
        self.assertEqual(
            self.adapter.query_calls,
            ["select top 1 * from t"],
        )

    def test_batch_limit_is_enforced(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r3",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=100001,
        )
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    def test_unknown_capability_is_rejected(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r4",
            provider_id="local_dolphindb",
            capability="ORDER_SUBMIT",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=1,
        )
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    def test_unknown_operation_is_rejected(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r5",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="WRITE_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={},
            maximum_rows=1,
        )
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    def test_iter_pages_yields_one_legacy_batch(self):
        self.open()
        request = ProviderQueryRequest(
            request_id="r6",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=5,
        )
        pages = list(self.bridge.iter_pages(request))
        self.assertEqual(len(pages), 1)
        self.assertIsNone(pages[0].next_cursor)

    def test_subscribe_is_not_supported(self):
        request = ProviderSubscriptionRequest(
            subscription_id="s1",
            provider_id="local_dolphindb",
            capability="REALTIME_SUBSCRIPTION",
            symbols=("000001",),
            fields=("last",),
        )
        with self.assertRaises(DataContractError):
            self.bridge.subscribe(request)

    def test_unsubscribe_is_not_supported(self):
        with self.assertRaises(DataContractError):
            self.bridge.unsubscribe("s1")

    def test_close_uses_existing_adapter_when_available(self):
        self.open()
        self.bridge.close_session()
        self.assertTrue(self.adapter.closed)

    def test_close_blocks_future_query(self):
        self.open()
        self.bridge.close_session()
        request = ProviderQueryRequest(
            request_id="r7",
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": "dfs://a_stock_daily_k",
                "source_object_name": "a_stock_daily_k",
            },
            maximum_rows=1,
        )
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    def test_config_rejects_custom_query_engine(self):
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["custom_query_engine_implemented"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_dolphindb_provider_plugin_bridge_config(path)


if __name__ == "__main__":
    unittest.main()
