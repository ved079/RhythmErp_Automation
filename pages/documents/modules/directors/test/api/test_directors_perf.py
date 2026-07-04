"""
test_directors_perf.py
----------------------
Performance benchmark tests for the Directors screen API.

Measures:
  - Single entry creation latency
  - Batch creation throughput
  - List/retrieval response time

Run with:
  ERP_TOKEN=eyJ... pytest pages/registration/modules/directors/test/api/test_directors_perf.py -v
"""

import os
import sys
import time
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.directors.data.directors_data import (
    generate_directors_api_payload,
    generate_batch_payloads,
)


# Performance thresholds (seconds)
SINGLE_CREATE_MAX = 5.0      # Single create should be under 5s
BATCH_CREATE_PER_ENTRY = 2.0  # Each batch entry under 2s
LIST_RESPONSE_MAX = 5.0       # List should respond under 5s


@pytest.mark.performance
class TestDirectorsPerformance:
    """Performance benchmarks for Directors API operations."""

    @pytest.fixture(autouse=True)
    def skip_without_api(self, api_client):
        """Skip all tests in this class if no API client is available."""
        if api_client is None:
            pytest.skip("No API client available for performance tests")

    def test_single_create_latency(self, api_client):
        """Measure single director creation latency."""
        payload = generate_directors_api_payload()
        start = time.time()
        result = api_client.create_entry(payload)
        elapsed = time.time() - start

        assert result is not None, "Create failed"
        assert elapsed < SINGLE_CREATE_MAX, (
            f"Single create took {elapsed:.2f}s (max {SINGLE_CREATE_MAX}s)"
        )

    def test_batch_create_throughput(self, api_client):
        """Measure batch of 3 directors creation throughput."""
        payloads = generate_batch_payloads(3)
        start = time.time()

        for i, payload in enumerate(payloads):
            result = api_client.create_entry(payload)
            assert result is not None, f"Batch create failed at entry {i+1}"
            if i < len(payloads) - 1:
                time.sleep(0.25)

        elapsed = time.time() - start
        per_entry = elapsed / len(payloads)

        assert per_entry < BATCH_CREATE_PER_ENTRY, (
            f"Batch create: {per_entry:.2f}s per entry (max {BATCH_CREATE_PER_ENTRY}s)"
        )

    def test_list_response_time(self, api_client):
        """Measure list entries response time."""
        start = time.time()
        result = api_client.list_entries("Directors", page=1, page_size=20)
        elapsed = time.time() - start

        assert result is not None, "List failed"
        assert elapsed < LIST_RESPONSE_MAX, (
            f"List took {elapsed:.2f}s (max {LIST_RESPONSE_MAX}s)"
        )
