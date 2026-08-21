"""
test_cbr_payload.py — Fast API payload structure tests for Commodity Base Rate.
No browser needed. All tests validate in-memory payload generation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    build_cbr_api_payload,
    generate_cbr_payloads,
    generate_batch_payloads,
    PRICING_TYPE_ID_MAP,
    LOCATION_ID_MAP,
    DEFAULT_COMMODITY_BASE_RATE_FK_IDS,
    FIELD_VALIDATION_RULES,
)


@pytest.mark.api
class TestCBRAPIPayload:
    """Verify that generated Commodity Base Rate API payloads are structurally correct."""

    def test_payload_has_required_keys(self):
        """Payload must include id, attribute_name, and all CBR header fields."""
        payloads = generate_cbr_payloads(count=1)
        payload = payloads[0]
        required_keys = {
            "id", "attribute_name", "pricing_type_ref_id",
            "from_date", "to_date", "location_ref_id",
        }
        assert required_keys.issubset(set(payload.keys())), \
            f"Missing keys: {required_keys - set(payload.keys())}"

    def test_payload_has_children_with_detail_rows(self):
        """CBR payload must include a children stepper with at least one detail row."""
        payloads = generate_cbr_payloads(count=1)
        payload = payloads[0]
        assert "children" in payload
        assert len(payload["children"]) == 1
        stepper = payload["children"][0]
        assert stepper["is_stepper"] is True
        assert len(stepper["details"]) >= 1
        row = stepper["details"][0]
        assert isinstance(row["item_ref_id"], int)
        assert isinstance(row["uom"], int)
        assert "minimum_range" in row
        assert "maximum_range" in row
        assert "details" in row

    def test_payload_attribute_name(self):
        """attribute_name must be exactly 'Commodity Base Rate'."""
        payloads = generate_cbr_payloads(count=1)
        assert payloads[0]["attribute_name"] == "Commodity Base Rate"

    def test_payload_id_is_empty_string(self):
        """id must be empty string for create operations."""
        payloads = generate_cbr_payloads(count=1)
        assert payloads[0]["id"] == ""

    def test_payload_pricing_type_is_integer(self):
        """pricing_type_ref_id must be an integer FK ID."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["pricing_type_ref_id"], int)

    def test_payload_from_date_is_string(self):
        """from_date must be a string (ISO datetime)."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["from_date"], str)

    def test_payload_to_date_is_string(self):
        """to_date must be a string (ISO datetime)."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["to_date"], str)

    def test_payload_location_ref_id_is_integer(self):
        """location_ref_id must be an integer FK ID."""
        payloads = generate_cbr_payloads(count=1)
        assert isinstance(payloads[0]["location_ref_id"], int)

    def test_payload_no_status_field(self):
        """CBR does not have a status field."""
        payloads = generate_cbr_payloads(count=1)
        assert "status" not in payloads[0]

    def test_payload_pricing_type_in_valid_pool(self):
        """pricing_type_ref_id value must be from PRICING_TYPE_ID_MAP."""
        payloads = generate_cbr_payloads(count=5)
        valid_ids = set(PRICING_TYPE_ID_MAP.values())
        for p in payloads:
            assert p["pricing_type_ref_id"] in valid_ids, \
                f"pricing_type_ref_id {p['pricing_type_ref_id']} not in PRICING_TYPE_ID_MAP"

    def test_payload_location_in_valid_pool(self):
        """location_ref_id value must be from LOCATION_ID_MAP."""
        payloads = generate_cbr_payloads(count=5)
        valid_ids = set(LOCATION_ID_MAP.values())
        for p in payloads:
            assert p["location_ref_id"] in valid_ids, \
                f"location_ref_id {p['location_ref_id']} not in LOCATION_ID_MAP"

    def test_build_with_explicit_values(self):
        """build_cbr_api_payload with explicit values should use them."""
        payload = build_cbr_api_payload(
            pricing_type_ref_id=118,
            location_ref_id=1,
            from_date="2025-04-01T00:00:00Z",
            to_date="2099-12-30T18:30:00Z",
        )
        assert payload["pricing_type_ref_id"] == 118
        assert payload["location_ref_id"] == 1
        assert payload["from_date"] == "2025-04-01T00:00:00Z"
        assert payload["to_date"] == "2099-12-30T18:30:00Z"
        assert payload["attribute_name"] == "Commodity Base Rate"

    def test_payload_to_date_format(self):
        """to_date should follow ISO datetime format with Z suffix."""
        payloads = generate_cbr_payloads(count=5)
        for p in payloads:
            assert p["to_date"].endswith("Z"), \
                f"to_date should end with Z, got: {p['to_date']}"


