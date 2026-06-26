import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    HSN_SAC_TYPE_IDS,
)


def _make_no(prefix="T"):
    """Generate a unique alphanumeric HSN/SAC code using timestamp."""
    ts = datetime.now().strftime("%H%M%S%f")[:10]
    return f"{prefix}{ts}"


def _type_id():
    return HSN_SAC_TYPE_IDS["Commodity"]


def _payload(hsn_no, desc="auto test", type_id=None):
    return {
        "id": "",
        "attribute_name": "HSN SAC",
        "hsn_sac_no": hsn_no,
        "hsn_sac_type": type_id or _type_id(),
        "hsn_sac_description": desc,
    }


@pytest.mark.live_api
class TestHsnSacLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_duplicate_hsn_sac_no_behavior(self, api_client):
        """Document API behavior for duplicate hsn_sac_no.
        Known bug: API allows duplicate codes (no uniqueness check on hsn_sac_no).
        Test records the actual behavior without asserting pass or fail on the bug."""
        no = _make_no("DUP")
        try:
            first = api_client.create_entry(_payload(no, "first"))
            assert first is not None and first.get("id"), "First create must succeed"

            second = api_client.create_entry(_payload(no, "second"))
            # Document the actual API behavior — duplicate is currently allowed (bug).
            # If the API is ever fixed to reject duplicates, this assertion will flip.
            assert second is not None and second.get("id"), (
                "API currently allows duplicate hsn_sac_no (known bug). "
                "If this fails, the bug has been fixed — update assertion to expect rejection."
            )
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create HSN SAC records across edge cases: all 4 types, 255-char no, 255-char description."""
        try:
            base = _make_no("BD")
            no_255 = (base + "A" * 255)[:255]
            desc_255 = ("AutoTest " + "D" * 255)[:255]

            cases = [
                ("services_type",     _make_no("SV"), HSN_SAC_TYPE_IDS["Services"],       "services desc"),
                ("transportation",    _make_no("TR"), HSN_SAC_TYPE_IDS["Transportation"],  "transport desc"),
                ("commission",        _make_no("CM"), HSN_SAC_TYPE_IDS["Commission"],      "commission desc"),
                ("commodity",         _make_no("CO"), HSN_SAC_TYPE_IDS["Commodity"],       "commodity desc"),
                ("255_char_no",       no_255,          _type_id(),                          "boundary no"),
                ("255_char_desc",     _make_no("DC"), _type_id(),                          desc_255),
            ]
            for label, no, type_id, desc in cases:
                result = api_client.create_entry(_payload(no, desc, type_id))
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass

    def test_hsn_sac_no_validation(self, api_client):
        """Verify which hsn_sac_no values the API accepts and rejects.
        Accepted: alphanumeric codes (digits, letters). Rejected: special chars (@#$%)."""
        accepted = [
            ("digits_only",    "9999001122"),
            ("letters_only",   _make_no("ALPHA")),
            ("alphanumeric",   _make_no("AZ99")),
        ]
        for label, no in accepted:
            result = api_client.create_entry(_payload(no))
            assert result is not None and result.get("id"), \
                f"'{no}' ({label}) must be accepted by API. Got: {result}"

        rejected = [
            ("special_chars",  f"@#${_make_no('X')}"),
        ]
        for label, no in rejected:
            result = api_client.create_entry(_payload(no))
            assert result is None or "id" not in result, \
                f"'{no}' ({label}) must be rejected by API. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update description -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        try:
            no = _make_no("LC")
            created = api_client.create_entry(_payload(no, "initial description"))
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("HSN SAC", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("hsn_sac_no") == no

            # LIST
            listing = api_client.list_entries("HSN SAC", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE description in ONE call (one update max per record)
            update_payload = dict(detail)
            update_payload["hsn_sac_description"] = "updated description"
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("HSN SAC", current_id)
            assert updated is not None
            assert updated.get("hsn_sac_description") == "updated description", \
                f"Description must be updated. Got: {updated.get('hsn_sac_description')}"

        finally:
            pass  # No cleanup — ERP has no delete and no second update
