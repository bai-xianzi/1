"""TASK_016A 七类日线资金入库前解析与质量门禁。

本模块只处理本地源文件并生成写入计划，不连接或修改 DolphinDB。

支持的数据集：
- hq / kphq：个股行情与集合竞价；
- hy / gn / kphy / kpgn：行业、概念收盘及集合竞价；
- zj：个股资金流。

源文件扩展名是 .xls，但实际格式是 GB18030 编码的制表符文本。
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


DATE_DIR_PATTERN = re.compile(r"^\d{8}$")
INSTRUMENT_CODE_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")
MISSING_DEFAULTS = {"", "—", "--", "N/A", "NA", "null", "NULL"}
MAGNITUDE_MULTIPLIERS = (
    ("万亿", 1_000_000_000_000.0),
    ("亿", 100_000_000.0),
    ("万", 10_000.0),
    ("千", 1_000.0),
)
BLOCKING_PARSE_CODES = {
    "UNKNOWN_SCHEMA",
    "MALFORMED_ROW",
    "DUPLICATE_ENTITY_KEY",
    "ROW_NORMALIZATION_FAILED",
}


class DailyFundsIngestError(ValueError):
    """日线资金解析或合同错误。"""


@dataclass(frozen=True, slots=True)
class KnownSchema:
    """一个已知来源表头版本。"""

    dataset_id: str
    schema_version: str
    exact_header_sha256: str
    headers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """一个逻辑数据集的来源合同。"""

    dataset_id: str
    file_name: str
    family: str
    snapshot_phase: str
    classification_type: str | None
    entity_key: str
    schemas: tuple[KnownSchema, ...]


@dataclass(frozen=True, slots=True)
class DailyFundsContract:
    """完整的七类日线资金来源合同。"""

    contract_version: str
    source_encoding: str
    source_delimiter: str
    missing_tokens: frozenset[str]
    database_plan: dict[str, Any]
    coverage_gates: dict[str, dict[str, Any]]
    semantic_aliases: dict[str, str]
    datasets: dict[str, DatasetSpec]

    def schema_index(self) -> dict[tuple[str, str], KnownSchema]:
        """按 dataset_id 和表头哈希建立索引。"""
        result: dict[tuple[str, str], KnownSchema] = {}
        for dataset in self.datasets.values():
            for schema in dataset.schemas:
                key = (dataset.dataset_id, schema.exact_header_sha256)
                if key in result:
                    raise DailyFundsIngestError(f"Schema重复：{key}")
                result[key] = schema
        return result


@dataclass(frozen=True, slots=True)
class ParsedSourceFile:
    """单个文件的解析结果摘要。"""

    dataset_id: str
    snapshot_date: date
    file_path: Path
    file_size_bytes: int
    source_file_sha256: str
    schema_version: str | None
    exact_header_sha256: str
    row_count: int
    unique_key_count: int
    duplicate_key_count: int
    malformed_row_count: int
    missing_cell_count: int
    normalization_error_count: int
    entity_keys: frozenset[str]
    normalized_samples: tuple[dict[str, Any], ...]
    anomaly_codes: tuple[str, ...]
    anomaly_details: tuple[str, ...]

    @property
    def has_blocking_parse_error(self) -> bool:
        """是否存在阻断该文件写入的解析问题。"""
        return any(code in BLOCKING_PARSE_CODES for code in self.anomaly_codes)


def load_daily_funds_contract(path: Path) -> DailyFundsContract:
    """读取并验证 YAML 来源合同。"""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DailyFundsIngestError("来源合同根节点必须是字典。")

    source_format = payload.get("source_format")
    datasets_payload = payload.get("datasets")
    if not isinstance(source_format, dict):
        raise DailyFundsIngestError("source_format 缺失或类型错误。")
    if not isinstance(datasets_payload, dict):
        raise DailyFundsIngestError("datasets 缺失或类型错误。")

    datasets: dict[str, DatasetSpec] = {}
    for dataset_id, raw_spec in datasets_payload.items():
        if not isinstance(raw_spec, dict):
            raise DailyFundsIngestError(
                f"数据集配置必须是字典：{dataset_id}"
            )

        schemas_payload = raw_spec.get("schemas")
        if not isinstance(schemas_payload, list) or not schemas_payload:
            raise DailyFundsIngestError(
                f"数据集必须至少有一个已知Schema：{dataset_id}"
            )

        schemas: list[KnownSchema] = []
        for schema_payload in schemas_payload:
            if not isinstance(schema_payload, dict):
                raise DailyFundsIngestError(
                    f"Schema配置必须是字典：{dataset_id}"
                )
            headers = schema_payload.get("headers")
            if not isinstance(headers, list) or not all(
                isinstance(item, str) for item in headers
            ):
                raise DailyFundsIngestError(
                    f"Schema headers 非法：{dataset_id}"
                )
            expected_hash = str(
                schema_payload.get("exact_header_sha256", "")
            )
            actual_hash = header_fingerprint(headers)
            if expected_hash != actual_hash:
                raise DailyFundsIngestError(
                    f"Schema表头哈希不一致："
                    f"{dataset_id}/"
                    f"{schema_payload.get('schema_version')}"
                )
            schemas.append(
                KnownSchema(
                    dataset_id=str(dataset_id),
                    schema_version=str(
                        schema_payload.get("schema_version", "")
                    ),
                    exact_header_sha256=expected_hash,
                    headers=tuple(headers),
                )
            )

        dataset_spec = DatasetSpec(
            dataset_id=str(dataset_id),
            file_name=str(raw_spec.get("file_name", "")),
            family=str(raw_spec.get("family", "")),
            snapshot_phase=str(
                raw_spec.get("snapshot_phase", "")
            ),
            classification_type=(
                None
                if raw_spec.get("classification_type") is None
                else str(raw_spec.get("classification_type"))
            ),
            entity_key=str(raw_spec.get("entity_key", "")),
            schemas=tuple(schemas),
        )
        if not dataset_spec.file_name:
            raise DailyFundsIngestError(
                f"file_name 不能为空：{dataset_id}"
            )
        if dataset_spec.family not in {
            "security_snapshot",
            "classification_snapshot",
            "money_flow_snapshot",
        }:
            raise DailyFundsIngestError(
                f"family 非法：{dataset_id}/{dataset_spec.family}"
            )
        datasets[dataset_spec.dataset_id] = dataset_spec

    required_dataset_ids = {
        "hq",
        "hy",
        "gn",
        "kphq",
        "kphy",
        "kpgn",
        "zj",
    }
    if set(datasets) != required_dataset_ids:
        raise DailyFundsIngestError(
            "七类数据集必须完整登记。"
            f" expected={sorted(required_dataset_ids)}"
            f" actual={sorted(datasets)}"
        )

    contract = DailyFundsContract(
        contract_version=str(payload.get("contract_version", "")),
        source_encoding=str(source_format.get("encoding", "")),
        source_delimiter=str(source_format.get("delimiter", "")),
        missing_tokens=frozenset(
            str(item)
            for item in source_format.get(
                "missing_tokens", MISSING_DEFAULTS
            )
        ),
        database_plan=dict(payload.get("database_plan", {})),
        coverage_gates=dict(payload.get("coverage_gates", {})),
        semantic_aliases={
            str(key): str(value)
            for key, value in dict(
                payload.get("semantic_aliases", {})
            ).items()
        },
        datasets=datasets,
    )
    contract.schema_index()
    return contract


def validate_daily_funds_contract(
    contract: DailyFundsContract,
) -> dict[str, Any]:
    """返回来源合同的机器校验结果。"""
    schema_count = sum(
        len(dataset.schemas)
        for dataset in contract.datasets.values()
    )
    hashes = [
        schema.exact_header_sha256
        for dataset in contract.datasets.values()
        for schema in dataset.schemas
    ]
    issues: list[dict[str, Any]] = []
    if len(hashes) != len(set((schema.dataset_id, schema.exact_header_sha256)
                              for dataset in contract.datasets.values()
                              for schema in dataset.schemas)):
        issues.append(
            {
                "severity": "ERROR",
                "code": "DUPLICATE_SCHEMA_KEY",
                "message": "dataset_id + header hash 必须唯一。",
            }
        )

    for child, gate in contract.coverage_gates.items():
        reference = str(gate.get("reference_dataset_id", ""))
        threshold = gate.get("minimum_intersection_ratio")
        if child not in contract.datasets:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "UNKNOWN_COVERAGE_CHILD",
                    "message": child,
                }
            )
        if reference not in contract.datasets:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "UNKNOWN_COVERAGE_REFERENCE",
                    "message": reference,
                }
            )
        if not isinstance(threshold, (int, float)) or not 0 < float(
            threshold
        ) <= 1:
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "INVALID_COVERAGE_THRESHOLD",
                    "message": child,
                }
            )

    physical_tables = contract.database_plan.get(
        "physical_tables", {}
    )
    if not isinstance(physical_tables, dict):
        issues.append(
            {
                "severity": "ERROR",
                "code": "PHYSICAL_TABLE_PLAN_MISSING",
                "message": "physical_tables 必须是字典。",
            }
        )

    return {
        "task_id": "TASK_016A",
        "contract_version": contract.contract_version,
        "dataset_count": len(contract.datasets),
        "schema_count": schema_count,
        "coverage_gate_count": len(contract.coverage_gates),
        "overall_status": (
            "PASSED"
            if not any(
                item["severity"] == "ERROR" for item in issues
            )
            else "FAILED"
        ),
        "issues": issues,
    }


def strip_cell(value: Any) -> str:
    """统一去除来源单元格两端空白和BOM。"""
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def header_fingerprint(headers: Iterable[str]) -> str:
    """生成与 TASK_015B 一致的精确表头哈希。"""
    normalized = [strip_cell(item) for item in headers]
    payload = "\x1f".join(normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def deduplicate_headers(headers: Iterable[str]) -> list[str]:
    """保留重复表头，并为后续重复项增加 __2、__3 后缀。"""
    result: list[str] = []
    counts: Counter[str] = Counter()
    for raw_name in headers:
        name = strip_cell(raw_name)
        counts[name] += 1
        suffix = "" if counts[name] == 1 else f"__{counts[name]}"
        result.append(f"{name}{suffix}")
    return result


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """流式计算文件SHA256。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    """生成稳定、可哈希的JSON。"""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def parse_snapshot_date_from_path(path: Path) -> date:
    """从父目录 YYYYMMDD 推导快照日期。"""
    directory_name = path.parent.name
    if not DATE_DIR_PATTERN.fullmatch(directory_name):
        raise DailyFundsIngestError(
            f"快照目录不是YYYYMMDD：{path.parent}"
        )
    return datetime.strptime(directory_name, "%Y%m%d").date()


