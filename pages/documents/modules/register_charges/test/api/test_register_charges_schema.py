"""
test_register_charges_schema.py â€” Verify Register Charges schema matches code expectations.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.register_charges.data.register_charges_data import (
    build_api_payload,
    TYPE_OF_CHARGE_IDS,
    TYPE_OF_CHARGE_NAMES,
)


class TestRegisterChargesSchema:
    """Verify the Register Charges screen metadata."""

    def test_screen_name_in_payload(self):
        payload = build_api_payload()
        assert payload["attribute_name"] == "Register Charges"

    def test_type_of_charge_has_three_options(self):
        assert len(TYPE_OF_CHARGE_IDS) == 3
        assert TYPE_OF_CHARGE_NAMES[1909] == "Mortgage"
        assert TYPE_OF_CHARGE_NAMES[1910] == "Hypothecation"
        assert TYPE_OF_CHARGE_NAMES[1911] == "Pledge"

    def test_all_type_of_charge_ids_have_names(self):
        for tid in TYPE_OF_CHARGE_IDS:
            assert tid in TYPE_OF_CHARGE_NAMES, f"ID {tid} missing name"

    def test_all_type_of_charge_names_have_ids(self):
        for tid, name in TYPE_OF_CHARGE_NAMES.items():
            assert tid in TYPE_OF_CHARGE_IDS, f"Name '{name}' ID {tid} not in ids"
