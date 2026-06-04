"""
test_designation_perf.py — Performance benchmarks for Designation payload generation.
No browser needed. Pure in-memory speed tests.
"""

import time
import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.designation.data.designation_data import (
    generate_designation_api_payload,
    generate_batch_payloads,
)


@pytest.mark.performance
class TestDesignationPerformance:
    """Verify Designation payload generation meets speed benchmarks."""

    def test_payload_generation_speed(self):
        start = time.perf_counter()
        for _ in range(100):
            generate_designation_api_payload()
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Average payload generation took {avg_ms:.2f}ms (expected < 10ms)"

    def test_batch_payloads_speed(self):
        start = time.perf_counter()
        generate_batch_payloads(count=100)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Batch of 100 took {elapsed:.3f}s (expected < 0.5s)"

    @pytest.mark.skip(reason="Live API CRUD tests blocked by workflow issue — will add later")
    def test_batch_create_5_designations(self, api_client):
        pass
