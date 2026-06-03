"""
test_supplier_perf.py — Performance benchmarks for Supplier API.
No browser needed. Measures speed of API creation and payload generation.
"""

import pytest
import time
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.supplier.data.supplier_data import (
    generate_supplier_api_payload,
    generate_batch_payloads,
)


@pytest.mark.performance
class TestSupplierPerformance:
    """Performance benchmarks for Supplier operations."""

    def test_batch_create_5_suppliers(self, api_client):
        """Create 5 suppliers via API — should complete in under 15s."""
        start = time.time()
        for _ in range(5):
            payload = generate_supplier_api_payload()
            api_client.create_entry(payload)
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 15, f"5 suppliers took {elapsed:.1f}s (expected < 15s)"

    def test_payload_generation_speed(self):
        """Generate 100 payloads — should complete in under 2s."""
        start = time.time()
        for _ in range(100):
            generate_supplier_api_payload()
        elapsed = time.time() - start
        assert elapsed < 2, f"100 payloads took {elapsed:.2f}s (expected < 2s)"

    def test_batch_payloads_speed(self):
        """Generate batch of 50 payloads — should be fast."""
        start = time.time()
        generate_batch_payloads(50)
        elapsed = time.time() - start
        assert elapsed < 1, f"50 batch payloads took {elapsed:.2f}s (expected < 1s)"
