# 测试模块总览：验证 `test_vendor_query_manifest` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
import unittest

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.vendor_query_manifest import (
    ChunkPolicy,
    VendorManifestRegistry,
    VendorOperation,
    VendorQueryManifest,
)


# 测试类 `TestVendorQueryManifest`：集中验证 `test_vendor_query_manifest` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestVendorQueryManifest(unittest.TestCase):
    # 测试函数 `_manifest`：封装 `_manifest` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：manifest_id、enabled。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _manifest(
        self,
        *,
        manifest_id: str = "m1",
        enabled: bool = False,
    ) -> VendorQueryManifest:
        return VendorQueryManifest(
            manifest_id=manifest_id,
            source_id="ifind_http",
            dataset_id="a_stock_daily_bar",
            canonical_object="DailyBar",
            operation=VendorOperation.HISTORICAL_QUOTES,
            request_template={
                "endpoint": "/api/v1/cmd_history_quotation",
                "codes": "{vendor_codes}",
                "indicators": [
                    "open",
                    "high",
                    "low",
                    "close",
                ],
            },
            field_mapping={
                "open": "DailyBar.open",
                "high": "DailyBar.high",
                "low": "DailyBar.low",
                "close": "DailyBar.close",
            },
            response_data_path="tables",
            mapping_version="0.1.0",
            source_schema_version="official-example-2022",
            generated_by="official_example_template",
            enabled=enabled,
            chunk_policy=ChunkPolicy(
                max_rows_hint=2_000_000,
                split_strategy="BY_CODES_AND_DATE",
            ),
        )

    # 测试函数 `test_manifest_round_trip`：验证 `manifest、round、trip` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manifest_round_trip(self) -> None:
        original = self._manifest()
        restored = VendorQueryManifest.from_dict(
            original.to_dict()
        )
        self.assertEqual(
            restored.to_dict(),
            original.to_dict(),
        )

    # 测试函数 `test_secret_fields_are_rejected`：验证 `secret、fields、are、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_secret_fields_are_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            VendorQueryManifest(
                manifest_id="bad",
                source_id="ifind_http",
                dataset_id="dataset",
                canonical_object="DailyBar",
                operation=VendorOperation.REALTIME_QUOTES,
                request_template={
                    "access_token": "do-not-store",
                },
                field_mapping={
                    "latest": "DailyBar.close",
                },
                response_data_path="tables",
                mapping_version="1",
                source_schema_version="1",
                generated_by="manual",
            )

    # 测试函数 `test_disabled_manifests_are_hidden`：验证 `disabled、manifests、are、hidden` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_disabled_manifests_are_hidden(self) -> None:
        registry = VendorManifestRegistry()
        registry.register(self._manifest())
        self.assertEqual(
            registry.list_for_dataset(
                "a_stock_daily_bar"
            ),
            (),
        )
        self.assertEqual(
            len(
                registry.list_for_dataset(
                    "a_stock_daily_bar",
                    include_disabled=True,
                )
            ),
            1,
        )

    # 测试函数 `test_duplicate_manifest_is_rejected`：验证 `duplicate、manifest、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_manifest_is_rejected(self) -> None:
        registry = VendorManifestRegistry()
        registry.register(self._manifest())
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            registry.register(self._manifest())


if __name__ == "__main__":
    unittest.main()
