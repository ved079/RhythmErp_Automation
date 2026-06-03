"""
test_bank_schema.py — Verify Bank code matches live ERP schema.
No browser needed. Pure in-memory validation.
"""

import pytest
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.bank.data.bank_data import (
    FIELD_VALIDATION_RULES,
    STATUS_OPTIONS,
    ACCOUNT_TYPE_IDS,
    ACCOUNT_REF_IDS,
    ACCOUNT_TYPE_NAMES,
    ACCOUNT_REF_NAMES,
    DEFAULT_BANK_FK_IDS,
)


@pytest.mark.schema
class TestBankSchema:
    """Verify the Bank screen schema matches our code expectations."""

    # ── Field count and presence ──

    def test_field_validation_rules_has_14_fields(self):
        """Bank should have exactly 14 fields in FIELD_VALIDATION_RULES."""
        assert len(FIELD_VALIDATION_RULES) == 14

    def test_field_validation_rules_has_text_fields(self):
        """FIELD_VALIDATION_RULES must include all 10 text/character fields."""
        text_fields = {
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        }
        assert text_fields.issubset(set(FIELD_VALIDATION_RULES.keys()))

    def test_field_validation_rules_has_dropdown_fields(self):
        """FIELD_VALIDATION_RULES must include both FK dropdown fields."""
        assert "account_type" in FIELD_VALIDATION_RULES
        assert "account_ref_id" in FIELD_VALIDATION_RULES

    def test_field_validation_rules_has_toggle_fields(self):
        """FIELD_VALIDATION_RULES must include both toggle fields."""
        assert "is_default_bank" in FIELD_VALIDATION_RULES
        assert "status" in FIELD_VALIDATION_RULES

    # ── Required fields ──

    def test_required_fields_marked_correctly(self):
        """Required fields should be marked as required=True."""
        required_fields = {
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "ifsc_code", "cash_credit_limit",
            "bank_address", "account_type", "account_ref_id",
        }
        for field in required_fields:
            assert FIELD_VALIDATION_RULES[field]["required"] is True, \
                f"{field} should be required"

    def test_optional_fields_marked_correctly(self):
        """Optional fields should be marked as required=False."""
        optional_fields = {"swift_number", "iban_number", "is_default_bank", "status"}
        for field in optional_fields:
            assert FIELD_VALIDATION_RULES[field]["required"] is False, \
                f"{field} should NOT be required"

    # ── Max length checks ──

    def test_text_fields_max_length_is_255(self):
        """All text/character fields should have max_length of 255."""
        text_fields = [
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        ]
        for field in text_fields:
            assert FIELD_VALIDATION_RULES[field]["max_length"] == 255, \
                f"{field} max_length should be 255"

    # ── Field types ──

    def test_text_fields_are_character_type(self):
        """Text fields should be type='character'."""
        text_fields = [
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        ]
        for field in text_fields:
            assert FIELD_VALIDATION_RULES[field]["type"] == "character", \
                f"{field} type should be 'character'"

    def test_dropdown_fields_are_dropdown_type(self):
        """FK dropdown fields should be type='dropdown'."""
        assert FIELD_VALIDATION_RULES["account_type"]["type"] == "dropdown"
        assert FIELD_VALIDATION_RULES["account_ref_id"]["type"] == "dropdown"

    def test_toggle_fields_are_toggle_type(self):
        """Toggle fields should be type='toggle'."""
        assert FIELD_VALIDATION_RULES["is_default_bank"]["type"] == "toggle"
        assert FIELD_VALIDATION_RULES["status"]["type"] == "toggle"

    # ── FK options counts ──

    def test_account_type_has_2_options(self):
        """Account Type should have 2 options (Current, Saving)."""
        assert FIELD_VALIDATION_RULES["account_type"]["fk_options_count"] == 2

    def test_account_ref_id_options_count(self):
        """account_ref_id fk_options_count should match ACCOUNT_REF_IDS length."""
        assert FIELD_VALIDATION_RULES["account_ref_id"]["fk_options_count"] == len(ACCOUNT_REF_IDS)

    # ── Toggle defaults ──

    def test_is_default_bank_default_is_false(self):
        """is_default_bank default should be False."""
        assert FIELD_VALIDATION_RULES["is_default_bank"]["default"] is False

    def test_status_default_is_true(self):
        """status default should be True (Active)."""
        assert FIELD_VALIDATION_RULES["status"]["default"] is True

    # ── Status options ──

    def test_status_options_has_2_entries(self):
        """STATUS_OPTIONS should have 2 entries: Active and Inactive."""
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        """Active status should map to True."""
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        """Inactive status should map to False."""
        assert STATUS_OPTIONS["Inactive"] is False

    # ── FK ID pools ──

    def test_account_type_ids_has_current_and_saving(self):
        """ACCOUNT_TYPE_IDS must have Current and Saving."""
        assert "Current" in ACCOUNT_TYPE_IDS
        assert "Saving" in ACCOUNT_TYPE_IDS

    def test_account_type_ids_values_are_integers(self):
        """ACCOUNT_TYPE_IDS values should be integers."""
        for name, uid in ACCOUNT_TYPE_IDS.items():
            assert isinstance(uid, int), f"ACCOUNT_TYPE_IDS['{name}'] = {uid} is not int"

    def test_account_ref_ids_has_at_least_5_entries(self):
        """ACCOUNT_REF_IDS should have at least 5 bank-related options."""
        assert len(ACCOUNT_REF_IDS) >= 5

    def test_account_ref_ids_values_are_integers(self):
        """ACCOUNT_REF_IDS values should be integers."""
        for name, uid in ACCOUNT_REF_IDS.items():
            assert isinstance(uid, int), f"ACCOUNT_REF_IDS['{name}'] = {uid} is not int"

    # ── Default FK IDs structure ──

    def test_default_fk_ids_has_account_type(self):
        """DEFAULT_BANK_FK_IDS must have account_type pool."""
        assert "account_type" in DEFAULT_BANK_FK_IDS

    def test_default_fk_ids_has_account_ref_id(self):
        """DEFAULT_BANK_FK_IDS must have account_ref_id pool."""
        assert "account_ref_id" in DEFAULT_BANK_FK_IDS

    def test_default_fk_ids_pools_match_source(self):
        """DEFAULT_BANK_FK_IDS pools should match ACCOUNT_TYPE_IDS and ACCOUNT_REF_IDS."""
        assert DEFAULT_BANK_FK_IDS["account_type"] == ACCOUNT_TYPE_IDS
        assert DEFAULT_BANK_FK_IDS["account_ref_id"] == ACCOUNT_REF_IDS

    # ── Name mappings ──

    def test_account_type_names_matches_ids(self):
        """ACCOUNT_TYPE_NAMES should match ACCOUNT_TYPE_IDS."""
        assert ACCOUNT_TYPE_NAMES == ACCOUNT_TYPE_IDS

    def test_account_ref_names_matches_ids(self):
        """ACCOUNT_REF_NAMES should match ACCOUNT_REF_IDS."""
        assert ACCOUNT_REF_NAMES == ACCOUNT_REF_IDS

    # ── FK pool lengths match rules ──

    def test_fk_pool_lengths_match_rules(self):
        """FK pool lengths should match the fk_options_count in FIELD_VALIDATION_RULES."""
        for field_name, rules in FIELD_VALIDATION_RULES.items():
            if rules["type"] == "dropdown" and "fk_options_count" in rules:
                if field_name in DEFAULT_BANK_FK_IDS:
                    actual = len(DEFAULT_BANK_FK_IDS[field_name])
                    expected = rules["fk_options_count"]
                    assert actual == expected, \
                        f"{field_name}: pool has {actual} options, rules say {expected}"

    def test_account_type_ids_no_duplicate_values(self):
        """ACCOUNT_TYPE_IDS should not have duplicate ID values."""
        values = list(ACCOUNT_TYPE_IDS.values())
        assert len(values) == len(set(values))

    def test_account_ref_ids_no_duplicate_values(self):
        """ACCOUNT_REF_IDS should not have duplicate ID values."""
        values = list(ACCOUNT_REF_IDS.values())
        assert len(values) == len(set(values))
