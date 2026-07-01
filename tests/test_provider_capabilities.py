from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.provider_capabilities import (
    ProviderLifecycle,
    load_provider_capability_matrix,
    load_single_machine_resource_profile,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    ROOT
    / "configs"
    / "providers"
    / "provider_capability_matrix_v0.json"
)
PROFILE_PATH = (
    ROOT
    / "configs"
    / "runtime"
    / "windows_single_machine_resource_profile_v0.json"
)


class TestProviderCapabilities(unittest.TestCase):
    def setUp(self):
        self.matrix = load_provider_capability_matrix(MATRIX_PATH)
        self.profile = load_single_machine_resource_profile(
            PROFILE_PATH
        )

    def test_matrix_is_provider_neutral(self):
        self.assertTrue(self.matrix.provider_neutral)
        self.assertFalse(self.matrix.core_system_may_import_vendor_sdk)
        self.assertFalse(
            self.matrix.upper_layers_may_depend_on_vendor_fields
        )

    def test_required_provider_targets_exist(self):
        for provider_id in (
            "local_dolphindb",
            "wind",
            "ifind",
            "galaxy_xingyao",
        ):
            self.assertEqual(
                self.matrix.provider(provider_id).provider_id,
                provider_id,
            )

    def test_target_list_is_open_ended(self):
        self.assertGreaterEqual(len(self.matrix.provider_targets), 10)

    def test_unknown_vendor_capabilities_are_not_guessed(self):
        for provider_id in (
            "wind",
            "ifind",
            "galaxy_xingyao",
            "qmt",
            "ptrade",
        ):
            target = self.matrix.provider(provider_id)
            self.assertEqual(target.capabilities, {})
            self.assertEqual(
                target.discovery_status.value,
                "DISCOVERY_REQUIRED",
            )

    def test_execution_providers_are_registered_not_activated(self):
        for provider_id in ("qmt", "ptrade"):
            target = self.matrix.provider(provider_id)
            self.assertTrue(target.execution_capability)
            self.assertIs(
                target.lifecycle,
                ProviderLifecycle.REGISTERED_TARGET,
            )

    def test_secrets_are_forbidden(self):
        self.assertFalse(self.matrix.secret_storage_allowed)

    def test_automatic_activation_is_forbidden(self):
        self.assertFalse(self.matrix.automatic_activation_allowed)

    def test_unaccepted_provider_is_not_eligible(self):
        self.assertEqual(
            self.matrix.eligible_providers("EOD_MARKET_DATA"),
            (),
        )

    def test_profile_matches_known_machine(self):
        self.assertEqual(self.profile.physical_core_count, 6)
        self.assertEqual(self.profile.logical_thread_count, 12)
        self.assertEqual(self.profile.memory_gib, 16)
        self.assertEqual(self.profile.gpu_memory_gib, 4)

    def test_profile_uses_conservative_parallelism(self):
        self.assertLessEqual(
            self.profile.max_parallel_provider_calls,
            2,
        )
        self.assertLessEqual(self.profile.max_parallel_cpu_jobs, 2)
        self.assertLessEqual(
            self.profile.max_parallel_database_queries,
            2,
        )

    def test_default_batch_is_twenty_thousand(self):
        self.assertEqual(self.profile.choose_batch_rows(), 20000)

    def test_batch_override_within_limit_is_allowed(self):
        self.assertEqual(
            self.profile.choose_batch_rows(50000),
            50000,
        )

    def test_batch_override_above_limit_is_rejected(self):
        with self.assertRaises(DataContractError):
            self.profile.choose_batch_rows(100001)

    def test_large_download_requires_override(self):
        with self.assertRaises(DataContractError):
            self.profile.assert_storage_safe(
                free_space_gib=100,
                planned_download_gib=6,
            )

    def test_low_remaining_disk_is_rejected(self):
        with self.assertRaises(DataContractError):
            self.profile.assert_storage_safe(
                free_space_gib=18,
                planned_download_gib=4,
            )

    def test_small_download_with_safe_space_is_allowed(self):
        self.profile.assert_storage_safe(
            free_space_gib=30,
            planned_download_gib=2,
        )

    def test_35gb_automatic_import_is_forbidden(self):
        self.assertFalse(
            self.profile.automatic_35gb_minute_data_import_allowed
        )

    def test_gpu_is_not_default(self):
        self.assertFalse(self.profile.gpu_enabled_by_default)

    def test_matrix_rejects_guessed_capabilities(self):
        raw = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        for item in raw["provider_targets"]:
            if item["provider_id"] == "wind":
                item["capabilities"]["EOD_MARKET_DATA"] = "IMPLEMENTED"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_provider_capability_matrix(path)

    def test_profile_rejects_excess_parallelism(self):
        raw = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        raw["default_execution"]["max_parallel_provider_calls"] = 6
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_single_machine_resource_profile(path)


if __name__ == "__main__":
    unittest.main()
