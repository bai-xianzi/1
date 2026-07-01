from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.reuse_first_policy import (
    ReuseCandidateAssessment,
    ReuseCandidateType,
    ReuseDecisionRecord,
    ReuseDecisionType,
    ReviewStatus,
    load_reuse_first_policy,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "configs"
    / "engineering"
    / "reuse_first_policy_v0.json"
)


def reusable_candidate():
    return ReuseCandidateAssessment(
        candidate_id="existing-adapter",
        candidate_type=(
            ReuseCandidateType.EXISTING_PROJECT_COMPONENT
        ),
        name="DolphinDBDataSourceAdapter",
        source_ref="repo:src/a_stock_quant/dolphindb_adapter.py",
        version="current",
        license_id="PROJECT_INTERNAL",
        license_status=ReviewStatus.PASSED,
        security_status=ReviewStatus.PASSED,
        maintenance_status=ReviewStatus.PASSED,
        compatibility_status=ReviewStatus.PASSED,
        semantic_gap_status=ReviewStatus.PASSED_WITH_WARNINGS,
        supported_requirements=("readonly-query", "health-check"),
        gaps=("provider-plugin-protocol",),
        warnings=("thin-bridge-required",),
        evidence_refs=("repo:dolphindb_adapter.py",),
    )


class TestReuseFirstPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = load_reuse_first_policy(POLICY_PATH)

    def test_policy_is_reuse_first(self):
        self.assertEqual(
            self.policy.principle,
            "REUSE_FIRST_CUSTOM_BUILD_LAST",
        )

    def test_custom_build_is_not_default(self):
        self.assertFalse(
            self.policy.custom_implementation_default_allowed
        )

    def test_unknown_license_is_forbidden(self):
        self.assertFalse(self.policy.unknown_license_reuse_allowed)

    def test_copy_without_provenance_is_forbidden(self):
        self.assertFalse(self.policy.copy_without_provenance_allowed)

    def test_vendor_sdk_reimplementation_is_forbidden(self):
        self.assertFalse(
            self.policy.vendor_sdk_reimplementation_allowed
        )

    def test_custom_implementation_is_last(self):
        self.assertEqual(
            self.policy.reuse_order[-1],
            "CUSTOM_IMPLEMENTATION_LAST_RESORT",
        )

    def test_reusable_candidate_is_reusable(self):
        self.assertTrue(reusable_candidate().reusable)

    def test_passed_license_requires_license_id(self):
        with self.assertRaises(DataContractError):
            ReuseCandidateAssessment(
                candidate_id="x",
                candidate_type=(
                    ReuseCandidateType.MATURE_OPEN_SOURCE_LIBRARY
                ),
                name="x",
                source_ref="repo:x",
                version="1",
                license_id=None,
                license_status=ReviewStatus.PASSED,
                security_status=ReviewStatus.PASSED,
                maintenance_status=ReviewStatus.PASSED,
                compatibility_status=ReviewStatus.PASSED,
                semantic_gap_status=ReviewStatus.PASSED,
                supported_requirements=(),
                gaps=(),
                warnings=(),
                evidence_refs=("repo:x",),
            )

    def test_reuse_candidate_requires_evidence(self):
        with self.assertRaises(DataContractError):
            ReuseCandidateAssessment(
                candidate_id="x",
                candidate_type=(
                    ReuseCandidateType.OFFICIAL_VENDOR_SDK
                ),
                name="x",
                source_ref="vendor:x",
                version="1",
                license_id="PROPRIETARY",
                license_status=ReviewStatus.PASSED,
                security_status=ReviewStatus.PASSED,
                maintenance_status=ReviewStatus.PASSED,
                compatibility_status=ReviewStatus.PASSED,
                semantic_gap_status=ReviewStatus.PASSED,
                supported_requirements=(),
                gaps=(),
                warnings=(),
                evidence_refs=(),
            )

    def test_thin_adapter_decision_accepts_existing_component(self):
        record = ReuseDecisionRecord(
            decision_id="reuse:dolphindb",
            problem_statement="Bridge legacy adapter to plugin protocol.",
            requirements=("plugin-protocol",),
            candidates=(reusable_candidate(),),
            decision=ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            selected_candidate_id="existing-adapter",
            rationale="Reuse query and session logic.",
            custom_build_evidence={},
            maintenance_owner=None,
            test_plan_ref=None,
            migration_path=None,
            evidence_refs=("repo:dolphindb_adapter.py",),
        )
        self.assertEqual(
            record.decision,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
        )

    def test_reuse_decision_rejects_blocked_candidate(self):
        blocked = ReuseCandidateAssessment(
            candidate_id="blocked",
            candidate_type=ReuseCandidateType.OFFICIAL_VENDOR_SDK,
            name="blocked",
            source_ref="vendor:blocked",
            version="1",
            license_id="UNKNOWN",
            license_status=ReviewStatus.BLOCKED,
            security_status=ReviewStatus.PASSED,
            maintenance_status=ReviewStatus.PASSED,
            compatibility_status=ReviewStatus.PASSED,
            semantic_gap_status=ReviewStatus.PASSED,
            supported_requirements=(),
            gaps=("license",),
            warnings=(),
            evidence_refs=("vendor:blocked",),
        )
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="x",
                problem_statement="x",
                requirements=("x",),
                candidates=(blocked,),
                decision=ReuseDecisionType.REUSE_AS_IS,
                selected_candidate_id="blocked",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner=None,
                test_plan_ref=None,
                migration_path=None,
                evidence_refs=("x",),
            )

    def test_custom_build_requires_complete_evidence(self):
        custom = ReuseCandidateAssessment(
            candidate_id="custom",
            candidate_type=ReuseCandidateType.CUSTOM_IMPLEMENTATION,
            name="custom",
            source_ref="internal:new",
            version=None,
            license_id=None,
            license_status=ReviewStatus.NOT_REVIEWED,
            security_status=ReviewStatus.NOT_REVIEWED,
            maintenance_status=ReviewStatus.NOT_REVIEWED,
            compatibility_status=ReviewStatus.NOT_REVIEWED,
            semantic_gap_status=ReviewStatus.NOT_REVIEWED,
            supported_requirements=(),
            gaps=(),
            warnings=(),
            evidence_refs=(),
        )
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="custom:x",
                problem_statement="x",
                requirements=("x",),
                candidates=(custom,),
                decision=ReuseDecisionType.CUSTOM_BUILD_APPROVED,
                selected_candidate_id="custom",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner="owner",
                test_plan_ref="tests:x",
                migration_path="replace:x",
                evidence_refs=("x",),
            )

    def test_custom_build_accepts_complete_evidence(self):
        custom = ReuseCandidateAssessment(
            candidate_id="custom",
            candidate_type=ReuseCandidateType.CUSTOM_IMPLEMENTATION,
            name="custom",
            source_ref="internal:new",
            version=None,
            license_id=None,
            license_status=ReviewStatus.NOT_REVIEWED,
            security_status=ReviewStatus.NOT_REVIEWED,
            maintenance_status=ReviewStatus.NOT_REVIEWED,
            compatibility_status=ReviewStatus.NOT_REVIEWED,
            semantic_gap_status=ReviewStatus.NOT_REVIEWED,
            supported_requirements=(),
            gaps=(),
            warnings=(),
            evidence_refs=(),
        )
        keys = self.policy.required_custom_build_evidence
        evidence = {key: f"evidence:{key}" for key in keys}
        record = ReuseDecisionRecord(
            decision_id="custom:x",
            problem_statement="x",
            requirements=("x",),
            candidates=(custom,),
            decision=ReuseDecisionType.CUSTOM_BUILD_APPROVED,
            selected_candidate_id="custom",
            rationale="x",
            custom_build_evidence=evidence,
            maintenance_owner="owner",
            test_plan_ref="tests:x",
            migration_path="replace:x",
            evidence_refs=("x",),
        )
        self.assertEqual(
            record.decision,
            ReuseDecisionType.CUSTOM_BUILD_APPROVED,
        )

    def test_selected_candidate_must_exist(self):
        with self.assertRaises(DataContractError):
            ReuseDecisionRecord(
                decision_id="x",
                problem_statement="x",
                requirements=("x",),
                candidates=(reusable_candidate(),),
                decision=ReuseDecisionType.REUSE_AS_IS,
                selected_candidate_id="missing",
                rationale="x",
                custom_build_evidence={},
                maintenance_owner=None,
                test_plan_ref=None,
                migration_path=None,
                evidence_refs=("x",),
            )

    def test_to_dict_is_json_safe(self):
        record = ReuseDecisionRecord(
            decision_id="reuse:dolphindb",
            problem_statement="Bridge adapter.",
            requirements=("plugin-protocol",),
            candidates=(reusable_candidate(),),
            decision=ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            selected_candidate_id="existing-adapter",
            rationale="reuse",
            custom_build_evidence={},
            maintenance_owner=None,
            test_plan_ref=None,
            migration_path=None,
            evidence_refs=("repo:x",),
        )
        encoded = json.dumps(record.to_dict(), ensure_ascii=False)
        self.assertIn("WRAP_WITH_THIN_ADAPTER", encoded)

    def test_policy_rejects_custom_build_default(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["custom_implementation_default_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_reuse_first_policy(path)


if __name__ == "__main__":
    unittest.main()
