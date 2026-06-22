"""DolphinDB 数据集覆盖边界与增量更新准备核验。

本模块用于：
1. 核对数据库实际最大日期与人工声明的数据截止日期；
2. 明确数据集是快照数据，而不是实时数据；
3. 可选盘点尚未导入的源文件和导入日志；
4. 输出可被后续数据集注册表使用的覆盖边界清单。

本模块只读 DolphinDB，不导入、不更新、不删除任何数据。
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

from .data_contracts import (
    DataContractError,
    QualityStatus,
)
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from .dolphindb_daily_profile import _first_record
from .dolphindb_probe import resolve_password


class DatasetMode(str, Enum):
    """当前支持的数据集运行模式。"""

    SNAPSHOT = "SNAPSHOT"


_FILENAME_DATE_PATTERNS = (
    re.compile(
        r"(?<!\d)(20\d{2})[-_.年](\d{1,2})[-_.月](\d{1,2})日?(?!\d)"
    ),
    re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)"),
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, float) and (
        math.isnan(value) or math.isinf(value)
    ):
        return None

    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            return _json_safe(item_method())
        except (TypeError, ValueError):
            pass

    return value


def _as_date(value: Any, field_name: str) -> date:
    """把常见日期值转换为 date。"""

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if value is None:
        raise DataContractError(f"{field_name} 不能为空。")

    text = str(value).strip()

    if not text:
        raise DataContractError(f"{field_name} 不能为空。")

    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError as exc:
            raise DataContractError(
                f"{field_name} 不是合法日期：{value!r}"
            ) from exc


def _extract_date_from_filename(filename: str) -> date | None:
    """从文件名中提取 YYYYMMDD 或 YYYY-MM-DD 等日期。"""

    for pattern in _FILENAME_DATE_PATTERNS:
        match = pattern.search(filename)

        if match is None:
            continue

        try:
            return date(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
        except ValueError:
            continue

    return None


@dataclass(slots=True)
class DatasetCoverageReport:
    """一个 DolphinDB 数据集的覆盖边界报告。"""

    dataset_id: str
    dataset_mode: DatasetMode
    database_uri: str
    table_name: str
    date_field: str
    entity_field: str | None
    declared_cutoff_date: date
    generated_at: datetime
    database_summary: dict[str, Any]
    coverage_evaluation: dict[str, Any]
    source_inventory: list[dict[str, Any]]
    import_log_inventory: list[dict[str, Any]]
    checks: list[dict[str, Any]] = field(default_factory=list)
    overall_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    blocks_downstream: bool = True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(self)


class DolphinDBDatasetCoverageVerifier:
    """核验快照数据集的声明截止日期和实际覆盖范围。"""

    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        *,
        dataset_id: str,
        database_uri: str,
        table_name: str,
        date_field: str,
        entity_field: str | None,
        declared_cutoff_date: date,
        source_dirs: Sequence[str] = (),
        import_logs: Sequence[str] = (),
    ) -> None:
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise DataContractError("dataset_id 不能为空。")

        adapter._validate_database_uri(database_uri)
        adapter._validate_table_name(table_name)
        adapter._validate_table_name(date_field)

        if entity_field is not None:
            adapter._validate_table_name(entity_field)

        self.adapter = adapter
        self.dataset_id = dataset_id.strip()
        self.database_uri = database_uri
        self.table_name = table_name
        self.date_field = date_field
        self.entity_field = entity_field
        self.declared_cutoff_date = declared_cutoff_date
        self.source_dirs = [str(item) for item in source_dirs]
        self.import_logs = [str(item) for item in import_logs]

    @property
    def _table_ref(self) -> str:
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )

    def _query_database_summary(self) -> dict[str, Any]:
        """分别查询日期范围和实体数量，避免嵌套聚合。"""

        summary_result = self.adapter.run_readonly_query(
            "select\n    "
            "count(*) as row_count,\n    "
            f"min({self.date_field}) as min_data_date,\n    "
            f"max({self.date_field}) as max_data_date\n"
            f"from {self._table_ref}"
        )
        summary = _first_record(summary_result)

        if self.entity_field is None:
            return summary

        entity_result = self.adapter.run_readonly_query(
            "select count(*) as entity_count\n"
            "from (\n"
            f"    select distinct {self.entity_field}\n"
            f"    from {self._table_ref}\n"
            ")"
        )
        entity_summary = _first_record(entity_result)
        summary["entity_count"] = entity_summary.get(
            "entity_count"
        )
        return summary

    @staticmethod
    def _inventory_source_dir(
        directory_text: str,
    ) -> dict[str, Any]:
        directory = Path(directory_text).expanduser()

        if not directory.exists():
            return {
                "path": str(directory),
                "exists": False,
                "is_directory": False,
                "file_count": 0,
                "latest_filename_date": None,
                "newest_modified_at": None,
                "extensions": {},
                "errors": ["目录不存在。"],
            }

        if not directory.is_dir():
            return {
                "path": str(directory),
                "exists": True,
                "is_directory": False,
                "file_count": 0,
                "latest_filename_date": None,
                "newest_modified_at": None,
                "extensions": {},
                "errors": ["路径不是目录。"],
            }

        file_count = 0
        latest_filename_date: date | None = None
        newest_mtime: datetime | None = None
        extensions: Counter[str] = Counter()
        errors: list[str] = []

        try:
            iterator = directory.rglob("*")

            for path in iterator:
                try:
                    if not path.is_file():
                        continue

                    file_count += 1
                    extensions[path.suffix.lower() or "<无扩展名>"] += 1

                    filename_date = _extract_date_from_filename(
                        path.name
                    )
                    if (
                        filename_date is not None
                        and (
                            latest_filename_date is None
                            or filename_date > latest_filename_date
                        )
                    ):
                        latest_filename_date = filename_date

                    modified_at = datetime.fromtimestamp(
                        path.stat().st_mtime,
                        tz=timezone.utc,
                    )
                    if (
                        newest_mtime is None
                        or modified_at > newest_mtime
                    ):
                        newest_mtime = modified_at
                except OSError as exc:
                    errors.append(f"{path}: {exc}")
        except OSError as exc:
            errors.append(str(exc))

        return {
            "path": str(directory),
            "exists": True,
            "is_directory": True,
            "file_count": file_count,
            "latest_filename_date": latest_filename_date,
            "newest_modified_at": newest_mtime,
            "extensions": dict(sorted(extensions.items())),
            "errors": errors[:20],
        }

    @staticmethod
    def _inventory_import_log(
        log_text: str,
    ) -> dict[str, Any]:
        path = Path(log_text).expanduser()

        if not path.exists():
            return {
                "path": str(path),
                "exists": False,
                "size_bytes": None,
                "modified_at": None,
                "last_nonempty_line": None,
                "error": "日志文件不存在。",
            }

        if not path.is_file():
            return {
                "path": str(path),
                "exists": True,
                "size_bytes": None,
                "modified_at": None,
                "last_nonempty_line": None,
                "error": "日志路径不是文件。",
            }

        try:
            stat = path.stat()
            last_line: str | None = None

            with path.open(
                "r",
                encoding="utf-8-sig",
                errors="replace",
            ) as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped[:500]

            return {
                "path": str(path),
                "exists": True,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ),
                "last_nonempty_line": last_line,
                "error": None,
            }
        except OSError as exc:
            return {
                "path": str(path),
                "exists": True,
                "size_bytes": None,
                "modified_at": None,
                "last_nonempty_line": None,
                "error": str(exc),
            }

    def collect(self) -> DatasetCoverageReport:
        """执行覆盖边界与可选源文件盘点。"""

        database_summary = self._query_database_summary()
        db_min_date = _as_date(
            database_summary.get("min_data_date"),
            "min_data_date",
        )
        db_max_date = _as_date(
            database_summary.get("max_data_date"),
            "max_data_date",
        )

        source_inventory = [
            self._inventory_source_dir(item)
            for item in self.source_dirs
        ]
        import_log_inventory = [
            self._inventory_import_log(item)
            for item in self.import_logs
        ]

        latest_source_date: date | None = None

        for item in source_inventory:
            value = item.get("latest_filename_date")

            if value is None:
                continue

            candidate = _as_date(
                value,
                "latest_filename_date",
            )
            if (
                latest_source_date is None
                or candidate > latest_source_date
            ):
                latest_source_date = candidate

        checks: list[dict[str, Any]] = []
        blocks_downstream = False

        if db_max_date == self.declared_cutoff_date:
            cutoff_status = QualityStatus.PASSED
            cutoff_message = (
                "数据库最大日期与人工声明的快照截止日期一致。"
            )
        elif db_max_date < self.declared_cutoff_date:
            cutoff_status = QualityStatus.FAILED
            cutoff_message = (
                "数据库最大日期早于人工声明截止日期，"
                "声明范围内可能缺少数据。"
            )
            blocks_downstream = True
        else:
            cutoff_status = QualityStatus.WARNING
            cutoff_message = (
                "数据库最大日期晚于人工声明截止日期，"
                "需要更新数据集覆盖清单。"
            )

        checks.append(
            {
                "check_name": "快照截止日期一致性",
                "status": cutoff_status,
                "blocking": cutoff_status is QualityStatus.FAILED,
                "details": {
                    "declared_cutoff_date":
                        self.declared_cutoff_date,
                    "database_max_date": db_max_date,
                },
                "description": cutoff_message,
            }
        )

        pending_import = (
            latest_source_date is not None
            and latest_source_date > db_max_date
        )
        checks.append(
            {
                "check_name": "源文件待导入日期检查",
                "status": (
                    QualityStatus.WARNING
                    if pending_import
                    else QualityStatus.PASSED
                ),
                "blocking": False,
                "details": {
                    "latest_source_filename_date":
                        latest_source_date,
                    "database_max_date": db_max_date,
                    "pending_import": pending_import,
                    "source_inventory_provided":
                        bool(source_inventory),
                },
                "description": (
                    "检测到文件名日期晚于数据库最大日期，"
                    "可能存在尚未导入的数据。"
                    if pending_import
                    else (
                        "未发现文件名日期晚于数据库最大日期。"
                        if source_inventory
                        else "本次未提供源文件目录，仅核验数据库边界。"
                    )
                ),
            }
        )

        lag_days = (
            datetime.now(timezone.utc).date() - db_max_date
        ).days

        coverage_evaluation = {
            "dataset_mode": DatasetMode.SNAPSHOT,
            "declared_cutoff_date": self.declared_cutoff_date,
            "database_min_date": db_min_date,
            "database_max_date": db_max_date,
            "database_matches_declared_cutoff":
                db_max_date == self.declared_cutoff_date,
            "calendar_lag_days_informational": lag_days,
            "calendar_lag_is_blocking": False,
            "allowed_request_start_date": db_min_date,
            "allowed_request_end_date": db_max_date,
            "pending_import_detected": pending_import,
            "latest_source_filename_date": latest_source_date,
            "coverage_version": (
                f"{self.dataset_id}@{db_max_date.isoformat()}"
            ),
        }

        statuses = {
            item["status"]
            for item in checks
        }

        if QualityStatus.FAILED in statuses:
            overall_status = QualityStatus.FAILED
        elif QualityStatus.WARNING in statuses:
            overall_status = QualityStatus.WARNING
        else:
            overall_status = QualityStatus.PASSED

        return DatasetCoverageReport(
            dataset_id=self.dataset_id,
            dataset_mode=DatasetMode.SNAPSHOT,
            database_uri=self.database_uri,
            table_name=self.table_name,
            date_field=self.date_field,
            entity_field=self.entity_field,
            declared_cutoff_date=self.declared_cutoff_date,
            generated_at=_utc_now(),
            database_summary=database_summary,
            coverage_evaluation=coverage_evaluation,
            source_inventory=source_inventory,
            import_log_inventory=import_log_inventory,
            checks=checks,
            overall_status=overall_status,
            blocks_downstream=blocks_downstream,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "核验DolphinDB快照数据集的声明截止日期和实际覆盖边界。"
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--database-uri", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--date-field", required=True)
    parser.add_argument("--entity-field")
    parser.add_argument(
        "--declared-cutoff-date",
        required=True,
        help="人工确认的数据快照截止日期，格式YYYY-MM-DD。",
    )
    parser.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help="可重复指定尚未或已经导入的源文件目录。",
    )
    parser.add_argument(
        "--import-log",
        action="append",
        default=[],
        help="可重复指定导入成功或失败日志文件。",
    )
    parser.add_argument(
        "--output",
        default="reports/task_008_dataset_coverage.json",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cutoff_date = _as_date(
            args.declared_cutoff_date,
            "declared_cutoff_date",
        )
        settings = DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=resolve_password(),
        )
        adapter = DolphinDBDataSourceAdapter(settings=settings)
        health = adapter.health_check()

        if health.blocks_downstream:
            print(f"健康检查失败：{health.description}")
            return 1

        report = DolphinDBDatasetCoverageVerifier(
            adapter=adapter,
            dataset_id=args.dataset_id,
            database_uri=args.database_uri,
            table_name=args.table,
            date_field=args.date_field,
            entity_field=args.entity_field,
            declared_cutoff_date=cutoff_date,
            source_dirs=args.source_dir,
            import_logs=args.import_log,
        ).collect()
    except DataContractError as exc:
        print(f"数据覆盖边界核验失败：{exc}")
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    evaluation = report.coverage_evaluation

    print("=== 数据集覆盖边界核验完成 ===")
    print(f"数据集：{report.dataset_id}")
    print(f"模式：{report.dataset_mode.value}")
    print(
        "数据库范围："
        f"{evaluation['database_min_date']} "
        f"至 {evaluation['database_max_date']}"
    )
    print(f"声明截止日期：{report.declared_cutoff_date}")
    print(
        "截止日期一致："
        f"{evaluation['database_matches_declared_cutoff']}"
    )
    print(
        "日历滞后天数（仅信息）："
        f"{evaluation['calendar_lag_days_informational']}"
    )
    print(
        "检测到待导入源文件："
        f"{evaluation['pending_import_detected']}"
    )
    print(f"覆盖版本：{evaluation['coverage_version']}")
    print(f"整体状态：{report.overall_status.value}")
    print(f"阻断下游：{report.blocks_downstream}")
    print(f"完整报告：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
