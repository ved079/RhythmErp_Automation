"""
test_register_charges_live.py — Live API integration tests for Register Charges.

These tests hit the real ERP API and require authentication.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from pages.registration.modules.register_charges.data.register_charges_data import (
    generate_batch_payloads,
)

SCREEN_NAME = "Register Charges"


@pytest.mark.api
class TestRegisterChargesLiveCRUD:
    """Live API CRUD tests for Register Charges."""

    @pytest.fixture(autouse=True)
    def setup(self):
        token = os.environ.get("ERP_TOKEN")
        tenant = os.environ.get("ERP_TENANT", "711")
        if not token:
            pytest.skip("ERP_TOKEN env var not set")
        self.api = ErpApiClient()
        self.api.set_session_from_token(token, tenant_id=tenant)
        yield
        self.api.close()

    def test_create_single_entry(self):
        payloads = generate_batch_payloads(count=1)
        results = self.api.batch_create(SCREEN_NAME, payloads)
        assert len(results) == 1
        assert results[0].get("success"), f"Create failed: {results[0]}"

    def test_create_multiple_entries(self):
        payloads = generate_batch_payloads(count=3)
        results = self.api.batch_create(SCREEN_NAME, payloads)
        assert len(results) == 3
        successes = sum(1 for r in results if r.get("success"))
        assert successes == 3, f"Expected 3/3 created, got {successes}/3"

    def test_list_entries(self):
        result = self.api.list_entries(SCREEN_NAME, page=1, page_size=5)
        assert result is not None
        assert "screenmatlistingdata_set" in result

    def test_get_entry(self):
        # First create one
        payloads = generate_batch_payloads(count=1)
        results = self.api.batch_create(SCREEN_NAME, payloads)
        if not results or not results[0].get("success"):
            pytest.skip("Could not create entry for get test")
        entry_id = results[0].get("id")
        detail = self.api.get_entry(SCREEN_NAME, entry_id)
        assert detail is not None
        assert detail.get("attribute_name") == SCREEN_NAME
