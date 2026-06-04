"""
test_employee_schema.py — Verify Employee code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.employee.data.employee_data import (
    FIELD_VALIDATION_RULES,
    DESIGNATION_IDS,
    DESIGNATION_NAMES,
    DESIGNATION_OPTIONS_COUNT,
    DEFAULT_EMPLOYEE_FK_IDS,
)


@pytest.mark.schema
class TestEmployeeSchema:
    """Verify the Employee screen schema matches our code expectations."""

    def test_field_validation_rules_complete(self):
        """FIELD_VALIDATION_RULES should cover all 6 Employee fields."""
        expected_fields = {"name", "email_id", "mobile_no", "designation", "department", "status"}
        actual_fields = set(FIELD_VALIDATION_RULES.keys())
        assert expected_fields == actual_fields, f"Missing: {expected_fields - actual_fields}, Extra: {actual_fields - expected_fields}"

    def test_name_pattern_matches_schema(self):
        """Name pattern should match ^[A-Za-z ]+$."""
        assert FIELD_VALIDATION_RULES["name"]["pattern"] == r"^[A-Za-z ]+$"

    def test_phone_pattern_matches_schema(self):
        """Phone pattern should match ^[6-9]\\d{9}$."""
        assert FIELD_VALIDATION_RULES["mobile_no"]["pattern"] == r"^[6-9]\d{9}$"

    def test_designation_has_56_options(self):
        """Designation dropdown should have 56 options."""
        assert FIELD_VALIDATION_RULES["designation"]["fk_options_count"] == 56

    def test_department_has_0_options(self):
        """Department dropdown should have 0 options."""
        assert FIELD_VALIDATION_RULES["department"]["fk_options_count"] == 0

    def test_status_is_required(self):
        """Only status should be required; all others are optional."""
        assert FIELD_VALIDATION_RULES["status"]["required"] is True
        # Verify all other fields are NOT required
        for field_key, rule in FIELD_VALIDATION_RULES.items():
            if field_key != "status":
                assert rule.get("required") is False, f"{field_key} should not be required"

    def test_default_fk_ids_valid(self):
        """DEFAULT_EMPLOYEE_FK_IDS values should be in valid pools."""
        designation = DEFAULT_EMPLOYEE_FK_IDS["designation"]
        assert designation in DESIGNATION_IDS, f"Default designation {designation} not in valid pool"
        assert DEFAULT_EMPLOYEE_FK_IDS["department"] is None
        assert DEFAULT_EMPLOYEE_FK_IDS["party_ref_id"] is None

    def test_designation_names_map_complete(self):
        """DESIGNATION_NAMES should map every ID in DESIGNATION_IDS."""
        for did in DESIGNATION_IDS:
            assert did in DESIGNATION_NAMES, f"Missing name for designation {did}"

    def test_fk_pool_lengths_match_rules(self):
        """DESIGNATION_IDS length should match FIELD_VALIDATION_RULES count."""
        assert len(DESIGNATION_IDS) == FIELD_VALIDATION_RULES["designation"]["fk_options_count"]
        # Also verify the DESIGNATION_OPTIONS_COUNT constant
        assert DESIGNATION_OPTIONS_COUNT == 56
        assert len(DESIGNATION_IDS) == DESIGNATION_OPTIONS_COUNT
