"""测试最小数据接入契约。"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    BlockingLevel,
    CanonicalDataBatch,
    ConfirmationStatus,
    DataContractError,
    DataLineageRecord,
    DataQualityResult,
    DataSourceAdapter,
    FieldMappingResult,
    MappingStatus,
    PendingConfirmation,
    QualityLevel,
    QualityStatus,
    RawDataBatch,
    SourceType,
)


class TestRawDataBatch(unittest.TestCase):
    def test_create_raw_data_batch(self) -> None:
        batch = RawDataBatch(
            source_id="test_source",
            source_type=SourceType.FILE,
            source_object_name="daily_sample.csv",
            raw_fields=["symbol", "trade_date", "close"],
            records=[
                {"symbol": "000001.SZ", "trade_date": "2026-06-20", "close": 12.34},
                {"symbol": "000002.SZ", "trade_date": "2026-06-20", "close": 8.76},
            ],
        )
        self.assertEqual(batch.row_count, 2)
        self.assertTrue(batch.batch_id)

    def test_duplicate_raw_fields_raise_error(self) -> None:
        with self.assertRaises(DataContractError):
            RawDataBatch(
                source_id="test_source",
                source_type=SourceType.FILE,
                source_object_name="duplicate.csv",
                raw_fields=["symbol", "close", "close"],
                records=[],
            )

    def test_invalid_time_range_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            RawDataBatch(
                source_id="test_source",
                source_type=SourceType.FILE,
                source_object_name="daily.csv",
                raw_fields=[],
                records=[],
                data_start=datetime(2026, 6, 21, tzinfo=timezone.utc),
                data_end=datetime(2026, 6, 20, tzinfo=timezone.utc),
            )


class TestFieldMappingResult(unittest.TestCase):
    def test_create_mapped_field_result(self) -> None:
        result = FieldMappingResult(
            source_field="close",
            canonical_field_ref="market_daily.close_raw_cny",
            status=MappingStatus.MAPPED,
        )
        self.assertEqual(result.status, MappingStatus.MAPPED)

    def test_invalid_canonical_field_ref_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            FieldMappingResult(
                source_field="close",
                canonical_field_ref="close_raw_cny",
                status=MappingStatus.MAPPED,
            )

    def test_pending_mapping_requires_confirmation(self) -> None:
        with self.assertRaises(DataContractError):
            FieldMappingResult(
                source_field="close",
                canonical_field_ref="market_daily.close_raw_cny",
                status=MappingStatus.PENDING_CONFIRMATION,
                requires_confirmation=False,
            )


class TestDataQualityResult(unittest.TestCase):
    def test_calculate_failure_rate(self) -> None:
        result = DataQualityResult(
            check_name="检查收盘价是否为空",
            level=QualityLevel.ERROR,
            status=QualityStatus.FAILED,
            checked_row_count=100,
            failed_row_count=10,
            blocking=True,
        )
        self.assertEqual(result.failure_rate, 0.1)
        self.assertTrue(result.blocks_downstream)

    def test_passed_status_cannot_have_failed_rows(self) -> None:
        with self.assertRaises(DataContractError):
            DataQualityResult(
                check_name="检查股票代码",
                level=QualityLevel.INFO,
                status=QualityStatus.PASSED,
                checked_row_count=100,
                failed_row_count=1,
                blocking=False,
            )

    def test_failed_rows_cannot_exceed_checked_rows(self) -> None:
        with self.assertRaises(DataContractError):
            DataQualityResult(
                check_name="检查交易日期",
                level=QualityLevel.CRITICAL,
                status=QualityStatus.FAILED,
                checked_row_count=10,
                failed_row_count=11,
                blocking=True,
            )


class TestPendingConfirmation(unittest.TestCase):
    def test_open_blocking_confirmation_blocks_downstream(self) -> None:
        confirmation = PendingConfirmation(
            category="ADJUSTMENT_METHOD",
            source_object="stock_daily_k",
            issue_description="尚未确认价格是否经过复权。",
            blocking_level=BlockingLevel.BLOCKING,
        )
        self.assertTrue(confirmation.blocks_downstream)

    def test_resolved_confirmation_requires_resolution_details(self) -> None:
        with self.assertRaises(DataContractError):
            PendingConfirmation(
                category="VOLUME_UNIT",
                source_object="stock_daily_k",
                issue_description="成交量单位尚未确认。",
                status=ConfirmationStatus.RESOLVED,
            )

    def test_empty_possible_option_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            PendingConfirmation(
                category="DATE_SEMANTICS",
                source_object="fundamental_snapshot",
                issue_description="日期字段含义尚未确认。",
                possible_options=["TRADE_DATE", ""],
            )


class TestCanonicalDataBatch(unittest.TestCase):
    def test_create_passed_canonical_batch(self) -> None:
        batch = CanonicalDataBatch(
            raw_batch_id="raw-001",
            domain_code="market_daily",
            canonical_object_name="MarketDailyRecord",
            field_dictionary_version="0.5",
            mapping_version="mapping-v1",
            records=[{"symbol": "000001.SZ"}],
            quality_status=QualityStatus.PASSED,
        )
        self.assertEqual(batch.row_count, 1)
        self.assertFalse(batch.blocks_downstream)

    def test_failed_canonical_batch_blocks_downstream(self) -> None:
        batch = CanonicalDataBatch(
            raw_batch_id="raw-002",
            domain_code="market_daily",
            canonical_object_name="MarketDailyRecord",
            field_dictionary_version="0.5",
            mapping_version="mapping-v1",
            records=[],
            quality_status=QualityStatus.FAILED,
        )
        self.assertTrue(batch.blocks_downstream)

    def test_blocking_confirmation_blocks_canonical_batch(self) -> None:
        confirmation = PendingConfirmation(
            category="ADJUSTMENT_METHOD",
            source_object="stock_daily_k",
            issue_description="尚未确认价格复权方式。",
            blocking_level=BlockingLevel.BLOCKING,
        )
        batch = CanonicalDataBatch(
            raw_batch_id="raw-003",
            domain_code="market_daily",
            canonical_object_name="MarketDailyRecord",
            field_dictionary_version="0.5",
            mapping_version="mapping-v1",
            records=[],
            quality_status=QualityStatus.PASSED,
            pending_confirmations=[confirmation],
        )
        self.assertTrue(batch.blocks_downstream)


class TestDataLineageRecord(unittest.TestCase):
    def test_create_lineage_record(self) -> None:
        record = DataLineageRecord(
            source_batch_id="raw-001",
            target_batch_id="canonical-001",
            source_location="DolphinDB/stock_daily_k",
            target_object="MarketDailyRecord",
            mapping_version="mapping-v1",
            transformation_version="transform-v1",
            code_version="git-abc123",
        )
        self.assertTrue(record.lineage_id)

    def test_same_source_and_target_batch_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            DataLineageRecord(
                source_batch_id="same-id",
                target_batch_id="same-id",
                source_location="file.csv",
                target_object="MarketDailyRecord",
                mapping_version="mapping-v1",
                transformation_version="transform-v1",
            )


class DummyFileAdapter(DataSourceAdapter):
    """仅供测试使用的最小适配器。"""

    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        return RawDataBatch(
            source_id=self.source_id,
            source_type=self.source_type,
            source_object_name=source_object_name,
            raw_fields=["symbol"],
            records=[{"symbol": "000001.SZ"}],
        )

    def health_check(self) -> DataQualityResult:
        return DataQualityResult(
            check_name="测试数据源健康检查",
            level=QualityLevel.INFO,
            status=QualityStatus.PASSED,
            checked_row_count=1,
            failed_row_count=0,
            blocking=False,
        )


class TestDataSourceAdapter(unittest.TestCase):
    def test_abstract_adapter_cannot_be_instantiated(self) -> None:
        with self.assertRaises(TypeError):
            DataSourceAdapter("source", SourceType.FILE)

    def test_concrete_adapter_implements_contract(self) -> None:
        adapter = DummyFileAdapter("file-source", SourceType.FILE)
        batch = adapter.read_raw("sample.csv")
        health = adapter.health_check()
        self.assertEqual(batch.row_count, 1)
        self.assertEqual(health.status, QualityStatus.PASSED)


if __name__ == "__main__":
    unittest.main()
