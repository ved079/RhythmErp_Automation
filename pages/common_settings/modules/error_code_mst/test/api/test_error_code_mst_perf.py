"""
test_error_code_mst_perf.py — Performance benchmarks for Error Code Mst.
"""

import time
import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_error_code_mst_api_payloads,
    generate_batch_payloads,
)


@pytest.mark.performance
class TestErrorCodeMstPerformance:
    def test_payload_generation_speed(self):
        start = time.perf_counter()
        for _ in range(100):
            generate_error_code_mst_api_payloads(count=1)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Avg {avg_ms:.2f}ms (expected < 10ms)"

    def test_batch_payloads_speed(self):
        start = time.perf_counter()
        generate_batch_payloads(count=100)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Batch of 100 took {elapsed:.3f}s"

    @pytest.mark.skip(reason="Live API CRUD tests blocked by workflow issue")
    def test_batch_create_5_error_codes(self, api_client):
        pass
