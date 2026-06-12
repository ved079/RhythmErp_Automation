"""
test_farmer_perf.py — Performance benchmarks for Farmer API.
No browser needed. Measures speed of API creation and payload generation.

NOTE: Known ERP bug — Farmer creation via API POST returns 500
"token has wrong type". The batch_create test is marked xfail until
the ERP bug is fixed. Payload generation benchmarks still apply.
"""

import pytest
import time
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.farmer.data.farmer_data import (
    generate_farmer_api_payload,
    generate_batch_payloads,
    KnownBugs,
)


@pytest.mark.performance
class TestFarmerPerformance:
    """Performance benchmarks for Farmer operations."""

    @pytest.mark.xfail(
        reason=KnownBugs.API_500,
        strict=False,
    )
    def test_batch_create_5_farmers(self, api_client):
        """Create 5 farmers via API — should complete in under 15s.

        XFAIL: Farmer creation via POST returns 500 "token has wrong type".
        This test will pass once the ERP bug is fixed.
        """
        start = time.time()
        for _ in range(5):
            payload = generate_farmer_api_payload()
            api_client.create_entry(payload)
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 15, f"5 farmers took {elapsed:.1f}s (expected < 15s)"

    def test_payload_generation_speed(self):
        """Generate 100 payloads — should complete in under 5s.

        Farmer payloads are more complex (13 stepper children)
        than Supplier (3 stepper children), so the threshold is higher.
        """
        start = time.time()
        for _ in range(100):
            generate_farmer_api_payload()
        elapsed = time.time() - start
        assert elapsed < 5, f"100 payloads took {elapsed:.2f}s (expected < 5s)"

    def test_batch_payloads_speed(self):
        """Generate batch of 50 payloads — should be fast."""
        start = time.time()
        generate_batch_payloads(50)
        elapsed = time.time() - start
        assert elapsed < 3, f"50 batch payloads took {elapsed:.2f}s (expected < 3s)"

    @pytest.mark.xfail(
        reason=KnownBugs.API_500,
        strict=False,
    )
    def test_single_create_response_time(self, api_client):
        """Single Farmer create — response should come back in under 5s.

        XFAIL: Farmer creation via POST returns 500 "token has wrong type".
        """
        payload = generate_farmer_api_payload()
        start = time.time()
        api_client.create_entry(payload)
        elapsed = time.time() - start
        assert elapsed < 5, f"Single create took {elapsed:.1f}s (expected < 5s)"

    def test_list_farmers_response_time(self, api_client):
        """List Farmers — response should come back in under 3s."""
        start = time.time()
        api_client.list_entries("Farmer", page=1, page_size=10)
        elapsed = time.time() - start
        assert elapsed < 3, f"List farmers took {elapsed:.1f}s (expected < 3s)"

    def test_schema_fetch_response_time(self, api_client):
        """Fetch Farmer schema — response should come back in under 3s."""
        start = time.time()
        api_client.get_screen_schema("Farmer")
        elapsed = time.time() - start
        assert elapsed < 3, f"Schema fetch took {elapsed:.1f}s (expected < 3s)"
