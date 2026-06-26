"""test_vehicle_master_schema.py — Verify Vehicle Master code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    FIELD_VALIDATION_RULES, get_field_validation_rules, get_fk_screen_mapping,
    VEHICLE_NAME_MAX_LENGTH,
)

@pytest.mark.schema
class TestVehicleMasterSchema:
    def test_has_5_fields(self):
        assert len(FIELD_VALIDATION_RULES) == 5

    def test_has_all_fields(self):
        assert set(FIELD_VALIDATION_RULES.keys()) == {
            "name", "vehicle_price", "vehicle_type_id", "fuel_type_ref_id", "description"
        }

    def test_name_required(self):
        assert FIELD_VALIDATION_RULES["name"]["required"] is True

    def test_price_required(self):
        assert FIELD_VALIDATION_RULES["vehicle_price"]["required"] is True

    def test_vehicle_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["vehicle_type_id"]["type"] == "dropdown"

    def test_fuel_type_is_dropdown(self):
        assert FIELD_VALIDATION_RULES["fuel_type_ref_id"]["type"] == "dropdown"

    def test_description_is_optional(self):
        assert FIELD_VALIDATION_RULES["description"]["required"] is False

    def test_fk_options_count_placeholder(self):
        for fn in ("vehicle_type_id", "fuel_type_ref_id"):
            assert FIELD_VALIDATION_RULES[fn]["fk_options_count"] == 0

    def test_name_max_length_255(self):
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_price_max_length_255(self):
        assert FIELD_VALIDATION_RULES["vehicle_price"]["max_length"] == 255

    def test_get_field_validation_rules_is_callable(self):
        rules = get_field_validation_rules()
        assert rules["name"]["required"] is True

    def test_get_fk_screen_mapping_has_2_entries(self):
        mapping = get_fk_screen_mapping()
        assert len(mapping) == 2
        fields = set(mapping)
        assert fields == {"vehicle_type_id", "fuel_type_ref_id"}

    def test_fk_screen_mapping_returns_2_keys(self):
        m = get_fk_screen_mapping()
        assert set(m.keys()) == {"vehicle_type_id", "fuel_type_ref_id"}

    def test_generate_batch_payloads_accepts_standard_params(self):
        from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import generate_batch_payloads
        mock_ids = {
            "vehicle_type_id": {"Truck": 1, "Trailer": 2},
            "fuel_type_ref_id": {"Diesel": 1, "CNG": 3},
        }
        result = generate_batch_payloads(count=3, prefix=None, dropdown_ids=mock_ids, offset=0, existing_entries=None)
        assert len(result) == 3

    def test_vehicle_name_max_length_is_255(self):
        assert VEHICLE_NAME_MAX_LENGTH == 255
