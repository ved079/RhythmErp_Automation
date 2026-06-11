"""
test_agent_api_validations.py
-----------------------------
API-only validation test suite for RhythmERP Agent screen.
~12 test cases that verify server-side validation via direct API calls.
No browser needed — all tests use ``agt_api`` fixture only.

Bucket A — API-Only Tests: Verify server-side validation, boundary
conditions, and security that can only be tested at the API level.

PROBE RESULTS (2026-06-11, after field mapping fix):
  With correct field keys (name, mobile_no, email_id), the server DOES
  validate most inputs. Previous "no validation" finding was caused by
  wrong field names in our payloads (agent_name, phone_number, email).

  Server REJECTS:  empty mobile_no, 256-char name, invalid email,
                   invalid phone, invalid IFSC
  Server ACCEPTS:  spaces-only name, special chars, SQL injection,
                   XSS payload (genuine validation gaps)
  GET 200 OK:      all accepted records open fine (no NoneType crash)
  GET 500 NoneType: was caused by wrong field names creating blank records

Known Backend Bugs (Agent-specific, confirmed via probe 2026-06-11):
  AGT-BUG-004: Spaces-only name accepted (server stores as None)
  AGT-BUG-001: SQL injection payload accepted (no sanitization)
  AGT-BUG-002: XSS payload accepted (no sanitization)
  AGT-BUG-005: Special characters in name accepted (no format validation)
  AGT-BUG-006: Duplicate agent name accepted (no uniqueness check)
  AGT-BUG-007: Invalid email accepted on UPDATE (validated on CREATE only)

Test Inventory (12 tests):
  AGT-AC01 — Empty submit             (server REJECTS — validates mobile_no)
  AGT-AC02 — Spaces-only agent name   (xfail — BUG: accepted as None)
  AGT-AC03 — Special chars agent name (xfail — BUG: no name format validation)
  AGT-AC04 — SQL injection agent name (xfail — BUG: no sanitization)
  AGT-AC05 — XSS payload agent name   (xfail — BUG: no sanitization)
  AGT-AC06 — 255-char agent name      (server ACCEPTS — max boundary)
  AGT-AC07 — 256-char agent name      (server REJECTS — length check works)
  AGT-AC08 — Invalid email format     (server REJECTS — email validated)
  AGT-AC09 — Invalid phone number     (server REJECTS — phone validated)
  AGT-AC10 — Invalid IFSC code        (server REJECTS — IFSC validated)
  AGT-AD01 — Duplicate agent name     (xfail — BUG: no uniqueness check)
  AGT-AE01 — Edit with invalid email  (xfail — BUG: not validated on update)

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
# AGT-AC01 through AGT-AC10: Create Validation
# ====================================================================

class TestCreateValidation:
    """API-only: Validate Agent creation with various invalid payloads."""

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC01_empty_submit(self, agt_api):
        """POST with all empty required fields -> server rejects (validates mobile_no).

        Probe result: Server returns "'mobile_no' is required".
        """
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
        reason="BUG: Spaces-only name accepted — server stores as None (AGT-BUG-004)",
    )
    def test_AGT_AC02_spaces_only_name(self, agt_api):
        """Agent Name = spaces only -> should be rejected.

        Probe result: Server ACCEPTS, stores name as None in DB.
        This creates a record with a null name — no format validation.
        """
        log.info("AGT-AC02: Spaces-only agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_spaces_only()},
            name_prefix="SpacesAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="SpacesAGT")
        assert result is None, "Spaces-only agent name should be rejected"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: Special characters in name accepted — no name format validation (AGT-BUG-005)",
    )
    def test_AGT_AC03_special_chars_name(self, agt_api):
        """Agent Name with special chars -> should be rejected.

        Probe result: Server ACCEPTS '!@#$%^&*()Agent'. No name format
        validation on the server side.
        """
        log.info("AGT-AC03: Special chars agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_special_char_name()},
            name_prefix="SpecialAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="SpecialAGT")
        assert result is None, "Special chars agent name should be rejected"

    @pytest.mark.api
    @pytest.mark.bug
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: SQL injection payloads accepted — no input sanitization (AGT-BUG-001)",
    )
    def test_AGT_AC04_sql_injection(self, agt_api):
        """Agent Name with SQL injection -> should be rejected.

        Probe result: Server ACCEPTS "'; DROP TABLE Agent; --".
        No input sanitization or parameterized query enforcement.
        """
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
        reason="BUG: XSS payloads accepted — no input sanitization (AGT-BUG-002)",
    )
    def test_AGT_AC05_xss_payload(self, agt_api):
        """Agent Name with XSS payload -> should be rejected.

        Probe result: Server ACCEPTS "<script>alert('xss')</script>".
        No HTML/script sanitization — potential stored XSS vulnerability.
        """
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
        """Agent Name with 255 chars -> should be accepted (max boundary).

        Probe result: Server ACCEPTS — within max length.
        """
        log.info("AGT-AC06: 255-char agent name via API")
        result = agt_api.create_agent(
            agent_data={"name": generate_string_255()},
            name_prefix="255AGT",
        )
        assert result is not None, "255-char agent name should be accepted (max boundary)"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC07_256_char_name(self, agt_api):
        """Agent Name with 256 chars -> server rejects (length check works).

        Probe result: Server REJECTS with "Failed to save record".
        The server does enforce a max length on the name field.
        """
        log.info("AGT-AC07: 256-char agent name via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"name": generate_string_256()},
            name_prefix="256AGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="256AGT")
        assert result is None, "256-char agent name should be rejected (over max)"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC08_invalid_email(self, agt_api):
        """Invalid email format -> server rejects.

        Probe result: Server REJECTS with "Invalid Email".
        Email format validation IS enforced on CREATE.
        """
        log.info("AGT-AC08: Invalid email via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"email_id": generate_invalid_email()},
            name_prefix="InvEmailAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="InvEmailAGT")
        assert result is None, "Invalid email should be rejected"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC09_invalid_phone(self, agt_api):
        """Invalid phone number -> server rejects.

        Probe result: Server REJECTS with "Invalid Phone Number".
        Phone format validation IS enforced on CREATE.
        """
        log.info("AGT-AC09: Invalid phone via API")
        payload = agt_api.generate_unique_payload(
            agent_data={"mobile_no": generate_invalid_phone()},
            name_prefix="InvPhoneAGT",
        )
        result = agt_api.create_and_expect_failure(payload, name_prefix="InvPhoneAGT")
        assert result is None, "Invalid phone number should be rejected"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_AGT_AC10_invalid_ifsc(self, agt_api):
        """Invalid IFSC code -> server rejects.

        Probe result: Server REJECTS with "Invalid IFSC Code".
        IFSC format validation IS enforced on CREATE.
        """
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
        reason="BUG: Agent API has no duplicate name validation — accepted (AGT-BUG-006)",
    )
    def test_AGT_AD01_duplicate_name(self, agt_api):
        """Create agent with same name twice -> second should be rejected.

        The server does not enforce name uniqueness for Agent records.
        """
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
        reason="BUG: Agent API has no email validation on update — invalid email accepted (AGT-BUG-007)",
    )
    def test_AGT_AE01_edit_invalid_email(self, agt_api):
        """Update agent with invalid email -> should be rejected.

        Email IS validated on CREATE (probe confirmed "Invalid Email"
        rejection), but may NOT be validated on UPDATE. This test
        verifies whether the same validation applies to edits.
        """
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
