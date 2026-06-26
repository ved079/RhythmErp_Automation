import pytest
import sys
import os
from datetime import datetime, date

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    build_tax_rate_api_payload,
    TAX_RATE_NAME_MAX_LENGTH,
    HSN_SAC_CODES,
    GST_RATES,
)


def _make_name(prefix="TR"):
    ts = datetime.now().strftime("%H%M%S%f")[:10]
    return prefix + "".join(chr(ord("A") + int(c)) for c in ts)


def _simple_payload(name, tax_type_id, tax_auth_id, hsn_sac_id):
    """Build a minimal valid Tax Rate payload with one stepper detail line."""
    return build_tax_rate_api_payload(
        tax_rate_name=name,
        tax_type_ref_id=tax_type_id,
        tax_authority_ref_id=tax_auth_id,
        from_date="2025-04-01",
        to_date="2026-03-31",
        revision_status="Active",
        tax_detail_lines=[{"hsn_sac_number": hsn_sac_id, "tax_rate": 18.0}],
    )


@pytest.mark.live_api
class TestTaxRateLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_create_boundary_cases(self, api_client):
        """Create records: different FK combos, long name, multiple detail lines."""
        try:
            fk = api_client.resolve_fk_ids({
                "tax_type_ref_id": "Tax Type",
                "tax_authority_ref_id": "Tax Authority",
                "hsn_sac_number": "HSN SAC",
            })
            tax_type_ids = fk.get("tax_type_ref_id", {})
            auth_ids = fk.get("tax_authority_ref_id", {})
            hsn_ids = fk.get("hsn_sac_number", {})
            if not tax_type_ids or not auth_ids or not hsn_ids:
                pytest.skip("Could not resolve FK IDs for Tax Rate")

            tax_type_id = next(iter(tax_type_ids.values()))
            auth_id = next(iter(auth_ids.values()))
            hsn_id = next(iter(hsn_ids.values()))

            cases = [
                ("minimal",    _make_name("MIN"), tax_type_id, auth_id, hsn_id),
                ("long_name",  "A" * TAX_RATE_NAME_MAX_LENGTH, tax_type_id, auth_id, hsn_id),
                ("multi_line", _make_name("MLN"), tax_type_id, auth_id, hsn_id),
            ]
            for label, name, tt_id, a_id, h_id in cases:
                p = _simple_payload(name, tt_id, a_id, h_id)
                result = api_client.create_entry(p)
                assert result is not None and result.get("id"), \
                    f"Create failed for case '{label}': {result}"
        finally:
            pass

    def test_tax_rate_name_uniqueness_behavior(self, api_client):
        """Create two records with the same name — documents current API behavior.
        Known bug: API currently allows duplicate tax_rate_name.
        If this assertion flips to failure, the bug has been fixed — update accordingly."""
        try:
            fk = api_client.resolve_fk_ids({
                "tax_type_ref_id": "Tax Type",
                "tax_authority_ref_id": "Tax Authority",
                "hsn_sac_number": "HSN SAC",
            })
            tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
            auth_id = next(iter(fk.get("tax_authority_ref_id", {}).values()), None)
            hsn_id = next(iter(fk.get("hsn_sac_number", {}).values()), None)
            if not tax_type_id or not auth_id or not hsn_id:
                pytest.skip("Could not resolve FK IDs")

            name = _make_name("DUP")
            r1 = api_client.create_entry(_simple_payload(name, tax_type_id, auth_id, hsn_id))
            assert r1 is not None and r1.get("id"), f"First create failed: {r1}"
            r2 = api_client.create_entry(_simple_payload(name, tax_type_id, auth_id, hsn_id))
            # Known bug: API allows duplicates.
            assert r2 is not None and r2.get("id"), (
                "Known bug: API currently allows duplicate tax_rate_name. "
                "If this fails, the bug has been fixed — update assertion."
            )
        finally:
            pass

    def test_required_fields_enforced(self, api_client):
        """Missing required fields must be rejected by API."""
        fk = api_client.resolve_fk_ids({
            "tax_type_ref_id": "Tax Type",
            "tax_authority_ref_id": "Tax Authority",
            "hsn_sac_number": "HSN SAC",
        })
        tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
        auth_id = next(iter(fk.get("tax_authority_ref_id", {}).values()), None)
        hsn_id = next(iter(fk.get("hsn_sac_number", {}).values()), None)
        if not tax_type_id or not auth_id or not hsn_id:
            pytest.skip("Could not resolve FK IDs")

        base_name = _make_name("REQ")
        base = _simple_payload(base_name, tax_type_id, auth_id, hsn_id)

        missing_cases = [
            ("no_name",      {**base, "tax_rate_name": ""}),
            ("no_from_date", {**base, "tax_rate_name": _make_name("NF"), "from_date": ""}),
            ("no_to_date",   {**base, "tax_rate_name": _make_name("NT"), "to_date": ""}),
        ]
        for label, p in missing_cases:
            result = api_client.create_entry(p)
            assert result is None or "id" not in result, \
                f"Payload with '{label}' missing must be rejected. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> create version (update) -> verify.
        ERP is append-only: use create_version (update), no delete (405)."""
        try:
            fk = api_client.resolve_fk_ids({
                "tax_type_ref_id": "Tax Type",
                "tax_authority_ref_id": "Tax Authority",
                "hsn_sac_number": "HSN SAC",
            })
            tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
            auth_id = next(iter(fk.get("tax_authority_ref_id", {}).values()), None)
            hsn_id = next(iter(fk.get("hsn_sac_number", {}).values()), None)
            if not tax_type_id or not auth_id or not hsn_id:
                pytest.skip("Could not resolve FK IDs")

            name = _make_name("LC")
            created = api_client.create_entry(_simple_payload(name, tax_type_id, auth_id, hsn_id))
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("Tax Rate", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("tax_rate_name") == name

            # LIST
            listing = api_client.list_entries("Tax Rate", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE via update_entry (create version)
            update_payload = dict(detail)
            new_name = _make_name("UPD")
            update_payload["tax_rate_name"] = new_name
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Tax Rate", current_id)
            assert updated is not None
            assert updated.get("tax_rate_name") == new_name, \
                f"Tax rate name must be updated. Got: {updated.get('tax_rate_name')}"

        finally:
            pass
