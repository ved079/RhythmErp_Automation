"""test_vehicle_master_payload.py — Fast API payload structure tests for Vehicle Master."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    build_vehicle_master_api_payload, generate_vehicle_master_api_payloads,
    generate_batch_payloads,
)

MOCK_FK_IDS = {
    "vehicle_type_id": {"Truck": 1, "Trailer": 2, "Tanker": 3, "Mini Truck": 4, "Pickup": 5},
    "fuel_type_ref_id": {"Diesel": 1, "Petrol": 2, "CNG": 3, "Electric": 4, "LPG": 5},
}

@pytest.mark.api
class TestVehicleMasterAPIPayload:
    def test_payload_has_required_keys(self):
        p = generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        for k in ["id", "attribute_name", "name", "vehicle_price", "vehicle_type_id", "fuel_type_ref_id", "description"]:
            assert k in p

    def test_payload_is_flat_no_children(self):
        p = generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        assert "children" not in p and "details" not in p

    def test_payload_attribute_name(self):
        assert generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["attribute_name"] == "Vehicle Master"

    def test_payload_id_is_empty(self):
        assert generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["id"] == ""

    def test_payload_name_is_string(self):
        assert isinstance(generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["name"], str)

    def test_payload_price_is_numeric(self):
        p = generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]
        assert isinstance(p["vehicle_price"], (int, float))

    def test_payload_vehicle_type_is_integer(self):
        assert isinstance(generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["vehicle_type_id"], int)

    def test_payload_fuel_type_is_integer(self):
        assert isinstance(generate_vehicle_master_api_payloads(count=1, fk_ids=MOCK_FK_IDS)[0]["fuel_type_ref_id"], int)

    def test_payload_vehicle_type_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["vehicle_type_id"].values())
        for p in generate_vehicle_master_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["vehicle_type_id"] in valid

    def test_payload_fuel_type_in_valid_pool(self):
        valid = set(MOCK_FK_IDS["fuel_type_ref_id"].values())
        for p in generate_vehicle_master_api_payloads(count=5, fk_ids=MOCK_FK_IDS):
            assert p["fuel_type_ref_id"] in valid

    def test_build_with_explicit_values(self):
        p = build_vehicle_master_api_payload("Test Truck", 1000000, 1, 1, "Test desc")
        assert p["name"] == "Test Truck"
        assert p["vehicle_price"] == 1000000
        assert p["vehicle_type_id"] == 1
        assert p["fuel_type_ref_id"] == 1

    def test_build_with_empty_description(self):
        p = build_vehicle_master_api_payload("Truck", 500000, 1, 1)
        assert p["description"] == ""

    def test_generate_raises_without_fk_ids(self):
        with pytest.raises(ValueError, match="fk_ids is required"):
            generate_vehicle_master_api_payloads(count=1, fk_ids=None)

@pytest.mark.api
class TestVehicleMasterBatchGeneration:
    def test_batch_count(self):
        assert len(generate_batch_payloads(count=5, dropdown_ids=MOCK_FK_IDS)) == 5

    def test_batch_default_20(self):
        assert len(generate_batch_payloads(count=20, dropdown_ids=MOCK_FK_IDS)) == 20

    def test_batch_all_attribute_name(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["attribute_name"] == "Vehicle Master"

    def test_batch_all_fk_valid(self):
        vt = set(MOCK_FK_IDS["vehicle_type_id"].values())
        vf = set(MOCK_FK_IDS["fuel_type_ref_id"].values())
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert p["vehicle_type_id"] in vt
            assert p["fuel_type_ref_id"] in vf

    def test_batch_all_flat(self):
        for p in generate_batch_payloads(count=10, dropdown_ids=MOCK_FK_IDS):
            assert "children" not in p and "details" not in p

    def test_batch_names_match_realistic_data(self):
        payloads = generate_batch_payloads(count=5, dropdown_ids=MOCK_FK_IDS)
        for p in payloads:
            assert isinstance(p["name"], str) and len(p["name"]) > 0

    def test_batch_raises_without_dropdown_ids(self):
        with pytest.raises(ValueError, match="dropdown_ids is required"):
            generate_batch_payloads(count=5)
