"""TASK_016B 七类日线资金 DolphinDB Raw 层建库与导入。

安全边界：
1. contract 模式只校验本地合同和DDL计划；
2. probe 模式只读探测 DolphinDB，不创建或修改对象；
3. create 模式只创建缺失数据库/表，不删除或覆盖已有对象；
4. import 模式重新运行 TASK_016A 预导入门禁后逐文件写入；
5. 覆盖不足的文件只写隔离日志，不进入主Raw表；
6. 主表以 dataset_id + source_file_sha256 + source_row_number
   作为TSDB幂等排序键，keepDuplicates=LAST；
7. 不把source_file_mtime伪装成available_at。
"""
from __future__ import annotations

import csv
import getpass
import importlib
import json
import os
import re
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from .daily_funds_ingest import (
    DailyFundsContract,
    DailyFundsIngestError,
    DatasetSpec,
    _trim_trailing_delimiter_cell,
    deduplicate_headers,
    discover_snapshot_directories,
    file_sha256,
    header_fingerprint,
    iter_source_rows,
    load_daily_funds_contract,
    normalize_row,
    parse_snapshot_date_from_path,
    run_daily_funds_preflight,
    strip_cell,
    validate_daily_funds_contract,
)


DATABASE_URI = "dfs://A_STOCK_DAILY_FUNDS_DB"
PARTITION_START_MONTH = "1990.01M"
PARTITION_END_MONTH = "2100.12M"

TABLE_NAMES = {
    "security_snapshot": "security_market_snapshot_raw",
    "classification_snapshot": "classification_market_snapshot_raw",
    "money_flow_snapshot": "money_flow_snapshot_raw",
    "ingest_batch": "ingest_batch_log",
    "ingest_file": "ingest_file_log",
    "quarantine_file": "quarantine_file_log",
}

FAMILY_TO_TABLE = {
    "security_snapshot": TABLE_NAMES["security_snapshot"],
    "classification_snapshot": TABLE_NAMES["classification_snapshot"],
    "money_flow_snapshot": TABLE_NAMES["money_flow_snapshot"],
}

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SYMBOL_LITERAL_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


class DailyFundsDolphinDBError(RuntimeError):
    """TASK_016B 建库、写入或验收错误。"""


class SessionProtocol(Protocol):
    """DolphinDB会话所需最小接口。"""

    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> Any:
        """建立连接。"""

    def run(self, script: str) -> Any:
        """执行DolphinDB脚本。"""


class AppenderProtocol(Protocol):
    """DolphinDB TableAppender 所需最小接口。"""

    def append(self, data: pd.DataFrame) -> Any:
        """追加DataFrame。"""


SessionFactory = Callable[[], SessionProtocol]
AppenderFactory = Callable[
    [str, str, SessionProtocol], AppenderProtocol
]


@dataclass(frozen=True, slots=True)
class DolphinDBWriteSettings:
    """DolphinDB写入连接参数。"""

    host: str = "127.0.0.1"
    port: int = 8848
    username: str = "admin"
    password: str = ""
    database_uri: str = DATABASE_URI

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise DailyFundsDolphinDBError("host不能为空。")
        if not 1 <= int(self.port) <= 65535:
            raise DailyFundsDolphinDBError(
                "port必须在1到65535之间。"
            )
        if not self.username.strip():
            raise DailyFundsDolphinDBError(
                "username不能为空。"
            )
        if not self.password:
            raise DailyFundsDolphinDBError(
                "DolphinDB密码不能为空。"
            )
        if not re.fullmatch(
            r"dfs://[A-Za-z0-9_.-]+",
            self.database_uri,
        ):
            raise DailyFundsDolphinDBError(
                "database_uri必须使用dfs://数据库名格式。"
            )


