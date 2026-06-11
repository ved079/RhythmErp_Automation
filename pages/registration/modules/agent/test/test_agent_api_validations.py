"""
test_agent_api_validations.py
-----------------------------
API-only validation test suite for RhythmERP Agent screen.
~12 test cases that verify server-side validation via direct API calls.
No browser needed — all tests use ``agt_api`` fixture only.

Bucket A — API-Only Tests: Verify server-side validation, boundary
conditions, and security that can only be tested at the API level.

IMPORTANT — Known Backend Bugs (Agent-specific):
  - NO server-side validation on POST — empty/invalid data accepted
  - GET /core/dynamic-screen-wrapper/Agent/{id}/ returns HTTP 500 for
    records created with broken children data (wrong stepper_name,
    missing address FK chains, etc.). Properly created records work.
  - Customer and Supplier DO validate — Agent does not

PAYLOAD FIX (2026-06-11):
  The Agent API requires exact stepper names in children[]:
    children[0] = "Address Details" (NOT just any name)
    children[1] = "Payment Details" (NOT "Additional Details"!)
    children[2] = "Bank Details"
  Using wrong names causes broken records that GET can't retrieve.

Test Inventory (12 tests):
  AGT-AC01 — Empty submit (xfail — BUG: accepted)
  AGT-AC02 — Spaces-only agent name (xfail — BUG: accepted)
  AGT-AC03 — Special chars agent name (document behavior)
  AGT-AC04 — SQL injection agent name (xfail — BUG: accepted)
  AGT-AC05 — XSS payload agent name (xfail — BUG: accepted)
  AGT-AC06 — 255-char agent name (max boundary)
  AGT-AC07 — 256-char agent name (xfail — BUG: accepted)
  AGT-AC08 — Invalid email format (xfail — BUG: accepted)
  AGT-AC09 — Invalid phone number (xfail — BUG: accepted)
  AGT-AC10 — Invalid IFSC code (xfail — BUG: accepted)
  AGT-AD01 — Duplicate agent name (xfail — BUG: accepted)
  AGT-AE01 — Edit with invalid email (xfail — no email validation on update)

Field Key Mapping (from Agent schema):
  UI "Agent Name"   -> API key "name"
  UI "Phone Number" -> API key "mobile_no"
  UI "Email"        -> API key "email_id"

Run:
  pytest test_agent_api_validations.py -v --tb=short
  pytest test_agent_api_validations.py -v -m api --tb=short
  pytest test_agent_api_validations.py -v -k "AGT_AC01" --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.registration.modules.agent.data.agent_data import (
    generate_spaces_only,
    generate_string_255,
    generate_string_256,
    generate_special_char_name,
    generate_sql_injection,
    generate_xss_payload,
    generate_invalid_email,
    generate_invalid_phone,
    generate_invalid_ifsc,
)


# ====================================================================
# AGT-AC01: Empty submit
# ====================================================================

class TestCreateValidation:
    """API-only: Validate Agent creation with various invalid payloads."""

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no server-side validation — empty payload accepted (AGT-BUG-003)",
    )
    def test_AGT_AC01_empty_submit(self, agt_api):
        """POST with all empty required fields → should fail validation."""
        log.info("AGT-AC01: Empty submit via API")
        payload = {
            "attribute_name": "Agent",
            "name": "",
            "mobile_no": "",
            "email_id": "",
        }
        result = agt_api.create_and_expect_failure(payload, name_prefix="EmptyAGT")
        assert result is None, "Empty payload should be rejected by server"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no server-side validation — spaces-only name accepted (AGT-BUG-003)",
    )
    def test_AGT_AC02_spaces_only_name(self, agt_api):
        """Agent Name = spaces only → should be rejected."""
        log.info("AGT-AC02: Spaces-only agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_spaces_only()},
            name_prefix="SpacesAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="SpacesAGT")
        assert result is None, "Spaces-only agent name should be rejected"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC03_special_chars_name(self, agt_api):
        """Agent Name with special chars → document accept/reject behavior."""
        log.info("AGT-AC03: Special chars agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_special_char_name()},
            name_prefix="SpecialAGT",
        )
        doc = agt_api.create_and_document(
            payload,
            field_being_tested="name",
            name_prefix="SpecialAGT",
        )
        log.info(f"Special chars result: accepted={doc['accepted']}, status={doc['status_code']}")

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: SQL injection payloads accepted by server (AGT-BUG-001)",
    )
    def test_AGT_AC04_sql_injection(self, agt_api):
        """Agent Name with SQL injection → should be rejected."""
        log.info("AGT-AC04: SQL injection via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_sql_injection()},
            name_prefix="SQLAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="SQLAGT")
        assert result is None, "SQL injection should be rejected"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: XSS payloads accepted by server (AGT-BUG-002)",
    )
    def test_AGT_AC05_xss_payload(self, agt_api):
        """Agent Name with XSS payload → should be rejected."""
        log.info("AGT-AC05: XSS payload via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_xss_payload()},
            name_prefix="XSSAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="XSSAGT")
        assert result is None, "XSS payload should be rejected"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC06_255_char_name(self, agt_api):
        """Agent Name with 255 chars → should be accepted (max boundary)."""
        log.info("AGT-AC06: 255-char agent name via API")
        result = agt_api.create_agent(
            agent_data={"name": generate_string_255()},
            name_prefix="255AGT",
        )
        if result is not None:
            log.info("255-char agent name accepted (max boundary)")
        else:
            log.warning("255-char agent name rejected — may be below max")

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no length validation — 256-char name accepted (AGT-BUG-003)",
    )
    def test_AGT_AC07_256_char_name(self, agt_api):
        """Agent Name with 256 chars → should be rejected (over max)."""
        log.info("AGT-AC07: 256-char agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_string_256()},
            name_prefix="256AGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="256AGT")
        assert result is None, "256-char agent name should be rejected (over max)"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no email format validation — invalid email accepted (AGT-BUG-003)",
    )
    def test_AGT_AC08_invalid_email(self, agt_api):
        """Invalid email format → should be rejected."""
        log.info("AGT-AC08: Invalid email via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"email_id": generate_invalid_email()},
            name_prefix="InvEmailAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="InvEmailAGT")
        assert result is None, "Invalid email should be rejected"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no phone format validation — invalid phone accepted (AGT-BUG-003)",
    )
    def test_AGT_AC09_invalid_phone(self, agt_api):
        """Invalid phone number → should be rejected."""
        log.info("AGT-AC09: Invalid phone via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"mobile_no": generate_invalid_phone()},
            name_prefix="InvPhoneAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="InvPhoneAGT")
        assert result is None, "Invalid phone number should be rejected"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no IFSC format validation — invalid IFSC accepted (AGT-BUG-003)",
    )
    def test_AGT_AC10_invalid_ifsc(self, agt_api):
        """Invalid IFSC code → should be rejected."""
        log.info("AGT-AC10: Invalid IFSC via API")
        payload = agt_api.generate_unique_payload(
            name_prefix="InvIFSAGT",
        )
        # Override bank IFSC in children[] Bank Details stepper
        for child in payload.get("children", []):
            if child.get("stepper_name") == "Bank Details":
                for detail in child.get("details", []):
                    detail["bank_ifsc_code"] = generate_invalid_ifsc()
        result = agt_api.create_and_expect_failure(payload, name_prefix="InvIFSAGT")
        assert result is None, "Invalid IFSC code should be rejected"


# ====================================================================
# AGT-AD01: Duplicate agent name
# ====================================================================

class TestDuplicateValidation:
    """API-only: Validate duplicate agent name rejection."""

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no duplicate name validation — accepted (AGT-BUG-003)",
    )
    def test_AGT_AD01_duplicate_name(self, agt_api):
        """Create agent with same name twice → second should be rejected."""
        log.info("AGT-AD01: Duplicate agent name via API")

        # Create first agent
        result1 = agt_api.create_agent(name_prefix="DupAGT")
        assert result1 is not None, "First agent creation failed"
        agent_name = result1.get("name", "")
        log.info(f"First agent created: {agent_name}")

        # Try to create second with same name
        payload2 = agt_api.generate_unique_payload(
            agent_data={"name": agent_name},
            name_prefix="DupAGT",
        )
        result2 = agt_api.create_and_expect_failure(payload2, name_prefix="DupAGT2")

        if result2 is None:
            log.info("Duplicate agent name correctly rejected")
        else:
            log.warning(
                f"BUG: Duplicate agent name was accepted! "
                f"Second agent id={result2.get('id')}"
            )

        assert result2 is None, "Duplicate agent name should be rejected"


# ====================================================================
# AGT-AE01: Edit with invalid email
# ====================================================================

class TestEditValidation:
    """API-only: Validate agent update with invalid data."""

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Agent API has no email validation on update — invalid email accepted (AGT-BUG-003)",
    )
    def test_AGT_AE01_edit_invalid_email(self, agt_api):
        """Update agent with invalid email → should be rejected."""
        log.info("AGT-AE01: Edit with invalid email via API")

        # Create an agent first (with correct payload — GET works for these)
        result = agt_api.create_agent(name_prefix="EditInvEmail")
        assert result is not None, "Agent creation for edit test failed"
        agent_id = result.get("id")
        agent_name = result.get("name", "")

        # Fetch full record for update
        # NOTE: GET works for records created with correct payload structure
        detail = agt_api.get_agent(agent_id)
        assert detail is not None, (
            f"Failed to fetch agent id={agent_id}. "
            f"This may happen if the record was created with broken children data."
        )

        # Modify email to invalid
        detail["email_id"] = generate_invalid_email()

        # Attempt update
        update_result = agt_api.update_agent(agent_id, detail)

        if update_result is None:
            log.info("Invalid email correctly rejected on update")
        else:
            log.warning(
                f"BUG: Invalid email was accepted on update for agent id={agent_id}"
            )

        assert update_result is None, "Invalid email should be rejected on update"
