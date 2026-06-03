"""
test_customer_live.py — Live API tests that create/read Customer entries.
Requires authenticated ERP API access. No browser needed.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.customer.data.customer_data import (
    generate_customer_api_payload,
)


@pytest.mark.api
class TestCustomerAPILive:
    """Live API tests — create entries and verify on the ERP."""

    def test_create_single_customer(self, api_client):
        """Create a single Customer via API and verify response."""
        payload = generate_customer_api_payload()
        result = api_client.create_entry(payload)
        assert result is not None, "API create returned None (likely failure)"

    def test_create_customer_with_partnership(self, api_client):
        """Create a Customer with Partnership ownership status."""
        payload = generate_customer_api_payload()
        payload["ownership_status_ref_id"] = 1262  # Partnership
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_customer_with_export_supply(self, api_client):
        """Create a Customer with Export supply type (Customer-specific FK)."""
        payload = generate_customer_api_payload()
        payload["supply_type_ref_id"] = 1494  # Export
        payload["sale_type_ref_id"] = 1267    # Consignment
        result = api_client.create_entry(payload)
        assert result is not None

    def test_create_customer_inactive(self, api_client):
        """Create an inactive Customer (status=False)."""
        payload = generate_customer_api_payload()
        payload["status"] = False
        result = api_client.create_entry(payload)
        assert result is not None

    def test_list_customers(self, api_client):
        """List Customer entries — should return valid response."""
        result = api_client.list_entries("Customer", page=1, page_size=5)
        assert result is not None
        assert "screenmatlistingdata_set" in result

    def test_get_customer_detail(self, api_client):
        """Get a specific Customer entry by ID."""
        result = api_client.list_entries("Customer", page=1, page_size=1)
        assert result is not None
        records = result.get("screenmatlistingdata_set", [])
        if records:
            entry_id = records[0]["id"]
            detail = api_client.get_entry("Customer", entry_id)
            assert detail is not None
            assert detail["attribute_name"] == "Customer"

    def test_discover_customer_structure(self, api_client):
        """Discover and verify the Customer payload structure."""
        detail = api_client.discover_structure("Customer")
        if detail:
            assert detail["attribute_name"] == "Customer"
            assert "children" in detail
            assert len(detail["children"]) == 3

    def test_customer_has_3_steppers(self, api_client):
        """Verify Customer has 3 stepper children."""
        detail = api_client.discover_structure("Customer")
        if detail:
            stepper_names = [c.get("stepper_name") for c in detail["children"]]
            assert "Additional Details" in stepper_names
            assert "Customer Details" in stepper_names
            assert "Customer Bank Details" in stepper_names
