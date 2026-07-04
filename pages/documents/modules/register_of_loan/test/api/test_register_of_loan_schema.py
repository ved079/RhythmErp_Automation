"""
test_register_of_loan_schema.py â€” Verify Register of Loan schema matches code.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pages.documents.modules.register_of_loan.data.register_of_loan_data import (
    build_api_payload,
    FACILITY_DETAILS_IDS,
    FACILITY_DETAILS_NAMES,
    EMI_PERIOD_IDS,
    EMI_PERIOD_NAMES,
)


class TestRegisterOfLoanSchema:
    """Verify the Register of Loan screen metadata."""

    def test_screen_name_in_payload(self):
        payload = build_api_payload()
        assert payload["attribute_name"] == "Register of Loan"

    def test_facility_details_has_three_options(self):
        assert len(FACILITY_DETAILS_IDS) == 3
        assert FACILITY_DETAILS_NAMES[652] == "CC"
        assert FACILITY_DETAILS_NAMES[651] == "Term Loan"

    def test_emi_period_has_four_options(self):
        assert len(EMI_PERIOD_IDS) == 4
        assert EMI_PERIOD_NAMES[1528] == "Monthly"
        assert EMI_PERIOD_NAMES[1529] == "Quaterly"
        assert EMI_PERIOD_NAMES[1530] == "Half Yearly"
        assert EMI_PERIOD_NAMES[1531] == "Yearly"

    def test_all_ids_have_names(self):
        for tid in FACILITY_DETAILS_IDS:
            assert tid in FACILITY_DETAILS_NAMES
        for eid in EMI_PERIOD_IDS:
            assert eid in EMI_PERIOD_NAMES
