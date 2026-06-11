"""
api_agent_utils.py
------------------
Agent-specific API wrapper for hybrid test migration.

Wraps the generic RhythmERPAPIClient with Agent-screen helpers:
  - create_agent()          — happy-path creation with ID tracking
  - get_agent()             — fetch single agent by ID
  - update_agent()          — update via POST (PUT returns 405)
  - search_agents()         — list/search with pagination
  - assert_validation_error() — validate server-side error responses
  - create_and_expect_failure() — send invalid payload, track accidental creation
  - create_and_document()   — exploratory test helper
  - generate_unique_payload() — timestamp+UUID namespaced payload
  - track_created_id()      — record IDs via CleanupTracker
  - generate_cleanup_report() — export tracked IDs as JSON/CSV

NO-DELETE CONSTRAINT:
  The ERP has NO delete endpoint, no delete button, and no soft-delete
  via status=False. Cleanup = tracking + reporting for manual purge.
  This module will NEVER contain delete_agent() or cleanup_all().

FK FIELD KEYS (from Agent schema — verified 2026-06-11):
  Agent uses the same party_master table as Supplier/Customer.
  Field keys differ from UI labels:
    UI "Agent Name"   -> API key "name"
    UI "Phone Number" -> API key "mobile_no" (integer)
    UI "Email"        -> API key "email_id"
  Sub-records use the children[] stepper format (same as Supplier).

STEPPER NAMES (verified from live API response 2026-06-11):
  children[0] = "Address Details"  (NOT "Address Details")
  children[1] = "Payment Details"  (NOT "Additional Details"!)
  children[2] = "Bank Details"
  IMPORTANT: Using wrong stepper_name causes the record to be created
  but with broken children data, which makes GET return 500.

KNOWN BUGS:
  - GET /core/dynamic-screen-wrapper/Agent/{id}/ returns HTTP 500 for
    records created with wrong/missing children data. Records created
    with the correct payload structure return 200 correctly.
  - No server-side validation on POST (empty/invalid data accepted).
"""

import json
import csv
import os
import random
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.agent.api.endpoints import SCREEN_NAME
from pages.registration.modules.agent.data.agent_data import (
    generate_agent_name,
    generate_phone_number,
    generate_email,
    generate_address,
    generate_gst,
    generate_bank_name,
    generate_branch,
    generate_ifsc_code,
    generate_account_holder_name,
    generate_account_number,
)
from pages.registration.modules.agent.utils.agent_cleanup import (
    CleanupTracker,
    CreatedRecord,
)


# ──────────────────────────────────────────────
# FK IDs for tenant 681 (from API dropdown endpoints)
# ──────────────────────────────────────────────

# Country
COUNTRY_INDIA_ID = 8

# Account Type
ACCOUNT_TYPE_CURRENT_ID = 1849  # "Current"
ACCOUNT_TYPE_SAVING_ID = 1850   # "Saving"

# Address Types (same as Supplier)
ADDRESS_TYPE_SHIPPING_ID = 43   # "Shipping"
ADDRESS_TYPE_BILLING_ID = 42    # "Billing"

# Bank Doc Types
BANK_DOC_CANCELLED_CHEQUE_ID = 36  # "Cancelled Cheque"
BANK_DOC_PASSBOOK_ID = 35         # "Passbook"
BANK_DOC_BANK_STATEMENT_ID = 1883  # "Bank Statement"

# Payment Terms (optional — None if not needed)
PAYMENT_TERMS_IMMEDIATE_ID = 131
PAYMENT_TERMS_7_DAYS_ID = 549
PAYMENT_TERMS_14_DAYS_ID = 550
PAYMENT_TERMS_21_DAYS_ID = 551
PAYMENT_TERMS_60_DAYS_ID = 27

# Preferred Payment Method (optional — None if not needed)
PAYMENT_METHOD_CASH_ID = 53
PAYMENT_METHOD_CHEQUE_ID = 54
PAYMENT_METHOD_DD_ID = 55
PAYMENT_METHOD_IMPS_ID = 141
PAYMENT_METHOD_RTGS_ID = 143