COMMON_COLUMNS = (
    ("dataset_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("snapshot_phase", "SYMBOL"),
    ("schema_version", "SYMBOL"),
    ("entity_key", "STRING"),
    ("source_row_number", "INT"),
    ("source_file_name", "STRING"),
    ("source_file_relative_path", "STRING"),
    ("source_file_size_bytes", "LONG"),
    ("source_file_mtime_utc", "TIMESTAMP"),
    ("source_file_sha256", "SYMBOL"),
    ("row_sha256", "STRING"),
    ("ingest_batch_id", "SYMBOL"),
    ("ingested_at_utc", "TIMESTAMP"),
    ("quality_status", "SYMBOL"),
    ("raw_row_json", "STRING"),
)

SECURITY_COLUMNS = COMMON_COLUMNS + (
    ("instrument_id", "SYMBOL"),
    ("market_candidate", "SYMBOL"),
    ("instrument_name", "STRING"),
    ("last_price", "DOUBLE"),
    ("pct_change", "DOUBLE"),
    ("price_change", "DOUBLE"),
    ("total_volume_lot", "DOUBLE"),
    ("current_volume_lot", "DOUBLE"),
    ("bid_price", "DOUBLE"),
    ("ask_price", "DOUBLE"),
    ("speed_pct", "DOUBLE"),
    ("turnover_pct", "DOUBLE"),
    ("amount_cny", "DOUBLE"),
    ("pe_dynamic", "DOUBLE"),
    ("industry_name", "STRING"),
    ("high_price", "DOUBLE"),
    ("low_price", "DOUBLE"),
    ("open_price", "DOUBLE"),
    ("prev_close", "DOUBLE"),
    ("amplitude_pct", "DOUBLE"),
    ("volume_ratio", "DOUBLE"),
    ("order_imbalance_pct", "DOUBLE"),
    ("order_imbalance_lot", "DOUBLE"),
    ("avg_price", "DOUBLE"),
    ("inner_volume_lot", "DOUBLE"),
    ("outer_volume_lot", "DOUBLE"),
    ("inner_outer_ratio", "DOUBLE"),
    ("bid1_volume_lot", "DOUBLE"),
    ("ask1_volume_lot", "DOUBLE"),
    ("pb", "DOUBLE"),
    ("total_shares", "DOUBLE"),
    ("total_market_cap_cny", "DOUBLE"),
    ("float_shares", "DOUBLE"),
    ("float_market_cap_cny", "DOUBLE"),
    ("return_3d_pct", "DOUBLE"),
    ("return_6d_pct", "DOUBLE"),
    ("turnover_3d_pct", "DOUBLE"),
    ("turnover_6d_pct", "DOUBLE"),
    ("consecutive_up_days", "INT"),
    ("return_month_pct", "DOUBLE"),
    ("return_ytd_pct", "DOUBLE"),
    ("return_1m_pct", "DOUBLE"),
    ("return_1y_pct", "DOUBLE"),
    ("listing_date_raw", "STRING"),
    ("speed_5m_pct", "DOUBLE"),
    ("return_20d_pct", "DOUBLE"),
    ("source_volume_unit", "SYMBOL"),
    ("canonical_volume_transform", "SYMBOL"),
    ("source_amount_unit", "SYMBOL"),
)

CLASSIFICATION_COLUMNS = COMMON_COLUMNS + (
    ("classification_type", "SYMBOL"),
    ("node_name_raw", "STRING"),
    ("pct_change", "DOUBLE"),
    ("return_3d_pct", "DOUBLE"),
    ("speed_pct", "DOUBLE"),
    ("leading_stock_name", "STRING"),
    ("up_count", "INT"),
    ("down_count", "INT"),
    ("breadth_ratio", "DOUBLE"),
    ("breadth_status", "SYMBOL"),
    ("limit_up_count", "INT"),
    ("turnover_pct", "DOUBLE"),
    ("volume_ratio", "DOUBLE"),
    ("turnover_3d_pct", "DOUBLE"),
    ("return_5d_pct", "DOUBLE"),
    ("return_10d_pct", "DOUBLE"),
    ("return_20d_pct", "DOUBLE"),
    ("volume_lot", "DOUBLE"),
    ("amount_cny", "DOUBLE"),
    ("total_market_cap_cny", "DOUBLE"),
    ("float_market_cap_cny", "DOUBLE"),
    ("average_return_pct", "DOUBLE"),
    ("average_shares", "DOUBLE"),
    ("pe_ratio", "DOUBLE"),
    ("source_volume_unit", "SYMBOL"),
    ("canonical_volume_transform", "SYMBOL"),
    ("source_amount_unit", "SYMBOL"),
)

MONEY_FLOW_COLUMNS = COMMON_COLUMNS + (
    ("instrument_id", "SYMBOL"),
    ("market_candidate", "SYMBOL"),
    ("instrument_name", "STRING"),
    ("last_price", "DOUBLE"),
    ("pct_change", "DOUBLE"),
    ("main_net_inflow_cny", "DOUBLE"),
    ("auction_net_inflow_cny", "DOUBLE"),
    ("super_large_inflow_cny", "DOUBLE"),
    ("super_large_outflow_cny", "DOUBLE"),
    ("super_large_net_cny", "DOUBLE"),
    ("super_large_net_ratio_pct", "DOUBLE"),
    ("large_inflow_cny", "DOUBLE"),
    ("large_outflow_cny", "DOUBLE"),
    ("large_net_cny", "DOUBLE"),
    ("large_net_ratio_pct", "DOUBLE"),
    ("medium_inflow_cny", "DOUBLE"),
    ("medium_outflow_cny", "DOUBLE"),
    ("medium_net_cny", "DOUBLE"),
    ("medium_net_ratio_pct", "DOUBLE"),
    ("small_inflow_cny", "DOUBLE"),
    ("small_outflow_cny", "DOUBLE"),
    ("small_net_cny", "DOUBLE"),
    ("small_net_ratio_pct", "DOUBLE"),
    ("source_amount_unit", "SYMBOL"),
    ("outflow_sign_policy", "SYMBOL"),
)

INGEST_BATCH_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("batch_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("status", "SYMBOL"),
    ("scan_root", "STRING"),
    ("contract_version", "STRING"),
    ("preflight_status", "SYMBOL"),
    ("source_file_count", "INT"),
    ("ready_file_count", "INT"),
    ("quarantined_file_count", "INT"),
    ("blocked_file_count", "INT"),
    ("planned_row_count", "LONG"),
    ("inserted_row_count", "LONG"),
    ("skipped_row_count", "LONG"),
    ("failed_file_count", "INT"),
    ("message", "STRING"),
)

INGEST_FILE_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("dataset_id", "SYMBOL"),
    ("family", "SYMBOL"),
    ("source_file_name", "STRING"),
    ("source_file_sha256", "SYMBOL"),
    ("schema_version", "SYMBOL"),
    ("row_count", "LONG"),
    ("existing_row_count_before", "LONG"),
    ("inserted_row_count", "LONG"),
    ("final_row_count", "LONG"),
    ("status", "SYMBOL"),
    ("message", "STRING"),
)

QUARANTINE_FILE_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("dataset_id", "SYMBOL"),
    ("source_file_name", "STRING"),
    ("source_file_sha256", "SYMBOL"),
    ("row_count", "LONG"),
    ("reason_code", "SYMBOL"),
    ("reason_detail", "STRING"),
    ("reference_dataset_id", "SYMBOL"),
    ("coverage_ratio", "DOUBLE"),
    ("minimum_ratio", "DOUBLE"),
)

TABLE_SCHEMAS = {
    TABLE_NAMES["security_snapshot"]: SECURITY_COLUMNS,
    TABLE_NAMES["classification_snapshot"]: CLASSIFICATION_COLUMNS,
    TABLE_NAMES["money_flow_snapshot"]: MONEY_FLOW_COLUMNS,
    TABLE_NAMES["ingest_batch"]: INGEST_BATCH_COLUMNS,
    TABLE_NAMES["ingest_file"]: INGEST_FILE_COLUMNS,
    TABLE_NAMES["quarantine_file"]: QUARANTINE_FILE_COLUMNS,
}

