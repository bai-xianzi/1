import unittest
from datetime import date

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.source_governance import (
    CredentialReference,
    DatasetSourceBinding,
    SourceCapability,
    SourceCatalog,
    SourceDescriptor,
    SourceOperationalStatus,
    SourceProtocol,
    SourceRole,
)


class TestSourceGovernance(unittest.TestCase):
    def _source(
        self,
        source_id: str,
        *,
        enabled: bool,
        capabilities: tuple[
            SourceCapability, ...
        ],
    ) -> SourceDescriptor:
        return SourceDescriptor(
            source_id=source_id,
            vendor_name=source_id,
            protocol=SourceProtocol.HTTP,
            capabilities=capabilities,
            enabled=enabled,
            operational_status=(
                SourceOperationalStatus.AVAILABLE
                if enabled
                else SourceOperationalStatus.DISABLED
            ),
        )

    def test_disabled_source_must_have_disabled_status(
        self,
    ) -> None:
        with self.assertRaises(DataContractError):
            SourceDescriptor(
                source_id="wind",
                vendor_name="Wind",
                protocol=SourceProtocol.SDK,
                capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
                enabled=False,
                operational_status=(
                    SourceOperationalStatus.CONFIGURED
                ),
            )

    def test_credentials_are_references_only(
        self,
    ) -> None:
        item = CredentialReference(
            reference_id="ifind_refresh_token",
            environment_variable="IFIND_REFRESH_TOKEN",
        )
        self.assertEqual(
            item.environment_variable,
            "IFIND_REFRESH_TOKEN",
        )

    def test_binding_requires_registered_source(
        self,
    ) -> None:
        catalog = SourceCatalog()
        with self.assertRaises(DataContractError):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id="unknown",
                    role=SourceRole.PRIMARY,
                    priority=1,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                )
            )

    def test_binding_requires_capability(
        self,
    ) -> None:
        catalog = SourceCatalog()
        catalog.register_source(
            self._source(
                "ifind",
                enabled=True,
                capabilities=(
                    SourceCapability.REALTIME_QUOTES,
                ),
            )
        )
        with self.assertRaises(DataContractError):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id="ifind",
                    role=SourceRole.PRIMARY,
                    priority=1,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                    required_capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                    enabled=True,
                )
            )

    def test_route_order_is_stable(
        self,
    ) -> None:
        catalog = SourceCatalog()
        for source_id in (
            "primary",
            "fallback",
            "reconcile",
        ):
            catalog.register_source(
                self._source(
                    source_id,
                    enabled=True,
                    capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                )
            )

        for source_id, role, priority in (
            ("fallback", SourceRole.FALLBACK, 1),
            ("primary", SourceRole.PRIMARY, 1),
            (
                "reconcile",
                SourceRole.RECONCILIATION,
                1,
            ),
        ):
            catalog.register_binding(
                DatasetSourceBinding(
                    dataset_id="a_stock_daily_bar",
                    source_id=source_id,
                    role=role,
                    priority=priority,
                    source_locator={},
                    mapping_version="1.0",
                    source_schema_version="1.0",
                    required_capabilities=(
                        SourceCapability.HISTORICAL_QUOTES,
                    ),
                    enabled=True,
                )
            )

        routes = catalog.routes_for(
            "a_stock_daily_bar",
            required_capabilities=(
                SourceCapability.HISTORICAL_QUOTES,
            ),
        )
        self.assertEqual(
            [route.source.source_id for route in routes],
            ["primary", "fallback", "reconcile"],
        )

    def test_effective_date_filters_binding(
        self,
    ) -> None:
        catalog = SourceCatalog()
        catalog.register_source(
            self._source(
                "primary",
                enabled=True,
                capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
            )
        )
        catalog.register_binding(
            DatasetSourceBinding(
                dataset_id="dataset",
                source_id="primary",
                role=SourceRole.PRIMARY,
                priority=1,
                source_locator={},
                mapping_version="1.0",
                source_schema_version="1.0",
                required_capabilities=(
                    SourceCapability.TIME_SERIES,
                ),
                enabled=True,
                effective_from=date(2026, 1, 1),
            )
        )
        self.assertEqual(
            catalog.routes_for(
                "dataset",
                target_date=date(2025, 12, 31),
            ),
            (),
        )
        self.assertEqual(
            len(
                catalog.routes_for(
                    "dataset",
                    target_date=date(2026, 1, 1),
                )
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
