import pytest
import sys
import os
from datetime import datetime
import random
import string
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.uom.data.uom_data import (
    generate_uom_api_payload,
    generate_uom_data,
)


def _make_code(prefix="T"):
    """Generate a unique UOM code: prefix + 6-char timestamp. Max 7 chars, uppercase+digits only."""
    return (prefix + datetime.now().strftime("%H%M%S"))[:10]


def _deactivate(api_client, entry_id):
    """Soft-delete a UOM entry by setting is_active=False. ERP has no hard delete API."""
    try:
        detail = api_client.get_entry("UOM", entry_id)
        if detail:
            p = dict(detail)
            p["is_active"] = False
            api_client.update_entry(entry_id, p)
    except Exception:
        pass


@pytest.mark.live_api
class TestUOMLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded data assumed."""

    def test_duplicate_code_rejected(self, api_client):
        """Create a UOM, then POST the same code again — second must fail."""
        code = _make_code("DUP")[:10]
        first_id = None
        try:
            first = api_client.create_entry({
                "id": "", "attribute_name": "UOM",
                "uom_code": code, "uom_description": "duplicate base", "status": True,
            })
            assert first is not None and first.get("id"), "First create must succeed"
            first_id = first["id"]

            time.sleep(0.1)
            second = api_client.create_entry({
                "id": "", "attribute_name": "UOM",
                "uom_code": code, "uom_description": "duplicate attempt", "status": True,
            })
            assert second is None or "id" not in second, \
                "Second create with same code must be rejected"
        finally:
            if first_id:
                _deactivate(api_client, first_id)

    def test_create_boundary_cases(self, api_client):
        """Create UOMs covering: numbers in code, 255-char description, no description."""
        created_ids = []
        try:
            ts = datetime.now().strftime("%H%M%S")
            cases = [
                ("numbers_in_code", f"N{ts}"[:10],   "numbers in code test"),
                ("255_char_desc",   f"D{ts}"[:10],   "D" * 255),
                ("no_description",  f"E{ts}"[:10],   None),
            ]
            for label, uom_code, uom_description in cases:
                payload = {
                    "id": "", "attribute_name": "UOM",
                    "uom_code": uom_code, "uom_description": uom_description, "status": True,
                }
                result = api_client.create_entry(payload)
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
                created_ids.append(result["id"])
        finally:
            for entry_id in created_ids:
                _deactivate(api_client, entry_id)

    def test_create_with_hyphen_and_underscore(self, api_client):
        """Backend must accept hyphen and underscore in UOM code."""
        ts = datetime.now().strftime("%M%S")
        code = f"H-_{ts}"[:10]
        entry_id = None
        try:
            result = api_client.create_entry({
                "id": "", "attribute_name": "UOM",
                "uom_code": code, "uom_description": "hyphen underscore test", "status": True,
            })
            assert result is not None and result.get("id"), \
                f"Backend must accept hyphen and underscore in code. Got: {result}"
            entry_id = result["id"]
        finally:
            if entry_id:
                _deactivate(api_client, entry_id)

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> search -> update -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        current_id = None
        try:
            # CREATE — use short unique code safe for any tenant
            ts = datetime.now().strftime("%H%M%S")
            code = f"L{ts}"[:10]
            created = api_client.create_entry({
                "id": "", "attribute_name": "UOM",
                "uom_code": code, "uom_description": "lifecycle test", "status": True,
            })
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET by id
            detail = api_client.get_entry("UOM", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("uom_code") == code

            # LIST — entry must appear
            listing = api_client.list_entries("UOM", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # SEARCH — entry must appear
            search_result = api_client.list_entries("UOM", page=1, page_size=200, search=code)
            assert search_result is not None
            search_items = search_result.get("screenmatlistingdata_set", [])
            assert any(item.get("uom_code") == code for item in search_items), \
                "Created entry must appear in search results"

            # UPDATE description + status in one call
            # ERP versioning: update creates a NEW version row with a new id.
            # Cannot chain two updates on the same record — second would fail with
            # "already exists". Change both fields in a single update call.
            update_payload = dict(detail)
            update_payload["uom_description"] = "updated desc"
            update_payload["status"] = False
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]  # follow the new version id

            updated = api_client.get_entry("UOM", current_id)
            assert updated is not None
            assert updated.get("uom_description") == "updated desc", \
                f"Description must be updated. Got: {updated.get('uom_description')}"
            assert updated.get("status") is False, \
                f"Status must be False after update. Got: {updated.get('status')}"

            # NOTE: ERP allows only ONE update per record (versioning creates a new row).
            # A second update fails with "already exists". No hard delete API exists (405).
            # Lifecycle verified: create → get → list → search → update → confirm update.

        finally:
            pass  # No cleanup possible — ERP has no delete and no second update
