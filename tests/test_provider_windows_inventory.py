# 本测试文件核心功能：验证TASK_023B机器级盘点、证据评分、安全边界和候选排序。
"""TASK_023B Windows Provider盘点测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_environment_discovery import ProviderTargetSpec
from a_stock_quant.provider_windows_inventory import (
    InstalledApplicationEvidence,
    ProviderWindowsRule,
    PythonInterpreterEvidence,
    build_windows_inventory_report,
    build_windows_provider_findings,
    load_windows_inventory_rules,
    rank_task_023c_candidates,
)


class ProviderWindowsInventoryTests(unittest.TestCase):
    def _target(
        self,
        provider_id: str,
        *,
        modules: tuple[str, ...] = (),
        credentials: tuple[str, ...] = (),
        execution: bool = False,
        priority: int = 30,
    ) -> ProviderTargetSpec:
        return ProviderTargetSpec(
            provider_id=provider_id,
            display_name=provider_id,
            provider_kind="TEST",
            execution_capability=execution,
            priority=priority,
            python_module_candidates=modules,
            credential_reference_names=credentials,
            discovery_method="TEST",
            evidence_level="TEST",
            license_review_required=True,
        )

    def _rule(
        self,
        provider_id: str,
        *,
        tokens: tuple[str, ...] = (),
        executables: tuple[str, ...] = (),
    ) -> ProviderWindowsRule:
        return ProviderWindowsRule(provider_id, tokens, executables)

    def test_rules_reject_secret_or_network_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "secret_values_allowed": False,
                        "vendor_sdk_import_allowed": False,
                        "network_calls_allowed": True,
                        "registry_install_location_allowed": False,
                        "providers": [],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "network_calls_allowed"):
                load_windows_inventory_rules(path)

    def test_current_interpreter_module_has_highest_evidence_weight(self) -> None:
        target = self._target("vendor", modules=("sdk",))
        interpreters = (
            PythonInterpreterEvidence(
                executable=sys.executable,
                version="3.11",
                source="CURRENT_INTERPRETER",
                detected_modules=("sdk",),
                probe_status="PASSED",
            ),
        )
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor"),),
            interpreters,
            (),
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertEqual(finding.evidence_score, 100)
        self.assertTrue(finding.eligible_for_task_023c_review)

    def test_other_interpreter_and_installed_client_are_separate_evidence(self) -> None:
        target = self._target("vendor", modules=("sdk",))
        interpreters = (
            PythonInterpreterEvidence(
                executable="C:/OtherPython/python.exe",
                version="3.10",
                source="PY_LAUNCHER",
                detected_modules=("sdk",),
                probe_status="PASSED",
            ),
        )
        applications = (
            InstalledApplicationEvidence("Vendor Terminal", "1.0", "Vendor"),
        )
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor", tokens=("Vendor Terminal",)),),
            interpreters,
            applications,
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertEqual(finding.evidence_score, 120)
        self.assertEqual(finding.other_interpreter_modules, ("sdk",))
        self.assertEqual(finding.matched_installed_applications, ("Vendor Terminal",))

    def test_execution_provider_is_never_task_023c_auto_candidate(self) -> None:
        target = self._target("broker", modules=("sdk",), execution=True)
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("broker"),),
            (
                PythonInterpreterEvidence(
                    sys.executable,
                    "3.11",
                    "CURRENT_INTERPRETER",
                    ("sdk",),
                    "PASSED",
                ),
            ),
            (),
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertFalse(finding.eligible_for_task_023c_review)
        self.assertEqual(finding.inventory_status, "SEPARATE_EXECUTION_REVIEW_REQUIRED")

    def test_secret_value_and_install_path_never_enter_report(self) -> None:
        secret = "never-record-this-token"
        target = self._target("vendor", credentials=("TOKEN_NAME",))
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor", tokens=("Vendor",)),),
            (),
            (InstalledApplicationEvidence("Vendor", "1.0", "Publisher"),),
            environ={"TOKEN_NAME": secret},
            executable_lookup=lambda _: None,
        )[0]
        report = build_windows_inventory_report(
            (finding,),
            (),
            (InstalledApplicationEvidence("Vendor", "1.0", "Publisher"),),
        )
        text = json.dumps(report, ensure_ascii=False)
        self.assertIn("TOKEN_NAME", text)
        self.assertNotIn(secret, text)
        self.assertNotIn("InstallLocation", text)
        self.assertNotIn("installed_applications", report)
        self.assertEqual(report["secret_values_recorded"], 0)
        self.assertEqual(report["installation_paths_recorded"], 0)

    def test_candidate_ranking_prefers_evidence_then_priority(self) -> None:
        targets = (
            self._target("low_score", modules=("sdk_low",), priority=10),
            self._target("high_score_b", modules=("sdk_b",), priority=30),
            self._target("high_score_a", modules=("sdk_a",), priority=20),
        )
        rules = tuple(self._rule(target.provider_id) for target in targets)
        findings = build_windows_provider_findings(
            targets,
            rules,
            (
                PythonInterpreterEvidence(
                    sys.executable,
                    "3.11",
                    "CURRENT_INTERPRETER",
                    ("sdk_a", "sdk_b"),
                    "PASSED",
                ),
                PythonInterpreterEvidence(
                    "C:/Other/python.exe",
                    "3.10",
                    "PY_LAUNCHER",
                    ("sdk_low",),
                    "PASSED",
                ),
            ),
            (),
            environ={},
            executable_lookup=lambda _: None,
        )
        self.assertEqual(
            rank_task_023c_candidates(findings),
            ("high_score_a", "high_score_b", "low_score"),
        )

    def test_missing_rule_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing Windows inventory rule"):
            build_windows_provider_findings(
                (self._target("vendor"),),
                (),
                (),
                (),
                environ={},
                executable_lookup=lambda _: None,
            )


if __name__ == "__main__":
    unittest.main()
