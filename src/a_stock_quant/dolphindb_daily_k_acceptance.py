"""真实 DolphinDB 日K标准化抽样验收与字段覆盖报告。

本模块调用 TASK_010 的标准化读取服务，对真实 DolphinDB 数据执行
小规模、只读、可重复的抽样验收。

验收重点：
1. 标准对象是否成功生成；
2. 核心字段是否完整；
3. 计算字段是否内部一致；
4. 待确认来源字段是否仍保留；
5. 字段血缘是否携带映射版本和字典版本；
6. 已知来源反向涨跌幅是否只作为信息标记，而不阻断下游。
"""

from __future__ import annotations

import argparse
import getpass
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .data_contracts import DataContractError, MappingStatus
from .dataset_registry import DatasetRegistration, DatasetRegistry
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from .dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)


_DEFAULT_INSTRUMENTS = (
    "000001",
    "001332",
    "300622",
    "600694",
    "688012",
    "920029",
)
_DEFAULT_START_DATE = date(2026, 5, 26)
_DEFAULT_END_DATE = date(2026, 5, 29)

_DAILY_BAR_REQUIRED_FIELDS = (
    "instrument_id",
    "trade_date",
    "open_raw_cny",
    "high_raw_cny",
    "low_raw_cny",
    "close_raw_cny",
    "volume_shares",
    "amount_cny",
)
_OWNERSHIP_REQUIRED_FIELDS = (
    "instrument_id",
    "as_of_date",
    "float_shares",
    "total_shares",
)
_BLOCKING_QUALITY_FLAGS = {
    "SOURCE_PRICE_CHANGE_MISMATCH",
    "SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH",
    "SOURCE_ADJ_FORMULA_MISMATCH",
}
_INFORMATIONAL_QUALITY_FLAGS = {
    "SOURCE_PCT_CHANGE_SIGN_INVERTED",
    "MISSING_PRE_CLOSE",
}


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"日期必须为 YYYY-MM-DD：{value}"
        ) from exc


def _json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if hasattr(value, "item") and callable(value.item):
        try:
            return _json_safe(value.item())
        except (TypeError, ValueError):
            pass

    return value


def _record_value(record: Any, name: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(name)

    return getattr(record, name)


def _batch_value(batch: Any, name: str) -> Any:
    if isinstance(batch, Mapping):
        return batch.get(name)

    return getattr(batch, name)


def _close_enough(
    actual: Any,
    expected: Any,
    tolerance: float = 1e-6,
) -> bool:
    if actual is None or expected is None:
        return actual is expected

    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True, slots=True)
