import unittest

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.vendor_query_manifest import (
    ChunkPolicy,
    VendorManifestRegistry,
    VendorOperation,
    VendorQueryManifest,
)


class TestVendorQueryManifest(unittest.TestCase):
    def _manifest(
        self,
        *,
        manifest_id: str = "m1",
        enabled: bool = False,
    ) -> VendorQueryManifest:
        return VendorQueryManifest(
            manifest_id=manifest_id,
            source_id="ifind_http",
            dataset_id="a_stock_daily_bar",
            canonical_object="DailyBar",
            operation=VendorOperation.HISTORICAL_QUOTES,
            request_template={
                "endpoint": "/api/v1/cmd_history_quotation",
                "codes": "{vendor_codes}",
                "indicators": [
                    "open",
                    "high",
                    "low",
                    "close",
                ],
            },
            field_mapping={
                "open": "DailyBar.open",
                "high": "DailyBar.high",
                "low": "DailyBar.low",
                "close": "DailyBar.close",
            },
            response_data_path="tables",
            mapping_version="0.1.0",
            source_schema_version="official-example-2022",
            generated_by="official_example_template",
            enabled=enabled,
            chunk_policy=ChunkPolicy(
                max_rows_hint=2_000_000,
                split_strategy="BY_CODES_AND_DATE",
            ),
        )

    def test_manifest_round_trip(self) -> None:
        original = self._manifest()
        restored = VendorQueryManifest.from_dict(
            original.to_dict()
        )
        self.assertEqual(
            restored.to_dict(),
            original.to_dict(),
        )

    def test_secret_fields_are_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            VendorQueryManifest(
                manifest_id="bad",
                source_id="ifind_http",
                dataset_id="dataset",
                canonical_object="DailyBar",
                operation=VendorOperation.REALTIME_QUOTES,
                request_template={
                    "access_token": "do-not-store",
                },
                field_mapping={
                    "latest": "DailyBar.close",
                },
                response_data_path="tables",
                mapping_version="1",
                source_schema_version="1",
                generated_by="manual",
            )

    def test_disabled_manifests_are_hidden(self) -> None:
        registry = VendorManifestRegistry()
        registry.register(self._manifest())
        self.assertEqual(
            registry.list_for_dataset(
                "a_stock_daily_bar"
            ),
            (),
        )
        self.assertEqual(
            len(
                registry.list_for_dataset(
                    "a_stock_daily_bar",
                    include_disabled=True,
                )
            ),
            1,
        )

    def test_duplicate_manifest_is_rejected(self) -> None:
        registry = VendorManifestRegistry()
        registry.register(self._manifest())
        with self.assertRaises(DataContractError):
            registry.register(self._manifest())


if __name__ == "__main__":
    unittest.main()
