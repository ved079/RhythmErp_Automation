"""
test_agent_payload.py
---------------------
Payload variation tests for RhythmERP Agent API.
Tests various payload structures, missing fields, and edge cases.

~10 tests, all headless API calls.

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


class TestPayloadVariations:
    """Test various Agent API payload structures."""

    @pytest.mark.api
    @pytest.mark.sanity
    def test_minimal_payload(self, agt_api):
        """Create agent with only required fields — should succeed."""
        log.info("Payload: Minimal (required only)")
        payload = {
            "attribute_name": "Agent",
            "agent_name": f"MinPayload_{__import__('datetime').datetime.now().strftime('%Y%m%d%H%M%S')}",
            "phone_number": "9876543210",
        }
        result = agt_api.client.create_entry(payload)
        if result is not None:
            agt_api.tracker.track(
                id=result.get("id"),
                agent_name=payload["agent_name"],
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
                agent_name=payload.get("agent_name", "unknown"),
                payload_summary="Missing attribute_name — still accepted",
            )
            log.info("Payload accepted even without attribute_name")
        else:
            log.info("Payload rejected without attribute_name — expected")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_empty_address_set(self, agt_api):
        """Agent with empty address array — should fail (address required)."""
        log.info("Payload: Empty address set")
        payload = agt_api.generate_unique_payload(name_prefix="NoAddr")
        payload["screenmatlistingdata_set"] = []
        result = agt_api.create_and_expect_failure(payload, name_prefix="NoAddr")
        assert result is None, "Agent without address should be rejected"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_empty_bank_details(self, agt_api):
        """Agent with empty bank details — may or may not be required."""
        log.info("Payload: Empty bank details")
        payload = agt_api.generate_unique_payload(name_prefix="NoBank")
        payload["bank_details"] = []
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="bank_details",
            name_prefix="NoBank",
        )
        log.info(f"Empty bank details: accepted={doc['accepted']}")

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
            agent_data={"agent_name": "Agent\u00e9\u00f1\u00fc"},
            name_prefix="UnicodeAGT",
        )
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="agent_name",
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
        """Agent with multiple address rows — should succeed."""
        log.info("Payload: Multiple addresses")
        from pages.registration.modules.agent.data.agent_data import (
            generate_address, generate_pin_code,
        )
        payload = agt_api.generate_unique_payload(name_prefix="MultiAddr")
        payload["screenmatlistingdata_set"] = [
            {
                "address_type": "Permanent",
                "country": "India",
                "state": "Maharashtra",
                "district": "Pune",
                "taluka": "Haveli",
                "village": "",
                "address": generate_address(),
                "pin_code": generate_pin_code(),
                "gst_number": "",
            },
            {
                "address_type": "Communication",
                "country": "India",
                "state": "Maharashtra",
                "district": "Pune",
                "taluka": "Haveli",
                "village": "",
                "address": generate_address(),
                "pin_code": generate_pin_code(),
                "gst_number": "",
            },
        ]
        result = agt_api.client.create_entry(payload)
        if result is not None:
            agt_api.tracker.track(
                id=result.get("id"),
                agent_name=payload["agent_name"],
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
            agent_data={"email": long_email},
            name_prefix="LongEmail",
        )
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="email",
            name_prefix="LongEmail",
        )
        log.info(f"Long email: accepted={doc['accepted']}, status={doc['status_code']}")