TABLE_DEFINITIONS = {
    TABLE_NAMES["security_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["classification_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["money_flow_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["ingest_batch"]: {
        "partition_column": "batch_month",
        "sort_columns": ("ingest_batch_id", "logged_at"),
        "keep_duplicates": "ALL",
    },
    TABLE_NAMES["ingest_file"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "ingest_batch_id",
            "source_file_sha256",
            "logged_at",
        ),
        "keep_duplicates": "ALL",
    },
    TABLE_NAMES["quarantine_file"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "ingest_batch_id",
            "source_file_sha256",
            "logged_at",
        ),
        "keep_duplicates": "ALL",
    },
}


def _validate_identifier(value: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise DailyFundsDolphinDBError(
            f"非法DolphinDB标识符：{value!r}"
        )
    return value


def _symbol_literal(value: str) -> str:
    if not SYMBOL_LITERAL_RE.fullmatch(value):
        raise DailyFundsDolphinDBError(
            f"不能安全构造SYMBOL字面量：{value!r}"
        )
    return f"`{value}"


def _schema_table_expression(
    columns: Sequence[tuple[str, str]],
) -> str:
    names = ",".join(
        f"`{_validate_identifier(name)}" for name, _ in columns
    )
    types = ",".join(data_type for _, data_type in columns)
    return f"table(1:0, [{names}], [{types}])"


def build_create_database_script(
    database_uri: str = DATABASE_URI,
) -> str:
    """生成幂等、非破坏性的DolphinDB建库建表脚本。"""
    if not re.fullmatch(
        r"dfs://[A-Za-z0-9_.-]+",
        database_uri,
    ):
        raise DailyFundsDolphinDBError(
            "database_uri格式非法。"
        )

    lines = [
        f'dbPath = "{database_uri}"',
        "if(!existsDatabase(dbPath)){",
        (
            "    db = database("
            f"dbPath, VALUE, "
            f"{PARTITION_START_MONTH}..{PARTITION_END_MONTH}, "
            ', "TSDB")'
        ),
        "}else{",
        "    db = database(dbPath)",
        "}",
    ]

    for index, (table_name, columns) in enumerate(
        TABLE_SCHEMAS.items(),
        start=1,
    ):
        definition = TABLE_DEFINITIONS[table_name]
        schema_var = f"schema_{index}"
        partition_column = definition["partition_column"]
        sort_columns = ",".join(
            f"`{_validate_identifier(item)}"
            for item in definition["sort_columns"]
        )
        keep_duplicates = definition["keep_duplicates"]
        lines.extend(
            [
                f"if(!existsTable(dbPath, `{table_name})){{",
                (
                    f"    {schema_var} = "
                    f"{_schema_table_expression(columns)}"
                ),
                (
                    "    db.createPartitionedTable("
                    f"{schema_var}, `{table_name}, "
                    f"`{partition_column}, , "
                    f"[{sort_columns}], {keep_duplicates})"
                ),
                "}",
            ]
        )

    lines.append(
        "tableNames = "
        + "[" + ",".join(
            f"`{name}" for name in TABLE_SCHEMAS
        ) + "]"
    )
    lines.append(
        "tableExists = each(existsTable{dbPath}, tableNames)"
    )
    lines.append(
        "table(tableNames as table_name, "
        "tableExists as table_exists)"
    )
    return "\n".join(lines)


def validate_local_contract(
    contract_path: Path,
) -> dict[str, Any]:
    """不连接DolphinDB，验证来源合同与物理Schema计划。"""
    contract = load_daily_funds_contract(contract_path)
    contract_result = validate_daily_funds_contract(contract)

    issues = list(contract_result.get("issues", []))
    planned_tables = dict(
        contract.database_plan.get(
            "physical_tables",
            {},
        )
    )
    for plan_key, expected_table in TABLE_NAMES.items():
        actual = planned_tables.get(plan_key)
        if actual != expected_table:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PHYSICAL_TABLE_PLAN_MISMATCH",
                    "plan_key": plan_key,
                    "expected": expected_table,
                    "actual": actual,
                }
            )

    for table_name, columns in TABLE_SCHEMAS.items():
        names = [name for name, _ in columns]
        if len(names) != len(set(names)):
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "DUPLICATE_PHYSICAL_COLUMN",
                    "table_name": table_name,
                }
            )
        definition = TABLE_DEFINITIONS[table_name]
        if definition["partition_column"] not in names:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PARTITION_COLUMN_MISSING",
                    "table_name": table_name,
                }
            )
        if any(
            item not in names
            for item in definition["sort_columns"]
        ):
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "SORT_COLUMN_MISSING",
                    "table_name": table_name,
                }
            )

    ddl = build_create_database_script(
        str(
            contract.database_plan.get(
                "database_uri",
                DATABASE_URI,
            )
        )
    )
    return {
        "task_id": "TASK_016B",
        "mode": "CONTRACT",
        "contract_version": contract.contract_version,
        "dataset_count": len(contract.datasets),
        "physical_table_count": len(TABLE_SCHEMAS),
        "main_raw_table_count": len(FAMILY_TO_TABLE),
        "database_uri": contract.database_plan.get(
            "database_uri"
        ),
        "partition_domain": (
            f"{PARTITION_START_MONTH}.."
            f"{PARTITION_END_MONTH}"
        ),
        "overall_status": (
            "PASSED"
            if not any(
                item.get("severity") == "ERROR"
                for item in issues
            )
            else "FAILED"
        ),
        "issues": issues,
        "ddl_sha256": hashlib_sha256_text(ddl),
    }


def hashlib_sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _default_session_factory() -> SessionProtocol:
    try:
        ddb = importlib.import_module("dolphindb")
    except ImportError as exc:
        raise DailyFundsDolphinDBError(
            "未安装dolphindb Python客户端。"
        ) from exc
    session_class = getattr(ddb, "Session", None)
    if session_class is not None:
        return session_class()
    legacy_factory = getattr(ddb, "session", None)
    if legacy_factory is None:
        raise DailyFundsDolphinDBError(
            "dolphindb包没有Session/session入口。"
        )
    return legacy_factory()