from pages.commodity_settings.modules.commodity_base_rate.data.cbr_data import (
    ITEM_ID_MAP, UOM_ID_MAP,
)

_ITEM_UOM_MAP = {int(v): list(UOM_ID_MAP.values())[i % len(UOM_ID_MAP)] for i, v in enumerate(ITEM_ID_MAP.values())}
_MOCK_DROPDOWN_IDS = {
    "location_ref_id": LOCATION_ID_MAP,
    "item_ref_id": ITEM_ID_MAP,
    "uom": UOM_ID_MAP,
    "item_uom_map": _ITEM_UOM_MAP,
}

# Mock existing entries: 2 locations, each with 1 item already in grid
_LOC_IDS = list(LOCATION_ID_MAP.values())
_ITEM_IDS = list(ITEM_ID_MAP.values())
_MOCK_EXISTING = [
    {
        "id": 1,
        "location_ref_id": _LOC_IDS[0],
        "pricing_type_ref_id": 118,
        "from_date": "2026-06-02T00:00:00Z",
        "to_date": "2099-12-31T18:30:00Z",
        "_existing_item_ids": {_ITEM_IDS[0]},
        "_detail": {
            "id": 1,
            "attribute_name": "Commodity Base Rate",
            "pricing_type_ref_id": 118,
            "location_ref_id": _LOC_IDS[0],
            "from_date": "2026-06-02T00:00:00Z",
            "to_date": "2099-12-31T18:30:00Z",
            "details": [],
            "children": [{
                "stepper_name": "Define Item Rate Commision Details",
                "is_stepper": True,
                "details": [{"item_ref_id": _ITEM_IDS[0], "uom": 2, "minimum_range": 1000.0, "maximum_range": 5000.0, "details": []}],
                "children": [],
            }],
        },
    },
    {
        "id": 2,
        "location_ref_id": _LOC_IDS[1],
        "pricing_type_ref_id": 118,
        "from_date": "2026-06-02T00:00:00Z",
        "to_date": "2099-12-31T18:30:00Z",
        "_existing_item_ids": {_ITEM_IDS[0]},
        "_detail": {
            "id": 2,
            "attribute_name": "Commodity Base Rate",
            "pricing_type_ref_id": 118,
            "location_ref_id": _LOC_IDS[1],
            "from_date": "2026-06-02T00:00:00Z",
            "to_date": "2099-12-31T18:30:00Z",
            "details": [],
            "children": [{
                "stepper_name": "Define Item Rate Commision Details",
                "is_stepper": True,
                "details": [{"item_ref_id": _ITEM_IDS[0], "uom": 2, "minimum_range": 1000.0, "maximum_range": 5000.0, "details": []}],
                "children": [],
            }],
        },
    },
]


@pytest.mark.api
class TestCBRBatchGeneration:
    """Verify batch payload generation for Commodity Base Rate."""

    def test_batch_creates_for_all_locations(self):
        """With no existing entries, generates one CREATE payload per location."""
        payloads = generate_batch_payloads(count=100, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=[])
        assert len(payloads) == len(LOCATION_ID_MAP)

    def test_batch_updates_existing_and_creates_new(self):
        """With 2 existing locations, updates those + creates for remaining locations."""
        total_locs = len(LOCATION_ID_MAP)
        payloads = generate_batch_payloads(count=100, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=_MOCK_EXISTING)
        assert len(payloads) == total_locs  # all locations covered

    def test_batch_all_have_attribute_name(self):
        """Every payload must have attribute_name='Commodity Base Rate'."""
        payloads = generate_batch_payloads(count=5, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=[])
        for p in payloads:
            assert p["attribute_name"] == "Commodity Base Rate"

    def test_batch_all_have_detail_rows(self):
        """Every payload must have all items in the detail grid."""
        payloads = generate_batch_payloads(count=5, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=[])
        for p in payloads:
            assert "children" in p
            rows = p["children"][0]["details"]
            assert len(rows) == len(ITEM_ID_MAP)

    def test_batch_update_has_entry_id(self):
        """Update payloads (existing locations) must have a non-empty id."""
        payloads = generate_batch_payloads(count=100, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=_MOCK_EXISTING)
        existing_loc_ids = {int(list(LOCATION_ID_MAP.values())[0]), int(list(LOCATION_ID_MAP.values())[1])}
        for p in payloads:
            if p.get("location_ref_id") in existing_loc_ids:
                assert p["id"] not in ("", None, 0)

    def test_batch_no_status_field(self):
        """No payload in batch should have a status field."""
        payloads = generate_batch_payloads(count=5, dropdown_ids=_MOCK_DROPDOWN_IDS,
                                           existing_entries=[])
        for p in payloads:
            assert "status" not in p
