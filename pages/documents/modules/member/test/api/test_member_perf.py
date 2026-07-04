"""
test_member_perf.py â€” Performance benchmarks for Member API.
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

from pages.documents.modules.member.data.member_data import (
    generate_member_api_payload,
    generate_batch_payloads,
)


@pytest.mark.performance
class TestMemberPerformance:
    """Performance benchmarks for Member operations."""

    def test_batch_create_5_members(self, api_client):
        """Create 5 members via API â€” should complete in under 15s."""
        start = time.time()
        for _ in range(5):
            payload = generate_member_api_payload()
            api_client.create_entry(payload)
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 15, f"5 members took {elapsed:.1f}s (expected < 15s)"

    def test_payload_generation_speed(self):
        """Generate 100 payloads â€” should complete in under 2s."""
        start = time.time()
        for _ in range(100):
            generate_member_api_payload()
        elapsed = time.time() - start
        assert elapsed < 2, f"100 payloads took {elapsed:.2f}s (expected < 2s)"

    def test_batch_payloads_speed(self):
        """Generate batch of 50 payloads â€” should be fast."""
        start = time.time()
        generate_batch_payloads(50)
        elapsed = time.time() - start
        assert elapsed < 1, f"50 batch payloads took {elapsed:.2f}s (expected < 1s)"
