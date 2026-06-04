"""
test_uom_conversion_perf.py — Performance benchmarks + Live CRUD tests.
No browser needed. In-memory speed tests + live API CRUD verification.
"""

import time
import datetime
import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_api_payloads, generate_batch_payloads,
)

SCREEN_NAME = "UOM Conversion"


@pytest.mark.performance
class TestUOMConversionPerformance:
    """Verify UOM Conversion payload generation meets speed benchmarks and live CRUD."""

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
    def test_batch_create_5_conversions(self, api_client):
        """Create, Read, and Update 5 UOM Conversion entries via live API."""

        from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import UOM_IDS

        # Fetch existing conversions to avoid duplicates
        # The unique constraint is bidirectional: (A→B) conflicts with (B→A)
        result = api_client.list_entries(SCREEN_NAME, page=1, page_size=200)
        existing = set()
        if result:
            for item in result.get("screenmatlistingdata_set", []):
                src = item.get("source_uom_code", "")
                tgt = item.get("target_uom_code", "")
                existing.add((src, tgt))
                existing.add((tgt, src))  # bidirectional

        # Get actual UOM entries from ERP to find correct name→id mapping
        uom_result = api_client.list_entries("UOM", page=1, page_size=200)
        uom_name_to_id = {}
        if uom_result:
            for item in uom_result.get("screenmatlistingdata_set", []):
                uom_name_to_id[item.get("uom_code", "")] = item["id"]

        # Build unique (source, target) pairs using ERP-verified IDs
        uom_names = list(uom_name_to_id.keys())
        unique_payloads = []
        pair_idx = 0

        for src in uom_names:
            for tgt in uom_names:
                if src == tgt:
                    continue
                # Check both directions against existing pairs
                if (src, tgt) not in existing and (tgt, src) not in existing:
                    payload = {
                        "id": "",
                        "attribute_name": SCREEN_NAME,
                        "source_uom_code": uom_name_to_id[src],
                        "target_uom_code": uom_name_to_id[tgt],
                        "conversion_factor": float(pair_idx + 1) * 1.5,
                    }
                    unique_payloads.append(payload)
                    pair_idx += 1
                    if len(unique_payloads) >= 5:
                        break
            if len(unique_payloads) >= 5:
                break

        assert len(unique_payloads) >= 1, "No unique UOM conversion pairs available"

        created_ids = []
        start = time.perf_counter()

        # ── CREATE phase ──
        for i, payload in enumerate(unique_payloads):
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
            update_payload = dict(detail)
            current_factor = float(detail.get("conversion_factor", 1))
            update_payload["conversion_factor"] = current_factor + 1.0
            updated = api_client.update_entry(entry_id, update_payload)
            assert updated is not None, f"Update failed for entry {entry_id}"

        # ── Timing check ──
        elapsed = time.perf_counter() - start
        assert elapsed < 30, f"CRUD for {len(unique_payloads)} entries took {elapsed:.1f}s (expected < 30s)"
