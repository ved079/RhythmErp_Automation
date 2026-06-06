"""
test_directors_schema.py
------------------------
Schema and structure verification tests for the Directors screen.

These tests fetch the LIVE schema from the ERP API and verify:
  - Screen metadata (ID, attribute_name, master_table)
  - All 15 top-level fields exist with correct properties
  - KYC Details stepper child structure
  - Dropdown/FK option counts match our data pools
  - Field types, required flags, and max_lengths
  - Auto-patch fields for party_ref_id

Run with:
  ERP_TOKEN=eyJ... pytest pages/registration/modules/directors/test/api/test_directors_schema.py -v
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.registration.modules.directors.data.directors_data import (
    PREFIX_IDS,
    PREFIX_NAMES,
    KYC_DOC_IDS,
    KYC_DOC_NAMES,
    DESIGNATION_IDS,
    DESIGNATION_NAMES,
    QUALIFICATION_IDS,
    QUALIFICATION_NAMES,
    PARTY_REF_IDS,
    FIELD_VALIDATION_RULES,
)


# ──────────────────────────────────────────────
# Schema fetch fixture
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def screen_schema(api_client):
    """Fetch the Directors screen schema once for all tests."""
    if api_client is None:
        pytest.skip("No API client available")
    schema = api_client.get_screen_schema("Directors")
    if schema is None:
        pytest.skip("Could not fetch Directors schema")
    return schema


@pytest.fixture(scope="module")
def field_map(screen_schema):
    """Create a dict of field_key → field definition for easy lookup."""
    field_set = screen_schema.get("screendefinition_set", [])
    result = {}
    for field in field_set:
        fkey = field.get("field_key")
        if fkey:
            result[fkey] = field
        # Also flatten children (stepper fields)
        for child in field.get("children", []):
            ckey = child.get("field_key")
            if ckey:
                result[ckey] = child
    return result


# ══════════════════════════════════════════════════════════════════════
# 1. SCREEN METADATA TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsScreenMetadata:
    """Verify screen-level metadata from the schema."""

    def test_screen_id_is_98(self, screen_schema):
        """Directors screen ID must be 98."""
        assert screen_schema.get("id") == 98

    def test_attribute_name_is_directors(self, screen_schema):
        """attribute_name must be 'Directors'."""
        assert screen_schema.get("attribute_name") == "Directors"

    def test_master_table_is_party_master(self, screen_schema):
        """master_table_name must be 'party_master'."""
        assert screen_schema.get("master_table_name") == "party_master"

    def test_is_bulk_upload_true(self, screen_schema):
        """Directors should support bulk upload."""
        assert screen_schema.get("is_bulk_upload") is True

    def test_is_workflow_applicable_false(self, screen_schema):
        """Directors should not have workflow."""
        assert screen_schema.get("is_workflow_applicable") is False

    def test_is_effective_dated_false(self, screen_schema):
        """Directors should not be effective dated."""
        assert screen_schema.get("is_effective_dated") is False

    def test_is_history_applicable_false(self, screen_schema):
        """Directors should not be history applicable."""
        assert screen_schema.get("is_history_applicable") is False

    def test_has_screendefinition_set(self, screen_schema):
        """Schema must contain screendefinition_set."""
        assert "screendefinition_set" in screen_schema
        assert len(screen_schema["screendefinition_set"]) > 0


# ══════════════════════════════════════════════════════════════════════
# 2. TOP-LEVEL FIELD EXISTENCE TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsFieldExistence:
    """Verify all 15 top-level fields exist in the schema."""

    @pytest.mark.parametrize("field_key", [
        "party_ref_id", "prefix_ref_id", "name", "designation",
        "pan_no", "residential_address", "mobile_no",
        "date_of_appointment", "date_of_cessation",
        "no_class_shares_held", "details_of_other_directorships",
        "percentage_of_shares", "age", "qualification_ref_id",
        "experience_in_years",
    ])
    def test_top_level_field_exists(self, field_map, field_key):
        """Each top-level field must exist in the schema."""
        assert field_key in field_map, f"Field '{field_key}' not found in schema"

    def test_total_top_level_field_count(self, screen_schema):
        """Schema should have 15 top-level fields + 1 KYC stepper = 16 definitions."""
        field_set = screen_schema.get("screendefinition_set", [])
        # Count non-stepper fields
        top_level = [f for f in field_set if not f.get("is_grid", False)]
        # The KYC stepper counts as one definition
        assert len(top_level) == 15 or len(field_set) == 16


# ══════════════════════════════════════════════════════════════════════
# 3. REQUIRED FIELD TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsRequiredFlags:
    """Verify is_required flags match our data definitions."""

    @pytest.mark.parametrize("field_key", [
        "prefix_ref_id", "name", "designation", "pan_no",
        "residential_address", "mobile_no", "date_of_appointment",
        "no_class_shares_held", "details_of_other_directorships",
        "percentage_of_shares", "age", "qualification_ref_id",
        "experience_in_years",
    ])
    def test_required_field_is_marked_required(self, field_map, field_key):
        """Required fields must have is_required=True in schema."""
        field = field_map.get(field_key)
        assert field is not None, f"Field '{field_key}' not found"
        assert field.get("is_required") is True, (
            f"Field '{field_key}' should be required"
        )

    @pytest.mark.parametrize("field_key", [
        "party_ref_id", "date_of_cessation",
    ])
    def test_optional_field_is_not_required(self, field_map, field_key):
        """Optional fields must have is_required=False in schema."""
        field = field_map.get(field_key)
        assert field is not None, f"Field '{field_key}' not found"
        assert field.get("is_required") is False, (
            f"Field '{field_key}' should be optional"
        )


# ══════════════════════════════════════════════════════════════════════
# 4. DROPDOWN / FK OPTION COUNT TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsDropdownOptions:
    """Verify dropdown option counts match our data pools."""

    def test_party_ref_has_357_options(self, field_map):
        """Party Reference dropdown should have 357 options."""
        field = field_map.get("party_ref_id")
        assert field is not None
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) == 357, (
            f"Expected 357 party_ref options, got {len(dropdown)}"
        )

    def test_prefix_has_3_options(self, field_map):
        """Prefix dropdown should have 3 options."""
        field = field_map.get("prefix_ref_id")
        assert field is not None
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) == 3, (
            f"Expected 3 prefix options, got {len(dropdown)}"
        )

    def test_designation_has_56_options(self, field_map):
        """Designation dropdown should have 56 options."""
        field = field_map.get("designation")
        assert field is not None
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) == 56, (
            f"Expected 56 designation options, got {len(dropdown)}"
        )

    def test_qualification_has_6_options(self, field_map):
        """Qualification dropdown should have 6 options."""
        field = field_map.get("qualification_ref_id")
        assert field is not None
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) == 6, (
            f"Expected 6 qualification options, got {len(dropdown)}"
        )

    def test_kyc_doc_has_2_options(self, field_map):
        """KYC Document dropdown should have 2 options."""
        field = field_map.get("kyc_doc_id")
        assert field is not None
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) == 2, (
            f"Expected 2 KYC doc options, got {len(dropdown)}"
        )

    def test_party_ref_dropdown_ids_match_pool(self, field_map):
        """All IDs in our PARTY_REF_IDS should exist in the schema dropdown."""
        field = field_map.get("party_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        dropdown_ids = {opt.get("id") for opt in dropdown}
        for pid in PARTY_REF_IDS:
            assert pid in dropdown_ids, (
                f"Party ref ID {pid} not found in schema dropdown"
            )

    def test_prefix_dropdown_ids_match_pool(self, field_map):
        """All IDs in our PREFIX_IDS should exist in the schema dropdown."""
        field = field_map.get("prefix_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        dropdown_ids = {opt.get("id") for opt in dropdown}
        for pid in PREFIX_IDS:
            assert pid in dropdown_ids, (
                f"Prefix ID {pid} not found in schema dropdown"
            )

    def test_designation_dropdown_ids_match_pool(self, field_map):
        """All IDs in our DESIGNATION_IDS should exist in the schema dropdown."""
        field = field_map.get("designation")
        dropdown = field.get("filter_dropdown_raw_query", [])
        dropdown_ids = {opt.get("id") for opt in dropdown}
        for did in DESIGNATION_IDS:
            assert did in dropdown_ids, (
                f"Designation ID {did} not found in schema dropdown"
            )

    def test_qualification_dropdown_ids_match_pool(self, field_map):
        """All IDs in our QUALIFICATION_IDS should exist in the schema dropdown."""
        field = field_map.get("qualification_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        dropdown_ids = {opt.get("id") for opt in dropdown}
        for qid in QUALIFICATION_IDS:
            assert qid in dropdown_ids, (
                f"Qualification ID {qid} not found in schema dropdown"
            )

    def test_kyc_doc_dropdown_ids_match_pool(self, field_map):
        """All IDs in our KYC_DOC_IDS should exist in the schema dropdown."""
        field = field_map.get("kyc_doc_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        dropdown_ids = {opt.get("id") for opt in dropdown}
        for kid in KYC_DOC_IDS:
            assert kid in dropdown_ids, (
                f"KYC doc ID {kid} not found in schema dropdown"
            )


# ══════════════════════════════════════════════════════════════════════
# 5. DROPDOWN NAME VERIFICATION TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsDropdownNames:
    """Verify dropdown option names/keys match our data."""

    def test_prefix_names_match(self, field_map):
        """Prefix option names should match our PREFIX_NAMES."""
        field = field_map.get("prefix_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        for opt in dropdown:
            opt_id = opt.get("id")
            opt_key = opt.get("key")
            if opt_id in PREFIX_NAMES:
                assert opt_key == PREFIX_NAMES[opt_id], (
                    f"Prefix ID {opt_id}: expected '{PREFIX_NAMES[opt_id]}', got '{opt_key}'"
                )

    def test_qualification_names_match(self, field_map):
        """Qualification option names should match our QUALIFICATION_NAMES."""
        field = field_map.get("qualification_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        for opt in dropdown:
            opt_id = opt.get("id")
            opt_key = opt.get("key")
            if opt_id in QUALIFICATION_NAMES:
                assert opt_key == QUALIFICATION_NAMES[opt_id], (
                    f"Qual ID {opt_id}: expected '{QUALIFICATION_NAMES[opt_id]}', got '{opt_key}'"
                )

    def test_kyc_doc_names_match(self, field_map):
        """KYC doc option names should match our KYC_DOC_NAMES."""
        field = field_map.get("kyc_doc_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        for opt in dropdown:
            opt_id = opt.get("id")
            opt_key = opt.get("key")
            if opt_id in KYC_DOC_NAMES:
                assert opt_key == KYC_DOC_NAMES[opt_id], (
                    f"KYC doc ID {opt_id}: expected '{KYC_DOC_NAMES[opt_id]}', got '{opt_key}'"
                )


# ══════════════════════════════════════════════════════════════════════
# 6. ON_CHANGE EVENT TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsOnChangeEvents:
    """Verify is_onchange_event flags on fields that trigger auto-patches."""

    def test_party_ref_is_onchange(self, field_map):
        """party_ref_id should trigger auto-patch (is_onchange_event=True)."""
        field = field_map.get("party_ref_id")
        assert field is not None
        assert field.get("is_onchange_event") is True, (
            "party_ref_id should have is_onchange_event=True"
        )

    def test_name_is_not_onchange(self, field_map):
        """name should not trigger auto-patch."""
        field = field_map.get("name")
        assert field is not None
        assert field.get("is_onchange_event") is False

    def test_designation_is_not_onchange(self, field_map):
        """designation should not trigger auto-patch."""
        field = field_map.get("designation")
        assert field is not None
        assert field.get("is_onchange_event") is False

    def test_pan_no_is_not_onchange(self, field_map):
        """pan_no should not trigger auto-patch."""
        field = field_map.get("pan_no")
        assert field is not None
        assert field.get("is_onchange_event") is False

    def test_qualification_is_not_onchange(self, field_map):
        """qualification_ref_id should not trigger auto-patch."""
        field = field_map.get("qualification_ref_id")
        assert field is not None
        assert field.get("is_onchange_event") is False


# ══════════════════════════════════════════════════════════════════════
# 7. KYC STEPPER STRUCTURE TESTS
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsKYCStepperSchema:
    """Verify KYC Details stepper structure in the schema."""

    def test_kyc_stepper_exists(self, screen_schema):
        """Schema must have a KYC Details stepper child."""
        field_set = screen_schema.get("screendefinition_set", [])
        kyc_found = False
        for field in field_set:
            if field.get("is_grid", False):
                children = field.get("children", [])
                if children:
                    kyc_found = True
                    break
        assert kyc_found, "No KYC stepper child found in schema"

    def test_kyc_has_3_child_fields(self, screen_schema):
        """KYC Details stepper must have 3 child fields."""
        field_set = screen_schema.get("screendefinition_set", [])
        for field in field_set:
            if field.get("is_grid", False):
                children = field.get("children", [])
                assert len(children) == 3, (
                    f"Expected 3 KYC child fields, got {len(children)}"
                )
                break

    def test_kyc_child_fields_exist(self, field_map):
        """All 3 KYC child fields must exist in the field map."""
        assert "kyc_doc_id" in field_map
        assert "kyc_account_no" in field_map
        assert "attachment_path" in field_map

    def test_kyc_doc_id_is_required(self, field_map):
        """KYC Document must be required."""
        field = field_map.get("kyc_doc_id")
        assert field is not None
        assert field.get("is_required") is True

    def test_kyc_account_no_is_required(self, field_map):
        """KYC Number must be required."""
        field = field_map.get("kyc_account_no")
        assert field is not None
        assert field.get("is_required") is True

    def test_attachment_path_is_optional(self, field_map):
        """KYC Attachment must be optional."""
        field = field_map.get("attachment_path")
        assert field is not None
        assert field.get("is_required") is False

    def test_kyc_doc_has_dropdown(self, field_map):
        """KYC Document must be a dropdown with options."""
        field = field_map.get("kyc_doc_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(dropdown) > 0, "KYC doc dropdown should have options"


# ══════════════════════════════════════════════════════════════════════
# 8. FIELD COUNT INTEGRITY
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.schema
class TestDirectorsFieldCountIntegrity:
    """Verify total field counts are consistent."""

    def test_total_field_definitions(self, screen_schema):
        """Schema should have 16 definitions (15 top-level + 1 KYC stepper)."""
        field_set = screen_schema.get("screendefinition_set", [])
        assert len(field_set) == 16, (
            f"Expected 16 field definitions, got {len(field_set)}"
        )

    def test_total_flattened_fields(self, field_map):
        """Flattened field map should have 19 entries (15 top-level + KYC stepper key + 3 KYC child fields)."""
        assert len(field_map) == 19, (
            f"Expected 19 flattened fields, got {len(field_map)}"
        )

    def test_validation_rules_covers_all_fields(self):
        """FIELD_VALIDATION_RULES should cover all 18 fields."""
        assert len(FIELD_VALIDATION_RULES) == 18, (
            f"Expected 18 validation rules, got {len(FIELD_VALIDATION_RULES)}"
        )

    def test_designation_ids_count_matches_schema(self, field_map):
        """DESIGNATION_IDS count should match the schema dropdown count."""
        field = field_map.get("designation")
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(DESIGNATION_IDS) == len(dropdown), (
            f"DESIGNATION_IDS has {len(DESIGNATION_IDS)}, schema has {len(dropdown)}"
        )

    def test_qualification_ids_count_matches_schema(self, field_map):
        """QUALIFICATION_IDS count should match the schema dropdown count."""
        field = field_map.get("qualification_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(QUALIFICATION_IDS) == len(dropdown), (
            f"QUALIFICATION_IDS has {len(QUALIFICATION_IDS)}, schema has {len(dropdown)}"
        )

    def test_party_ref_ids_count_matches_schema(self, field_map):
        """PARTY_REF_IDS count should match the schema dropdown count."""
        field = field_map.get("party_ref_id")
        dropdown = field.get("filter_dropdown_raw_query", [])
        assert len(PARTY_REF_IDS) == len(dropdown), (
            f"PARTY_REF_IDS has {len(PARTY_REF_IDS)}, schema has {len(dropdown)}"
        )
