from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    DataReadinessRequest,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.standard_data_service import StandardDataUsage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    PROJECT_ROOT
    / "configs"
    / "quality"
    / "data_readiness_policy_v0.json"
)


def make_evidence(
    *,
    overrides: dict[
        ReadinessDimension,
        EvidenceStatus,
    ] | None = None,
) -> tuple[ReadinessEvidence, ...]:
    overrides = overrides or {}
    return tuple(
        ReadinessEvidence(
            dimension=dimension,
            status=overrides.get(
                dimension,
                EvidenceStatus.PASSED,
            ),
            code=(
                "CHECK_PASSED"
                if overrides.get(
                    dimension,
                    EvidenceStatus.PASSED,
                )
                is EvidenceStatus.PASSED
                else "CHECK_NOT_PASSED"
            ),
            message=f"{dimension.value} evidence",
            metrics={"count": 1},
            evidence_refs=(f"report:{dimension.value}",),
        )
        for dimension in ReadinessDimension
    )


class DataReadinessContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_data_readiness_policy(
            POLICY_PATH
        )
        self.engine = DataReadinessEngine(self.policy)

    def request(
        self,
        *,
        usage: StandardDataUsage = (
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
        ),
        evidence: tuple[ReadinessEvidence, ...] | None = None,
    ) -> DataReadinessRequest:
        return DataReadinessRequest(
            dataset_id="a_stock_daily_k",
            usage=usage,
            evidence=evidence or make_evidence(),
            as_of_date=date(2026, 6, 27),
            decision_time=(
                datetime(
                    2026,
                    6,
                    27,
                    15,
                    30,
                    tzinfo=timezone.utc,
                )
                if usage
                is StandardDataUsage.MANUAL_DECISION_SUPPORT
                else None
            ),
        )

    def test_policy_loads_all_nine_datasets(self) -> None:
        self.assertEqual(
            len(self.policy.dataset_catalog),
            9,
        )
        self.assertEqual(
            {
                item.dataset_id
                for item in self.policy.dataset_catalog
            },
            {
                "a_stock_daily_k",
                "a_stock_fundamental_snapshot",
                "hq",
                "hy",
                "gn",
                "kphq",
                "kphy",
                "kpgn",
                "zj",
            },
        )

    def test_policy_covers_all_usages(self) -> None:
        self.assertEqual(
            set(self.policy.usage_policies),
            set(StandardDataUsage),
        )

    def test_all_passed_is_passed(self) -> None:
        result = self.engine.evaluate(self.request())
        self.assertEqual(
            result.status,
            ReadinessStatus.PASSED,
        )
        self.assertFalse(result.blocks_downstream)
        result.assert_usable()

    def test_current_research_freshness_warning_is_usable(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.FRESHNESS:
                        EvidenceStatus.WARNING,
                    }
                )
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.WARNING,
        )
        self.assertFalse(result.blocks_downstream)
        result.assert_usable()

    def test_current_research_temporal_unknown_is_warning(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.UNKNOWN,
                    }
                )
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.WARNING,
        )
        self.assertFalse(result.blocks_downstream)

    def test_missing_lineage_evidence_blocks(self) -> None:
        evidence = tuple(
            item
            for item in make_evidence()
            if item.dimension
            is not ReadinessDimension.LINEAGE
        )
        result = self.engine.evaluate(
            self.request(evidence=evidence)
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )
        self.assertTrue(result.blocks_downstream)
        self.assertIn(
            "LINEAGE:EVIDENCE_MISSING",
            result.blocking_reasons,
        )

    def test_manual_temporal_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    def test_manual_freshness_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.FRESHNESS:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    def test_historical_temporal_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.STRICT_HISTORICAL_BACKTEST
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    def test_historical_semantic_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.HISTORICAL_MODEL_TRAINING
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.SEMANTIC_CONFIDENCE:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    def test_failed_query_blocks_all_usages(self) -> None:
        for usage in StandardDataUsage:
            with self.subTest(usage=usage.value):
                result = self.engine.evaluate(
                    self.request(
                        usage=usage,
                        evidence=make_evidence(
                            overrides={
                                ReadinessDimension.QUERY_EXECUTION:
                                EvidenceStatus.FAILED,
                            }
                        ),
                    )
                )
                self.assertEqual(
                    result.status,
                    ReadinessStatus.BLOCKED,
                )

    def test_duplicate_dimension_is_rejected(self) -> None:
        item = make_evidence()[0]
        with self.assertRaises(DataContractError):
            DataReadinessRequest(
                dataset_id="a_stock_daily_k",
                usage=(
                    StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
                ),
                evidence=(item, item),
            )

    def test_manual_usage_requires_decision_time(self) -> None:
        with self.assertRaises(DataContractError):
            DataReadinessRequest(
                dataset_id="a_stock_daily_k",
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(),
            )

    def test_unknown_dataset_is_rejected(self) -> None:
        request = DataReadinessRequest(
            dataset_id="unknown_dataset",
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
            evidence=make_evidence(),
        )
        with self.assertRaises(DataContractError):
            self.engine.evaluate(request)

    def test_blocked_assert_usable_raises(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.COVERAGE:
                        EvidenceStatus.FAILED,
                    }
                )
            )
        )
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_to_dict_is_json_serialisable(self) -> None:
        result = self.engine.evaluate(self.request())
        serialised = result.to_dict()
        json.dumps(serialised, ensure_ascii=False)
        self.assertEqual(
            serialised["usage"],
            "CURRENT_SNAPSHOT_RESEARCH",
        )
        self.assertEqual(
            serialised["status"],
            "PASSED",
        )
        self.assertEqual(
            serialised["as_of_date"],
            "2026-06-27",
        )

    def test_policy_rejects_incomplete_dimension_list(self) -> None:
        raw = json.loads(
            POLICY_PATH.read_text(encoding="utf-8")
        )
        raw["dimensions"] = raw["dimensions"][:-1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_data_readiness_policy(path)


if __name__ == "__main__":
    unittest.main()
