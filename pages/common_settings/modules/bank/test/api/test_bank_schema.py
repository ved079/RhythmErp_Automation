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
    get_field_validation_rules,
    STATUS_OPTIONS,
    ACCOUNT_TYPE_IDS,
    ACCOUNT_REF_IDS,
)


@pytest.mark.schema
class TestBankSchema:
    """Verify the Bank screen schema matches our code expectations."""

    def _rules(self):
        return get_field_validation_rules()

    def test_field_validation_rules_has_14_fields(self):
        rules = self._rules()
        assert len(rules) == 14

    def test_field_validation_rules_has_text_fields(self):
        rules = self._rules()
        text_fields = {
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        }
        assert text_fields.issubset(set(rules.keys()))

    def test_field_validation_rules_has_dropdown_fields(self):
        rules = self._rules()
        assert "account_type" in rules
        assert "account_ref_id" in rules

    def test_field_validation_rules_has_toggle_fields(self):
        rules = self._rules()
        assert "is_default_bank" in rules
        assert "status" in rules

    def test_required_fields_marked_correctly(self):
        rules = self._rules()
        required_fields = {
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "ifsc_code", "cash_credit_limit",
            "bank_address", "account_type", "account_ref_id",
        }
        for field in required_fields:
            assert rules[field]["required"] is True, f"{field} should be required"

    def test_optional_fields_marked_correctly(self):
        rules = self._rules()
        optional_fields = {"swift_number", "iban_number", "is_default_bank", "status"}
        for field in optional_fields:
            assert rules[field]["required"] is False, f"{field} should NOT be required"

    def test_text_fields_max_length_is_255(self):
        rules = self._rules()
        text_fields = [
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        ]
        for field in text_fields:
            assert rules[field]["max_length"] == 255, f"{field} max_length should be 255"

    def test_text_fields_are_character_type(self):
        rules = self._rules()
        text_fields = [
            "bank_name", "bank_code", "branch_name", "branch_code",
            "account_number", "swift_number", "iban_number",
            "ifsc_code", "cash_credit_limit", "bank_address",
        ]
        for field in text_fields:
            assert rules[field]["type"] == "character", f"{field} type should be 'character'"

    def test_dropdown_fields_are_dropdown_type(self):
        rules = self._rules()
        assert rules["account_type"]["type"] == "dropdown"
        assert rules["account_ref_id"]["type"] == "dropdown"

    def test_toggle_fields_are_toggle_type(self):
        rules = self._rules()
        assert rules["is_default_bank"]["type"] == "toggle"
        assert rules["status"]["type"] == "toggle"

    def test_account_type_has_2_options_with_fk_ids(self):
        fk_ids = {"account_type": {"Current": 100, "Saving": 101}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["account_type"]["fk_options_count"] == 2

    def test_account_ref_id_options_count_with_fk_ids(self):
        fk_ids = {"account_type": {}, "account_ref_id": {"A": 1, "B": 2, "C": 3}}
        rules = get_field_validation_rules(fk_ids)
        assert rules["account_ref_id"]["fk_options_count"] == 3

    def test_is_default_bank_default_is_false(self):
        assert self._rules()["is_default_bank"]["default"] is False

    def test_status_default_is_true(self):
        assert self._rules()["status"]["default"] is True

    def test_status_options_has_2_entries(self):
        assert len(STATUS_OPTIONS) == 2

    def test_status_options_active_is_true(self):
        assert STATUS_OPTIONS["Active"] is True

    def test_status_options_inactive_is_false(self):
        assert STATUS_OPTIONS["Inactive"] is False

    def test_account_type_ids_has_current_and_saving(self):
        assert "Current" in ACCOUNT_TYPE_IDS
        assert "Saving" in ACCOUNT_TYPE_IDS

    def test_account_type_ids_values_are_integers(self):
        for name, uid in ACCOUNT_TYPE_IDS.items():
            assert isinstance(uid, int), f"ACCOUNT_TYPE_IDS['{name}'] = {uid} is not int"

    def test_account_ref_ids_has_at_least_5_entries(self):
        assert len(ACCOUNT_REF_IDS) >= 5

    def test_account_ref_ids_values_are_integers(self):
        for name, uid in ACCOUNT_REF_IDS.items():
            assert isinstance(uid, int), f"ACCOUNT_REF_IDS['{name}'] = {uid} is not int"

    def test_account_type_ids_no_duplicate_values(self):
        values = list(ACCOUNT_TYPE_IDS.values())
        assert len(values) == len(set(values))

    def test_account_ref_ids_no_duplicate_values(self):
        values = list(ACCOUNT_REF_IDS.values())
        assert len(values) == len(set(values))