def _default_appender_factory(
    database_uri: str,
    table_name: str,
    session: SessionProtocol,
) -> AppenderProtocol:
    try:
        ddb = importlib.import_module("dolphindb")
    except ImportError as exc:
        raise DailyFundsDolphinDBError(
            "未安装dolphindb Python客户端。"
        ) from exc

    appender_class = getattr(ddb, "TableAppender", None)
    if appender_class is None:
        appender_class = getattr(ddb, "tableAppender", None)
    if appender_class is None:
        raise DailyFundsDolphinDBError(
            "dolphindb包不支持TableAppender/tableAppender。"
        )
    return appender_class(
        dbPath=database_uri,
        tableName=table_name,
        ddbSession=session,
        action="fitColumnType",
    )


def connect_session(
    settings: DolphinDBWriteSettings,
    session_factory: SessionFactory = _default_session_factory,
) -> SessionProtocol:
    session = session_factory()
    try:
        session.connect(
            settings.host,
            int(settings.port),
            settings.username,
            settings.password,
        )
    except Exception as exc:
        raise DailyFundsDolphinDBError(
            f"DolphinDB连接失败：{exc}"
        ) from exc
    try:
        result = session.run("1 + 1")
    except Exception as exc:
        raise DailyFundsDolphinDBError(
            f"DolphinDB健康检查失败：{exc}"
        ) from exc
    if int(result) != 2:
        raise DailyFundsDolphinDBError(
            f"DolphinDB健康检查返回异常：{result!r}"
        )
    return session


def _to_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return bool(int(value))
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


def _default_runtime_info() -> dict[str, Any]:
    try:
        ddb = importlib.import_module("dolphindb")
        return {
            "python_client_version": str(
                getattr(ddb, "__version__", "UNKNOWN")
            ),
            "table_appender_available": bool(
                getattr(ddb, "TableAppender", None)
                or getattr(ddb, "tableAppender", None)
            ),
        }
    except ImportError:
        return {
            "python_client_version": "NOT_INSTALLED",
            "table_appender_available": False,
        }


def probe_dolphindb_environment(
    settings: DolphinDBWriteSettings,
    *,
    session_factory: SessionFactory = _default_session_factory,
    runtime_info_provider: Callable[
        [], dict[str, Any]
    ] = _default_runtime_info,
) -> dict[str, Any]:
    """只读探测服务器和目标数据库状态。"""
    session = connect_session(settings, session_factory)
    try:
        server_version = session.run("version()")
    except Exception as exc:
        server_version = f"UNAVAILABLE:{type(exc).__name__}:{exc}"

    database_exists = _to_bool(
        session.run(
            f'existsDatabase("{settings.database_uri}")'
        )
    )
    table_status: dict[str, bool] = {}
    for table_name in TABLE_SCHEMAS:
        table_status[table_name] = _to_bool(
            session.run(
                f'existsTable("{settings.database_uri}", '
                f"`{table_name})"
            )
        )

    runtime_info = runtime_info_provider()
    client_version = runtime_info.get(
        "python_client_version",
        "UNKNOWN",
    )
    appender_available = bool(
        runtime_info.get(
            "table_appender_available",
            False,
        )
    )

    if not database_exists:
        readiness = "READY_TO_CREATE"
    elif all(table_status.values()):
        readiness = "READY_TO_VALIDATE_EXISTING_SCHEMA"
    elif any(table_status.values()):
        readiness = "REVIEW_PARTIAL_EXISTING_SCHEMA"
    else:
        readiness = "READY_TO_CREATE_TABLES_IN_EXISTING_DB"

    return {
        "task_id": "TASK_016B",
        "mode": "PROBE",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "host": settings.host,
        "port": settings.port,
        "username": settings.username,
        "database_uri": settings.database_uri,
        "server_version": str(server_version),
        "python_client_version": str(client_version),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "table_appender_available": appender_available,
        "database_exists": database_exists,
        "target_table_status": table_status,
        "readiness": readiness,
        "overall_status": (
            "PASSED"
            if appender_available
            and readiness
            != "REVIEW_PARTIAL_EXISTING_SCHEMA"
            else "REVIEW_REQUIRED"
        ),
        "safety": [
            "本次PROBE只执行健康检查、版本查询和exists检查。",
            "未创建、删除或修改数据库和表。",
            "未读取或写入本地日线资金源文件。",
        ],
    }


def _normalize_coldefs(result: Any) -> list[dict[str, str]]:
    if result is None:
        return []
    if isinstance(result, list):
        rows = result
    else:
        to_dict = getattr(result, "to_dict", None)
        if not callable(to_dict):
            raise DailyFundsDolphinDBError(
                "无法解析DolphinDB schema.colDefs返回值。"
            )
        try:
            rows = to_dict(orient="records")
        except TypeError:
            rows = to_dict("records")
    normalized: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise DailyFundsDolphinDBError(
                "schema.colDefs包含非字典行。"
            )
        normalized.append(
            {
                "name": str(row.get("name", "")),
                "typeString": str(
                    row.get(
                        "typeString",
                        row.get("type", ""),
                    )
                ).upper(),
            }
        )
    return normalized


def inspect_existing_table_schema(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
) -> list[dict[str, str]]:
    _validate_identifier(table_name)
    script = (
        f'schema(loadTable("{database_uri}", '
        f"`{table_name})).colDefs"
    )
    return _normalize_coldefs(session.run(script))


