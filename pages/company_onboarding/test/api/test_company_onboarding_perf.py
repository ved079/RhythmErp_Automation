"""
test_company_onboarding_perf.py — Performance benchmarks for Company Onboarding API.
No browser needed. Measures speed of payload generation.

NOTE: Live API CRUD tests are skipped due to workflow issue
("Workflow company sync failed"). Only payload generation benchmarks are run.
"""

import pytest
import time
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.company_onboarding.data.company_onboarding_data import (
    generate_company_onboarding_api_payload,
    generate_batch_payloads,
)


@pytest.mark.performance
class TestCompanyOnboardingPerformance:
    """Performance benchmarks for Company Onboarding operations."""

    def test_payload_generation_speed(self):
        """Generate 100 payloads — should complete in under 2s."""
        start = time.time()
        for _ in range(100):
            generate_company_onboarding_api_payload()
        elapsed = time.time() - start
        assert elapsed < 2, f"100 payloads took {elapsed:.2f}s (expected < 2s)"

    def test_batch_payloads_speed(self):
        """Generate batch of 50 payloads — should be fast."""
        start = time.time()
        generate_batch_payloads(50)
        elapsed = time.time() - start
        assert elapsed < 1, f"50 batch payloads took {elapsed:.2f}s (expected < 1s)"

    @pytest.mark.skip(reason="Live API CRUD blocked by workflow issue — will enable later")
    def test_batch_create_5_companies(self, api_client):
        """Create 5 companies via API — should complete in under 15s.

        SKIPPED: Company Onboarding API returns
        "Workflow company sync failed" on POST.
        Re-enable once the workflow is fixed.
        """
        start = time.time()
        for _ in range(5):
            payload = generate_company_onboarding_api_payload()
            api_client.create_entry(payload)
            time.sleep(0.1)
        elapsed = time.time() - start
        assert elapsed < 15, f"5 companies took {elapsed:.1f}s (expected < 15s)"
