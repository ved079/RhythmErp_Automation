import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


def _make_name(prefix="S"):
    """Generate unique all-alphabetic season name. Converts timestamp digits to letters."""
    ts = datetime.now().strftime("%H%M%S")
    ts_alpha = "".join(chr(ord('A') + int(c)) for c in ts)
    return f"{prefix} {ts_alpha}"


@pytest.mark.live_api
class TestSeasonLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded data."""

    def test_duplicate_name_rejected(self, api_client):
        """API enforces name uniqueness — second create with same name must fail."""
        name = _make_name("DUP")
        try:
            first = api_client.create_entry({
                "id": "", "attribute_name": "Season",
                "name": name, "description": "first", "status": True,
            })
            assert first is not None and first.get("id"), "First create must succeed"

            second = api_client.create_entry({
                "id": "", "attribute_name": "Season",
                "name": name, "description": "second", "status": True,
            })
            assert second is None or "id" not in second, \
                "Duplicate name must be rejected by API"
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create seasons: no description, inactive status, hyphen in name (API accepts hyphen)."""
        try:
            base = _make_name("BD")
            name_with_hyphen = f"{_make_name('H')}-Crop"
            name_255 = (base + " " + "A" * 255)[:255]

            cases = [
                ("no_description",  _make_name("ND"), None,            True),
                ("inactive",        _make_name("IN"), "inactive test", False),
                ("hyphen_in_name",  name_with_hyphen, "hyphen test",   True),
                ("255_char_name",   name_255,          None,            True),
            ]
            for label, name, desc, status in cases:
                result = api_client.create_entry({
                    "id": "", "attribute_name": "Season",
                    "name": name, "description": desc, "status": status,
                })
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass

    def test_name_character_rules(self, api_client):
        """Verify exact API name validation rules discovered via probe:
        - Underscore: rejected (Invalid Seasson Name)
        - Special chars (@#$%): rejected (Invalid Seasson Name)
        - Hyphen: accepted (frontend rejects it but API does not)
        - Numbers + letters: accepted"""
        ts = _make_name("V")

        accepted = [
            ("hyphen",         f"H-{ts}"),
            ("numbers_mixed",  f"123{ts}"),
        ]
        for label, name in accepted:
            result = api_client.create_entry({
                "id": "", "attribute_name": "Season",
                "name": name, "description": None, "status": True,
            })
            assert result is not None and result.get("id"), \
                f"'{name}' ({label}) must be accepted by API. Got: {result}"

        rejected = [
            ("underscore",     f"K_{ts}"),
            ("special_chars",  f"@#{ts}"),
        ]
        for label, name in rejected:
            result = api_client.create_entry({
                "id": "", "attribute_name": "Season",
                "name": name, "description": None, "status": True,
            })
            assert result is None or "id" not in result, \
                f"'{name}' ({label}) must be rejected by API. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> search -> update -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        try:
            name = _make_name("LC")
            created = api_client.create_entry({
                "id": "", "attribute_name": "Season",
                "name": name, "description": "initial desc", "status": True,
            })
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            detail = api_client.get_entry("Season", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("name") == name

            listing = api_client.list_entries("Season", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            search_result = api_client.list_entries("Season", page=1, page_size=200, search=name[:5])
            assert search_result is not None
            search_items = search_result.get("screenmatlistingdata_set", [])
            assert any(item.get("name") == name for item in search_items), \
                "Entry must appear in partial search results"

            update_payload = dict(detail)
            update_payload["description"] = "updated desc"
            update_payload["status"] = False
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Season", current_id)
            assert updated is not None
            assert updated.get("description") == "updated desc", \
                f"Description must be updated. Got: {updated.get('description')}"
            assert updated.get("status") is False, \
                f"Status must be False. Got: {updated.get('status')}"

        finally:
            pass  # No cleanup — ERP has no delete and no second update
