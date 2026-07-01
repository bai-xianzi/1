# 测试模块总览：验证 `test_dolphindb_provider_plugin` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试类 `FakeStatus`：集中验证 `test_dolphindb_provider_plugin` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


# 测试类 `FakeAdapter`：集中验证 `test_dolphindb_provider_plugin` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：health_status、blocking。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `health_check`：封装 `health_check` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def health_check(self):
        self.health_calls += 1
        return SimpleNamespace(
            status=self.health_status,
            blocking=self.blocking,
            description="fake health",
        )

    # 测试函数 `read_raw`：封装 `read_raw` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：source_object_name、**kwargs。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def read_raw(self, source_object_name, **kwargs):
        self.read_calls.append((source_object_name, kwargs))
        return SimpleNamespace(
            records=[
                {"instrument_id": "000001", "close": 10.0},
                {"instrument_id": "000002", "close": 11.0},
            ]
        )

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script):
        self.query_calls.append(script)
        return [{"value": 1}]

    # 测试函数 `_normalise_records`：封装 `_normalise_records` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：result。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    @staticmethod
    def _normalise_records(result):
        return (
            list(result[0]) if result else [],
            [dict(item) for item in result],
        )

    # 测试函数 `close`：封装 `close` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def close(self):
        self.closed = True


# 测试函数 `runtime_probe`：封装 `runtime_probe` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：installed。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def runtime_probe(installed=True):
    return {
        "installed": installed,
        "sdk_version": "3.0.0" if installed else None,
        "python_version": "3.11",
        "operating_system": "Windows",
        "architecture": "AMD64",
        "probe": "fake",
    }


# 测试类 `TestDolphinDBProviderPluginBridge`：集中验证 `test_dolphindb_provider_plugin` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDolphinDBProviderPluginBridge(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `tearDown`：清理本组测试创建的临时状态和外部资源。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def tearDown(self):
        # 测试分支：根据 `self.old_password is None` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if self.old_password is None:
            os.environ.pop("DOLPHINDB_PASSWORD", None)
        else:
            os.environ["DOLPHINDB_PASSWORD"] = self.old_password

    # 测试函数 `open`：封装 `open` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def open(self):
        self.bridge.open_session(
            self.config.authentication_reference
        )

    # 测试函数 `test_config_reuses_legacy_adapter`：验证 `config、reuses、legacy、adapter` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_config_has_no_secret_value`：验证 `config、has、no、secret、value` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_config_has_no_secret_value(self):
        locator = self.config.authentication_reference.locator
        self.assertEqual(locator, "env://DOLPHINDB_PASSWORD")
        self.assertNotIn("test-only-secret", locator)

    # 测试函数 `test_bridge_satisfies_runtime_protocol`：验证 `bridge、satisfies、runtime、protocol` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_bridge_satisfies_runtime_protocol(self):
        self.assertIsInstance(self.bridge, ProviderPlugin)

    # 测试函数 `test_describe_is_not_route_enabled`：验证 `describe、is、not、route、enabled` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_describe_is_not_route_enabled(self):
        descriptor = self.bridge.describe()
        self.assertIs(
            descriptor.registration_status,
            PluginRegistrationStatus.DISCOVERY_PENDING,
        )
        self.assertFalse(descriptor.enabled_for_routing)

    # 测试函数 `test_describe_has_new_entrypoint`：验证 `describe、has、new、entrypoint` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_describe_has_new_entrypoint(self):
        descriptor = self.bridge.describe()
        self.assertIn(
            "DolphinDBProviderPluginBridge",
            descriptor.entrypoint,
        )

    # 测试函数 `test_health_passed_maps_to_healthy`：验证 `health、passed、maps、to、healthy` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_health_passed_maps_to_healthy(self):
        result = self.bridge.health_check()
        self.assertIs(result.status, ProviderHealthStatus.HEALTHY)

    # 测试函数 `test_health_warning_maps_to_degraded`：验证 `health、warning、maps、to、degraded` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_health_failure_maps_to_unavailable`：验证 `health、failure、maps、to、unavailable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_discovery_complete_when_installed_and_healthy`：验证 `discovery、complete、when、installed、and、healthy` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_discovery_complete_when_installed_and_healthy(self):
        result = self.bridge.discover()
        self.assertIs(result.outcome, DiscoveryOutcome.COMPLETE)
        self.assertTrue(result.runtime.installed)
        self.assertEqual(result.errors, ())

    # 测试函数 `test_discovery_fails_when_client_missing`：验证 `discovery、fails、when、client、missing` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_discovery_fails_when_health_unavailable`：验证 `discovery、fails、when、health、unavailable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_open_requires_matching_reference`：验证 `open、requires、matching、reference` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_open_requires_matching_reference(self):
        bad = AuthenticationReference(
            reference_id="auth:other",
            kind=AuthenticationReferenceKind.ENVIRONMENT_VARIABLE,
            locator="env://DOLPHINDB_PASSWORD",
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.open_session(bad)

    # 测试函数 `test_open_requires_environment_value`：验证 `open、requires、environment、value` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_open_requires_environment_value(self):
        os.environ.pop("DOLPHINDB_PASSWORD", None)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.open()

    # 测试函数 `test_query_requires_open_session`：验证 `query、requires、open、session` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    # 测试函数 `test_read_raw_delegates_to_existing_adapter`：验证 `read、raw、delegates、to、existing、adapter` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_readonly_query_delegates_and_normalises`：验证 `readonly、query、delegates、and、normalises` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_batch_limit_is_enforced`：验证 `batch、limit、is、enforced` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    # 测试函数 `test_unknown_capability_is_rejected`：验证 `unknown、capability、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    # 测试函数 `test_unknown_operation_is_rejected`：验证 `unknown、operation、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    # 测试函数 `test_iter_pages_yields_one_legacy_batch`：验证 `iter、pages、yields、one、legacy、batch` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_subscribe_is_not_supported`：验证 `subscribe、is、not、supported` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_subscribe_is_not_supported(self):
        request = ProviderSubscriptionRequest(
            subscription_id="s1",
            provider_id="local_dolphindb",
            capability="REALTIME_SUBSCRIPTION",
            symbols=("000001",),
            fields=("last",),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.subscribe(request)

    # 测试函数 `test_unsubscribe_is_not_supported`：验证 `unsubscribe、is、not、supported` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unsubscribe_is_not_supported(self):
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.unsubscribe("s1")

    # 测试函数 `test_close_uses_existing_adapter_when_available`：验证 `close、uses、existing、adapter、when、available` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_close_uses_existing_adapter_when_available(self):
        self.open()
        self.bridge.close_session()
        self.assertTrue(self.adapter.closed)

    # 测试函数 `test_close_blocks_future_query`：验证 `close、blocks、future、query` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.bridge.query_batch(request)

    # 测试函数 `test_config_rejects_custom_query_engine`：验证 `config、rejects、custom、query、engine` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_config_rejects_custom_query_engine(self):
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["custom_query_engine_implemented"] = True
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
                load_dolphindb_provider_plugin_bridge_config(path)


if __name__ == "__main__":
    unittest.main()
