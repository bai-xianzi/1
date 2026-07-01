"""测试通用数据集注册表与标准字段映射引擎。"""
# 测试模块总览：验证 `test_dataset_registry` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    MappingStatus,
    SourceType,
)
from a_stock_quant.dataset_registry import (
    CanonicalFieldCatalog,
    CanonicalMappingEngine,
    DatasetRegistration,
    DatasetRegistry,
    FieldMappingRule,
)


# 测试函数 `make_registration`：封装 `make_registration` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_registration() -> DatasetRegistration:
    return DatasetRegistration(
        dataset_id="demo_daily",
        source_type=SourceType.DOLPHINDB,
        source_locator={
            "database_uri": "dfs://DEMO",
            "table_name": "daily",
        },
        dataset_mode="SNAPSHOT",
        coverage_version="demo_daily@2026-05-29",
        schema_version="1.0.0",
        mapping_version="1.0.0",
        dictionary_revision="0.5",
        date_field="trade_date",
        entity_field="stock_code",
        primary_key_fields=(
            "stock_code",
            "trade_date",
        ),
        source_fields=(
            "stock_code",
            "trade_date",
            "close",
            "float_shares",
            "source_signal",
        ),
        canonical_objects=(
            "DailyBar",
            "OwnershipSnapshot",
        ),
        field_mappings=(
            FieldMappingRule(
                source_fields=("stock_code",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="instrument_id",
                required=True,
            ),
            FieldMappingRule(
                source_fields=("trade_date",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="trade_date",
                required=True,
            ),
            FieldMappingRule(
                source_fields=("close",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="close_raw_cny",
            ),
            FieldMappingRule(
                source_fields=("float_shares",),
                status=MappingStatus.MAPPED,
                target_object="OwnershipSnapshot",
                canonical_field="float_shares",
                transform_id="multiply",
                transform_params={"factor": 10000},
            ),
            FieldMappingRule(
                source_fields=("source_signal",),
                status=MappingStatus.PENDING_CONFIRMATION,
                notes="来源专有信号。",
            ),
        ),
    )


# 测试类 `TestDatasetRegistration`：集中验证 `test_dataset_registry` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDatasetRegistration(unittest.TestCase):
    # 测试函数 `test_all_source_fields_are_accounted`：验证 `all、source、fields、are、accounted` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_source_fields_are_accounted(self) -> None:
        coverage = make_registration().mapping_coverage()

        self.assertTrue(
            coverage["all_source_fields_accounted"]
        )
        self.assertEqual(
            coverage["pending_fields"],
            ["source_signal"],
        )

    # 测试函数 `test_unknown_mapping_source_is_rejected`：验证 `unknown、mapping、source、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_mapping_source_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DatasetRegistration(
                dataset_id="bad",
                source_type=SourceType.DOLPHINDB,
                source_locator={},
                dataset_mode="SNAPSHOT",
                coverage_version="bad@1",
                schema_version="1",
                mapping_version="1",
                dictionary_revision="0.5",
                date_field=None,
                entity_field=None,
                primary_key_fields=(),
                source_fields=("a",),
                canonical_objects=("DailyBar",),
                field_mappings=(
                    FieldMappingRule(
                        source_fields=("missing",),
                        status=MappingStatus.MAPPED,
                        target_object="DailyBar",
                        canonical_field="trade_date",
                    ),
                ),
            )

    # 测试函数 `test_primary_key_must_be_source_field`：验证 `primary、key、must、be、source、field` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_primary_key_must_be_source_field(self) -> None:
        value = make_registration().to_dict()
        value["primary_key_fields"] = ["missing"]

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DatasetRegistration.from_dict(value)

    # 测试函数 `test_round_trip_dict`：验证 `round、trip、dict` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_round_trip_dict(self) -> None:
        original = make_registration()
        restored = DatasetRegistration.from_dict(
            original.to_dict()
        )

        self.assertEqual(restored, original)


# 测试类 `TestCanonicalFieldCatalog`：集中验证 `test_dataset_registry` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestCanonicalFieldCatalog(unittest.TestCase):
    # 测试函数 `test_valid_registration_passes`：验证 `valid、registration、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_valid_registration_passes(self) -> None:
        catalog = CanonicalFieldCatalog({
            "DailyBar": {
                "instrument_id",
                "trade_date",
                "close_raw_cny",
            },
            "OwnershipSnapshot": {
                "float_shares",
            },
        })

        catalog.assert_valid(make_registration())

    # 测试函数 `test_unknown_canonical_field_fails`：验证 `unknown、canonical、field、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_canonical_field_fails(self) -> None:
        catalog = CanonicalFieldCatalog({
            "DailyBar": {
                "instrument_id",
                "trade_date",
            },
            "OwnershipSnapshot": {
                "float_shares",
            },
        })

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            catalog.assert_valid(make_registration())


# 测试类 `TestDatasetRegistry`：集中验证 `test_dataset_registry` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDatasetRegistry(unittest.TestCase):
    # 测试函数 `test_register_and_filter`：验证 `register、and、filter` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_register_and_filter(self) -> None:
        registry = DatasetRegistry()
        registration = make_registration()
        registry.register(registration)

        self.assertEqual(
            registry.get("demo_daily"),
            registration,
        )
        self.assertEqual(
            len(
                registry.list(
                    canonical_object="DailyBar"
                )
            ),
            1,
        )

    # 测试函数 `test_duplicate_registration_rejected`：验证 `duplicate、registration、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_registration_rejected(self) -> None:
        registry = DatasetRegistry()
        registration = make_registration()
        registry.register(registration)

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            registry.register(registration)

    # 测试函数 `test_load_json`：验证 `load、json` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_load_json(self) -> None:
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            path.write_text(
                json.dumps(
                    make_registration().to_dict(),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            registry = DatasetRegistry()
            loaded = registry.load_json(path)

        self.assertEqual(loaded.dataset_id, "demo_daily")


# 测试类 `TestCanonicalMappingEngine`：集中验证 `test_dataset_registry` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestCanonicalMappingEngine(unittest.TestCase):
    # 测试函数 `test_maps_multiple_standard_objects`：验证 `maps、multiple、standard、objects` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_maps_multiple_standard_objects(self) -> None:
        result = CanonicalMappingEngine().map_record(
            make_registration(),
            {
                "stock_code": "000001",
                "trade_date": "2026-05-29",
                "close": 10.5,
                "float_shares": 123.4,
                "source_signal": "X",
            },
        )

        self.assertEqual(
            result.outputs["DailyBar"][
                "close_raw_cny"
            ],
            10.5,
        )
        self.assertEqual(
            result.outputs["OwnershipSnapshot"][
                "float_shares"
            ],
            1_234_000.0,
        )
        self.assertEqual(
            result.source_extensions["source_signal"],
            "X",
        )

    # 测试函数 `test_required_missing_field_fails`：验证 `required、missing、field、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_required_missing_field_fails(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            CanonicalMappingEngine().map_record(
                make_registration(),
                {
                    "trade_date": "2026-05-29",
                    "close": 10.5,
                    "float_shares": 123.4,
                },
            )

    # 测试函数 `test_pct_change_transform_uses_context`：验证 `pct、change、transform、uses、context` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_pct_change_transform_uses_context(self) -> None:
        rule = FieldMappingRule(
            source_fields=("close",),
            status=MappingStatus.MAPPED,
            target_object="DailyBar",
            canonical_field="pct_change_pct",
            transform_id="pct_change_from_prev_close",
            transform_params={"precision": 2},
        )
        value = make_registration().to_dict()
        value["field_mappings"].append(
            rule.to_dict()
        )
        registration = DatasetRegistration.from_dict(value)

        result = CanonicalMappingEngine().map_record(
            registration,
            {
                "stock_code": "000001",
                "trade_date": "2026-05-29",
                "close": 11.0,
                "float_shares": 100.0,
                "source_signal": None,
            },
            context={"prev_close": 10.0},
        )

        self.assertEqual(
            result.outputs["DailyBar"][
                "pct_change_pct"
            ],
            10.0,
        )


if __name__ == "__main__":
    unittest.main()