def is_missing(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> bool:
    """判断来源值是否为缺失标记。"""
    return strip_cell(value) in missing_tokens


def parse_source_number(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> float | None:
    """解析中文数量级数值，保持原有正负号。

    示例：
    - 30.3万 -> 303000
    - 6.06亿 -> 606000000
    - 3.97万亿 -> 3970000000000
    - -35.0亿 -> -3500000000
    - — -> None
    """
    text = strip_cell(value)
    if text in missing_tokens:
        return None

    normalized = (
        text.replace(",", "")
        .replace("％", "%")
        .replace("−", "-")
        .replace("－", "-")
        .replace("＋", "+")
        .replace(" ", "")
    )
    if normalized.endswith("%"):
        normalized = normalized[:-1]

    multiplier = 1.0
    for suffix, candidate in MAGNITUDE_MULTIPLIERS:
        if normalized.endswith(suffix):
            multiplier = candidate
            normalized = normalized[: -len(suffix)]
            break

    if normalized in {"", "+", "-"}:
        return None

    try:
        result = float(normalized) * multiplier
    except ValueError as exc:
        raise DailyFundsIngestError(
            f"无法解析数值：{text!r}"
        ) from exc

    if not math.isfinite(result):
        raise DailyFundsIngestError(
            f"数值不是有限数：{text!r}"
        )
    return result


def parse_source_int(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> int | None:
    """解析整数或带中文数量级的整数。"""
    parsed = parse_source_number(value, missing_tokens)
    if parsed is None:
        return None
    rounded = round(parsed)
    if abs(parsed - rounded) > 1e-9:
        raise DailyFundsIngestError(
            f"来源值不是整数：{value!r}"
        )
    return int(rounded)


def normalize_instrument_code(value: Any) -> str:
    """把 = "000001"、="000001" 等来源值标准化为6位代码。"""
    text = strip_cell(value)
    match = INSTRUMENT_CODE_PATTERN.search(text)
    if match is None:
        raise DailyFundsIngestError(
            f"无法识别6位证券代码：{text!r}"
        )
    return match.group(1)


def infer_market_candidate(instrument_id: str) -> str:
    """按代码前缀给出市场候选，不作为最终身份权威。"""
    if instrument_id.startswith(("4", "8", "92")):
        return "BJ"
    if instrument_id.startswith("6"):
        return "SH"
    if instrument_id.startswith(("0", "2", "3")):
        return "SZ"
    return "UNKNOWN"


def parse_breadth_counts(value: Any) -> tuple[int | None, int | None]:
    """解析“涨跌家数”，例如 7/6。"""
    text = strip_cell(value)
    if text in MISSING_DEFAULTS:
        return None, None
    match = re.fullmatch(r"(\d+)\s*/\s*(\d+)", text)
    if match is None:
        raise DailyFundsIngestError(
            f"无法解析涨跌家数：{text!r}"
        )
    return int(match.group(1)), int(match.group(2))


def parse_breadth_ratio(
    value: Any,
    up_count: int | None,
    down_count: int | None,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> tuple[float | None, str]:
    """解析涨跌比，并保留全涨、全跌等状态。"""
    text = strip_cell(value)
    if text in missing_tokens:
        return None, "UNKNOWN"
    if text == "全涨":
        return None, "ALL_UP"
    if text == "全跌":
        return None, "ALL_DOWN"
    ratio = parse_source_number(text, missing_tokens)
    if ratio is None:
        return None, "UNKNOWN"

    if (
        up_count is not None
        and down_count not in {None, 0}
        and abs(ratio - up_count / down_count) > 0.05
    ):
        return ratio, "RATIO_MISMATCH_WARNING"
    return ratio, "NORMAL"


def first_non_missing(
    row: dict[str, str],
    names: Iterable[str],
    missing_tokens: frozenset[str] | set[str],
) -> str | None:
    """按优先级取得首个非缺失来源字段。"""
    for name in names:
        value = row.get(name)
        if value is not None and not is_missing(value, missing_tokens):
            return value
    return None


def normalized_base_metadata(
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    raw_row: dict[str, str],
    entity_key: str,
    ingest_batch_id: str,
    ingested_at: datetime,
) -> dict[str, Any]:
    """构造三类物理Raw表共享的血缘字段。"""
    mtime = datetime.fromtimestamp(
        source_file.stat().st_mtime,
        tz=timezone.utc,
    )
    return {
        "dataset_id": dataset.dataset_id,
        "snapshot_date": snapshot_date.isoformat(),
        "snapshot_month": snapshot_date.strftime("%Y-%m"),
        "snapshot_phase": dataset.snapshot_phase,
        "schema_version": schema_version,
        "entity_key": entity_key,
        "source_row_number": source_row_number,
        "source_file_name": source_file.name,
        "source_file_relative_path": (
            f"{source_file.parent.name}/{source_file.name}"
        ),
        "source_file_size_bytes": source_file.stat().st_size,
        "source_file_mtime_utc": mtime.isoformat(),
        "source_file_sha256": source_file_hash,
        "row_sha256": hashlib.sha256(
            stable_json(raw_row).encode("utf-8")
        ).hexdigest(),
        "ingest_batch_id": ingest_batch_id,
        "ingested_at_utc": ingested_at.astimezone(
            timezone.utc
        ).isoformat(),
        "quality_status": "PASSED",
        "raw_row_json": stable_json(raw_row),
    }


def normalize_security_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 hq / kphq 到安全Raw结构。"""
    instrument_id = normalize_instrument_code(row.get("代码"))
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=instrument_id,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )

    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )
    integer = lambda *names: parse_source_int(
        value(*names), missing_tokens
    )

    base.update(
        {
            "instrument_id": instrument_id,
            "market_candidate": infer_market_candidate(
                instrument_id
            ),
            "instrument_name": strip_cell(row.get("名称")),
            "last_price": number("最新"),
            "pct_change": number("涨幅%"),
            "price_change": number("涨跌"),
            "total_volume_lot": number("总量", "总手"),
            "current_volume_lot": number("现量", "现手"),
            "bid_price": number("买入价"),
            "ask_price": number("卖出价"),
            "speed_pct": number("涨速%"),
            "turnover_pct": number("换手%"),
            "amount_cny": number("金额"),
            "pe_dynamic": number("市盈率(动)"),
            "industry_name": strip_cell(row.get("所属行业")),
            "high_price": number("最高"),
            "low_price": number("最低"),
            "open_price": number("开盘"),
            "prev_close": number("昨收"),
            "amplitude_pct": number("振幅%"),
            "volume_ratio": number("量比"),
            "order_imbalance_pct": number("委比%"),
            "order_imbalance_lot": number("委差"),
            "avg_price": number("均价"),
            "inner_volume_lot": number("内盘"),
            "outer_volume_lot": number("外盘"),
            "inner_outer_ratio": number("内外比"),
            "bid1_volume_lot": number("买一量"),
            "ask1_volume_lot": number("卖一量"),
            "pb": number("市净率"),
            "total_shares": number("总股本"),
            "total_market_cap_cny": number("总市值"),
            "float_shares": number("流通股本"),
            "float_market_cap_cny": number("流通市值"),
            "return_3d_pct": number("3日涨幅%"),
            "return_6d_pct": number("6日涨幅%"),
            "turnover_3d_pct": number("3日换手%"),
            "turnover_6d_pct": number("6日换手%"),
            "consecutive_up_days": integer(
                "连涨天数1", "连涨天数__2", "连涨天数"
            ),
            "return_month_pct": number("本月涨幅%"),
            "return_ytd_pct": number(
                "今年涨幅%1", "今年涨幅%__2", "今年涨幅%"
            ),
            "return_1m_pct": number("近一月涨幅%"),
            "return_1y_pct": number(
                "近一年涨幅%1", "近一年涨幅%__2", "近一年涨幅%"
            ),
            "listing_date_raw": strip_cell(row.get("上市日")),
            "speed_5m_pct": number("5分钟涨速%"),
            "return_20d_pct": number("20日涨幅%"),
            "source_volume_unit": "LOT_CANDIDATE",
            "canonical_volume_transform": "multiply_by_100",
            "source_amount_unit": "CNY",
        }
    )
    return base


def normalize_classification_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 hy / gn / kphy / kpgn 到安全Raw结构。"""
    node_name = strip_cell(row.get("名称"))
    if not node_name:
        raise DailyFundsIngestError("分类节点名称为空。")
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=node_name,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )

    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )
    integer = lambda *names: parse_source_int(
        value(*names), missing_tokens
    )
    up_count, down_count = parse_breadth_counts(
        row.get("涨跌家数")
    )
    breadth_ratio, breadth_status = parse_breadth_ratio(
        row.get("涨跌比"),
        up_count,
        down_count,
        missing_tokens,
    )

    base.update(
        {
            "classification_type": dataset.classification_type,
            "node_name_raw": node_name,
            "pct_change": number("涨幅%"),
            "return_3d_pct": number("3日涨幅%"),
            "speed_pct": number("涨速%"),
            "leading_stock_name": strip_cell(row.get("领涨股")),
            "up_count": up_count,
            "down_count": down_count,
            "breadth_ratio": breadth_ratio,
            "breadth_status": breadth_status,
            "limit_up_count": integer("涨停家数"),
            "turnover_pct": number("换手%"),
            "volume_ratio": number("量比"),
            "turnover_3d_pct": number("3日换手%"),
            "return_5d_pct": number("5日涨幅%"),
            "return_10d_pct": number("10日涨幅%"),
            "return_20d_pct": number("20日涨幅%"),
            "volume_lot": number("成交量"),
            "amount_cny": number("金额"),
            "total_market_cap_cny": number("总市值"),
            "float_market_cap_cny": number("流通市值"),
            "average_return_pct": number("平均收益"),
            "average_shares": number("平均股本"),
            "pe_ratio": number("市盈率"),
            "source_volume_unit": "LOT_CANDIDATE",
            "canonical_volume_transform": "multiply_by_100",
            "source_amount_unit": "CNY",
        }
    )
    return base


def normalize_money_flow_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 zj，保留来源流出字段的原始负号。"""
    instrument_id = normalize_instrument_code(row.get("代码"))
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=instrument_id,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )
    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )

    base.update(
        {
            "instrument_id": instrument_id,
            "market_candidate": infer_market_candidate(
                instrument_id
            ),
            "instrument_name": strip_cell(row.get("名称")),
            "last_price": number("最新"),
            "pct_change": number("涨幅%"),
            "main_net_inflow_cny": number("主力净流入"),
            "auction_net_inflow_cny": number("集合竞价"),
            "super_large_inflow_cny": number("超大单流入"),
            "super_large_outflow_cny": number("超大单流出"),
            "super_large_net_cny": number("超大单净额"),
            "super_large_net_ratio_pct": number(
                "超大单净占比%"
            ),
            "large_inflow_cny": number("大单流入"),
            "large_outflow_cny": number("大单流出"),
            "large_net_cny": number("大单净额"),
            "large_net_ratio_pct": number("大单净占比%"),
            "medium_inflow_cny": number("中单流入"),
            "medium_outflow_cny": number("中单流出"),
            "medium_net_cny": number("中单净额"),
            "medium_net_ratio_pct": number("中单净占比%"),
            "small_inflow_cny": number("小单流入"),
            "small_outflow_cny": number("小单流出"),
            "small_net_cny": number("小单净额"),
            "small_net_ratio_pct": number("小单净占比%"),
            "source_amount_unit": "CNY",
            "outflow_sign_policy": "PRESERVE_SOURCE_SIGN",
        }
    )
    return base


def normalize_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """按三类物理Raw表选择标准化函数。"""
    kwargs = {
        "row": row,
        "dataset": dataset,
        "snapshot_date": snapshot_date,
        "source_file": source_file,
        "source_file_hash": source_file_hash,
        "schema_version": schema_version,
        "source_row_number": source_row_number,
        "ingest_batch_id": ingest_batch_id,
        "ingested_at": ingested_at,
        "missing_tokens": missing_tokens,
    }
    if dataset.family == "security_snapshot":
        return normalize_security_row(**kwargs)
    if dataset.family == "classification_snapshot":
        return normalize_classification_row(**kwargs)
    if dataset.family == "money_flow_snapshot":
        return normalize_money_flow_row(**kwargs)
    raise DailyFundsIngestError(
        f"不支持的family：{dataset.family}"
    )


def _trim_trailing_delimiter_cell(
    cells: list[str],
    expected_length: int | None = None,
) -> list[str]:
    """移除来源每行末尾额外制表符产生的空单元格。"""
    result = list(cells)
    if expected_length is None:
        while result and strip_cell(result[-1]) == "":
            result.pop()
        return result

    while (
        len(result) > expected_length
        and strip_cell(result[-1]) == ""
    ):
        result.pop()
    return result


def iter_source_rows(
    file_path: Path,
    *,
    encoding: str,
    delimiter: str,
) -> Iterator[tuple[int, list[str]]]:
    """逐行读取来源文件，返回物理行号和原始单元格。"""
    with file_path.open(
        "r",
        encoding=encoding,
        newline="",
        errors="strict",
    ) as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for physical_line_number, cells in enumerate(reader, start=1):
            yield physical_line_number, cells


def parse_source_file(
    file_path: Path,
    *,
    dataset: DatasetSpec,
    contract: DailyFundsContract,
    ingest_batch_id: str,
    ingested_at: datetime,
    sample_limit: int = 2,
) -> ParsedSourceFile:
    """完整扫描一个来源文件并生成解析摘要。"""
    snapshot_date = parse_snapshot_date_from_path(file_path)
    source_hash = file_sha256(file_path)
    schema_index = contract.schema_index()

    iterator = iter_source_rows(
        file_path,
        encoding=contract.source_encoding,
        delimiter=contract.source_delimiter,
    )
    try:
        header_line_number, header_cells = next(iterator)
    except StopIteration as exc:
        raise DailyFundsIngestError(
            f"空文件：{file_path}"
        ) from exc

    header_cells = _trim_trailing_delimiter_cell(header_cells)
    exact_hash = header_fingerprint(header_cells)
    known_schema = schema_index.get(
        (dataset.dataset_id, exact_hash)
    )

    anomaly_codes: list[str] = []
    anomaly_details: list[str] = []
    if known_schema is None:
        anomaly_codes.append("UNKNOWN_SCHEMA")
        anomaly_details.append(
            f"unknown_header_sha256={exact_hash}"
        )
        schema_version = None
        expected_header = [strip_cell(item) for item in header_cells]
    else:
        schema_version = known_schema.schema_version
        expected_header = list(known_schema.headers)

    deduplicated_header = deduplicate_headers(expected_header)
    expected_length = len(expected_header)
    row_count = 0
    malformed_row_count = 0
    missing_cell_count = 0
    normalization_error_count = 0
    keys: list[str] = []
    samples: list[dict[str, Any]] = []

    for physical_line_number, raw_cells in iterator:
        cells = _trim_trailing_delimiter_cell(
            raw_cells,
            expected_length=expected_length,
        )
        if not cells or all(strip_cell(item) == "" for item in cells):
            continue
        row_count += 1

        if len(cells) != expected_length:
            malformed_row_count += 1
            if malformed_row_count <= 10:
                anomaly_details.append(
                    "malformed_row:"
                    f"line={physical_line_number},"
                    f"expected={expected_length},"
                    f"actual={len(cells)}"
                )
            continue

        raw_row = {
            deduplicated_header[index]: strip_cell(value)
            for index, value in enumerate(cells)
        }
        missing_cell_count += sum(
            is_missing(value, contract.missing_tokens)
            for value in raw_row.values()
        )

        if known_schema is None:
            continue

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
        except Exception as exc:  # noqa: BLE001
            normalization_error_count += 1
            if normalization_error_count <= 10:
                anomaly_details.append(
                    "normalization_error:"
                    f"line={physical_line_number},"
                    f"type={type(exc).__name__},"
                    f"message={exc}"
                )
            continue

        keys.append(str(normalized["entity_key"]))
        if len(samples) < sample_limit:
            samples.append(normalized)

    duplicate_key_count = sum(
        count - 1
        for count in Counter(keys).values()
        if count > 1
    )
    if malformed_row_count:
        anomaly_codes.append("MALFORMED_ROW")
    if normalization_error_count:
        anomaly_codes.append("ROW_NORMALIZATION_FAILED")
    if duplicate_key_count:
        anomaly_codes.append("DUPLICATE_ENTITY_KEY")

    return ParsedSourceFile(
        dataset_id=dataset.dataset_id,
        snapshot_date=snapshot_date,
        file_path=file_path,
        file_size_bytes=file_path.stat().st_size,
        source_file_sha256=source_hash,
        schema_version=schema_version,
        exact_header_sha256=exact_hash,
        row_count=row_count,
        unique_key_count=len(set(keys)),
        duplicate_key_count=duplicate_key_count,
        malformed_row_count=malformed_row_count,
        missing_cell_count=missing_cell_count,
        normalization_error_count=normalization_error_count,
        entity_keys=frozenset(keys),
        normalized_samples=tuple(samples),
        anomaly_codes=tuple(anomaly_codes),
        anomaly_details=tuple(anomaly_details),
    )


def discover_snapshot_directories(root: Path) -> list[Path]:
    """发现根目录下一层的 YYYYMMDD 快照目录。"""
    if not root.exists():
        raise DailyFundsIngestError(
            f"数据根目录不存在：{root}"
        )
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and DATE_DIR_PATTERN.fullmatch(path.name)
    )


def _file_result_row(
    result: ParsedSourceFile,
    *,
    family: str,
    status: str,
    quarantine_reason: str = "",
) -> dict[str, Any]:
    return {
        "snapshot_date": result.snapshot_date.strftime("%Y%m%d"),
        "dataset_id": result.dataset_id,
        "family": family,
        "file_name": result.file_path.name,
        "file_size_bytes": result.file_size_bytes,
        "source_file_sha256": result.source_file_sha256,
        "schema_version": result.schema_version or "",
        "exact_header_sha256": result.exact_header_sha256,
        "row_count": result.row_count,
        "unique_key_count": result.unique_key_count,
        "duplicate_key_count": result.duplicate_key_count,
        "malformed_row_count": result.malformed_row_count,
        "missing_cell_count": result.missing_cell_count,
        "normalization_error_count": result.normalization_error_count,
        "status": status,
        "quarantine_reason": quarantine_reason,
        "anomaly_codes": "|".join(result.anomaly_codes),
        "anomaly_details": "|".join(result.anomaly_details),
    }


def _write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> None:
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def run_daily_funds_preflight(
    *,
    root: Path,
    contract_path: Path,
    output_dir: Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """执行全量只读预导入并写出报告。"""
    contract = load_daily_funds_contract(contract_path)
    contract_report = validate_daily_funds_contract(contract)
    if contract_report["overall_status"] != "PASSED":
        raise DailyFundsIngestError(
            f"来源合同校验失败：{contract_report['issues']}"
        )

    generated_at = generated_at or datetime.now(timezone.utc)
    ingest_batch_id = (
        "task016a_"
        + generated_at.astimezone(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    date_dirs = discover_snapshot_directories(root)
    file_results: list[dict[str, Any]] = []
    anomaly_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    sample_payload: dict[str, list[dict[str, Any]]] = {
        dataset_id: [] for dataset_id in contract.datasets
    }
    schema_usage: Counter[tuple[str, str]] = Counter()
    parsed_by_date: dict[
        str, dict[str, ParsedSourceFile]
    ] = {}
    family_by_dataset = {
        dataset_id: spec.family
        for dataset_id, spec in contract.datasets.items()
    }

    for date_dir in date_dirs:
        date_results: dict[str, ParsedSourceFile] = {}
        for dataset_id, dataset in contract.datasets.items():
            file_path = date_dir / dataset.file_name
            if not file_path.exists():
                anomaly_rows.append(
                    {
                        "severity": "WARNING",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": "MISSING_FILE",
                        "detail": dataset.file_name,
                    }
                )
                continue

            try:
                result = parse_source_file(
                    file_path,
                    dataset=dataset,
                    contract=contract,
                    ingest_batch_id=ingest_batch_id,
                    ingested_at=generated_at,
                )
            except Exception as exc:  # noqa: BLE001
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": "FILE_READ_FAILED",
                        "detail": (
                            f"{type(exc).__name__}: {exc}"
                        ),
                    }
                )
                continue

            date_results[dataset_id] = result
            if result.schema_version is not None:
                schema_usage[
                    (dataset_id, result.schema_version)
                ] += 1
            sample_payload[dataset_id].extend(
                list(result.normalized_samples)
            )
            sample_payload[dataset_id] = sample_payload[
                dataset_id
            ][:3]

            initial_status = (
                "BLOCKED"
                if result.has_blocking_parse_error
                else "READY"
            )
            file_results.append(
                _file_result_row(
                    result,
                    family=dataset.family,
                    status=initial_status,
                )
            )
            anomaly_summaries = {
                "UNKNOWN_SCHEMA": (
                    f"header_sha256={result.exact_header_sha256}"
                ),
                "MALFORMED_ROW": (
                    f"malformed_row_count="
                    f"{result.malformed_row_count}"
                ),
                "DUPLICATE_ENTITY_KEY": (
                    f"duplicate_key_count="
                    f"{result.duplicate_key_count}"
                ),
                "ROW_NORMALIZATION_FAILED": (
                    f"normalization_error_count="
                    f"{result.normalization_error_count}"
                ),
            }
            for code in result.anomaly_codes:
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": code,
                        "detail": anomaly_summaries.get(
                            code,
                            "|".join(result.anomaly_details),
                        ),
                    }
                )
        parsed_by_date[date_dir.name] = date_results

    # 覆盖门禁在全部文件解析后执行。
    quarantine_keys: dict[tuple[str, str], str] = {}
    for date_name, date_results in parsed_by_date.items():
        for child_id, gate in contract.coverage_gates.items():
            reference_id = str(
                gate.get("reference_dataset_id")
            )
            child = date_results.get(child_id)
            reference = date_results.get(reference_id)
            if child is None or reference is None:
                continue
            if (
                child.has_blocking_parse_error
                or reference.has_blocking_parse_error
            ):
                continue

            intersection = (
                child.entity_keys & reference.entity_keys
            )
            child_only = child.entity_keys - reference.entity_keys
            reference_only = (
                reference.entity_keys - child.entity_keys
            )
            ratio = (
                len(intersection) / len(reference.entity_keys)
                if reference.entity_keys
                else 0.0
            )
            threshold = float(
                gate.get("minimum_intersection_ratio", 0.95)
            )
            status = "PASSED" if ratio >= threshold else "FAILED"
            coverage_rows.append(
                {
                    "snapshot_date": date_name,
                    "dataset_id": child_id,
                    "reference_dataset_id": reference_id,
                    "intersection_count": len(intersection),
                    "child_only_count": len(child_only),
                    "reference_only_count": len(reference_only),
                    "coverage_ratio": round(ratio, 12),
                    "minimum_ratio": threshold,
                    "status": status,
                }
            )
            if status == "FAILED":
                reason = (
                    "UNIVERSE_COVERAGE_INCOMPLETE:"
                    f"{ratio:.6f}<{threshold:.6f}"
                )
                quarantine_keys[(date_name, child_id)] = reason
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_name,
                        "dataset_id": child_id,
                        "type": "UNIVERSE_COVERAGE_INCOMPLETE",
                        "detail": stable_json(
                            {
                                "reference_dataset_id": reference_id,
                                "intersection_count": len(
                                    intersection
                                ),
                                "child_only_count": len(child_only),
                                "reference_only_count": len(
                                    reference_only
                                ),
                                "coverage_ratio": ratio,
                                "minimum_ratio": threshold,
                                "action": gate.get(
                                    "failure_action",
                                    "QUARANTINE_FILE",
                                ),
                            }
                        ),
                    }
                )

    for row in file_results:
        key = (row["snapshot_date"], row["dataset_id"])
        if key in quarantine_keys and row["status"] == "READY":
            row["status"] = "QUARANTINED"
            row["quarantine_reason"] = quarantine_keys[key]

    blocking_files = [
        row for row in file_results if row["status"] == "BLOCKED"
    ]
    quarantined_files = [
        row
        for row in file_results
        if row["status"] == "QUARANTINED"
    ]
    importable_files = [
        row for row in file_results if row["status"] == "READY"
    ]

    dataset_counts: dict[str, dict[str, int]] = {}
    for dataset_id in contract.datasets:
        rows = [
            row
            for row in file_results
            if row["dataset_id"] == dataset_id
        ]
        dataset_counts[dataset_id] = {
            "profiled_file_count": len(rows),
            "ready_file_count": sum(
                row["status"] == "READY" for row in rows
            ),
            "quarantined_file_count": sum(
                row["status"] == "QUARANTINED" for row in rows
            ),
            "blocked_file_count": sum(
                row["status"] == "BLOCKED" for row in rows
            ),
            "parsed_row_count": sum(
                int(row["row_count"]) for row in rows
            ),
            "planned_insert_row_count": sum(
                int(row["row_count"])
                for row in rows
                if row["status"] == "READY"
            ),
        }

    family_insert_counts: Counter[str] = Counter()
    for row in importable_files:
        family_insert_counts[str(row["family"])] += int(
            row["row_count"]
        )

    missing_count = sum(
        item["type"] == "MISSING_FILE"
        for item in anomaly_rows
    )
    unknown_schema_count = sum(
        item["type"] == "UNKNOWN_SCHEMA"
        for item in anomaly_rows
    )
    parser_error_count = sum(
        item["type"]
        in {
            "FILE_READ_FAILED",
            "UNKNOWN_SCHEMA",
            "MALFORMED_ROW",
            "DUPLICATE_ENTITY_KEY",
            "ROW_NORMALIZATION_FAILED",
        }
        for item in anomaly_rows
    )

    if blocking_files or parser_error_count:
        overall_status = "BLOCKED"
    elif quarantined_files:
        overall_status = "READY_WITH_QUARANTINE"
    else:
        overall_status = "READY"

    schema_usage_rows = [
        {
            "dataset_id": dataset_id,
            "schema_version": schema_version,
            "file_count": file_count,
        }
        for (
            dataset_id,
            schema_version,
        ), file_count in sorted(schema_usage.items())
    ]

    summary = {
        "task_id": "TASK_016A",
        "generated_at": generated_at.isoformat(),
        "ingest_batch_id": ingest_batch_id,
        "scan_root": str(root),
        "contract_path": str(contract_path),
        "contract_version": contract.contract_version,
        "overall_status": overall_status,
        "snapshot_directory_count": len(date_dirs),
        "profiled_file_count": len(file_results),
        "ready_file_count": len(importable_files),
        "quarantined_file_count": len(quarantined_files),
        "blocked_file_count": len(blocking_files),
        "missing_file_warning_count": missing_count,
        "unknown_schema_count": unknown_schema_count,
        "parsed_row_count": sum(
            int(row["row_count"]) for row in file_results
        ),
        "planned_insert_row_count": sum(
            int(row["row_count"]) for row in importable_files
        ),
        "quarantined_row_count": sum(
            int(row["row_count"])
            for row in quarantined_files
        ),
        "dataset_counts": dataset_counts,
        "physical_table_write_plan": {
            contract.database_plan.get(
                "physical_tables", {}
            ).get(
                family, family
            ): count
            for family, count in sorted(
                family_insert_counts.items()
            )
        },
        "database_plan": contract.database_plan,
        "safety_decisions": [
            "TASK_016A不连接或修改DolphinDB。",
            "未知Schema、畸形行、重复实体键和标准化错误会阻断。",
            "覆盖率不足的文件进入隔离，不写入主Raw表。",
            "缺失文件只登记WARNING，不伪造记录。",
            "source_file_mtime仅保留为证据，不等同available_at。",
            "资金流流出字段保持来源负号，不再次取负。",
            "分类名称只作为source node_name_raw，不伪造稳定node_id。",
        ],
        "next_gate": (
            "TASK_016B_CREATE_TABLES_AND_IMPORT"
            if overall_status == "READY_WITH_QUARANTINE"
            else "RESOLVE_PREFLIGHT_BLOCKERS"
        ),
    }

    file_fields = [
        "snapshot_date",
        "dataset_id",
        "family",
        "file_name",
        "file_size_bytes",
        "source_file_sha256",
        "schema_version",
        "exact_header_sha256",
        "row_count",
        "unique_key_count",
        "duplicate_key_count",
        "malformed_row_count",
        "missing_cell_count",
        "normalization_error_count",
        "status",
        "quarantine_reason",
        "anomaly_codes",
        "anomaly_details",
    ]
    anomaly_fields = [
        "severity",
        "snapshot_date",
        "dataset_id",
        "type",
        "detail",
    ]
    coverage_fields = [
        "snapshot_date",
        "dataset_id",
        "reference_dataset_id",
        "intersection_count",
        "child_only_count",
        "reference_only_count",
        "coverage_ratio",
        "minimum_ratio",
        "status",
    ]

    _write_csv(
        output_dir / "task_016a_file_results.csv",
        file_results,
        file_fields,
    )
    _write_csv(
        output_dir / "task_016a_anomalies.csv",
        anomaly_rows,
        anomaly_fields,
    )
    _write_csv(
        output_dir / "task_016a_coverage_checks.csv",
        coverage_rows,
        coverage_fields,
    )
    _write_csv(
        output_dir / "task_016a_schema_usage.csv",
        schema_usage_rows,
        ["dataset_id", "schema_version", "file_count"],
    )

    (
        output_dir / "task_016a_normalized_samples.json"
    ).write_text(
        json.dumps(
            _json_safe(sample_payload),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary_path = (
        output_dir / "task_016a_preflight_summary.json"
    )
    summary_path.write_text(
        json.dumps(
            _json_safe(summary),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    markdown = _build_preflight_markdown(summary)
    (
        output_dir / "task_016a_preflight_summary.md"
    ).write_text(markdown, encoding="utf-8")

    return summary


def _build_preflight_markdown(
    summary: dict[str, Any],
) -> str:
    """构建人类可读预导入报告。"""
    dataset_lines = []
    for dataset_id, counts in summary["dataset_counts"].items():
        dataset_lines.append(
            "| {dataset} | {files} | {ready} | {quarantine} | "
            "{blocked} | {rows} | {planned} |".format(
                dataset=dataset_id,
                files=counts["profiled_file_count"],
                ready=counts["ready_file_count"],
                quarantine=counts[
                    "quarantined_file_count"
                ],
                blocked=counts["blocked_file_count"],
                rows=counts["parsed_row_count"],
                planned=counts[
                    "planned_insert_row_count"
                ],
            )
        )

    table_lines = [
        f"| {table_name} | {row_count} |"
        for table_name, row_count in summary[
            "physical_table_write_plan"
        ].items()
    ]

    return f"""# TASK_016A 日线资金预导入报告

总体状态：**{summary['overall_status']}**

## 一、扫描结果

- 快照目录：{summary['snapshot_directory_count']}
- 已画像文件：{summary['profiled_file_count']}
- 可写入文件：{summary['ready_file_count']}
- 隔离文件：{summary['quarantined_file_count']}
- 阻断文件：{summary['blocked_file_count']}
- 缺失文件警告：{summary['missing_file_warning_count']}
- 已解析行：{summary['parsed_row_count']}
- 计划写入行：{summary['planned_insert_row_count']}
- 隔离行：{summary['quarantined_row_count']}

## 二、七类数据

| 数据集 | 文件 | Ready | Quarantine | Blocked | 解析行 | 计划写入 |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(dataset_lines)}

## 三、物理表写入计划

| 物理表 | 计划行数 |
|---|---:|
{chr(10).join(table_lines)}

## 四、安全边界

{chr(10).join(f"- {item}" for item in summary['safety_decisions'])}

## 五、下一门禁

`{summary['next_gate']}`

TASK_016A没有连接或修改DolphinDB。
"""


__all__ = [
    "DailyFundsContract",
    "DailyFundsIngestError",
    "DatasetSpec",
    "KnownSchema",
    "ParsedSourceFile",
    "deduplicate_headers",
    "discover_snapshot_directories",
    "header_fingerprint",
    "infer_market_candidate",
    "load_daily_funds_contract",
    "normalize_instrument_code",
    "normalize_row",
    "parse_breadth_counts",
    "parse_breadth_ratio",
    "parse_snapshot_date_from_path",
    "parse_source_file",
    "parse_source_int",
    "parse_source_number",
    "run_daily_funds_preflight",
    "validate_daily_funds_contract",
]