def validate_remote_table_schemas(
    session: SessionProtocol,
    database_uri: str,
) -> dict[str, Any]:
    """校验所有目标表字段名和类型。"""
    issues: list[dict[str, Any]] = []
    tables: dict[str, Any] = {}
    for table_name, expected_columns in TABLE_SCHEMAS.items():
        exists = _to_bool(
            session.run(
                f'existsTable("{database_uri}", `{table_name})'
            )
        )
        if not exists:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "TABLE_MISSING",
                    "table_name": table_name,
                }
            )
            tables[table_name] = {
                "exists": False,
                "column_count": 0,
            }
            continue

        actual = inspect_existing_table_schema(
            session,
            database_uri,
            table_name,
        )
        expected = [
            {"name": name, "typeString": data_type}
            for name, data_type in expected_columns
        ]
        tables[table_name] = {
            "exists": True,
            "column_count": len(actual),
            "actual_columns": actual,
        }
        if actual != expected:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "TABLE_SCHEMA_MISMATCH",
                    "table_name": table_name,
                    "expected": expected,
                    "actual": actual,
                }
            )

    return {
        "database_uri": database_uri,
        "table_count": len(TABLE_SCHEMAS),
        "overall_status": (
            "PASSED"
            if not issues
            else "FAILED"
        ),
        "issues": issues,
        "tables": tables,
    }


def create_database_and_tables(
    settings: DolphinDBWriteSettings,
    *,
    session_factory: SessionFactory = _default_session_factory,
) -> dict[str, Any]:
    """创建缺失对象，不删除、不覆盖已有对象。"""
    session = connect_session(settings, session_factory)

    before = probe_dolphindb_environment(
        settings,
        session_factory=lambda: _ConnectedSessionProxy(session),
    )
    if before["readiness"] == "REVIEW_PARTIAL_EXISTING_SCHEMA":
        raise DailyFundsDolphinDBError(
            "目标数据库中只有部分目标表。"
            "为避免覆盖未知结构，本次拒绝自动创建。"
        )

    ddl = build_create_database_script(
        settings.database_uri
    )
    try:
        ddl_result = session.run(ddl)
    except Exception as exc:
        raise DailyFundsDolphinDBError(
            f"DolphinDB建库建表失败：{exc}"
        ) from exc

    schema_validation = validate_remote_table_schemas(
        session,
        settings.database_uri,
    )
    if schema_validation["overall_status"] != "PASSED":
        raise DailyFundsDolphinDBError(
            "建库建表后Schema验证失败："
            f"{schema_validation['issues']}"
        )

    return {
        "task_id": "TASK_016B",
        "mode": "CREATE",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "database_uri": settings.database_uri,
        "before": before,
        "ddl_result": _json_safe(ddl_result),
        "schema_validation": schema_validation,
        "overall_status": "PASSED",
        "safety": [
            "只创建不存在的数据库或表。",
            "未调用dropDatabase或dropTable。",
            "已有部分目标表时拒绝自动继续。",
            "创建后逐表验证字段名和类型。",
        ],
    }


class _ConnectedSessionProxy:
    """让probe复用已连接会话而不重复连接。"""

    def __init__(self, session: SessionProtocol) -> None:
        self._session = session

    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> bool:
        return True

    def run(self, script: str) -> Any:
        return self._session.run(script)


def load_normalized_file_rows(
    *,
    file_path: Path,
    dataset: DatasetSpec,
    contract: DailyFundsContract,
    ingest_batch_id: str,
    ingested_at: datetime,
) -> list[dict[str, Any]]:
    """再次严格解析一个READY文件并返回全部标准化Raw行。"""
    snapshot_date = parse_snapshot_date_from_path(file_path)
    source_hash = file_sha256(file_path)
    schema_index = contract.schema_index()

    iterator = iter_source_rows(
        file_path,
        encoding=contract.source_encoding,
        delimiter=contract.source_delimiter,
    )
    try:
        _, header_cells = next(iterator)
    except StopIteration as exc:
        raise DailyFundsDolphinDBError(
            f"空文件：{file_path}"
        ) from exc

    header_cells = _trim_trailing_delimiter_cell(
        header_cells
    )
    exact_hash = header_fingerprint(header_cells)
    known_schema = schema_index.get(
        (dataset.dataset_id, exact_hash)
    )
    if known_schema is None:
        raise DailyFundsDolphinDBError(
            f"未知Schema：{dataset.dataset_id}/{exact_hash}"
        )

    expected_header = list(known_schema.headers)
    deduplicated_header = deduplicate_headers(
        expected_header
    )
    expected_length = len(expected_header)
    rows: list[dict[str, Any]] = []

    for physical_line_number, raw_cells in iterator:
        cells = _trim_trailing_delimiter_cell(
            raw_cells,
            expected_length=expected_length,
        )
        if not cells or all(
            strip_cell(item) == "" for item in cells
        ):
            continue
        if len(cells) != expected_length:
            raise DailyFundsDolphinDBError(
                "再次解析发现畸形行："
                f"{file_path}, line={physical_line_number}, "
                f"expected={expected_length}, actual={len(cells)}"
            )
        raw_row = {
            deduplicated_header[index]: strip_cell(value)
            for index, value in enumerate(cells)
        }
        try:
            normalized = normalize_row(
                raw_row,
                dataset=dataset,
                snapshot_date=snapshot_date,
                source_file=file_path,
                source_file_hash=source_hash,
                schema_version=known_schema.schema_version,
                source_row_number=physical_line_number - 1,
                ingest_batch_id=ingest_batch_id,
                ingested_at=ingested_at,
                missing_tokens=contract.missing_tokens,
            )
        except Exception as exc:
            raise DailyFundsDolphinDBError(
                "再次解析标准化失败："
                f"{file_path}, line={physical_line_number}, "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        rows.append(normalized)

    return rows


def prepare_dataframe(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[tuple[str, str]],
) -> pd.DataFrame:
    """按目标DolphinDB类型准备DataFrame。"""
    names = [name for name, _ in columns]
    frame = pd.DataFrame(
        [{name: row.get(name) for name in names} for row in rows],
        columns=names,
    )
    for name, data_type in columns:
        if data_type == "DATE":
            frame[name] = pd.to_datetime(
                frame[name],
                errors="raise",
            ).values.astype("datetime64[D]")
        elif data_type == "MONTH":
            frame[name] = pd.to_datetime(
                frame[name],
                errors="raise",
            ).values.astype("datetime64[M]")
        elif data_type == "TIMESTAMP":
            parsed = pd.to_datetime(
                frame[name],
                errors="raise",
                utc=True,
            )
            frame[name] = parsed.dt.tz_convert(
                None
            ).astype("datetime64[ns]")
        elif data_type == "INT":
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("Int32")
        elif data_type == "LONG":
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("Int64")
        elif data_type == "DOUBLE":
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("float64")
        elif data_type in {"STRING", "SYMBOL"}:
            frame[name] = frame[name].where(
                frame[name].notna(),
                None,
            )
    return frame


def decide_file_write_action(
    existing_count: int,
    expected_count: int,
) -> str:
    """根据已存在行数决定幂等动作。"""
    if existing_count < 0 or expected_count < 0:
        raise DailyFundsDolphinDBError(
            "行数不能为负数。"
        )
    if existing_count == expected_count:
        return "SKIP_IDEMPOTENT"
    if existing_count == 0:
        return "WRITE_NEW"
    return "RECOVER_PARTIAL"


def _count_file_rows(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
    dataset_id: str,
    source_file_sha256: str,
) -> int:
    script = (
        "exec count(*) from "
        f'loadTable("{database_uri}", `{table_name}) '
        f"where dataset_id={_symbol_literal(dataset_id)} "
        f"and source_file_sha256="
        f"{_symbol_literal(source_file_sha256)}"
    )
    result = session.run(script)
    return int(result)


def _count_table_rows(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
) -> int:
    result = session.run(
        "exec count(*) from "
        f'loadTable("{database_uri}", `{table_name})'
    )
    return int(result)


def _append_rows(
    *,
    database_uri: str,
    table_name: str,
    session: SessionProtocol,
    rows: Sequence[dict[str, Any]],
    appender_factory: AppenderFactory,
) -> int:
    if not rows:
        return 0
    frame = prepare_dataframe(
        rows,
        TABLE_SCHEMAS[table_name],
    )
    appender = appender_factory(
        database_uri,
        table_name,
        session,
    )
    result = appender.append(frame)
    if isinstance(result, (int, np.integer)):
        return int(result)
    return len(frame)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(
            _json_safe(payload),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, Path)):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    return value


