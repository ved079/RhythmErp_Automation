"""
test_register_of_loan_perf.py â€” Performance benchmarks for Register of Loan API.
"""

import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.register_of_loan.data.register_of_loan_data import (
    generate_batch_payloads,
    generate_api_payload,
)


class TestRegisterOfLoanPerformance:
    """Performance benchmarks for payload generation."""

    def test_generate_single_payload_speed(self):
        start = time.time()
        count = 100
        for _ in range(count):
            generate_api_payload()
        elapsed = time.time() - start
        per_payload = elapsed / count
        assert per_payload < 0.01, f"Payload generation too slow: {per_payload:.4f}s each"

    def test_batch_generation_speed(self):
        start = time.time()
        payloads = generate_batch_payloads(100)
        elapsed = time.time() - start
        assert len(payloads) == 100
        per_payload = elapsed / 100
        assert per_payload < 0.01, f"Batch generation too slow: {per_payload:.4f}s each"

    def test_payloads_have_different_bank_names(self):
        payloads = generate_batch_payloads(20)
        names = set(p["bank_name"] for p in payloads)
        # At least 3 different banks should appear
        assert len(names) >= 3, f"Only {len(names)} unique bank names out of 20"
