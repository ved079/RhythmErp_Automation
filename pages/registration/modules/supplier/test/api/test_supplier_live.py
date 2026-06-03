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