class AcceptanceThresholds:
    """TASK_011 抽样验收阈值。"""

    minimum_record_count: int = 1
    minimum_daily_bar_coverage: float = 1.0
    minimum_ownership_coverage: float = 1.0
    minimum_lineage_coverage: float = 1.0
    minimum_pending_extension_coverage: float = 1.0
    computed_mismatch_limit: int = 0

    def __post_init__(self) -> None:
        if self.minimum_record_count < 1:
            raise DataContractError(
                "minimum_record_count 必须至少为1。"
            )

        for name in (
            "minimum_daily_bar_coverage",
            "minimum_ownership_coverage",
            "minimum_lineage_coverage",
            "minimum_pending_extension_coverage",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise DataContractError(
                    f"{name} 必须在0到1之间。"
                )

        if self.computed_mismatch_limit < 0:
            raise DataContractError(
                "computed_mismatch_limit 不能为负数。"
            )


class DailyKAcceptanceAnalyzer:
    """分析标准化批次并输出可审计验收报告。"""

    def __init__(
        self,
        registration: DatasetRegistration,
        thresholds: AcceptanceThresholds | None = None,
    ) -> None:
        self.registration = registration
        self.thresholds = thresholds or AcceptanceThresholds()

    def _pending_source_fields(self) -> tuple[str, ...]:
        fields = {
            source_field
            for rule in self.registration.field_mappings
            if rule.status is MappingStatus.PENDING_CONFIRMATION
            for source_field in rule.source_fields
        }
        return tuple(sorted(fields))

    @staticmethod
    def _field_coverage(
        records: Sequence[Any],
        object_name: str,
        required_fields: Sequence[str],
    ) -> dict[str, Any]:
        expected_cell_count = len(records) * len(required_fields)
        present_cell_count = 0
        missing_examples: list[dict[str, Any]] = []
        field_present_counts = Counter()

        for record in records:
            objects = _record_value(record, "canonical_objects")
            canonical_object = objects.get(object_name)

            for field_name in required_fields:
                present = (
                    canonical_object is not None
                    and field_name in canonical_object
                    and canonical_object[field_name] is not None
                )

                if present:
                    present_cell_count += 1
                    field_present_counts[field_name] += 1
                elif len(missing_examples) < 20:
                    missing_examples.append({
                        "source_record_id": _record_value(
                            record,
                            "source_record_id",
                        ),
                        "object_name": object_name,
                        "field_name": field_name,
                    })

        coverage = (
            present_cell_count / expected_cell_count
            if expected_cell_count
            else 0.0
        )

        return {
            "object_name": object_name,
            "record_count": len(records),
            "required_fields": list(required_fields),
            "expected_cell_count": expected_cell_count,
            "present_cell_count": present_cell_count,
            "coverage": coverage,
            "field_present_counts": dict(
                sorted(field_present_counts.items())
            ),
            "missing_examples": missing_examples,
        }

    def _pending_extension_coverage(
        self,
        records: Sequence[Any],
    ) -> dict[str, Any]:
        pending_fields = self._pending_source_fields()
        expected_cell_count = len(records) * len(pending_fields)
        present_cell_count = 0
        missing_examples: list[dict[str, Any]] = []
        present_counts = Counter()

        for record in records:
            extensions = _record_value(
                record,
                "source_extensions",
            )

            for field_name in pending_fields:
                if field_name in extensions:
                    present_cell_count += 1
                    present_counts[field_name] += 1
                elif len(missing_examples) < 20:
                    missing_examples.append({
                        "source_record_id": _record_value(
                            record,
                            "source_record_id",
                        ),
                        "field_name": field_name,
                    })

        coverage = (
            present_cell_count / expected_cell_count
            if expected_cell_count
            else 1.0
        )

        return {
            "pending_field_count": len(pending_fields),
            "pending_fields": list(pending_fields),
            "expected_cell_count": expected_cell_count,
            "present_cell_count": present_cell_count,
            "coverage": coverage,
            "field_present_counts": dict(
                sorted(present_counts.items())
            ),
            "missing_examples": missing_examples,
        }

    def _lineage_coverage(
        self,
        records: Sequence[Any],
    ) -> dict[str, Any]:
        records_with_lineage = 0
        invalid_lineage_count = 0
        invalid_examples: list[dict[str, Any]] = []

        for record in records:
            lineage = _record_value(record, "lineage")

            if lineage:
                records_with_lineage += 1

            for item in lineage:
                valid = (
                    item.get("mapping_version")
                    == self.registration.mapping_version
                    and item.get("dictionary_revision")
                    == self.registration.dictionary_revision
                    and bool(item.get("canonical_field"))
                    and bool(item.get("source_fields"))
                )

                if not valid:
                    invalid_lineage_count += 1
                    if len(invalid_examples) < 20:
                        invalid_examples.append(
                            _json_safe(item)
                        )

        coverage = (
            records_with_lineage / len(records)
            if records
            else 0.0
        )

        return {
            "record_count": len(records),
            "records_with_lineage": records_with_lineage,
            "coverage": coverage,
            "invalid_lineage_count": invalid_lineage_count,
            "invalid_examples": invalid_examples,
        }

    @staticmethod
    def _computed_consistency(
        records: Sequence[Any],
    ) -> dict[str, Any]:
        checked = Counter()
        mismatches = Counter()
        examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

        def record_mismatch(
            check_name: str,
            record: Any,
            actual: Any,
            expected: Any,
        ) -> None:
            mismatches[check_name] += 1
            if len(examples[check_name]) < 10:
                examples[check_name].append({
                    "source_record_id": _record_value(
                        record,
                        "source_record_id",
                    ),
                    "actual": _json_safe(actual),
                    "expected": _json_safe(expected),
                })

        for record in records:
            objects = _record_value(record, "canonical_objects")
            daily = objects.get("DailyBar", {})
            ownership = objects.get("OwnershipSnapshot", {})

            close = daily.get("close_raw_cny")
            pre_close = daily.get("pre_close_raw_cny")
            pct_change = daily.get("pct_change_pct")

            if (
                close is not None
                and pre_close not in {None, 0}
                and pct_change is not None
            ):
                checked["pct_change_pct"] += 1
                expected = (
                    float(close) / float(pre_close) - 1
                ) * 100
                if not _close_enough(
                    pct_change,
                    expected,
                    1e-5,
                ):
                    record_mismatch(
                        "pct_change_pct",
                        record,
                        pct_change,
                        expected,
                    )

            volume_shares = daily.get("volume_shares")
            volume_lots = daily.get("volume_lots")
            if (
                volume_shares is not None
                and volume_lots is not None
            ):
                checked["volume_lots"] += 1
                expected = float(volume_shares) / 100
                if not _close_enough(
                    volume_lots,
                    expected,
                ):
                    record_mismatch(
                        "volume_lots",
                        record,
                        volume_lots,
                        expected,
                    )

            amount = daily.get("amount_cny")
            vwap = daily.get("vwap_raw_cny")
            if (
                amount is not None
                and volume_shares not in {None, 0}
                and vwap is not None
            ):
                checked["vwap_raw_cny"] += 1
                expected = (
                    float(amount) / float(volume_shares)
                )
                if not _close_enough(vwap, expected, 1e-5):
                    record_mismatch(
                        "vwap_raw_cny",
                        record,
                        vwap,
                        expected,
                    )

            float_shares = ownership.get("float_shares")
            float_cap = daily.get("float_market_cap_cny")
            if (
                close is not None
                and float_shares is not None
                and float_cap is not None
            ):
                checked["float_market_cap_cny"] += 1
                expected = float(close) * float(float_shares)
                if not _close_enough(
                    float_cap,
                    expected,
                    0.01,
                ):
                    record_mismatch(
                        "float_market_cap_cny",
                        record,
                        float_cap,
                        expected,
                    )

            total_shares = ownership.get("total_shares")
            total_cap = daily.get("total_market_cap_cny")
            if (
                close is not None
                and total_shares is not None
                and total_cap is not None
            ):
                checked["total_market_cap_cny"] += 1
                expected = float(close) * float(total_shares)
                if not _close_enough(
                    total_cap,
                    expected,
                    0.01,
                ):
                    record_mismatch(
                        "total_market_cap_cny",
                        record,
                        total_cap,
                        expected,
                    )

        return {
            "checked_counts": dict(sorted(checked.items())),
            "mismatch_counts": dict(sorted(mismatches.items())),
            "total_mismatch_count": sum(mismatches.values()),
            "mismatch_examples": {
                key: value
                for key, value in sorted(examples.items())
            },
        }

    @staticmethod
    def _quality_flag_summary(
        records: Sequence[Any],
    ) -> dict[str, Any]:
        flag_counts = Counter(
            flag
            for record in records
            for flag in _record_value(record, "quality_flags")
        )

        blocking_count = sum(
            count
            for flag, count in flag_counts.items()
            if flag in _BLOCKING_QUALITY_FLAGS
        )
        informational_count = sum(
            count
            for flag, count in flag_counts.items()
            if flag in _INFORMATIONAL_QUALITY_FLAGS
        )

        return {
            "flag_counts": dict(sorted(flag_counts.items())),
            "blocking_flag_count": blocking_count,
            "informational_flag_count": informational_count,
            "blocking_flags": sorted(_BLOCKING_QUALITY_FLAGS),
            "informational_flags": sorted(
                _INFORMATIONAL_QUALITY_FLAGS
            ),
        }

    def analyze(self, batch: Any) -> dict[str, Any]:
        records = list(_batch_value(batch, "records"))
        source_row_count = int(
            _batch_value(batch, "source_row_count")
        )
        standardized_record_count = int(
            _batch_value(batch, "standardized_record_count")
        )

        daily_coverage = self._field_coverage(
            records,
            "DailyBar",
            _DAILY_BAR_REQUIRED_FIELDS,
        )
        ownership_coverage = self._field_coverage(
            records,
            "OwnershipSnapshot",
            _OWNERSHIP_REQUIRED_FIELDS,
        )
        pending_coverage = self._pending_extension_coverage(
            records
        )
        lineage_coverage = self._lineage_coverage(records)
        computed = self._computed_consistency(records)
        quality = self._quality_flag_summary(records)

        checks = [
            {
                "check_name": "标准化记录数量",
                "passed": (
                    standardized_record_count
                    >= self.thresholds.minimum_record_count
                    and source_row_count
                    == standardized_record_count
                    == len(records)
                ),
                "blocking": True,
                "details": {
                    "source_row_count": source_row_count,
                    "standardized_record_count":
                        standardized_record_count,
                    "actual_record_count": len(records),
                    "minimum_record_count":
                        self.thresholds.minimum_record_count,
                },
            },
            {
                "check_name": "DailyBar核心字段覆盖",
                "passed": (
                    daily_coverage["coverage"]
                    >= self.thresholds.minimum_daily_bar_coverage
                ),
                "blocking": True,
                "details": daily_coverage,
            },
            {
                "check_name": "OwnershipSnapshot核心字段覆盖",
                "passed": (
                    ownership_coverage["coverage"]
                    >= self.thresholds.minimum_ownership_coverage
                ),
                "blocking": True,
                "details": ownership_coverage,
            },
            {
                "check_name": "待确认来源字段保留",
                "passed": (
                    pending_coverage["coverage"]
                    >= self.thresholds.minimum_pending_extension_coverage
                ),
                "blocking": True,
                "details": pending_coverage,
            },
            {
                "check_name": "字段血缘完整性",
                "passed": (
                    lineage_coverage["coverage"]
                    >= self.thresholds.minimum_lineage_coverage
                    and lineage_coverage[
                        "invalid_lineage_count"
                    ] == 0
                ),
                "blocking": True,
                "details": lineage_coverage,
            },
            {
                "check_name": "标准计算字段内部一致性",
                "passed": (
                    computed["total_mismatch_count"]
                    <= self.thresholds.computed_mismatch_limit
                ),
                "blocking": True,
                "details": computed,
            },
            {
                "check_name": "来源质量异常",
                "passed": quality["blocking_flag_count"] == 0,
                "blocking": True,
                "details": quality,
            },
        ]

        blocking_failures = [
            item
            for item in checks
            if item["blocking"] and not item["passed"]
        ]
        status = "PASSED" if not blocking_failures else "FAILED"

        sample_records = [
            _json_safe(
                record.to_dict()
                if hasattr(record, "to_dict")
                else record
            )
            for record in records[:10]
        ]

        return {
            "dataset_id": _batch_value(batch, "dataset_id"),
            "coverage_version": _batch_value(
                batch,
                "coverage_version",
            ),
            "mapping_version": _batch_value(
                batch,
                "mapping_version",
            ),
            "dictionary_revision": _batch_value(
                batch,
                "dictionary_revision",
            ),
            "generated_at": datetime.now().astimezone().isoformat(),
            "request": _json_safe(
                _batch_value(batch, "request")
            ),
            "source_row_count": source_row_count,
            "standardized_record_count":
                standardized_record_count,
            "batch_warnings": list(
                _batch_value(batch, "warnings")
            ),
            "daily_bar_coverage": daily_coverage,
            "ownership_coverage": ownership_coverage,
            "pending_extension_coverage": pending_coverage,
            "lineage_coverage": lineage_coverage,
            "computed_consistency": computed,
            "quality_flag_summary": quality,
            "checks": checks,
            "overall_status": status,
            "blocks_downstream": bool(blocking_failures),
            "sample_records": sample_records,
        }


def _resolve_password(
    explicit_password: str | None,
    environment_name: str,
) -> str:
    if explicit_password:
        return explicit_password

    from_environment = os.getenv(environment_name)
    if from_environment:
        return from_environment

    return getpass.getpass("请输入 DolphinDB 密码：")


def _create_adapter(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
) -> DolphinDBDataSourceAdapter:
    try:
        settings = DolphinDBConnectionSettings(
            host=host,
            port=port,
            username=username,
            password=password,
        )
    except TypeError:
        settings = DolphinDBConnectionSettings(
            host=host,
            port=port,
            user=username,
            password=password,
        )

    try:
        return DolphinDBDataSourceAdapter(settings)
    except TypeError:
        return DolphinDBDataSourceAdapter(
            connection_settings=settings
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="真实 DolphinDB 日K标准化抽样验收。"
    )
    parser.add_argument(
        "--registration",
        default="configs/datasets/a_stock_daily_k.json",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password")
    parser.add_argument(
        "--password-env",
        default="DOLPHINDB_PASSWORD",
    )
    parser.add_argument(
        "--instrument",
        action="append",
        dest="instruments",
    )
    parser.add_argument(
        "--start-date",
        type=_parse_date,
        default=_DEFAULT_START_DATE,
    )
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        default=_DEFAULT_END_DATE,
    )
    parser.add_argument(
        "--limit-per-instrument",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--output",
        default="reports/task_011_daily_k_acceptance.json",
    )
    return parser


def run_acceptance(args: argparse.Namespace) -> dict[str, Any]:
    registry = DatasetRegistry()
    registration = registry.load_json(args.registration)

    password = _resolve_password(
        args.password,
        args.password_env,
    )
    adapter = _create_adapter(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
    )
    service = DolphinDBDailyKStandardizedService(
        adapter,
        registration,
    )
    request = DailyKReadRequest(
        instrument_ids=tuple(
            args.instruments or _DEFAULT_INSTRUMENTS
        ),
        start_date=args.start_date,
        end_date=args.end_date,
        limit_per_instrument=args.limit_per_instrument,
    )
    batch = service.read(request)
    report = DailyKAcceptanceAnalyzer(
        registration
    ).analyze(batch)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            _json_safe(report),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = run_acceptance(args)
    except Exception as exc:
        print(f"日K标准化抽样验收失败：{exc}")
        return 1

    print("=== 日K标准化抽样验收完成 ===")
    print(f"数据集：{report['dataset_id']}")
    print(f"覆盖版本：{report['coverage_version']}")
    print(
        "标准化记录数："
        f"{report['standardized_record_count']}"
    )
    print(
        "DailyBar核心字段覆盖率："
        f"{report['daily_bar_coverage']['coverage']:.4%}"
    )
    print(
        "OwnershipSnapshot核心字段覆盖率："
        f"{report['ownership_coverage']['coverage']:.4%}"
    )
    print(
        "待确认字段保留率："
        f"{report['pending_extension_coverage']['coverage']:.4%}"
    )
    print(
        "计算字段不一致数："
        f"{report['computed_consistency']['total_mismatch_count']}"
    )
    print(
        "阻断质量标记数："
        f"{report['quality_flag_summary']['blocking_flag_count']}"
    )
    print(f"整体状态：{report['overall_status']}")
    print(f"阻断下游：{report['blocks_downstream']}")
    print(f"完整报告：{args.output}")

    return 0 if report["overall_status"] == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
