"""
api_customer_utils.py
---------------------
Customer-specific API wrapper for hybrid test migration.

Wraps the generic RhythmERPAPIClient with Customer-screen helpers:
  - create_customer()        — happy-path creation with ID tracking
  - get_customer()           — fetch single customer by ID
  - update_customer()        — update via PUT
  - search_customers()       — list/search with pagination
  - assert_validation_error() — validate server-side error responses
  - create_and_expect_failure() — send invalid payload, track accidental creation
  - generate_unique_payload() — timestamp+UUID namespaced payload
  - track_created_id()       — record IDs via CleanupTracker
  - generate_cleanup_report() — export tracked IDs as JSON/CSV

NO-DELETE CONSTRAINT:
  The ERP has NO delete endpoint, no delete button, and no soft-delete
  via status=False. Cleanup = tracking + reporting for manual purge.
  This module will NEVER contain delete_customer() or cleanup_all().

Thread Safety:
  This module reads _last_raw_response from RhythmERPAPIClient, which
  is NOT thread-safe. See WARNING comments below.

URL Convention:
  All URL paths come from api/endpoints.py — no hardcoded paths.
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.customer.api.endpoints import SCREEN_NAME
from pages.registration.modules.customer.data.customer_data import (
    build_customer_api_payload,
    generate_valid_customer_data,
    generate_random_fk_ids,
)
from pages.registration.modules.customer.utils.customer_cleanup import (
    CleanupTracker,
    CreatedRecord,
)


class CustomerAPIUtils:
    """
    Customer-specific API utility for the hybrid test migration.

    Each instance wraps a single RhythmERPAPIClient and a CleanupTracker
    for recording created customer IDs.

    Usage:
        api = CustomerAPIUtils()
        api.client.login()

        # Create a customer
        result = api.create_customer()
        assert result is not None

        # Validate an error
        api.create_and_expect_failure(invalid_payload)
        api.assert_validation_error(
            field="name",
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

    def create_customer(
        self,
        customer_data: dict = None,
        dropdown_ids: dict = None,
        name_prefix: str = "AutoCust",
    ) -> Optional[Dict]:
        """
        Create a customer via API and track the resulting ID.

        Args:
            customer_data: Override data dict (merged with defaults).
            dropdown_ids:  Override FK IDs (merged with defaults).
            name_prefix:   Prefix for auto-generated company name.
                           Format: {prefix}_{timestamp}_{uuid8}

        Returns:
            Response JSON dict on success, None on failure.
            The created ID is automatically tracked via CleanupTracker.
        """
        payload = self.generate_unique_payload(
            customer_data=customer_data,
            dropdown_ids=dropdown_ids,
            name_prefix=name_prefix,
        )

        result = self.client.create_entry(payload)

        if result is not None:
            created_id = result.get("id")
            company_name = payload.get("name", "unknown")
            self.tracker.track(
                id=created_id,
                company_name=company_name,
                payload_summary=f"Created via API with prefix={name_prefix}",
            )
            log.info(
                f"[CustomerAPI] Created customer id={created_id} "
                f"name='{company_name}'"
            )
        else:
            log.warning(
                f"[CustomerAPI] Failed to create customer "
                f"name='{payload.get('name', 'unknown')}'"
            )

        return result

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """
        Fetch a single customer by ID.

        Args:
            customer_id: The customer's database ID.

        Returns:
            Complete customer dict with all fields and nested structures,
            or None if not found.
        """
        return self.client.get_entry(SCREEN_NAME, customer_id)

    def update_customer(
        self, customer_id: int, payload: Dict
    ) -> Optional[Dict]:
        """
        Update an existing customer via PUT.

        Args:
            customer_id: The customer's database ID.
            payload: Complete JSON payload with updated fields.
                     Must include "attribute_name": "Customer".

        Returns:
            Response JSON dict on success, None on failure.
        """
        payload.setdefault("attribute_name", SCREEN_NAME)
        return self.client.update_entry(customer_id, payload)

    def search_customers(
        self,
        search: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> Optional[Dict]:
        """
        Search/list customers with pagination.

        Args:
            search:     Search string (company name, PAN, etc.).
            page:       Page number.
            page_size:  Items per page.

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
        name_prefix: str = "FailCust",
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
            # ERP unexpectedly accepted invalid data
            unexpected_id = result.get("id", "unknown")
            unexpected_name = invalid_payload.get("name", "unknown")
            self.tracker.track_accidental(
                id=unexpected_id,
                company_name=unexpected_name,
            )
            log.warning(
                f"[CustomerAPI] UNEXPECTED: Invalid payload was accepted! "
                f"id={unexpected_id} prefix='{name_prefix}'. "
                f"This entry must be manually purged. "
                f"No delete endpoint exists."
            )
        else:
            log.info(
                f"[CustomerAPI] Validation error triggered as expected "
                f"for prefix='{name_prefix}'"
            )

        return result

    def assert_validation_error(
        self,
        field: str,
        expected_status: int = 400,
        expected_message_substring: str = "",
    ) -> Dict:
        """
        Assert that the last API call returned a validation error
        for the specified field.

        Reads _last_raw_response from the API client to inspect
        the full HTTP response including status code and error body.

        # WARNING: _last_raw_response is NOT thread-safe. Concurrent API calls may
        # overwrite this value. Do not run API validation tests in parallel until
        # the base client is refactored to return (result, response) tuples.

        Args:
            field:                       The field key expected to have the error
                                         (e.g., "name", "pan_no", "email_id").
            expected_status:             Expected HTTP status code (default 400).
            expected_message_substring:  Substring expected in the error message
                                         for the field (empty string = skip check).

        Returns:
            Structured dict with:
              - "status_code": HTTP status code from the response
              - "field": The field that was checked
              - "error_messages": List of error message strings for the field
              - "all_errors": Full error list from the response body
              - "raw_status": The actual HTTP status code received

        Raises:
            AssertionError: If any of the following are false:
              - _last_raw_response is not None
              - HTTP status code matches expected_status
              - The specified field appears in the error response
              - expected_message_substring is found in the field's error message
                (if provided)
        """
        # WARNING: _last_raw_response is NOT thread-safe. Concurrent API calls may
        # overwrite this value. Do not run API validation tests in parallel until
        # the base client is refactored to return (result, response) tuples.
        raw_resp = self.client._last_raw_response

        assert raw_resp is not None, (
            "No raw response available. Ensure create_and_expect_failure() "
            "or create_entry() was called before assert_validation_error(). "
            "Also check that _last_raw_response was not overwritten by a "
            "concurrent API call."
        )

        actual_status = raw_resp.status_code
        assert actual_status == expected_status, (
            f"Expected HTTP {expected_status}, got {actual_status}. "
            f"Response body: {raw_resp.text[:500]}"
        )

        # Parse error body
        try:
            error_body = raw_resp.json()
        except Exception:
            error_body = {}

        # Extract errors — handle both {"errors": [...]} and flat formats
        all_errors = error_body.get("errors", [])
        if not all_errors and "message" in error_body:
            all_errors = [{"error_message": error_body["message"]}]

        # Find errors matching the target field
        field_errors = []
        for err in all_errors:
            err_field = err.get("field", err.get("field_key", ""))
            err_msg = err.get("error_message", str(err))
            if err_field == field or not err_field:
                # Match if field matches OR if field is empty (generic error)
                field_errors.append(err_msg)

        # If no field-specific errors found, check all messages for field name
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

        # Check expected message substring if provided
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

    def generate_unique_payload(
        self,
        customer_data: dict = None,
        dropdown_ids: dict = None,
        name_prefix: str = "AutoCust",
    ) -> Dict:
        """
        Generate a timestamped+UUID namespaced Customer API payload.

        Uses format: {prefix}_{timestamp}_{uuid8} to prevent
        collisions and enable manual cleanup identification.

        Args:
            customer_data: Override data (merged with generated defaults).
            dropdown_ids:  Override FK IDs (merged with defaults).
            name_prefix:   Prefix for the company name.

        Returns:
            Complete JSON payload ready for POST (uses endpoints.py paths).
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]

        # Generate base data
        base_data = generate_valid_customer_data(name_prefix=name_prefix)
        # Override company name with timestamped+UUID version
        base_data["company_name"] = (
            f"{name_prefix}_{timestamp}_{uuid_short}"
        )

        # Merge with any overrides
        if customer_data:
            base_data.update(customer_data)

        # Generate random FK IDs
        fk_ids = generate_random_fk_ids()
        if dropdown_ids:
            fk_ids.update(dropdown_ids)

        return build_customer_api_payload(
            customer_data=base_data,
            dropdown_ids=fk_ids,
        )

    # ================================================================
    # Legacy Compatibility (kept for backward compat)
    # ================================================================

    def track_created_id(
        self,
        customer_id,
        company_name: str = "",
        payload: Dict = None,
    ):
        """
        Record a created customer ID for cleanup reporting.
        Delegates to CleanupTracker.track().

        Since the ERP has NO delete endpoint, we track all created
        IDs and generate reports for manual database purging.

        Args:
            customer_id:  The database ID returned by the API.
            company_name: The company name for easy identification.
            payload:      The full payload used (for audit trail).
        """
        self.tracker.track(
            id=customer_id,
            company_name=company_name,
            payload_summary="Created via API",
        )

    def generate_cleanup_report(
        self,
        output_path: str = None,
        fmt: str = "json",
    ) -> str:
        """
        Generate a cleanup report of all tracked customer IDs.
        Delegates to CleanupTracker.generate_reports().

        Args:
            output_path: File path for the report. If None, auto-generates.
            fmt:         Output format — "json" or "csv".

        Returns:
            Absolute path to the generated report file.
        """
        if output_path:
            output_dir = os.path.dirname(output_path)
        else:
            output_dir = None

        paths = self.tracker.generate_reports(output_dir=output_dir)

        if fmt == "json" and "json" in paths:
            return paths["json"]
        elif fmt == "csv" and "csv" in paths:
            return paths["csv"]
        return ""

    @property
    def tracked_count(self) -> int:
        """Number of customer IDs currently tracked."""
        return self.tracker.count

    @property
    def tracked_ids(self) -> List[Dict]:
        """Copy of the tracked IDs list."""
        return [
            {"id": r.id, "company_name": r.company_name,
             "timestamp": r.timestamp, "prefix": r.prefix}
            for r in self.tracker.records
        ]
