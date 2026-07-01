# 测试模块总览：验证 `test_daily_funds_ingest` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试函数 `_base_value`：封装 `_base_value` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：header、code、name。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _base_value(header: str, code: str, name: str) -> str:
    # 测试分支：根据 `header == '序'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "序":
        return "1"
    # 测试分支：根据 `header == '代码'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "代码":
        return f'= "{code}"'
    # 测试分支：根据 `header == '名称'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "名称":
        return name
    # 测试分支：根据 `header == '所属行业'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "所属行业":
        return "测试行业"
    # 测试分支：根据 `header == '领涨股'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "领涨股":
        return "测试股票"
    # 测试分支：根据 `header == '涨跌家数'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "涨跌家数":
        return "7/3"
    # 测试分支：根据 `header == '涨跌比'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "涨跌比":
        return "2.33"
    # 测试分支：根据 `header == '涨停家数'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "涨停家数":
        return "1"
    # 测试分支：根据 `header in {'总量', '总手', '现量', '现手'}` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header in {"总量", "总手", "现量", "现手"}:
        return "1.25万"
    # 测试分支：根据 `header in {'内盘', '外盘', '买一量', '卖一量', '委差', '成交量'}` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header in {
        "内盘",
        "外盘",
        "买一量",
        "卖一量",
        "委差",
        "成交量",
    }:
        return "1000"
    # 测试分支：根据 `header in {'金额', '总市值', '流通市值', '主力净流入', '集合竞价', '超大单流入', '超大单净额', '大单流入', '大单净额', '中单流入', '中单净额', '小单流入…` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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
    # 测试分支：根据 `'流出' in header` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if "流出" in header:
        return "-5000万"
    # 测试分支：根据 `header in {'总股本', '流通股本', '平均股本'}` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header in {"总股本", "流通股本", "平均股本"}:
        return "2.5亿"
    # 测试分支：根据 `header == '上市日'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header == "上市日":
        return "20200101"
    # 测试分支：根据 `header in {'连涨天数', '连涨天数1'}` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if header in {"连涨天数", "连涨天数1"}:
        return "2"
    return "1.25"


# 测试函数 `_write_source_file`：封装 `_write_source_file` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：path、headers、codes、names。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
    # 测试分支：根据 `len(names) != len(codes)` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if len(names) != len(codes):
        raise AssertionError("names和codes长度必须一致")

    # 测试上下文：通过 `path.open('w', encoding='gb18030', newline='')` 管理异常断言、临时资源或子测试范围。
    # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
    # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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
        # 参数化循环：逐项使用 `enumerate(zip(codes, names), start=1)` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
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


# 测试类 `TestDailyFundsIngest`：集中验证 `test_daily_funds_ingest` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyFundsIngest(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.contract = load_daily_funds_contract(CONTRACT_PATH)

    # 测试函数 `test_contract_has_seven_datasets_and_thirteen_schemas`：验证 `contract、has、seven、datasets、and、thirteen、schemas` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_has_seven_datasets_and_thirteen_schemas(
        self,
    ) -> None:
        report = validate_daily_funds_contract(self.contract)
        self.assertEqual(report["overall_status"], "PASSED")
        self.assertEqual(report["dataset_count"], 7)
        self.assertEqual(report["schema_count"], 13)

    # 测试函数 `test_chinese_magnitude_parser_and_missing`：验证 `chinese、magnitude、parser、and、missing` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_formula_like_code_normalization`：验证 `formula、like、code、normalization` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_formula_like_code_normalization(self) -> None:
        self.assertEqual(
            normalize_instrument_code('= "000001"'),
            "000001",
        )
        self.assertEqual(
            normalize_instrument_code('="920786"'),
            "920786",
        )
        # 测试上下文：通过 `self.assertRaises(DailyFundsIngestError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DailyFundsIngestError):
            normalize_instrument_code("测试")

    # 测试函数 `test_duplicate_headers_are_preserved`：验证 `duplicate、headers、are、preserved` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_headers_are_preserved(self) -> None:
        self.assertEqual(
            deduplicate_headers(
                ["名称", "今年涨幅%", "今年涨幅%"]
            ),
            ["名称", "今年涨幅%", "今年涨幅%__2"],
        )

    # 测试函数 `test_money_flow_outflow_sign_is_preserved`：验证 `money、flow、outflow、sign、is、preserved` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_money_flow_outflow_sign_is_preserved(self) -> None:
        dataset = self.contract.datasets["zj"]
        schema = dataset.schemas[0]
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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

    # 测试函数 `test_all_up_breadth_does_not_create_infinity`：验证 `all、up、breadth、does、not、create、infinity` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_up_breadth_does_not_create_infinity(self) -> None:
        ratio, status = parse_breadth_ratio(
            "全涨",
            up_count=46,
            down_count=0,
        )
        self.assertIsNone(ratio)
        self.assertEqual(status, "ALL_UP")

    # 测试函数 `test_incomplete_kphq_is_quarantined`：验证 `incomplete、kphq、is、quarantined` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_incomplete_kphq_is_quarantined(self) -> None:
        hq_schema = self.contract.datasets["hq"].schemas[0]
        kphq_schema = self.contract.datasets["kphq"].schemas[0]

        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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

            # 测试上下文：通过 `(output_dir / 'task_016a_file_results.csv').open(encoding='utf-8-sig', newline='')` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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

    # 测试函数 `test_unknown_header_blocks_preflight`：验证 `unknown、header、blocks、preflight` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_header_blocks_preflight(self) -> None:
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
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
