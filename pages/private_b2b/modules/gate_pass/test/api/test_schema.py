import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.private_b2b.modules.gate_pass.api.endpoints import SCREEN_NAME


class TestSchema:
    @pytest.mark.schema
    def test_GP_SC01_field_count(self, erp_api):
        log.info("GP-SC01: Schema has expected number of fields")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        assert schema is not None, "Schema fetch failed"
        fields = schema.get("screendefinition_set", [])
        assert len(fields) >= 15, f"Expected 15+ fields, got {len(fields)}"

    @pytest.mark.schema
    def test_GP_SC02_required_fields(self, erp_api):
        log.info("GP-SC02: Required fields have is_required=True")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        assert schema is not None
        fields = schema.get("screendefinition_set", [])
        required_keys = [
            "supplier_ref_id", "item_type_ref_id", "parameter1",
            "parameter3", "parameter4", "distance", "driver_name", "in_time",
        ]
        field_map = {f.get("field_key"): f for f in fields}
        for key in required_keys:
            field = field_map.get(key)
            assert field is not None, f"Field '{key}' not found in schema"
            assert field.get("is_required") is True or str(field.get("is_required")).lower() == "true", (
                f"Field '{key}' should be required"
            )

    @pytest.mark.schema
    def test_GP_SC03_field_types(self, erp_api):
        log.info("GP-SC03: Field types match expectations")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        assert schema is not None
        fields = schema.get("screendefinition_set", [])
        field_map = {f.get("field_key"): f.get("field_type_val") for f in fields}
        assert field_map.get("distance") == "integer"
        assert field_map.get("driver_name") == "character"
        assert field_map.get("supplier_ref_id") == "dropdown"
        assert field_map.get("in_time") in ("time", "datetime")

    @pytest.mark.schema
    def test_GP_SC04_dropdown_options(self, erp_api):
        log.info("GP-SC04: Dropdown fields have valid options")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        assert schema is not None
        fields = schema.get("screendefinition_set", [])
        for key in ["item_type_ref_id", "parameter1", "parameter3", "parameter4"]:
            field = next((f for f in fields if f.get("field_key") == key), None)
            assert field is not None, f"Field '{key}' not found"
            options = field.get("filter_dropdown_raw_query") or []
            assert len(options) >= 1, f"Field '{key}' should have dropdown options"

    @pytest.mark.schema
    def test_GP_SC05_gate_pass_details_grid(self, erp_api):
        log.info("GP-SC05: gate_pass_details is a grid stepper")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        fields = schema.get("screendefinition_set", [])
        gp_field = next((f for f in fields if f.get("field_key") == "gate_pass_details"), None)
        assert gp_field is not None, "gate_pass_details field not found"
        assert gp_field.get("is_grid") is True or str(gp_field.get("is_grid")).lower() == "true"

    @pytest.mark.schema
    def test_GP_SC06_grid_structure(self, erp_api):
        log.info("GP-SC06: Grid field has expected structure")
        schema = erp_api.get_screen_schema(SCREEN_NAME)
        fields = schema.get("screendefinition_set", [])
        gp_field = next((f for f in fields if f.get("field_key") == "gate_pass_details"), None)
        assert gp_field is not None, "gate_pass_details field not found"
        assert gp_field.get("is_grid") is True or str(gp_field.get("is_grid")).lower() == "true", "gate_pass_details should be a grid field"
        assert gp_field.get("is_stepper_name") is True or str(gp_field.get("is_stepper_name")).lower() == "true", "gate_pass_details should be a stepper"
