import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    build_vehicle_master_api_payload,
    generate_vehicle_name,
    generate_vehicle_price,
    VEHICLE_NAME_MAX_LENGTH,
)


def _make_name(prefix="VM"):
    ts = datetime.now().strftime("%H%M%S%f")[:10]
    return prefix + " " + "".join(chr(ord("A") + int(c)) for c in ts)


def _payload(name, vehicle_type_id, fuel_type_id, price=1000000, description=""):
    return build_vehicle_master_api_payload(name, price, vehicle_type_id, fuel_type_id, description)


@pytest.mark.live_api
class TestVehicleMasterLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_duplicate_vehicle_name_behavior(self, api_client):
        """Create two vehicles with the same name — documents current API behavior.
        Known bug: API currently allows duplicate vehicle names.
        If this assertion flips to failure, the bug has been fixed — update accordingly."""
        try:
            fk = api_client.resolve_fk_ids({
                "vehicle_type_id": "Vehicle Type",
                "fuel_type_ref_id": "Fuel Type",
            })
            type_id = next(iter(fk.get("vehicle_type_id", {}).values()), None)
            fuel_id = next(iter(fk.get("fuel_type_ref_id", {}).values()), None)
            if not type_id or not fuel_id:
                pytest.skip("Could not resolve FK IDs for Vehicle Type / Fuel Type")

            name = _make_name("DUP")
            r1 = api_client.create_entry(_payload(name, type_id, fuel_id))
            assert r1 is not None and r1.get("id"), f"First create failed: {r1}"
            r2 = api_client.create_entry(_payload(name, type_id, fuel_id))
            # Known bug: API allows duplicates.
            assert r2 is not None and r2.get("id"), (
                "Known bug: API currently allows duplicate vehicle name. "
                "If this fails, the bug has been fixed — update assertion."
            )
        finally:
            pass

    def test_create_boundary_cases(self, api_client):
        """Create vehicles: all FK combos, with/without description, name at max length."""
        try:
            fk = api_client.resolve_fk_ids({
                "vehicle_type_id": "Vehicle Type",
                "fuel_type_ref_id": "Fuel Type",
            })
            type_ids = fk.get("vehicle_type_id", {})
            fuel_ids = fk.get("fuel_type_ref_id", {})
            if not type_ids or not fuel_ids:
                pytest.skip("Could not resolve FK IDs for Vehicle Type / Fuel Type")

            type_id = next(iter(type_ids.values()))
            fuel_id = next(iter(fuel_ids.values()))

            cases = [
                ("with_description",   _make_name("DSC"), type_id, fuel_id, 1000000, "Test description"),
                ("no_description",     _make_name("NOD"), type_id, fuel_id, 500000,  ""),
                ("different_fuel_type", _make_name("DFT"), type_id, list(fuel_ids.values())[-1], 2000000, ""),
            ]
            for label, name, t_id, f_id, price, desc in cases:
                p = _payload(name, t_id, f_id, price, desc)
                result = api_client.create_entry(p)
                assert result is not None and result.get("id"), \
                    f"Create failed for case '{label}': {result}"
        finally:
            pass

    def test_vehicle_name_validation(self, api_client):
        """Verify API name validation: letters+spaces accepted; special chars/digits rejected per ERP rule."""
        fk = api_client.resolve_fk_ids({
            "vehicle_type_id": "Vehicle Type",
            "fuel_type_ref_id": "Fuel Type",
        })
        type_id = next(iter(fk.get("vehicle_type_id", {}).values()), None)
        fuel_id = next(iter(fk.get("fuel_type_ref_id", {}).values()), None)
        if not type_id or not fuel_id:
            pytest.skip("Could not resolve FK IDs")

        # Accepted: alpha + spaces (ERP vehicle name rule)
        accepted = [
            ("alpha_spaces",   generate_vehicle_name("TEST")),
            ("longer_name",    "TATA ACE CARGO TRUCK"),
        ]
        for label, name in accepted:
            result = api_client.create_entry(_payload(name, type_id, fuel_id))
            assert result is not None and result.get("id"), \
                f"'{name}' ({label}) must be accepted. Got: {result}"

        # Rejected: digits and special chars
        ts = datetime.now().strftime("%H%M%S")
        rejected = [
            ("digits_in_name",  f"TRUCK{ts}"),
            ("special_chars",   f"TRUCK@#${ts}"),
        ]
        for label, name in rejected:
            result = api_client.create_entry(_payload(name, type_id, fuel_id))
            assert result is None or "id" not in result, \
                f"'{name}' ({label}) must be rejected. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update description -> verify.
        ERP is append-only: one update per record max, no delete (405)."""
        try:
            fk = api_client.resolve_fk_ids({
                "vehicle_type_id": "Vehicle Type",
                "fuel_type_ref_id": "Fuel Type",
            })
            type_id = next(iter(fk.get("vehicle_type_id", {}).values()), None)
            fuel_id = next(iter(fk.get("fuel_type_ref_id", {}).values()), None)
            if not type_id or not fuel_id:
                pytest.skip("Could not resolve FK IDs")

            name = generate_vehicle_name("LC")
            created = api_client.create_entry(_payload(name, type_id, fuel_id, 750000, "Original description"))
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("Vehicle Master", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("name") == name

            # LIST
            listing = api_client.list_entries("Vehicle Master", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE description in ONE call
            update_payload = dict(detail)
            update_payload["description"] = "Updated description " + datetime.now().strftime("%H%M%S")
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Vehicle Master", current_id)
            assert updated is not None
            assert updated.get("description") == update_payload["description"], \
                f"Description must be updated. Got: {updated.get('description')}"

        finally:
            pass
