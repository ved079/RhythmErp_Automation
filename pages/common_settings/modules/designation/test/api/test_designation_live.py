import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


def _make_name(prefix="T"):
    """Generate a unique all-alphabetic designation name safe for any tenant.
    Maps timestamp digits to letters (0->A ... 9->J) to avoid digit rejection."""
    ts = datetime.now().strftime("%H%M%S")
    ts_alpha = "".join(chr(ord('A') + int(c)) for c in ts)
    return f"{prefix} Desig {ts_alpha}"


@pytest.mark.live_api
class TestDesignationLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded data assumed."""

    def test_duplicate_name_rejected(self, api_client):
        """API enforces name uniqueness — second create with same name must fail.
        Note: frontend also rejects duplicates (consistent behavior)."""
        name = _make_name("DUP")
        try:
            first = api_client.create_entry({
                "id": "", "attribute_name": "Designation",
                "name": name, "description": "first", "status": True,
            })
            assert first is not None and first.get("id"), "First create must succeed"

            second = api_client.create_entry({
                "id": "", "attribute_name": "Designation",
                "name": name, "description": "second", "status": True,
            })
            assert second is None or "id" not in second, \
                "Duplicate name must be rejected by API"
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create designations: 255-char name (unique prefix + padding), no description, inactive."""
        try:
            # 255-char name: unique 20-char prefix + padding to hit boundary
            base = _make_name("BD")  # ~20 chars, guaranteed unique
            name_255 = (base + " " + "A" * 255)[:255]
            cases = [
                ("255_char_name",  name_255,         None,             True),
                ("no_description", _make_name("ND"), None,             True),
                ("inactive",       _make_name("IN"), "inactive test",  False),
            ]
            for label, name, desc, status in cases:
                result = api_client.create_entry({
                    "id": "", "attribute_name": "Designation",
                    "name": name, "description": desc, "status": status,
                })
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass

    def test_name_validation_split_frontend_vs_backend(self, api_client):
        """Backend and frontend have different validation rules for name:
        - Digits mixed with letters: backend accepts, frontend rejects (type='character')
        - Special chars (@#$): backend rejects with 'Invalid Name', frontend also rejects
        This test documents the exact boundary."""
        ts = _make_name("V")

        # Digits mixed with letters — backend accepts (frontend-only restriction)
        digits_name = f"123{ts}"
        result_digits = api_client.create_entry({
            "id": "", "attribute_name": "Designation",
            "name": digits_name, "description": None, "status": True,
        })
        assert result_digits is not None and result_digits.get("id"), \
            f"Digits in name must be accepted by backend. Got: {result_digits}"

        # Special chars — backend rejects (both frontend and backend enforce this)
        special_name = f"@#{ts}"
        result_special = api_client.create_entry({
            "id": "", "attribute_name": "Designation",
            "name": special_name, "description": None, "status": True,
        })
        assert result_special is None or "id" not in result_special, \
            f"Special chars in name must be rejected by backend. Got: {result_special}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> search -> update -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        current_id = None
        try:
            name = _make_name("L")
            created = api_client.create_entry({
                "id": "", "attribute_name": "Designation",
                "name": name, "description": "lifecycle test", "status": True,
            })
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            detail = api_client.get_entry("Designation", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("name") == name

            listing = api_client.list_entries("Designation", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            search_result = api_client.list_entries("Designation", page=1, page_size=200, search=name)
            assert search_result is not None
            search_items = search_result.get("screenmatlistingdata_set", [])
            assert any(item.get("name") == name for item in search_items), \
                "Created entry must appear in search results"

            update_payload = dict(detail)
            update_payload["description"] = "updated desc"
            update_payload["status"] = False
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Designation", current_id)
            assert updated is not None
            assert updated.get("description") == "updated desc", \
                f"Description must be updated. Got: {updated.get('description')}"
            assert updated.get("status") is False, \
                f"Status must be False after update. Got: {updated.get('status')}"

        finally:
            pass
