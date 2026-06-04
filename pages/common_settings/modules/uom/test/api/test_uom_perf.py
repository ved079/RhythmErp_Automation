"""
test_uom_perf.py — Performance benchmarks + Live CRUD tests.
No browser needed. In-memory speed tests + live API CRUD verification.
"""

import time
import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom.data.uom_data import (
    generate_uom_api_payload, generate_batch_payloads,
)

SCREEN_NAME = "UOM"


@pytest.mark.performance
class TestUOMPerformance:
    """Verify UOM payload generation meets speed benchmarks and live CRUD."""

    def test_payload_generation_speed(self):
        """Single payload generation should complete in under 10ms."""
        start = time.perf_counter()
        for _ in range(100):
            generate_batch_payloads(count=1)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Average payload generation took {avg_ms:.2f}ms (expected < 10ms)"

    def test_batch_payloads_speed(self):
        """Batch of 100 payloads should complete in under 500ms."""
        start = time.perf_counter()
        generate_batch_payloads(count=100)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Batch of 100 took {elapsed:.3f}s (expected < 0.5s)"

    @pytest.mark.live_api
    def test_batch_create_5_uoms(self, api_client):
        """Create, Read, and Update 5 UOM entries via live API."""

        import datetime

        payloads = generate_batch_payloads(count=5)
        assert len(payloads) >= 1, "Need at least 1 payload to test"

        # Ensure uniqueness: append timestamp suffix to avoid duplicate-key errors
        ts = datetime.datetime.now().strftime("%H%M%S")
        for i, p in enumerate(payloads):
            p["uom_code"] = f"{p['uom_code']}{ts}{i}"
            p["uom_description"] = f"{p['uom_description']}-{ts}{i}"

        created_ids = []
        start = time.perf_counter()

        # ── CREATE phase ──
        for i, payload in enumerate(payloads):
            result = api_client.create_entry(payload)
            assert result is not None, f"Create failed for payload {i+1}: {payload}"
            entry_id = result.get("id")
            assert entry_id, f"Created entry {i+1} has no id"
            created_ids.append(entry_id)

        # ── READ phase ──
        for i, entry_id in enumerate(created_ids):
            detail = api_client.get_entry(SCREEN_NAME, entry_id)
            assert detail is not None, f"Read failed for entry {entry_id}"
            assert detail.get("id") == entry_id, f"ID mismatch: expected {entry_id}, got {detail.get('id')}"

        # ── UPDATE phase ──
        for i, entry_id in enumerate(created_ids):
            detail = api_client.get_entry(SCREEN_NAME, entry_id)
            assert detail is not None, f"Read-back failed for entry {entry_id}"
            current_val = detail.get("uom_description", "") or ""
            update_payload = dict(detail)
            update_payload["uom_description"] = current_val + "-UPD"
            updated = api_client.update_entry(entry_id, update_payload)
            assert updated is not None, f"Update failed for entry {entry_id}"

        # ── Timing check ──
        elapsed = time.perf_counter() - start
        assert elapsed < 30, f"CRUD for 5 entries took {elapsed:.1f}s (expected < 30s)"
