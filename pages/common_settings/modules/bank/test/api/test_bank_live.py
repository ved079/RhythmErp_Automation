import pytest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from pages.common_settings.modules.bank.data.bank_data import (
    ACCOUNT_TYPE_IDS,
    ACCOUNT_REF_IDS,
    generate_bank_name,
    generate_bank_code,
    generate_branch_name,
    generate_branch_code,
    generate_account_number,
    generate_ifsc_code,
    generate_cash_credit_limit,
    generate_bank_address,
    generate_swift_number,
)


def _payload(bank_name, bank_code=None, account_type_id=None, account_ref_id=None,
             branch_name=None, branch_code=None, account_number=None,
             ifsc_code=None, cash_credit_limit=None, bank_address=None,
             swift_number="", status=True):
    return {
        "id": "",
        "attribute_name": "Bank",
        "bank_name": bank_name,
        "bank_code": bank_code or generate_bank_code(),
        "branch_name": branch_name or generate_branch_name(),
        "branch_code": branch_code or generate_branch_code(),
        "account_number": account_number or generate_account_number(),
        "account_type": account_type_id or ACCOUNT_TYPE_IDS["Current"],
        "swift_number": swift_number,
        "iban_number": "",
        "ifsc_code": ifsc_code or generate_ifsc_code(),
        "cash_credit_limit": cash_credit_limit or generate_cash_credit_limit(),
        "bank_address": bank_address or generate_bank_address(),
        "account_ref_id": account_ref_id or list(ACCOUNT_REF_IDS.values())[0],
        "is_default_bank": False,
        "status": status,
    }


@pytest.mark.live_api
class TestBankLiveAPI:
    """Live CRUD tests against the real ERP API. Tenant-universal — no hardcoded records assumed."""

    def test_create_boundary_cases(self, api_client):
        """Create banks: both account types, with/without optional swift, inactive status."""
        try:
            ref_id = list(ACCOUNT_REF_IDS.values())[0]
            cases = [
                ("current_with_swift", generate_bank_name("CRNT"),
                 ACCOUNT_TYPE_IDS["Current"], ref_id, generate_swift_number(), True),
                ("saving_no_swift",    generate_bank_name("SAVG"),
                 ACCOUNT_TYPE_IDS["Saving"], ref_id, "", True),
                ("inactive_status",    generate_bank_name("INAC"),
                 ACCOUNT_TYPE_IDS["Current"], ref_id, "", False),
            ]
            for label, name, type_id, acct_ref, swift, status in cases:
                result = api_client.create_entry(
                    _payload(name, account_type_id=type_id,
                             account_ref_id=acct_ref, swift_number=swift, status=status)
                )
                assert result is not None and result.get("id"), \
                    f"Create failed for case: {label}"
        finally:
            pass

    def test_bank_name_validation(self, api_client):
        """Verify API bank_name validation: alpha+spaces accepted; digits and special chars rejected."""
        # Accepted: alpha-only names (>= 10 chars)
        accepted = [
            ("alpha_only",    generate_bank_name("ALPHA")),
            ("with_spaces",   "STATE BANK OF INDIA"),
        ]
        for label, name in accepted:
            result = api_client.create_entry(_payload(name))
            assert result is not None and result.get("id"), \
                f"'{name}' ({label}) must be accepted by API. Got: {result}"

        # Rejected: special chars and digits in name
        rejected = [
            ("special_chars",  f"BANK@#${datetime.now().strftime('%H%M%S')}XX"),
            ("digits_in_name", f"BANK{datetime.now().strftime('%H%M%S')}XX"),
        ]
        for label, name in rejected:
            result = api_client.create_entry(_payload(name))
            assert result is None or "id" not in result, \
                f"'{name}' ({label}) must be rejected by API. Got: {result}"

    def test_required_fields_enforced(self, api_client):
        """Missing required fields must be rejected by API."""
        ref_id = list(ACCOUNT_REF_IDS.values())[0]
        base = generate_bank_name("REQ")

        missing_cases = [
            ("no_bank_name",    {**_payload(base, account_ref_id=ref_id), "bank_name": ""}),
            ("no_ifsc",         {**_payload(base, account_ref_id=ref_id), "ifsc_code": ""}),
            ("no_account_num",  {**_payload(base, account_ref_id=ref_id), "account_number": ""}),
        ]
        for label, p in missing_cases:
            result = api_client.create_entry(p)
            assert result is None or "id" not in result, \
                f"Payload with '{label}' missing must be rejected. Got: {result}"

    def test_crud_lifecycle(self, api_client):
        """Full lifecycle: create -> get -> list -> update branch_name -> verify.
        ERP is append-only: one update per record max, no delete API (405)."""
        try:
            name = generate_bank_name("LC")
            ref_id = list(ACCOUNT_REF_IDS.values())[0]
            created = api_client.create_entry(_payload(name, account_ref_id=ref_id))
            assert created is not None and created.get("id"), "Create must return id"
            current_id = created["id"]

            # GET
            detail = api_client.get_entry("Bank", current_id)
            assert detail is not None, "GET must return the created entry"
            assert detail.get("id") == current_id
            assert detail.get("bank_name") == name

            # LIST
            listing = api_client.list_entries("Bank", page=1, page_size=200)
            assert listing is not None
            items = listing.get("screenmatlistingdata_set", [])
            assert any(item.get("id") == current_id for item in items), \
                "Created entry must appear in list"

            # UPDATE branch_name in ONE call
            update_payload = dict(detail)
            update_payload["branch_name"] = generate_branch_name()
            update_result = api_client.update_entry(current_id, update_payload)
            assert update_result is not None, "Update must succeed"
            current_id = update_result["id"]

            updated = api_client.get_entry("Bank", current_id)
            assert updated is not None
            assert updated.get("branch_name") == update_payload["branch_name"], \
                f"Branch name must be updated. Got: {updated.get('branch_name')}"

        finally:
            pass  # No cleanup — ERP has no delete and no second update
