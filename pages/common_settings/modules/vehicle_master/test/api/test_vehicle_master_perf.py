"""
test_vehicle_master_perf.py — Performance benchmarks + Live CRUD tests.
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

from common.fk_resolver import FkResolver
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_vehicle_master_api_payloads, generate_batch_payloads, get_fk_screen_mapping,
)

MOCK_FK_IDS = {
    "vehicle_type_id": {"Truck": 1, "Trailer": 2, "Tanker": 3, "Mini Truck": 4, "Pickup": 5},
    "fuel_type_ref_id": {"Diesel": 1, "Petrol": 2, "CNG": 3, "Electric": 4, "LPG": 5},
}

SCREEN_NAME = "Vehicle Master"


@pytest.mark.performance
class TestVehicleMasterPerformance:
    """Verify Vehicle Master payload generation meets speed benchmarks and live CRUD."""

    def test_payload_generation_speed(self):
        start = time.perf_counter()
        for _ in range(100):
            generate_batch_payloads(count=1, dropdown_ids=MOCK_FK_IDS)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Average payload generation took {avg_ms:.2f}ms (expected < 10ms)"

    def test_batch_payloads_speed(self):
        start = time.perf_counter()
        generate_batch_payloads(count=100, dropdown_ids=MOCK_FK_IDS)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Batch of 100 took {elapsed:.3f}s (expected < 0.5s)"

    @pytest.mark.live_api
    def test_batch_create_5_vehicle_masters(self, api_client):
        resolver = FkResolver(api_client)
        fk_ids = {}
        for field_key, screen_name in get_fk_screen_mapping().items():
            resolved = resolver.resolve(screen_name)
            if resolved:
                fk_ids[field_key] = resolved

        payloads = generate_batch_payloads(count=5, dropdown_ids=fk_ids or None)
        ts = datetime.datetime.now().strftime("%H%M%S")
        for i, p in enumerate(payloads):
            p["name"] = f"{p['name']}{ts}{i}"
            p["description"] = f"{p['description']}-{ts}{i}"
        assert len(payloads) >= 1, "Need at least 1 payload to test"

        created_ids = []
        start = time.perf_counter()

        for i, payload in enumerate(payloads):
            result = api_client.create_entry(payload)
            assert result is not None, f"Create failed for payload {i+1}: {payload}"
            entry_id = result.get("id")
            assert entry_id, f"Created entry {i+1} has no id"
            created_ids.append(entry_id)

        for i, entry_id in enumerate(created_ids):
            detail = api_client.get_entry(SCREEN_NAME, entry_id)
            assert detail is not None, f"Read failed for entry {entry_id}"
            assert detail.get("id") == entry_id, f"ID mismatch: expected {entry_id}, got {detail.get('id')}"

        for i, entry_id in enumerate(created_ids):
            detail = api_client.get_entry(SCREEN_NAME, entry_id)
            assert detail is not None, f"Read-back failed for entry {entry_id}"
            current_val = detail.get("description", "") or ""
            update_payload = dict(detail)
            update_payload["description"] = current_val + "-UPD"
            updated = api_client.update_entry(entry_id, update_payload)
            assert updated is not None, f"Update failed for entry {entry_id}"

        elapsed = time.perf_counter() - start
        assert elapsed < 30, f"CRUD for 5 entries took {elapsed:.1f}s (expected < 30s)"
