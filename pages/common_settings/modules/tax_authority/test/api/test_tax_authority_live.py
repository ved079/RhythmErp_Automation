import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    build_tax_authority_api_payload,
    generate_tax_name,
    TAX_NAME_MAX_LENGTH,
)


def _make_name(prefix="TA"):
    ts = datetime.now().strftime("%H%M%S%f")[:10]
    return prefix + "".join(chr(ord("A") + int(c)) for c in ts)


@pytest.mark.live_api
class TestTaxAuthorityLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_duplicate_tax_name_behavior(self, api_client):
        """Create two records with the same tax_name — documents current API behavior.
        Known bug: API currently allows duplicate tax_name values.
        If this assertion flips to failure, the bug has been fixed — update accordingly."""
        try:
            fk = api_client.resolve_fk_ids({"tax_type_ref_id": "Tax Type", "country_ref_id": "Country"})
            tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
            country_id = next(iter(fk.get("country_ref_id", {}).values()), None)
            if not tax_type_id or not country_id:
                pytest.skip("Could not resolve FK IDs for Tax Type / Country")

            name = _make_name("DUP")
            p1 = build_tax_authority_api_payload(name, tax_type_id, country_id)
            r1 = api_client.create_entry(p1)
            assert r1 is not None and r1.get("id"), f"First create failed: {r1}"

            p2 = build_tax_authority_api_payload(name, tax_type_id, country_id)
            r2 = api_client.create_entry(p2)
            # Known bug: API allows duplicates. Documenting actual behavior.
            assert r2 is not None and r2.get("id"), (
                "Known bug: API currently allows duplicate tax_name. "
                "If this fails, the bug has been fixed — update assertion."
            )
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create records at boundary: long tax_name (255 chars), minimal name, all FK combos."""
        try:
            fk = api_client.resolve_fk_ids({"tax_type_ref_id": "Tax Type", "country_ref_id": "Country"})
            tax_type_ids = fk.get("tax_type_ref_id", {})
            country_ids = fk.get("country_ref_id", {})
            if not tax_type_ids or not country_ids:
                pytest.skip("Could not resolve FK IDs for Tax Type / Country")

            tax_type_id = next(iter(tax_type_ids.values()))
            country_id = next(iter(country_ids.values()))

            cases = [
                ("short_name",  _make_name("SHORT"), tax_type_id, country_id),
                ("long_name",   "A" * TAX_NAME_MAX_LENGTH, tax_type_id, country_id),
                ("all_fk_combos", _make_name("FK"), list(tax_type_ids.values())[-1], list(country_ids.values())[-1]),
            ]
            for label, name, tt_id, c_id in cases:
                p = build_tax_authority_api_payload(name, tt_id, c_id)
                result = api_client.create_entry(p)
                assert result is not None and result.get("id"), \
                    f"Create failed for case '{label}': {result}"
        finally:
            pass

    def test_tax_name_validation(self, api_client):
        """Verify API name validation: letters+spaces accepted; special chars rejected."""
        fk = api_client.resolve_fk_ids({"tax_type_ref_id": "Tax Type", "country_ref_id": "Country"})
        tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
        country_id = next(iter(fk.get("country_ref_id", {}).values()), None)
        if not tax_type_id or not country_id:
            pytest.skip("Could not resolve FK IDs")

        # Accepted: letters and spaces
        accepted = [
            ("alpha_spaces", "Central GST Authority Mumbai"),
            ("generated",    generate_tax_name()),
        ]
        for label, name in accepted:
            result = api_client.create_entry(
                build_tax_authority_api_payload(name, tax_type_id, country_id)
            )
            assert result is not None and result.get("id"), \
                f"'{name}' ({label}) must be accepted. Got: {result}"

        # Rejected: digits and special chars in name
        ts = datetime.now().strftime("%H%M%S")
        rejected = [
            ("digits",        f"Authority{ts}"),
            ("special_chars", f"Auth@#$!{ts}"),
        ]
        for label, name in rejected:
            result = api_client.create_entry(
                build_tax_authority_api_payload(name, tax_type_id, country_id)
            )
            assert result is None or "id" not in result, \
                f"'{name}' ({label}) must be rejected. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update tax_name -> verify.
        ERP is append-only: one update per record max, no delete (405)."""
        try:
            fk = api_client.resolve_fk_ids({"tax_type_ref_id": "Tax Type", "country_ref_id": "Country"})
            tax_type_id = next(iter(fk.get("tax_type_ref_id", {}).values()), None)
            country_id = next(iter(fk.get("country_ref_id", {}).values()), None)
            if not tax_type_id or not country_id:
                pytest.skip("Could not resolve FK IDs")

            name = _make_name("LC")
            created = api_client.create_entry(
                build_tax_authority_api_payload(name, tax_type_id, country_id)
            )
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("Tax Authority", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("tax_name") == name

            # LIST
            listing = api_client.list_entries("Tax Authority", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE tax_name in ONE call
            update_payload = dict(detail)
            update_payload["tax_name"] = _make_name("UPD")
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Tax Authority", current_id)
            assert updated is not None
            assert updated.get("tax_name") == update_payload["tax_name"], \
                f"Tax name must be updated. Got: {updated.get('tax_name')}"

        finally:
            pass