def _batch_log_row(
    *,
    batch_id: str,
    now: datetime,
    status: str,
    root: Path,
    contract_version: str,
    preflight: dict[str, Any],
    inserted_row_count: int,
    skipped_row_count: int,
    failed_file_count: int,
    message: str,
) -> dict[str, Any]:
    return {
        "ingest_batch_id": batch_id,
        "batch_month": now.strftime("%Y-%m"),
        "logged_at": now.isoformat(),
        "status": status,
        "scan_root": str(root),
        "contract_version": contract_version,
        "preflight_status": str(
            preflight.get("overall_status", "")
        ),
        "source_file_count": int(
            preflight.get("profiled_file_count", 0)
        ),
        "ready_file_count": int(
            preflight.get("ready_file_count", 0)
        ),
        "quarantined_file_count": int(
            preflight.get("quarantined_file_count", 0)
        ),
        "blocked_file_count": int(
            preflight.get("blocked_file_count", 0)
        ),
        "planned_row_count": int(
            preflight.get("planned_insert_row_count", 0)
        ),
        "inserted_row_count": inserted_row_count,
        "skipped_row_count": skipped_row_count,
        "failed_file_count": failed_file_count,
        "message": message,
    }


def _coverage_index(
    coverage_rows: Sequence[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (
            row["snapshot_date"],
            row["dataset_id"],
        ): row
        for row in coverage_rows
    }


def run_daily_funds_import(
    *,
    settings: DolphinDBWriteSettings,
    root: Path,
    contract_path: Path,
    output_dir: Path,
    expected_planned_row_count: int | None = None,
    session_factory: SessionFactory = _default_session_factory,
    appender_factory: AppenderFactory = _default_appender_factory,
) -> dict[str, Any]:
    """执行真实导入；调用前必须已经创建并验证表。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    batch_id = (
        "task016b_"
        + started_at.strftime("%Y%m%dT%H%M%S%fZ")
    )

    preflight_dir = output_dir / "preflight"
    preflight = run_daily_funds_preflight(
        root=root,
        contract_path=contract_path,
        output_dir=preflight_dir,
        generated_at=started_at,
    )
    if preflight["overall_status"] not in {
        "READY",
        "READY_WITH_QUARANTINE",
    }:
        raise DailyFundsDolphinDBError(
            "TASK_016A重跑未通过，拒绝写入："
            f"{preflight['overall_status']}"
        )
    planned_count = int(
        preflight["planned_insert_row_count"]
    )
    if (
        expected_planned_row_count is not None
        and planned_count != expected_planned_row_count
    ):
        raise DailyFundsDolphinDBError(
            "计划写入行数发生变化，拒绝写入："
            f"expected={expected_planned_row_count}, "
            f"actual={planned_count}"
        )

    contract = load_daily_funds_contract(contract_path)
    session = connect_session(settings, session_factory)
    remote_validation = validate_remote_table_schemas(
        session,
        settings.database_uri,
    )
    if remote_validation["overall_status"] != "PASSED":
        raise DailyFundsDolphinDBError(
            "远端表结构未通过验收，拒绝写入："
            f"{remote_validation['issues']}"
        )

    file_rows = _read_csv(
        preflight_dir / "task_016a_file_results.csv"
    )
    coverage_rows = _read_csv(
        preflight_dir / "task_016a_coverage_checks.csv"
    )
    coverage_by_key = _coverage_index(coverage_rows)

    inserted_total = 0
    skipped_total = 0
    failed_files = 0
    file_reports: list[dict[str, Any]] = []

    _append_rows(
        database_uri=settings.database_uri,
        table_name=TABLE_NAMES["ingest_batch"],
        session=session,
        rows=[
            _batch_log_row(
                batch_id=batch_id,
                now=started_at,
                status="STARTED",
                root=root,
                contract_version=contract.contract_version,
                preflight=preflight,
                inserted_row_count=0,
                skipped_row_count=0,
                failed_file_count=0,
                message="TASK_016A门禁通过，开始逐文件导入。",
            )
        ],
        appender_factory=appender_factory,
    )

    try:
        for item in file_rows:
            snapshot_date = item["snapshot_date"]
            dataset_id = item["dataset_id"]
            status = item["status"]
            dataset = contract.datasets[dataset_id]
            source_file = (
                root
                / snapshot_date
                / item["file_name"]
            )
            source_hash = item["source_file_sha256"]
            expected_count = int(item["row_count"])
            table_name = FAMILY_TO_TABLE[
                dataset.family
            ]
            logged_at = datetime.now(timezone.utc)

            if status == "QUARANTINED":
                coverage = coverage_by_key.get(
                    (snapshot_date, dataset_id),
                    {},
                )
                reason = item["quarantine_reason"]
                reason_code = reason.split(":", 1)[0]
                quarantine_row = {
                    "ingest_batch_id": batch_id,
                    "snapshot_date": datetime.strptime(
                        snapshot_date,
                        "%Y%m%d",
                    ).date().isoformat(),
                    "snapshot_month": (
                        f"{snapshot_date[:4]}-"
                        f"{snapshot_date[4:6]}"
                    ),
                    "logged_at": logged_at.isoformat(),
                    "dataset_id": dataset_id,
                    "source_file_name": item["file_name"],
                    "source_file_sha256": source_hash,
                    "row_count": expected_count,
                    "reason_code": reason_code,
                    "reason_detail": reason,
                    "reference_dataset_id": coverage.get(
                        "reference_dataset_id",
                        "",
                    ),
                    "coverage_ratio": (
                        float(coverage["coverage_ratio"])
                        if coverage.get("coverage_ratio")
                        else None
                    ),
                    "minimum_ratio": (
                        float(coverage["minimum_ratio"])
                        if coverage.get("minimum_ratio")
                        else None
                    ),
                }
                _append_rows(
                    database_uri=settings.database_uri,
                    table_name=TABLE_NAMES[
                        "quarantine_file"
                    ],
                    session=session,
                    rows=[quarantine_row],
                    appender_factory=appender_factory,
                )
                file_reports.append(
                    {
                        "snapshot_date": snapshot_date,
                        "dataset_id": dataset_id,
                        "table_name": table_name,
                        "status": "QUARANTINED",
                        "row_count": expected_count,
                        "inserted_row_count": 0,
                        "final_row_count": 0,
                        "source_file_sha256": source_hash,
                    }
                )
                _append_rows(
                    database_uri=settings.database_uri,
                    table_name=TABLE_NAMES["ingest_file"],
                    session=session,
                    rows=[
                        {
                            "ingest_batch_id": batch_id,
                            "snapshot_date": datetime.strptime(
                                snapshot_date,
                                "%Y%m%d",
                            ).date().isoformat(),
                            "snapshot_month": (
                                f"{snapshot_date[:4]}-"
                                f"{snapshot_date[4:6]}"
                            ),
                            "logged_at": logged_at.isoformat(),
                            "dataset_id": dataset_id,
                            "family": dataset.family,
                            "source_file_name": item["file_name"],
                            "source_file_sha256": source_hash,
                            "schema_version": item["schema_version"],
                            "row_count": expected_count,
                            "existing_row_count_before": 0,
                            "inserted_row_count": 0,
                            "final_row_count": 0,
                            "status": "QUARANTINED",
                            "message": reason,
                        }
                    ],
                    appender_factory=appender_factory,
                )
                continue

            if status != "READY":
                raise DailyFundsDolphinDBError(
                    "发现非READY且非QUARANTINED文件："
                    f"{snapshot_date}/{dataset_id}/{status}"
                )

            actual_hash = file_sha256(source_file)
            if actual_hash != source_hash:
                raise DailyFundsDolphinDBError(
                    "源文件在预导入后发生变化："
                    f"{source_file}"
                )

            existing_count = _count_file_rows(
                session,
                settings.database_uri,
                table_name,
                dataset_id,
                source_hash,
            )
            action = decide_file_write_action(
                existing_count,
                expected_count,
            )
            inserted_count = 0

            if action == "SKIP_IDEMPOTENT":
                skipped_total += expected_count
            else:
                normalized_rows = load_normalized_file_rows(
                    file_path=source_file,
                    dataset=dataset,
                    contract=contract,
                    ingest_batch_id=batch_id,
                    ingested_at=started_at,
                )
                if len(normalized_rows) != expected_count:
                    raise DailyFundsDolphinDBError(
                        "再次解析行数不一致："
                        f"{source_file}, "
                        f"expected={expected_count}, "
                        f"actual={len(normalized_rows)}"
                    )
                inserted_count = _append_rows(
                    database_uri=settings.database_uri,
                    table_name=table_name,
                    session=session,
                    rows=normalized_rows,
                    appender_factory=appender_factory,
                )
                inserted_total += inserted_count

            final_count = _count_file_rows(
                session,
                settings.database_uri,
                table_name,
                dataset_id,
                source_hash,
            )
            if final_count != expected_count:
                raise DailyFundsDolphinDBError(
                    "文件写入后行数验收失败："
                    f"{source_file}, "
                    f"expected={expected_count}, "
                    f"actual={final_count}"
                )

            file_status = (
                "SKIPPED_IDEMPOTENT"
                if action == "SKIP_IDEMPOTENT"
                else (
                    "RECOVERED_PARTIAL"
                    if action == "RECOVER_PARTIAL"
                    else "COMMITTED"
                )
            )
            _append_rows(
                database_uri=settings.database_uri,
                table_name=TABLE_NAMES["ingest_file"],
                session=session,
                rows=[
                    {
                        "ingest_batch_id": batch_id,
                        "snapshot_date": datetime.strptime(
                            snapshot_date,
                            "%Y%m%d",
                        ).date().isoformat(),
                        "snapshot_month": (
                            f"{snapshot_date[:4]}-"
                            f"{snapshot_date[4:6]}"
                        ),
                        "logged_at": logged_at.isoformat(),
                        "dataset_id": dataset_id,
                        "family": dataset.family,
                        "source_file_name": item["file_name"],
                        "source_file_sha256": source_hash,
                        "schema_version": item["schema_version"],
                        "row_count": expected_count,
                        "existing_row_count_before": existing_count,
                        "inserted_row_count": inserted_count,
                        "final_row_count": final_count,
                        "status": file_status,
                        "message": action,
                    }
                ],
                appender_factory=appender_factory,
            )
            file_reports.append(
                {
                    "snapshot_date": snapshot_date,
                    "dataset_id": dataset_id,
                    "table_name": table_name,
                    "status": file_status,
                    "row_count": expected_count,
                    "inserted_row_count": inserted_count,
                    "final_row_count": final_count,
                    "source_file_sha256": source_hash,
                }
            )

        table_counts = {
            table_name: _count_table_rows(
                session,
                settings.database_uri,
                table_name,
            )
            for table_name in FAMILY_TO_TABLE.values()
        }

        quarantined_hashes = [
            item["source_file_sha256"]
            for item in file_rows
            if item["status"] == "QUARANTINED"
        ]
        quarantined_leak_count = 0
        for item in file_rows:
            if item["status"] != "QUARANTINED":
                continue
            dataset = contract.datasets[
                item["dataset_id"]
            ]
            quarantined_leak_count += _count_file_rows(
                session,
                settings.database_uri,
                FAMILY_TO_TABLE[dataset.family],
                item["dataset_id"],
                item["source_file_sha256"],
            )
        if quarantined_leak_count != 0:
            raise DailyFundsDolphinDBError(
                "隔离文件进入了主Raw表。"
            )

        completed_at = datetime.now(timezone.utc)
        _append_rows(
            database_uri=settings.database_uri,
            table_name=TABLE_NAMES["ingest_batch"],
            session=session,
            rows=[
                _batch_log_row(
                    batch_id=batch_id,
                    now=completed_at,
                    status="COMPLETED",
                    root=root,
                    contract_version=contract.contract_version,
                    preflight=preflight,
                    inserted_row_count=inserted_total,
                    skipped_row_count=skipped_total,
                    failed_file_count=0,
                    message="全部READY文件完成逐文件行数验收。",
                )
            ],
            appender_factory=appender_factory,
        )

        report = {
            "task_id": "TASK_016B",
            "mode": "IMPORT",
            "ingest_batch_id": batch_id,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "database_uri": settings.database_uri,
            "preflight": preflight,
            "inserted_row_count": inserted_total,
            "skipped_idempotent_row_count": skipped_total,
            "failed_file_count": 0,
            "file_status_counts": dict(
                Counter(
                    item["status"]
                    for item in file_reports
                )
            ),
            "main_table_row_counts": table_counts,
            "quarantined_source_hashes": quarantined_hashes,
            "quarantined_leak_count": quarantined_leak_count,
            "overall_status": "PASSED",
        }
    except Exception as exc:
        failed_files += 1
        failed_at = datetime.now(timezone.utc)
        try:
            _append_rows(
                database_uri=settings.database_uri,
                table_name=TABLE_NAMES["ingest_batch"],
                session=session,
                rows=[
                    _batch_log_row(
                        batch_id=batch_id,
                        now=failed_at,
                        status="FAILED",
                        root=root,
                        contract_version=contract.contract_version,
                        preflight=preflight,
                        inserted_row_count=inserted_total,
                        skipped_row_count=skipped_total,
                        failed_file_count=failed_files,
                        message=f"{type(exc).__name__}: {exc}",
                    )
                ],
                appender_factory=appender_factory,
            )
        except Exception:
            pass
        raise

    _write_json(
        output_dir / "task_016b_import_summary.json",
        report,
    )
    _write_json(
        output_dir / "task_016b_file_results.json",
        file_reports,
    )
    (
        output_dir / "task_016b_import_summary.md"
    ).write_text(
        _build_import_markdown(report),
        encoding="utf-8",
    )
    return report


def _build_import_markdown(
    report: dict[str, Any],
) -> str:
    table_lines = "\n".join(
        f"- `{name}`：{count}"
        for name, count in report[
            "main_table_row_counts"
        ].items()
    )
    return f"""# TASK_016B 七类日线资金真实导入

- 状态：**{report['overall_status']}**
- 批次：`{report['ingest_batch_id']}`
- 数据库：`{report['database_uri']}`
- 本次实际追加：{report['inserted_row_count']}
- 幂等跳过：{report['skipped_idempotent_row_count']}
- 失败文件：{report['failed_file_count']}
- 隔离泄漏行数：{report['quarantined_leak_count']}

## 主Raw表当前行数

{table_lines}

## 说明

- 本次先重新执行TASK_016A门禁；
- READY文件逐文件写入并逐文件回查行数；
- 相同源文件重复运行会按源文件哈希幂等跳过；
- 部分写入可通过TSDB keepDuplicates=LAST恢复；
- 隔离文件不进入主Raw表；
- source_file_mtime仅作为来源证据。
"""


def resolve_password() -> str:
    password = os.getenv("DOLPHINDB_PASSWORD")
    if password is None:
        password = getpass.getpass(
            "请输入 DolphinDB 密码："
        )
    if not password:
        raise DailyFundsDolphinDBError(
            "DolphinDB密码不能为空。"
        )
    return password
