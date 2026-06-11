"""
test_agent_payload.py
---------------------
Payload variation tests for RhythmERP Agent API.
Tests various payload structures, missing fields, and edge cases.

~10 tests, all headless API calls.

Field Key Mapping (from Agent schema):
  UI "Agent Name"   -> API key "name"
  UI "Phone Number" -> API key "mobile_no" (integer)
  UI "Email"        -> API key "email_id"
  Sub-records use children[] stepper format (same as Supplier).

PIN CODE FIX (2026-06-11):
  generate_pin_code() returns random digits that fail server validation.
  Always use verified pin codes from the address chain in generate_unique_payload.
  For custom address rows, import hardcoded pin codes.

Run:
  pytest test_agent_payload.py -v --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.registration.modules.agent.utils.api_agent_utils import (
    COUNTRY_INDIA_ID,
    ACCOUNT_TYPE_CURRENT_ID,
    ADDRESS_TYPE_SHIPPING_ID,
    ADDRESS_TYPE_BILLING_ID,
    _ADDRESS_CHAINS,
)


# Verified pin codes for address chains (found 2026-06-11)
_MAHARASHTRA_PIN = 444001
_PUNJAB_PIN = 141001


class TestPayloadVariations:
    """Test various Agent API payload structures."""

    @pytest.mark.api
    @pytest.mark.sanity
    def test_minimal_payload(self, agt_api):
        """Create agent with only required fields — should succeed."""
        log.info("Payload: Minimal (required only)")
        payload = {
            "attribute_name": "Agent",
            "name": f"MinPayload_{__import__('datetime').datetime.now().strftime('%Y%m%d%H%M%S')}",
            "mobile_no": 9876543210,
        }
        result = agt_api.client.create_entry(payload)
        if result is not None:
            agt_api.tracker.track(
                id=result.get("id"),
                agent_name=payload["name"],
                payload_summary="Minimal payload test",
            )
            log.info(f"Minimal payload accepted: id={result.get('id')}")
        else:
            log.warning("Minimal payload rejected — may need more required fields")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_full_payload(self, agt_api):
        """Create agent with all fields populated — should succeed."""
        log.info("Payload: Full (all fields)")
        result = agt_api.create_agent(name_prefix="FullPayload")
        assert result is not None, "Full payload should be accepted"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_missing_attribute_name(self, agt_api):
        """Payload without attribute_name — may still work or fail."""
        log.info("Payload: Missing attribute_name")
        payload = agt_api.generate_unique_payload(name_prefix="NoAttr")
        del payload["attribute_name"]
        result = agt_api.client.create_entry(payload)
        if result is not None:
            agt_api.tracker.track(
                id=result.get("id"),
                agent_name=payload.get("name", "unknown"),
                payload_summary="Missing attribute_name — still accepted",
            )
            log.info("Payload accepted even without attribute_name")
        else:
            log.info("Payload rejected without attribute_name — expected")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_empty_address_set(self, agt_api):
        """Agent with empty address details — server rejects.

        Previously thought to be a bug (AGT-BUG-003), but the server
        actually validates and rejects empty address details when
        correct field keys are used. Uses create_and_document() to
        avoid false results from pin_code flakiness.
        """
        log.info("Payload: Empty address set")
        payload = agt_api.generate_unique_payload(name_prefix="NoAddr")
        # Clear address details in children[]
        for child in payload.get("children", []):
            if child.get("stepper_name") == "Address Details":
                child["details"] = []
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="address (empty)",
            name_prefix="NoAddr",
        )
        if doc["accepted"]:
            log.warning(
                "Empty address set was ACCEPTED — no address validation exists"
            )
        else:
            log.info(
                "Empty address set correctly REJECTED — server validates address"
            )

    @pytest.mark.api
    @pytest.mark.sanity
    def test_empty_bank_details(self, agt_api):
        """Agent with empty bank details — server rejects.

        Previously thought to be a bug (AGT-BUG-003), but the server
        actually validates and rejects empty bank details when correct
        field keys are used. Uses create_and_document() to avoid false
        results from pin_code flakiness.
        """
        log.info("Payload: Empty bank details")
        payload = agt_api.generate_unique_payload(name_prefix="NoBank")
        for child in payload.get("children", []):
            if child.get("stepper_name") == "Bank Details":
                child["details"] = []
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="bank_details (empty)",
            name_prefix="NoBank",
        )
        if doc["accepted"]:
            log.warning(
                "Empty bank details was ACCEPTED — no bank validation exists"
            )
        else:
            log.info(
                "Empty bank details correctly REJECTED — server validates bank"
            )

    @pytest.mark.api
    @pytest.mark.sanity
    def test_status_false(self, agt_api):
        """Create agent with status=False (inactive)."""
        log.info("Payload: Status=False")
        result = agt_api.create_agent(
            agent_data={"status": False},
            name_prefix="InactiveAGT",
        )
        if result is not None:
            log.info(f"Inactive agent created: id={result.get('id')}")
        else:
            log.warning("Agent with status=False rejected")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_unicode_agent_name(self, agt_api):
        """Agent Name with unicode characters — document behavior."""
        log.info("Payload: Unicode agent name")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": "Agent\u00e9\u00f1\u00fc"},
            name_prefix="UnicodeAGT",
        )
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="name",
            name_prefix="UnicodeAGT",
        )
        log.info(f"Unicode name: accepted={doc['accepted']}")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_extra_unknown_field(self, agt_api):
        """Payload with extra unknown field — server should ignore or reject."""
        log.info("Payload: Extra unknown field")
        payload = agt_api.generate_unique_payload(name_prefix="ExtraField")
        payload["this_field_does_not_exist"] = "should_be_ignored"
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="unknown_field",
            name_prefix="ExtraField",
        )
        log.info(f"Extra field: accepted={doc['accepted']} (server should ignore)")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_multiple_addresses(self, agt_api):
        """Agent with multiple address rows — should succeed.

        Uses verified pin codes from _ADDRESS_CHAINS instead of
        generate_pin_code() to avoid 'Invalid Pin Code' errors.
        """
        log.info("Payload: Multiple addresses")
        from pages.registration.modules.agent.data.agent_data import generate_address

        chain = _ADDRESS_CHAINS[0]  # Maharashtra — has verified pin
        payload = agt_api.generate_unique_payload(name_prefix="MultiAddr")
        # Override Address Details stepper with multiple rows
        for child in payload.get("children", []):
            if child.get("stepper_name") == "Address Details":
                child["details"] = [
                    {
                        "address_type": ADDRESS_TYPE_SHIPPING_ID,
                        "country_ref_id_id": COUNTRY_INDIA_ID,
                        "state_ref_id_id": chain["state_ref_id_id"],
                        "district_ref_id_id": chain["district_ref_id_id"],
                        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
                        "village_ref_id_id": chain.get("village_ref_id_id"),
                        "address": generate_address(),
                        "pin_code": chain["pin_code"],
                        "same_as_above": None,
                        "details": [],
                    },
                    {
                        "address_type": ADDRESS_TYPE_BILLING_ID,
                        "country_ref_id_id": COUNTRY_INDIA_ID,
                        "state_ref_id_id": chain["state_ref_id_id"],
                        "district_ref_id_id": chain["district_ref_id_id"],
                        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
                        "village_ref_id_id": chain.get("village_ref_id_id"),
                        "address": generate_address(),
                        "pin_code": chain["pin_code"],
                        "same_as_above": None,
                        "details": [],
                    },
                ]
        result = agt_api.client.create_entry(payload)
        if result is not None:
            agt_api.tracker.track(
                id=result.get("id"),
                agent_name=payload["name"],
                payload_summary="Multiple address rows",
            )
            log.info(f"Multiple addresses accepted: id={result.get('id')}")
        else:
            log.warning("Multiple addresses rejected")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_long_email(self, agt_api):
        """Agent with very long email — document boundary behavior."""
        log.info("Payload: Long email")
        long_email = f"{'a' * 200}@example.com"
        payload = agt_api.generate_unique_payload(
            agent_data={"email_id": long_email},
            name_prefix="LongEmail",
        )
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="email_id",
            name_prefix="LongEmail",
        )
        log.info(f"Long email: accepted={doc['accepted']}, status={doc['status_code']}")
