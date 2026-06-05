"""
test_supplier_live.py — Live API tests that create/read Supplier entries.
Requires authenticated ERP API access. No browser needed.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.supplier.data.supplier_data import (
    generate_supplier_api_payload,
)


@pytest.mark.api
class TestSupplierAPILive:
    """Live API tests — create entries and verify on the ERP."""

    def test_create_single_supplier(self, api_client):
        """Create a single Supplier via API and verify response."""
        payload = generate_supplier_api_payload()
        # Verify payload has both Shipping and Billing addresses before sending
        addr_details = payload["children"][1]["details"]
        addr_types = [d["address_type"] for d in addr_details]
        assert 43 in addr_types, "Payload must include Shipping address (43)"
        assert 42 in addr_types, "Payload must include Billing address (42)"
        result = api_client.create_entry(payload)
        assert result is not None, "API create returned None (likely failure)"

    def test_create_supplier_with_partnership(self, api_client):
        """Create a Supplier with Partnership ownership status."""
        payload = generate_supplier_api_payload()
        payload["ownership_status_ref_id"] = 1262  # Partnership
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_supplier_inactive(self, api_client):
        """Create an inactive Supplier (status=False)."""
        payload = generate_supplier_api_payload()
        payload["status"] = False
        result = api_client.create_entry(payload)
        assert result is not None

    def test_list_suppliers(self, api_client):
        """List Supplier entries — should return valid response."""
        result = api_client.list_entries("Supplier", page=1, page_size=5)
        assert result is not None
        assert "screenmatlistingdata_set" in result

    def test_get_supplier_detail(self, api_client):
        """Get a specific Supplier entry by ID."""
        result = api_client.list_entries("Supplier", page=1, page_size=1)
        assert result is not None
        records = result.get("screenmatlistingdata_set", [])
        if records:
            entry_id = records[0]["id"]
            detail = api_client.get_entry("Supplier", entry_id)
            assert detail is not None
            assert detail["attribute_name"] == "Supplier"

    def test_discover_supplier_structure(self, api_client):
        """Discover and verify the Supplier payload structure."""
        detail = api_client.discover_structure("Supplier")
        if detail:
            assert detail["attribute_name"] == "Supplier"
            assert "children" in detail
            assert len(detail["children"]) == 3

    def test_supplier_has_3_steppers(self, api_client):
        """Verify Supplier has 3 stepper children."""
        detail = api_client.discover_structure("Supplier")
        if detail:
            stepper_names = [c.get("stepper_name") for c in detail["children"]]
            assert "Additional Details" in stepper_names
            assert "Address Details" in stepper_names
            assert "Bank Details" in stepper_names


@pytest.mark.api
class TestSupplierAddressValidation:
    """Verify ERP enforces the dual address type requirement for Suppliers."""

    def test_missing_billing_address_rejected(self, api_client):
        """Payload with only Shipping address should be rejected (400).
        ERP validates: 'Billing address is required for Supplier roles'.
        """
        payload = generate_supplier_api_payload()
        # Remove the Billing address row, keep only Shipping
        addr_details = payload["children"][1]["details"]
        payload["children"][1]["details"] = [
            d for d in addr_details if d.get("address_type") == 43  # Shipping only
        ]
        assert len(payload["children"][1]["details"]) == 1
        result = api_client.create_entry(payload)
        assert result is None, (
            "BUG: ERP accepted Supplier with only Shipping address — "
            "Billing address should be required"
        )

    def test_missing_shipping_address_rejected(self, api_client):
        """Payload with only Billing address should be rejected (400).
        ERP validates: 'Shipping address is required for Supplier roles'.
        """
        payload = generate_supplier_api_payload()
        # Remove the Shipping address row, keep only Billing
        addr_details = payload["children"][1]["details"]
        payload["children"][1]["details"] = [
            d for d in addr_details if d.get("address_type") == 42  # Billing only
        ]
        assert len(payload["children"][1]["details"]) == 1
        result = api_client.create_entry(payload)
        assert result is None, (
            "BUG: ERP accepted Supplier with only Billing address — "
            "Shipping address should be required"
        )
