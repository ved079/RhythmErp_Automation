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

ZERO FK POOLS:
  Unlike Supplier/Customer, Agent has no FK pool system. All dropdown
  values (Country, State, Account Type, etc.) are hardcoded from known
  tenant 681 data. The generate_unique_payload() uses these fixed values.
"""

import json
import csv
import os
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
    generate_pin_code,
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
# Hardcoded dropdown values for tenant 681
# (Agent has zero FK pools — these are fixed)
# ──────────────────────────────────────────────

# Address step dropdown defaults
DEFAULT_ADDRESS_TYPE = "Permanent"
DEFAULT_COUNTRY = "India"
DEFAULT_STATE = "Maharashtra"
DEFAULT_DISTRICT = "Pune"
DEFAULT_TALUKA = "Haveli"

# Payment step dropdown defaults (optional — no defaults needed)

# Bank step dropdown defaults
DEFAULT_ACCOUNT_TYPE = "Current"


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
    ) -> Optional[Dict]:
        """
        Create an agent via API and track the resulting ID.

        Args:
            agent_data:  Override data dict (merged with defaults).
            name_prefix: Prefix for auto-generated agent name.
                         Format: {prefix}_{timestamp}_{uuid8}

        Returns:
            Response JSON dict on success, None on failure.
            The created ID is automatically tracked via CleanupTracker.
        """
        payload = self.generate_unique_payload(
            agent_data=agent_data,
            name_prefix=name_prefix,
        )

        result = self.client.create_entry(payload)

        if result is not None:
            created_id = result.get("id")
            agent_name = payload.get("agent_name", "unknown")
            self.tracker.track(
                id=created_id,
                agent_name=agent_name,
                payload_summary=f"Created via API with prefix={name_prefix}",
            )
            log.info(
                f"[AgentAPI] Created agent id={created_id} "
                f"name='{agent_name}'"
            )
        else:
            log.warning(
                f"[AgentAPI] Failed to create agent "
                f"name='{payload.get('agent_name', 'unknown')}'"
            )

        return result

    def get_agent(self, agent_id: int) -> Optional[Dict]:
        """Fetch a single agent by ID."""
        return self.client.get_entry(SCREEN_NAME, agent_id)

    def update_agent(
        self, agent_id: int, payload: Dict
    ) -> Optional[Dict]:
        """
        Update an existing agent via POST.

        The ERP's dynamic-screen-wrapper uses POST for updates —
        PUT returns HTTP 405 (Method Not Allowed).

        Args:
            agent_id:  The agent's database ID.
            payload:   Complete JSON payload with updated fields.
                       Must include "attribute_name": "Agent".

        Returns:
            Response JSON dict on success, None on failure.
        """
        payload.setdefault("attribute_name", SCREEN_NAME)
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
            unexpected_name = invalid_payload.get("agent_name", "unknown")
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
            unexpected_name = payload.get("agent_name", "unknown")
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

        Args:
            agent_data:  Override data (merged with generated defaults).
            name_prefix: Prefix for the agent name.

        Returns:
            Complete JSON payload ready for POST.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]

        agent_name = f"{name_prefix}_{timestamp}_{uuid_short}"

        # Build the full payload
        payload = {
            "attribute_name": SCREEN_NAME,
            "agent_name": agent_name,
            "phone_number": generate_phone_number(),
            "email": generate_email(name_prefix.lower()),
            "status": True,
            "screenmatlistingdata_set": [
                {
                    "address_type": DEFAULT_ADDRESS_TYPE,
                    "country": DEFAULT_COUNTRY,
                    "state": DEFAULT_STATE,
                    "district": DEFAULT_DISTRICT,
                    "taluka": DEFAULT_TALUKA,
                    "village": "",
                    "address": generate_address(),
                    "pin_code": generate_pin_code(),
                    "gst_number": generate_gst(),
                }
            ],
            "payment_details": {
                "payment_terms": "",
                "preferred_payment_method": "",
            },
            "bank_details": [
                {
                    "bank_name": generate_bank_name(),
                    "branch": generate_branch(),
                    "ifsc_code": generate_ifsc_code(),
                    "account_type": DEFAULT_ACCOUNT_TYPE,
                    "account_holder_name": generate_account_holder_name(),
                    "account_number": generate_account_number(),
                }
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
