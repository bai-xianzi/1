from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.daily_funds_ingest import (  # noqa: E402
    DailyFundsIngestError,
    deduplicate_headers,
    header_fingerprint,
    load_daily_funds_contract,
    normalize_instrument_code,
    parse_breadth_ratio,
    parse_source_file,
    parse_source_number,
    run_daily_funds_preflight,
    validate_daily_funds_contract,
)


CONTRACT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_daily_funds_raw.yaml"
)


def _base_value(header: str, code: str, name: str) -> str:
    if header == "序":
        return "1"
    if header == "代码":
        return f'= "{code}"'
    if header == "名称":
        return name
    if header == "所属行业":
        return "测试行业"
    if header == "领涨股":
        return "测试股票"
    if header == "涨跌家数":
        return "7/3"
    if header == "涨跌比":
        return "2.33"
    if header == "涨停家数":
        return "1"
    if header in {"总量", "总手", "现量", "现手"}:
        return "1.25万"
    if header in {
        "内盘",
        "外盘",
        "买一量",
        "卖一量",
        "委差",
        "成交量",
    }:
        return "1000"
    if header in {
        "金额",
        "总市值",
        "流通市值",
        "主力净流入",
        "集合竞价",
        "超大单流入",
        "超大单净额",
        "大单流入",
        "大单净额",
        "中单流入",
        "中单净额",
        "小单流入",
        "小单净额",
    }:
        return "1.25亿"
    if "流出" in header:
        return "-5000万"
    if header in {"总股本", "流通股本", "平均股本"}:
        return "2.5亿"
    if header == "上市日":
        return "20200101"
    if header in {"连涨天数", "连涨天数1"}:
        return "2"
    return "1.25"


def _write_source_file(
    path: Path,
    headers: list[str],
    *,
    codes: list[str] | None = None,
    names: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    codes = codes or ["000001"]
    names = names or [f"测试{i}" for i in range(len(codes))]
    if len(names) != len(codes):
        raise AssertionError("names和codes长度必须一致")

    with path.open(
        "w",
        encoding="gb18030",
        newline="",
    ) as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writerow(headers + [""])
        for index, (code, name) in enumerate(
            zip(codes, names),
            start=1,
        ):
            row = [
                str(index)
                if header == "序"
                else _base_value(header, code, name)
                for header in headers
            ]
            writer.writerow(row + [""])


class TestDailyFundsIngest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_daily_funds_contract(CONTRACT_PATH)

    def test_contract_has_seven_datasets_and_thirteen_schemas(
        self,
    ) -> None:
        report = validate_daily_funds_contract(self.contract)
        self.assertEqual(report["overall_status"], "PASSED")
        self.assertEqual(report["dataset_count"], 7)
        self.assertEqual(report["schema_count"], 13)

    def test_chinese_magnitude_parser_and_missing(self) -> None:
        self.assertEqual(
            parse_source_number("30.3万"),
            303000.0,
        )
        self.assertEqual(
            parse_source_number("3.97万亿"),
            3_970_000_000_000.0,
        )
        self.assertEqual(
            parse_source_number("-35.0亿"),
            -3_500_000_000.0,
        )
        self.assertIsNone(parse_source_number("—"))

    def test_formula_like_code_normalization(self) -> None:
        self.assertEqual(
            normalize_instrument_code('= "000001"'),
            "000001",
        )
        self.assertEqual(
            normalize_instrument_code('="920786"'),
            "920786",
        )
        with self.assertRaises(DailyFundsIngestError):
            normalize_instrument_code("测试")

    def test_duplicate_headers_are_preserved(self) -> None:
        self.assertEqual(
            deduplicate_headers(
                ["名称", "今年涨幅%", "今年涨幅%"]
            ),
            ["名称", "今年涨幅%", "今年涨幅%__2"],
        )

    def test_money_flow_outflow_sign_is_preserved(self) -> None:
        dataset = self.contract.datasets["zj"]
        schema = dataset.schemas[0]
        with tempfile.TemporaryDirectory() as tmp:
            file_path = (
                Path(tmp) / "20251231" / dataset.file_name
            )
            _write_source_file(
                file_path,
                list(schema.headers),
                codes=["000001"],
                names=["测试股票"],
            )
            result = parse_source_file(
                file_path,
                dataset=dataset,
                contract=self.contract,
                ingest_batch_id="test_batch",
                ingested_at=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
            )
            self.assertEqual(result.row_count, 1)
            sample = result.normalized_samples[0]
            self.assertEqual(
                sample["super_large_outflow_cny"],
                -50_000_000.0,
            )
            self.assertEqual(
                sample["outflow_sign_policy"],
                "PRESERVE_SOURCE_SIGN",
            )

    def test_all_up_breadth_does_not_create_infinity(self) -> None:
        ratio, status = parse_breadth_ratio(
            "全涨",
            up_count=46,
            down_count=0,
        )
        self.assertIsNone(ratio)
        self.assertEqual(status, "ALL_UP")

    def test_incomplete_kphq_is_quarantined(self) -> None:
        hq_schema = self.contract.datasets["hq"].schemas[0]
        kphq_schema = self.contract.datasets["kphq"].schemas[0]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            day = root / "20251223"
            hq_codes = [f"{index:06d}" for index in range(1, 21)]
            _write_source_file(
                day / "hq.xls",
                list(hq_schema.headers),
                codes=hq_codes,
                names=[f"股票{index}" for index in range(1, 21)],
            )
            _write_source_file(
                day / "kphq.xls",
                list(kphq_schema.headers),
                codes=["000001"],
                names=["股票1"],
            )
            output_dir = Path(tmp) / "out"
            summary = run_daily_funds_preflight(
                root=root,
                contract_path=CONTRACT_PATH,
                output_dir=output_dir,
                generated_at=datetime(
                    2026,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
            )
            self.assertEqual(
                summary["overall_status"],
                "READY_WITH_QUARANTINE",
            )
            self.assertEqual(
                summary["quarantined_file_count"],
                1,
            )
            self.assertEqual(
                summary["planned_insert_row_count"],
                20,
            )

            with (
                output_dir / "task_016a_file_results.csv"
            ).open(encoding="utf-8-sig", newline="") as handle:
                file_rows = list(csv.DictReader(handle))
            kphq_row = next(
                row
                for row in file_rows
                if row["dataset_id"] == "kphq"
            )
            self.assertEqual(
                kphq_row["status"],
                "QUARANTINED",
            )

    def test_unknown_header_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            file_path = root / "20251231" / "hq.xls"
            _write_source_file(
                file_path,
                ["序", "代码", "名称", "未知列"],
                codes=["000001"],
                names=["测试"],
            )
            summary = run_daily_funds_preflight(
                root=root,
                contract_path=CONTRACT_PATH,
                output_dir=Path(tmp) / "out",
                generated_at=datetime(
                    2026,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
            )
            self.assertEqual(
                summary["overall_status"],
                "BLOCKED",
            )
            self.assertEqual(summary["unknown_schema_count"], 1)


if __name__ == "__main__":
    unittest.main()
