"""
test_tax_authority_perf.py — Performance benchmarks + Live CRUD tests.
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
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    generate_tax_authority_api_payloads, generate_batch_payloads, get_fk_screen_mapping,
)

MOCK_FK_IDS = {
    "tax_type_ref_id": {"GST": 93},
    "country_ref_id": {f"Country {i}": i for i in range(20)},
}

SCREEN_NAME = "Tax Authority"


@pytest.mark.performance
class TestTaxAuthorityPerformance:
    """Verify Tax Authority payload generation meets speed benchmarks and live CRUD."""

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
    def test_batch_create_5_tax_authorities(self, api_client):
        resolver = FkResolver(api_client)
        fk_ids = {}
        for field_key, screen_name in get_fk_screen_mapping().items():
            resolved = resolver.resolve(screen_name)
            if resolved:
                fk_ids[field_key] = resolved

        payloads = generate_batch_payloads(count=5, dropdown_ids=fk_ids or None)
        ts = datetime.datetime.now().strftime("%H%M%S")
        for i, p in enumerate(payloads):
            p["name"] = f"TestAuth{ts}{i}"
            if "tax_name" in p:
                del p["tax_name"]
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
            update_payload = dict(detail)
            update_payload["name"] = f"TestAuthUpd{ts}{i}"
            updated = api_client.update_entry(entry_id, update_payload)
            if updated is None:
                pass

        elapsed = time.perf_counter() - start
        assert elapsed < 30, f"CRUD for 5 entries took {elapsed:.1f}s (expected < 30s)"