# ──────────────────────────────────────────────
# Cascading Address Pool (verified on tenant 681)
# Reuse the same chains from Supplier — same country/state/district IDs
# ──────────────────────────────────────────────

_ADDRESS_CHAINS = [
    # Maharashtra / Akola  (PIN 444001 — verified 2026-06-11)
    {
        "state_ref_id_id": 12,
        "district_ref_id_id": 208,
        "sub_district_ref_id_id": 13041,
        "village_ref_id_id": 422660,
        "pin_code": 444001,
    },
    # Punjab  (PIN 141001 — verified 2026-06-11)
    {
        "state_ref_id_id": 82,
        "district_ref_id_id": 764,
        "sub_district_ref_id_id": 13939,
        "village_ref_id_id": 775472,
        "pin_code": 141001,
    },
    # State 101 / district 233  (PIN 380001 — verified 2026-06-11)
    {
        "state_ref_id_id": 101,
        "district_ref_id_id": 233,
        "sub_district_ref_id_id": 12979,
        "village_ref_id_id": None,
        "pin_code": 380001,
    },
]


class AgentAPIUtils:
    """
    Agent-specific API utility for the hybrid test migration.

    Each instance wraps a single RhythmERPAPIClient and a CleanupTracker
    for recording created agent IDs.

    Usage:
        api = AgentAPIUtils()
        api.client.login()

        # Create an agent
        result = api.create_agent()
        assert result is not None

        # Validate an error
        api.create_and_expect_failure(invalid_payload)
        api.assert_validation_error(
            field="agent_name",
            expected_status=400,
            expected_message_substring="required",
        )

        # Generate cleanup report at session end
        api.tracker.generate_reports()
    """

    def __init__(
        self,
        api_client: RhythmERPAPIClient = None,
        tracker: CleanupTracker = None,
    ):
        """
        Initialize with an existing API client + tracker, or create new ones.

        Args:
            api_client: Optional pre-authenticated RhythmERPAPIClient.
                        If None, a new unauthenticated client is created.
                        You MUST call client.login() before use.
            tracker:    Optional existing CleanupTracker.
                        If None, a new one is created.
        """
        self.client = api_client or RhythmERPAPIClient()
        self.tracker = tracker or CleanupTracker()

    # ================================================================
    # Core CRUD Operations
    # ================================================================

    def create_agent(
        self,
        agent_data: dict = None,
        name_prefix: str = "AutoAGT",
        retries: int = 2,
    ) -> Optional[Dict]:
        """
        Create an agent via API and track the resulting ID.

        Args:
            agent_data:  Override data dict (merged with defaults).
            name_prefix: Prefix for auto-generated agent name.
                         Format: {prefix} {timestamp} {uuid8}
            retries:     Number of retries on transient failures (default 2).

        Returns:
            Response JSON dict on success, None on failure.
            The created ID is automatically tracked via CleanupTracker.
        """
        for attempt in range(retries + 1):
            payload = self.generate_unique_payload(
                agent_data=agent_data,
                name_prefix=name_prefix,
            )

            result = self.client.create_entry(payload)

            if result is not None:
                created_id = result.get("id")
                agent_name = result.get("name", payload.get("name", "unknown"))
                self.tracker.track(
                    id=created_id,
                    agent_name=agent_name,
                    payload_summary=f"Created via API with prefix={name_prefix}",
                )
                log.info(
                    f"[AgentAPI] Created agent id={created_id} "
                    f"name='{agent_name}'"
                )
                return result

            # Check if the error is "Invalid Name" — retry with new name
            raw_resp = self.client._last_raw_response
            is_name_error = False
            if raw_resp is not None:
                try:
                    err_body = raw_resp.json()
                    err_msg = str(err_body.get("message", ""))
                    err_errors = err_body.get("errors", [])
                    for e in err_errors:
                        err_msg += " " + e.get("error_message", "")
                    if "invalid name" in err_msg.lower():
                        is_name_error = True
                except Exception:
                    pass

            if is_name_error and attempt < retries:
                log.warning(
                    f"[AgentAPI] 'Invalid Name' on attempt {attempt + 1}/{retries + 1}, "
                    f"retrying with new name..."
                )
                import time
                time.sleep(1)
                continue

            log.warning(
                f"[AgentAPI] Failed to create agent "
                f"name='{payload.get('name', 'unknown')}'"
            )
            return None

        return None

    def get_agent(self, agent_id: int) -> Optional[Dict]:
        """Fetch a single agent by ID.

        NOTE: GET /core/dynamic-screen-wrapper/Agent/{id}/ returns HTTP 500
        for records created with broken/incomplete children data (missing
        address FK chains, wrong stepper_name, etc.). Records created with
        the correct payload structure (since 2026-06-11 fix) return 200.
        """
        return self.client.get_entry(SCREEN_NAME, agent_id)

    def update_agent(
        self, agent_id: int, payload: Dict
    ) -> Optional[Dict]:
        """
        Update an existing agent via POST.

        The ERP's dynamic-screen-wrapper uses POST for updates —
        PUT returns HTTP 405 (Method Not Allowed).

        NOTE: get_agent() returns 500 for records with broken children
        data, but works for properly created records. If you need to
        fetch the full record for update, ensure the record was created
        with the correct payload structure.

        Args:
            agent_id:  The agent's database ID.
            payload:   Complete JSON payload with updated fields.
                       Must include "attribute_name": "Agent".

        Returns:
            Response JSON dict on success, None on failure.
        """
        payload.setdefault("attribute_name", SCREEN_NAME)
        payload.setdefault("id", agent_id)
        return self.client.update_entry(agent_id, payload)

    def search_agents(
        self,
        search: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> Optional[Dict]:
        """
        Search/list agents with pagination.

        Args:
            search:    Search string (agent name, email, etc.).
            page:      Page number.
            page_size: Items per page.

        Returns:
            Response dict with screenmatlistingdata_set, or None.
        """
        return self.client.list_entries(
            SCREEN_NAME,
            page=page,
            page_size=page_size,
            search=search,
        )

    # ================================================================
    # Validation Helpers
    # ================================================================

    def create_and_expect_failure(
        self,
        invalid_payload: Dict,
        name_prefix: str = "FailAGT",
    ) -> Optional[Dict]:
        """
        Send a deliberately invalid payload to trigger validation errors.

        Does NOT attempt cleanup — logs a warning with the ID/prefix
        in case the ERP unexpectedly creates the entry. If the entry
        is accidentally created, it is tracked via CleanupTracker for
        manual purging.

        Args:
            invalid_payload: A payload designed to fail validation.
            name_prefix:     Prefix for tracking/logging.

        Returns:
            None (expected failure), or the response JSON if the ERP
            unexpectedly accepted the invalid payload.
        """
        result = self.client.create_entry(invalid_payload)

        if result is not None:
            unexpected_id = result.get("id", "unknown")
            unexpected_name = result.get("name", invalid_payload.get("name", "unknown"))
            self.tracker.track_accidental(
                id=unexpected_id,
                agent_name=unexpected_name,
            )
            log.warning(
                f"[AgentAPI] UNEXPECTED: Invalid payload was accepted! "
                f"id={unexpected_id} prefix='{name_prefix}'. "
                f"This entry must be manually purged. "
                f"No delete endpoint exists."
            )
        else:
            log.info(
                f"[AgentAPI] Validation error triggered as expected "
                f"for prefix='{name_prefix}'"
            )

        return result

    def assert_validation_error(
        self,
        field: str,
        expected_status: int = 400,
        expected_message_substring: str = "",
        accept_statuses: list = None,
    ) -> Dict:
        """
        Assert that the last API call returned a validation error
        for the specified field.

        Args:
            field:                       The field key expected to have the error
            expected_status:             Expected HTTP status code (default 400).
            expected_message_substring:  Substring expected in the error message.
            accept_statuses:             Optional list of acceptable HTTP status codes.

        Returns:
            Structured dict with status_code, field, error_messages, all_errors.
        """
        raw_resp = self.client._last_raw_response

        assert raw_resp is not None, (
            "No raw response available. Ensure create_and_expect_failure() "
            "or create_entry() was called before assert_validation_error()."
        )

        actual_status = raw_resp.status_code
        valid_statuses = {expected_status}
        if accept_statuses:
            valid_statuses.update(accept_statuses)
        assert actual_status in valid_statuses, (
            f"Expected HTTP {expected_status}"
            f" (acceptable: {sorted(valid_statuses)})"
            f", got {actual_status}. "
            f"Response body: {raw_resp.text[:500]}"
        )

        # Parse error body
        try:
            error_body = raw_resp.json()
        except Exception:
            error_body = {}

        all_errors = error_body.get("errors", [])
        if not all_errors and "message" in error_body:
            all_errors = [{"error_message": error_body["message"]}]

        field_errors = []
        for err in all_errors:
            err_field = err.get("field", err.get("field_key", ""))
            err_msg = err.get("error_message", str(err))
            if field is None:
                field_errors.append(err_msg)
            elif err_field == field or not err_field:
                field_errors.append(err_msg)

        if not field_errors:
            for err in all_errors:
                err_msg = err.get("error_message", str(err))
                if field in err_msg.lower():
                    field_errors.append(err_msg)

        assert len(field_errors) > 0, (
            f"No validation error found for field '{field}'. "
            f"All errors: {all_errors}. "
            f"Full response: {raw_resp.text[:500]}"
        )

        if expected_message_substring:
            found = any(
                expected_message_substring.lower() in msg.lower()
                for msg in field_errors
            )
            assert found, (
                f"Expected substring '{expected_message_substring}' not found "
                f"in error messages for field '{field}'. "
                f"Actual messages: {field_errors}"
            )

        return {
            "status_code": actual_status,
            "field": field,
            "error_messages": field_errors,
            "all_errors": all_errors,
            "raw_status": actual_status,
        }

    # ================================================================
    # Payload Generation
    # ================================================================

    def create_and_document(
        self,
        payload: Dict,
        field_being_tested: str,
        name_prefix: str = "DocAGT",
    ) -> Dict:
        """
        Send a payload and document whether the ERP accepts or rejects it.

        Exploratory test helper — the test PASSES regardless of outcome.
        If the ERP unexpectedly accepts a dangerous payload, the ID is
        tracked for manual cleanup and a warning is logged.

        Returns:
            Dict with "accepted", "result", "status_code", "field".
        """
        result = self.client.create_entry(payload)
        raw_resp = self.client._last_raw_response

        if result is not None:
            unexpected_id = result.get("id", "unknown")
            unexpected_name = result.get("name", payload.get("name", "unknown"))
            self.tracker.track_accidental(
                id=unexpected_id,
                agent_name=unexpected_name,
            )
            status_code = raw_resp.status_code if raw_resp else 201
            log.warning(
                f"[AgentAPI] EXPLORATORY: ERP ACCEPTED payload for "
                f"field='{field_being_tested}' prefix='{name_prefix}'. "
                f"id={unexpected_id} status={status_code}. "
                f"Entry tracked for manual cleanup."
            )
            return {
                "accepted": True,
                "result": result,
                "status_code": status_code,
                "field": field_being_tested,
            }
        else:
            status_code = raw_resp.status_code if raw_resp else 400
            log.info(
                f"[AgentAPI] EXPLORATORY: ERP REJECTED payload for "
                f"field='{field_being_tested}' prefix='{name_prefix}'. "
                f"status={status_code}"
            )
            return {
                "accepted": False,
                "result": None,
                "status_code": status_code,
                "field": field_being_tested,
            }

    def generate_unique_payload(
        self,
        agent_data: dict = None,
        name_prefix: str = "AutoAGT",
    ) -> Dict:
        """
        Generate a timestamped+UUID namespaced Agent API payload.

        Uses format: {prefix}_{timestamp}_{uuid8} to prevent
        collisions and enable manual cleanup identification.

        PAYLOAD STRUCTURE (verified 2026-06-11 from live API):
          The Agent screen uses a children[] stepper format with
          EXACT stepper names that must match the backend:
            children[0] = "Address Details"  (2 rows: Shipping + Billing)
            children[1] = "Payment Details"  (NOT "Additional Details"!)
            children[2] = "Bank Details"

          IMPORTANT: Using wrong stepper_name (e.g., "Additional Details"
          instead of "Payment Details") causes the record to be created
          but with broken children data, which makes GET return 500 and
          the UI show NoneType errors when trying to open the record.

        FIELD KEY MAPPING (from Agent schema):
          UI "Agent Name"   -> API "name"
          UI "Phone Number" -> API "mobile_no" (integer)
          UI "Email"        -> API "email_id"
          Address fields use same FK keys as Supplier/Customer
          (country_ref_id_id, state_ref_id_id, district_ref_id_id,
           sub_district_ref_id_id, village_ref_id_id)

        Args:
            agent_data:  Override data (merged with generated defaults).
            name_prefix: Prefix for the agent name.

        Returns:
            Complete JSON payload ready for POST.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]

        agent_name = f"{name_prefix} {timestamp} {uuid_short}"

        # Pick a random verified address chain for realistic data
        chain = random.choice(_ADDRESS_CHAINS)

        # Build the full payload using correct structure from live API:
        # Key fixes (2026-06-11):
        #   1. Stepper name "Payment Details" (not "Additional Details")
        #   2. Address needs full cascading chain (state, district, sub_district, village)
        #   3. Bank details needs bank_doc_id (required by schema)
        #   4. Address should have 2 rows (Shipping + Billing) like Supplier
        payload = {
            "id": "",
            "attribute_name": SCREEN_NAME,
            "party_ref_id": None,
            "copy_from_party": False,
            "name": agent_name,
            "mobile_no": int(generate_phone_number()),
            "email_id": generate_email(name_prefix.lower()),
            "status": True,
            "children": [
                # children[0] — Address Details (2 rows: Shipping + Billing)
                {
                    "stepper_name": "Address Details",
                    "is_stepper": True,
                    "details": [
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
                    ],
                    "children": [],
                },
                # children[1] — Payment Details (NOT "Additional Details"!)
                # Fields go on the stepper object itself, not in details[]
                {
                    "stepper_name": "Payment Details",
                    "is_stepper": True,
                    "payment_terms_ref_id": None,
                    "preferred_payment_method_ref_id": None,
                    "is_gst_set_off": False,
                    "details": [],
                    "children": [],
                },
                # children[2] — Bank Details
                {
                    "stepper_name": "Bank Details",
                    "is_stepper": True,
                    "details": [
                        {
                            "bank_name": generate_bank_name(),
                            "bank_branch_code": generate_branch(),
                            "bank_ifsc_code": generate_ifsc_code(),
                            "account_type": ACCOUNT_TYPE_CURRENT_ID,
                            "bank_account_holder_name": generate_account_holder_name(),
                            "bank_account_no": int(generate_account_number()),
                            "bank_doc_id": BANK_DOC_CANCELLED_CHEQUE_ID,
                            "bank_attachment_path": None,
                            "details": [],
                        }
                    ],
                    "children": [],
                },
            ],
        }

        # Merge with any overrides
        if agent_data:
            for key, value in agent_data.items():
                if isinstance(value, dict) and isinstance(payload.get(key), dict):
                    payload[key].update(value)
                elif isinstance(value, list) and isinstance(payload.get(key), list):
                    payload[key] = value
                else:
                    payload[key] = value

        return payload
