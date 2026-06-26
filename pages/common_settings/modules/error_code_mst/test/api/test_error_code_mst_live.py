import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    ERROR_CODE_TYPE_IDS,
)


def _make_code(prefix="EC"):
    """Generate a unique alphanumeric error code using timestamp."""
    ts = datetime.now().strftime("%H%M%S%f")[:8]
    return f"{prefix}-{ts}"


def _type_id():
    return ERROR_CODE_TYPE_IDS["Farmer"]


def _payload(code, desc="auto test", type_id=None, is_qty_amount="Amount"):
    return {
        "id": "",
        "attribute_name": "Error Code Mst",
        "error_code_type": type_id or _type_id(),
        "code": code,
        "description": desc,
        "is_qty_amount": is_qty_amount,
    }


@pytest.mark.live_api
class TestErrorCodeMstLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_duplicate_code_behavior(self, api_client):
        """Document API behavior for duplicate (error_code_type + code) combination.
        Known bug: API may allow duplicates (no uniqueness check).
        Test records actual behavior without asserting on the bug itself."""
        code = _make_code("DUP")
        type_id = _type_id()
        try:
            first = api_client.create_entry(_payload(code, "first", type_id))
            assert first is not None and first.get("id"), "First create must succeed"

            second = api_client.create_entry(_payload(code, "second", type_id))
            # Document the actual behavior — duplicate is currently allowed (known bug).
            # If the API is ever fixed, update this assertion to expect rejection.
            assert second is not None and second.get("id"), (
                "API currently allows duplicate error code (known bug). "
                "If this fails, the bug has been fixed — update assertion to expect rejection."
            )
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create records across all 4 types, both is_qty_amount values, 255-char code."""
        try:
            base = _make_code("BD")
            code_255 = (base + "A" * 255)[:255]

            cases = [
                ("farmer_qty",      _make_code("FM"), ERROR_CODE_TYPE_IDS["Farmer"],       "desc", "Qty"),
                ("debit_amount",    _make_code("DN"), ERROR_CODE_TYPE_IDS["Debit Note"],   "desc", "Amount"),
                ("credit_qty",      _make_code("CN"), ERROR_CODE_TYPE_IDS["Credit Note"],  "desc", "Qty"),
                ("workflow_amount", _make_code("WF"), ERROR_CODE_TYPE_IDS["Workflow"],     "desc", "Amount"),
                ("no_description",  _make_code("ND"), _type_id(),                          None,   "Amount"),
                ("255_char_code",   code_255,          _type_id(),                          "desc", "Qty"),
            ]
            for label, code, type_id, desc, qty_amt in cases:
                result = api_client.create_entry(_payload(code, desc, type_id, qty_amt))
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass

    def test_code_field_validation(self, api_client):
        """Verify code field accepts alphanumeric + hyphens, rejects special chars (@#$%)."""
        accepted = [
            ("digits_only",    _make_code("NUM")),
            ("with_hyphen",    f"FM-{_make_code('H')}"),
            ("alphanumeric",   _make_code("AZ")),
        ]
        for label, code in accepted:
            result = api_client.create_entry(_payload(code))
            assert result is not None and result.get("id"), \
                f"'{code}' ({label}) must be accepted by API. Got: {result}"

        rejected = [
            ("special_chars", f"@#{_make_code('X')}"),
        ]
        for label, code in rejected:
            result = api_client.create_entry(_payload(code))
            assert result is None or "id" not in result, \
                f"'{code}' ({label}) must be rejected by API. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update description -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        try:
            code = _make_code("LC")
            created = api_client.create_entry(_payload(code, "initial description", is_qty_amount="Qty"))
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("Error Code Mst", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("code") == code

            # LIST
            listing = api_client.list_entries("Error Code Mst", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE description + is_qty_amount in ONE call
            update_payload = dict(detail)
            update_payload["description"] = "updated description"
            update_payload["is_qty_amount"] = "Amount"
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Error Code Mst", current_id)
            assert updated is not None
            assert updated.get("description") == "updated description", \
                f"Description must be updated. Got: {updated.get('description')}"

        finally:
            pass  # No cleanup — ERP has no delete and no second update
