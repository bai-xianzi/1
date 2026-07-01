# 测试模块总览：验证 `test_data_readiness_external_evidence` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from a_stock_quant.data_contracts import QualityStatus
from a_stock_quant.data_readiness import (
    EvidenceStatus,
    ReadinessDimension,
)
from a_stock_quant.data_readiness_evidence import (
    EvidenceBuildContext,
    load_evidence_rule_config,
)
from a_stock_quant.data_readiness_external_evidence import (
    ExternalEvidenceOverlayBuilder,
    ReportBackedEvidenceResolver,
    load_activation_registry,
    load_external_evidence_config,
    load_trading_calendar,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryMetadata,
    StandardQueryResult,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_DIR = PROJECT_ROOT / "configs" / "quality"


# 测试函数 `_write_json`：封装 `_write_json` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：path、payload。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# 测试函数 `_daily_k_report`：封装 `_daily_k_report` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _daily_k_report() -> dict:
    return {
        "dataset_id": "a_stock_daily_k",
        "overall_status": "PASSED",
        "blocks_downstream": False,
        "database_summary": {
            "row_count": 16548275,
            "entity_count": 5523,
            "min_data_date": "1990-12-19T00:00:00",
            "max_data_date": "2026-05-29T00:00:00",
        },
        "coverage_evaluation": {
            "declared_cutoff_date": "2026-05-29",
            "database_max_date": "2026-05-29",
            "database_matches_declared_cutoff": True,
        },
    }


# 测试函数 `_fundamental_report`：封装 `_fundamental_report` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _fundamental_report() -> dict:
    return {
        "overall_status": "PENDING_CONFIRMATION",
        "blocks_downstream": True,
        "blocks_strict_historical_backtest": True,
        "allows_current_snapshot_research": True,
        "summary": {
            "row_count": 5541,
            "stock_count": 5541,
            "min_snapshot_date": "2026-06-19T00:00:00",
            "max_snapshot_date": "2026-06-19T00:00:00",
        },
        "duplicate_summary": {
            "duplicate_group_count": 0,
            "duplicate_extra_row_count": 0,
        },
    }


# 测试函数 `_funds_canonical_report`：封装 `_funds_canonical_report` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _funds_canonical_report() -> dict:
    return {
        "task_id": "TASK_017C",
        "coverage_version": (
            "daily-funds-raw@2025-11-20..2025-12-31"
        ),
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": [
            {
                "dataset_id": dataset_id,
                "result_count": 1,
            }
            for dataset_id in (
                "hq",
                "hy",
                "gn",
                "kphq",
                "kphy",
                "kpgn",
                "zj",
            )
        ],
    }


# 测试函数 `_funds_service_report`：封装 `_funds_service_report` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def _funds_service_report() -> dict:
    selector_modes = {
        "hq": "INSTRUMENT_ID",
        "hy": "ENTITY_ID",
        "gn": "ENTITY_ID",
        "kphq": "INSTRUMENT_ID",
        "kphy": "ENTITY_ID",
        "kpgn": "ENTITY_ID",
        "zj": "INSTRUMENT_ID",
    }
    return {
        "task_id": "TASK_017D",
        "overall_status": "PASSED_WITH_WARNINGS",
        "datasets": [
            {
                "dataset_id": dataset_id,
                "result_count": 1,
                "selector_mode": selector_modes[dataset_id],
            }
            for dataset_id in selector_modes
        ],
    }


