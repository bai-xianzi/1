# 本测试文件核心功能：验证TASK_023A环境发现合同、安全边界和候选排序。
"""TASK_023A Provider环境发现测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_environment_discovery import (
    ProviderTargetSpec,
    build_provider_environment_report,
    discover_provider_environment,
    load_provider_discovery_manifest,
    rank_next_discovery_candidates,
)


class ProviderEnvironmentDiscoveryTests(unittest.TestCase):
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

    def test_manifest_rejects_secret_and_network_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "secret_values_allowed": True,
                        "vendor_sdk_import_allowed": False,
                        "network_calls_allowed": False,
                        "targets": [{}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "secret_values_allowed"):
                load_provider_discovery_manifest(path)

    def test_discovery_uses_find_spec_without_importing_vendor_sdk(self) -> None:
        calls: list[str] = []

        def fake_find_spec(name: str) -> object | None:
            calls.append(name)
            return object() if name == "installed_sdk" else None

        findings = discover_provider_environment(
            (self._target("vendor", modules=("installed_sdk", "missing_sdk")),),
            environ={},
            find_spec=fake_find_spec,
        )
        self.assertEqual(calls, ["installed_sdk", "missing_sdk"])
        self.assertEqual(findings[0].runtime_status, "RUNTIME_PRESENT")
        self.assertEqual(findings[0].detected_python_modules, ("installed_sdk",))

    def test_credential_values_never_enter_report(self) -> None:
        secret_value = "must-not-appear"
        findings = discover_provider_environment(
            (self._target("vendor", modules=("sdk",), credentials=("TOKEN_NAME",)),),
            environ={"TOKEN_NAME": secret_value},
            find_spec=lambda _: object(),
        )
        report_text = json.dumps(build_provider_environment_report(findings), ensure_ascii=False)
        self.assertIn("TOKEN_NAME", report_text)
        self.assertNotIn(secret_value, report_text)
        self.assertEqual(findings[0].present_credential_references, ("TOKEN_NAME",))

    def test_execution_provider_is_never_recommended_automatically(self) -> None:
        findings = discover_provider_environment(
            (
                self._target("data_provider", modules=("sdk",), priority=20),
                self._target("broker", modules=("sdk",), execution=True, priority=10),
            ),
            environ={},
            find_spec=lambda _: object(),
        )
        self.assertEqual(rank_next_discovery_candidates(findings), ("data_provider",))

    def test_candidate_ranking_is_deterministic(self) -> None:
        findings = discover_provider_environment(
            (
                self._target("z_provider", modules=("sdk",), priority=30),
                self._target("a_provider", modules=("sdk",), priority=30),
                self._target("first_provider", modules=("sdk",), priority=10),
            ),
            environ={},
            find_spec=lambda _: object(),
        )
        self.assertEqual(
            rank_next_discovery_candidates(findings),
            ("first_provider", "a_provider", "z_provider"),
        )

    def test_manual_review_target_remains_blocked(self) -> None:
        findings = discover_provider_environment(
            (self._target("manual_provider"),),
            environ={},
            find_spec=lambda _: None,
        )
        self.assertEqual(findings[0].runtime_status, "MANUAL_REVIEW_REQUIRED")
        self.assertFalse(findings[0].eligible_for_next_discovery)
        self.assertIn("NO_VERIFIED_PYTHON_MODULE_HINT", findings[0].blockers)


if __name__ == "__main__":
    unittest.main()
