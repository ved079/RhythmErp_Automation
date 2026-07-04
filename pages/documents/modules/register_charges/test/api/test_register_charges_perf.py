"""
test_register_charges_perf.py â€” Performance benchmarks for Register Charges API.
"""

import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.register_charges.data.register_charges_data import (
    generate_batch_payloads,
    generate_api_payload,
)


class TestRegisterChargesPerformance:
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

    def test_roc_id_uniqueness_in_large_batch(self):
        payloads = generate_batch_payloads(200)
        roc_ids = [p["roc_charge_id"] for p in payloads]
        unique = len(set(roc_ids))
        assert unique == len(roc_ids), f"Only {unique}/{len(roc_ids)} unique ROC IDs"
