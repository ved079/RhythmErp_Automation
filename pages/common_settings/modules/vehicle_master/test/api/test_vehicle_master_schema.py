"""test_vehicle_master_schema.py — Verify Vehicle Master code matches live ERP schema."""
import pytest, sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    FIELD_VALIDATION_RULES, VEHICLE_TYPE_IDS, FUEL_TYPE_IDS,
    VEHICLE_TYPE_NAMES, FUEL_TYPE_NAMES, DEFAULT_VEHICLE_MASTER_FK_IDS,
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

    def test_vehicle_type_has_5_options(self):
        assert FIELD_VALIDATION_RULES["vehicle_type_id"]["fk_options_count"] == 5

    def test_fuel_type_has_5_options(self):
        assert FIELD_VALIDATION_RULES["fuel_type_ref_id"]["fk_options_count"] == 5

    def test_vehicle_type_names_matches(self):
        assert VEHICLE_TYPE_NAMES == VEHICLE_TYPE_IDS

    def test_fuel_type_names_matches(self):
        assert FUEL_TYPE_NAMES == FUEL_TYPE_IDS

    def test_default_fk_ids_has_both(self):
        assert "vehicle_type_id" in DEFAULT_VEHICLE_MASTER_FK_IDS
        assert "fuel_type_ref_id" in DEFAULT_VEHICLE_MASTER_FK_IDS

    def test_default_fk_ids_pools_match(self):
        assert DEFAULT_VEHICLE_MASTER_FK_IDS["vehicle_type_id"] == VEHICLE_TYPE_IDS
        assert DEFAULT_VEHICLE_MASTER_FK_IDS["fuel_type_ref_id"] == FUEL_TYPE_IDS

    def test_fk_pool_lengths_match_rules(self):
        for fn, r in FIELD_VALIDATION_RULES.items():
            if r["type"] == "dropdown" and "fk_options_count" in r:
                if fn in DEFAULT_VEHICLE_MASTER_FK_IDS:
                    assert len(DEFAULT_VEHICLE_MASTER_FK_IDS[fn]) == r["fk_options_count"]

    def test_vehicle_type_ids_no_dup_values(self):
        v = list(VEHICLE_TYPE_IDS.values())
        assert len(v) == len(set(v))

    def test_fuel_type_ids_no_dup_values(self):
        v = list(FUEL_TYPE_IDS.values())
        assert len(v) == len(set(v))

    def test_name_max_length_255(self):
        assert FIELD_VALIDATION_RULES["name"]["max_length"] == 255

    def test_price_max_length_255(self):
        assert FIELD_VALIDATION_RULES["vehicle_price"]["max_length"] == 255