# 测试类 `ExternalEvidenceTests`：集中验证 `test_data_readiness_external_evidence` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class ExternalEvidenceTests(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(
            QUALITY_DIR,
            self.root / "configs" / "quality",
        )
        _write_json(
            self.root
            / "reports"
            / "task_008_dataset_coverage.json",
            _daily_k_report(),
        )
        _write_json(
            self.root
            / "reports"
            / "task_013_fundamental_profile.json",
            _fundamental_report(),
        )
        _write_json(
            self.root
            / "reports"
            / "task_017c_real_acceptance.json",
            _funds_canonical_report(),
        )
        _write_json(
            self.root
            / "reports"
            / "task_017d_real_acceptance.json",
            _funds_service_report(),
        )
        self.resolver = ReportBackedEvidenceResolver.from_project(
            project_root=self.root,
            config_path=(
                "configs/quality/"
                "data_readiness_external_evidence_v0.json"
            ),
        )

    # 测试函数 `tearDown`：清理本组测试创建的临时状态和外部资源。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def tearDown(self) -> None:
        self.tmp.cleanup()

    # 测试函数 `test_calendar_latest_trading_day`：验证 `calendar、latest、trading、day` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_calendar_latest_trading_day(self) -> None:
        calendar = load_trading_calendar(
            QUALITY_DIR / "a_share_trading_calendar_2026.json"
        )
        self.assertEqual(
            calendar.latest_trading_day(date(2026, 6, 27)),
            date(2026, 6, 26),
        )
        self.assertFalse(
            calendar.is_trading_day(date(2026, 6, 19))
        )
        self.assertTrue(
            calendar.is_trading_day(date(2026, 6, 22))
        )

    # 测试函数 `test_daily_k_trading_session_lag_is_19`：验证 `daily、k、trading、session、lag、is、19` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_k_trading_session_lag_is_19(self) -> None:
        evidence = self.resolver.freshness_evidence(
            "a_stock_daily_k",
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            date(2026, 6, 27),
        )
        self.assertEqual(
            evidence.metrics["trading_session_lag"],
            19,
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.WARNING,
        )

    # 测试函数 `test_fundamental_lag_within_research_sla`：验证 `fundamental、lag、within、research、sla` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_fundamental_lag_within_research_sla(self) -> None:
        evidence = self.resolver.freshness_evidence(
            "a_stock_fundamental_snapshot",
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            date(2026, 6, 27),
        )
        self.assertEqual(
            evidence.metrics["trading_session_lag"],
            5,
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.PASSED,
        )

    # 测试函数 `test_daily_funds_are_stale_for_current_research`：验证 `daily、funds、are、stale、for、current、research` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_funds_are_stale_for_current_research(self) -> None:
        evidence = self.resolver.freshness_evidence(
            "hq",
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            date(2026, 6, 27),
        )
        self.assertEqual(
            evidence.code,
            "TRADING_SESSION_LAG_EXCEEDS_SLA",
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.WARNING,
        )
        self.assertGreater(
            evidence.metrics["trading_session_lag"],
            1,
        )

    # 测试函数 `test_historical_freshness_is_not_currentness_gate`：验证 `historical、freshness、is、not、currentness、gate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_historical_freshness_is_not_currentness_gate(self) -> None:
        evidence = self.resolver.freshness_evidence(
            "hq",
            StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            date(2026, 6, 27),
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.PASSED,
        )
        self.assertIn(
            "NOT_APPLICABLE",
            evidence.code,
        )

    # 测试函数 `test_daily_k_coverage_is_passed`：验证 `daily、k、coverage、is、passed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_k_coverage_is_passed(self) -> None:
        evidence = self.resolver.coverage_evidence(
            "a_stock_daily_k"
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.PASSED,
        )
        self.assertEqual(
            evidence.metrics["entity_count"],
            5523,
        )

    # 测试函数 `test_fundamental_current_snapshot_coverage_passes`：验证 `fundamental、current、snapshot、coverage、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_fundamental_current_snapshot_coverage_passes(self) -> None:
        evidence = self.resolver.coverage_evidence(
            "a_stock_fundamental_snapshot"
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.PASSED,
        )
        self.assertEqual(
            evidence.metrics["entity_count"],
            5541,
        )

    # 测试函数 `test_daily_funds_coverage_remains_warning`：验证 `daily、funds、coverage、remains、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_funds_coverage_remains_warning(self) -> None:
        evidence = self.resolver.coverage_evidence("hy")
        self.assertEqual(
            evidence.status,
            EvidenceStatus.WARNING,
        )
        self.assertFalse(
            evidence.metrics[
                "exhaustive_entity_coverage_proven"
            ]
        )

    # 测试函数 `test_all_nine_current_research_activations_pass`：验证 `all、nine、current、research、activations、pass` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_nine_current_research_activations_pass(self) -> None:
        # 参数化循环：逐项使用 `self.resolver.config.datasets` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for dataset in self.resolver.config.datasets:
            # 测试上下文：通过 `self.subTest(dataset=dataset.dataset_id)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(dataset=dataset.dataset_id):
                evidence = self.resolver.activation_evidence(
                    dataset.dataset_id,
                    StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
                    date(2026, 6, 27),
                )
                self.assertEqual(
                    evidence.status,
                    EvidenceStatus.PASSED,
                )

    # 测试函数 `test_only_daily_k_historical_activation_passes`：验证 `only、daily、k、historical、activation、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_only_daily_k_historical_activation_passes(self) -> None:
        passed = []
        failed = []
        # 参数化循环：逐项使用 `self.resolver.config.datasets` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for dataset in self.resolver.config.datasets:
            evidence = self.resolver.activation_evidence(
                dataset.dataset_id,
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
                date(2026, 6, 27),
            )
            # 测试分支：根据 `evidence.status is EvidenceStatus.PASSED` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if evidence.status is EvidenceStatus.PASSED:
                passed.append(dataset.dataset_id)
            else:
                failed.append(dataset.dataset_id)
        self.assertEqual(passed, ["a_stock_daily_k"])
        self.assertEqual(len(failed), 8)

    # 测试函数 `test_manual_decision_activation_is_denied`：验证 `manual、decision、activation、is、denied` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manual_decision_activation_is_denied(self) -> None:
        # 参数化循环：逐项使用 `self.resolver.config.datasets` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for dataset in self.resolver.config.datasets:
            # 测试上下文：通过 `self.subTest(dataset=dataset.dataset_id)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(dataset=dataset.dataset_id):
                evidence = self.resolver.activation_evidence(
                    dataset.dataset_id,
                    StandardDataUsage.MANUAL_DECISION_SUPPORT,
                    date(2026, 6, 27),
                )
                self.assertEqual(
                    evidence.status,
                    EvidenceStatus.FAILED,
                )

    # 测试函数 `test_resolve_returns_three_external_dimensions`：验证 `resolve、returns、three、external、dimensions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_resolve_returns_three_external_dimensions(self) -> None:
        evidence = self.resolver.resolve(
            dataset_id="hq",
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
            as_of_date=date(2026, 6, 27),
        )
        self.assertEqual(
            {item.dimension for item in evidence},
            {
                ReadinessDimension.COVERAGE,
                ReadinessDimension.FRESHNESS,
                ReadinessDimension.ACTIVATION,
            },
        )

    # 测试函数 `test_config_and_activation_have_same_nine_datasets`：验证 `config、and、activation、have、same、nine、datasets` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_config_and_activation_have_same_nine_datasets(self) -> None:
        config = load_external_evidence_config(
            QUALITY_DIR
            / "data_readiness_external_evidence_v0.json"
        )
        activations = load_activation_registry(
            QUALITY_DIR
            / "data_readiness_dataset_activation_v0.json"
        )
        self.assertEqual(len(config.datasets), 9)
        self.assertEqual(
            {item.dataset_id for item in config.datasets},
            set(activations),
        )

    # 测试函数 `_query_result`：封装 `_query_result` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _query_result(self) -> tuple[
        StandardQueryResult,
        ProviderDescriptor,
    ]:
        query = StandardDataQuery(
            dataset_id="a_stock_daily_k",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2026, 5, 29),
            end_date=date(2026, 5, 29),
            as_of_date=date(2026, 6, 27),
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
        )
        record = StandardDataRecord(
            canonical_object="DailyBar",
            primary_key={
                "instrument_id": "000001",
                "trade_date": date(2026, 5, 29),
            },
            values={
                "instrument_id": "000001",
                "trade_date": date(2026, 5, 29),
            },
            source_record_id="daily-k:000001:2026-05-29",
            lineage=(
                {
                    "canonical_field": "trade_date",
                    "source_field": "trade_date",
                },
            ),
        )
        metadata = StandardQueryMetadata(
            dataset_id="a_stock_daily_k",
            canonical_object="DailyBar",
            provider_id=(
                "dolphindb_daily_k_standard_provider"
            ),
            coverage_version="a_stock_daily_k@2026-05-29",
            mapping_version="0.1.0",
            dictionary_revision="0.6.0",
            source_row_count=1,
            result_count=1,
            status=QualityStatus.PASSED,
            blocks_downstream=False,
            lineage_item_count=1,
        )
        descriptor = ProviderDescriptor(
            provider_id=metadata.provider_id,
            dataset_id=query.dataset_id,
            supported_objects=("DailyBar",),
            coverage_version=metadata.coverage_version,
            mapping_version=metadata.mapping_version,
            dictionary_revision=metadata.dictionary_revision,
        )
        return (
            StandardQueryResult(
                query=query,
                metadata=metadata,
                records=(record,),
            ),
            descriptor,
        )

    # 测试函数 `test_overlay_replaces_three_generic_dimensions`：验证 `overlay、replaces、three、generic、dimensions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_overlay_replaces_three_generic_dimensions(self) -> None:
        rules = load_evidence_rule_config(
            QUALITY_DIR
            / "data_readiness_evidence_rules_v0.json"
        )
        builder = ExternalEvidenceOverlayBuilder(
            base_rules=rules,
            resolver=self.resolver,
        )
        result, descriptor = self._query_result()
        evidence = builder.build(
            result,
            descriptor,
            EvidenceBuildContext(),
        )
        by_dimension = {
            item.dimension: item
            for item in evidence
        }
        self.assertEqual(len(by_dimension), 8)
        self.assertEqual(
            by_dimension[ReadinessDimension.COVERAGE].code,
            "FULL_DATABASE_SNAPSHOT_COVERAGE_PROVEN",
        )
        self.assertEqual(
            by_dimension[ReadinessDimension.FRESHNESS].code,
            "TRADING_SESSION_LAG_EXCEEDS_SLA",
        )
        self.assertEqual(
            by_dimension[ReadinessDimension.ACTIVATION].code,
            "DATASET_USAGE_ACTIVATION_VERIFIED",
        )

    # 测试函数 `test_external_evidence_references_reports_and_calendar`：验证 `external、evidence、references、reports、and、calendar` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_external_evidence_references_reports_and_calendar(self) -> None:
        evidence = self.resolver.coverage_evidence("hq")
        self.assertTrue(
            any(
                ref.startswith("report:")
                for ref in evidence.evidence_refs
            )
        )
        self.assertTrue(
            any(
                ref.startswith("calendar:")
                for ref in evidence.evidence_refs
            )
        )

    # 测试函数 `test_bad_daily_k_report_fails_coverage`：验证 `bad、daily、k、report、fails、coverage` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_bad_daily_k_report_fails_coverage(self) -> None:
        report_path = (
            self.root
            / "reports"
            / "task_008_dataset_coverage.json"
        )
        payload = _daily_k_report()
        payload["overall_status"] = "FAILED"
        _write_json(report_path, payload)
        resolver = ReportBackedEvidenceResolver.from_project(
            project_root=self.root,
            config_path=(
                "configs/quality/"
                "data_readiness_external_evidence_v0.json"
            ),
        )
        evidence = resolver.coverage_evidence(
            "a_stock_daily_k"
        )
        self.assertEqual(
            evidence.status,
            EvidenceStatus.FAILED,
        )

    # 测试函数 `test_missing_report_is_rejected`：验证 `missing、report、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_report_is_rejected(self) -> None:
        (
            self.root
            / "reports"
            / "task_008_dataset_coverage.json"
        ).unlink()
        resolver = ReportBackedEvidenceResolver.from_project(
            project_root=self.root,
            config_path=(
                "configs/quality/"
                "data_readiness_external_evidence_v0.json"
            ),
        )
        # 测试上下文：通过 `self.assertRaises(Exception)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(Exception):
            resolver.coverage_evidence("a_stock_daily_k")

    # 测试函数 `test_unknown_dataset_is_rejected`：验证 `unknown、dataset、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_dataset_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(Exception)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(Exception):
            self.resolver.coverage_evidence("unknown")


if __name__ == "__main__":
    unittest.main()
