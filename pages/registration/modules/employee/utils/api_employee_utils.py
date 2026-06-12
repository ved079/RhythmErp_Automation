"""
api_employee_utils.py
---------------------
Employee-specific API wrapper for hybrid test migration.

Wraps the generic RhythmERPAPIClient with Employee-screen helpers:
  - create_employee()          — happy-path creation with ID tracking
  - get_employee()             — fetch single employee by ID
  - update_employee()          — update via PUT (standard REST)
  - search_employees()         — list/search with pagination
  - assert_validation_error()  — validate server-side error responses
  - create_and_expect_failure() — send invalid payload, track accidental creation
  - create_and_document()      — exploratory test helper
  - generate_unique_payload()  — random letter namespaced payload
  - track_created_id()         — record IDs via CleanupTracker
  - generate_cleanup_report()  — export tracked IDs as JSON/CSV

NO-DELETE CONSTRAINT:
  The ERP has NO delete endpoint, no delete button, and no soft-delete
  via status=False. Cleanup = tracking + reporting for manual purge.
  This module will NEVER contain delete_employee() or cleanup_all().

EMPLOYEE SCREEN STRUCTURE (FLAT — NO STEPPERS):
  Unlike Agent/Supplier/Customer which use children[] stepper arrays,
  Employee is a FLAT form — all fields go at the root level:
    {
      "id": "",
      "attribute_name": "Employee",
      "party_ref_id": null,
      "name": "Rajesh Sharma",
      "email_id": "rajesh.sharma@gmail.com",
      "mobile_no": 9876543210,
      "designation": 2,
      "department": null,
      "status": true,
      "details": [],
      "children": []
    }

FIELD KEY MAPPING (from Employee schema):
  UI "Employee Name" -> API "name"        (string, REQUIRED, pattern: ^[A-Za-z ]+$)
  UI "Email"         -> API "email_id"    (string, REQUIRED)
  UI "Phone Number"  -> API "mobile_no"   (integer, REQUIRED)
  UI "Designation"   -> API "designation" (FK, REQUIRED)
  UI "Department"    -> API "department"  (FK, optional — 0 options currently)
  UI "Status"        -> API "status"      (boolean, REQUIRED)

NAME VALIDATION:
  Server only accepts letters and spaces in the name field.
  Pattern: ^[A-Za-z ]+$
  No digits, no underscores, no special characters.
  Spaces ARE allowed (e.g., "Rajesh Sharma" is valid).

UPDATE METHOD:
  Employee uses PUT for updates (unlike Agent which uses POST).
  PUT /core/dynamic-screen-wrapper/Employee/{id}/

KNOWN BUGS:
  - SQL injection and XSS payloads are accepted without sanitization in name field
"""

import json
import csv
import os
import random
from datetime import datetime
from typing import Dict, List, Optional
import string

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.employee.api.endpoints import SCREEN_NAME
from pages.registration.modules.employee.data.employee_data import (
    generate_employee_name,
    generate_phone,
    generate_email,
    generate_designation_id,
)
from pages.registration.modules.employee.utils.employee_cleanup import (
    CleanupTracker,
    CreatedRecord,
)


# ──────────────────────────────────────────────
# FK IDs for tenant 681 (from API dropdown endpoints)
# ──────────────────────────────────────────────

# Designation — 56 verified options on tenant 681
# (Subset used for random selection — see employee_data.py for full list)
DESIGNATION_DEFAULT_ID = 2  # Farm Supervisor

# Department — 0 options currently
DEPARTMENT_NONE = None


class EmployeeAPIUtils:
    """
    Employee-specific API utility for the hybrid test migration.

    Each instance wraps a single RhythmERPAPIClient and a CleanupTracker
    for recording created employee IDs.

    Usage:
        api = EmployeeAPIUtils()
        api.client.login()

        # Create an employee
        result = api.create_employee()
        assert result is not None

        # Validate an error
        api.create_and_expect_failure(invalid_payload)
        api.assert_validation_error(
            field="name",
            expected_status=400,
            expected_message_substring="Invalid Name",
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

    def create_employee(
        self,
        employee_data: dict = None,
        name_prefix: str = "AutoEMP",
        retries: int = 2,
    ) -> Optional[Dict]:
        """
        Create an employee via API and track the resulting ID.

        Args:
            employee_data:  Override data dict (merged with defaults).
            name_prefix:    Prefix for auto-generated employee name.
                            Format: {prefix} {rand_letters}
                            Only letters/spaces allowed — no digits/special chars.
            retries:        Number of retries on transient failures (default 2).

        Returns:
            Response JSON dict on success, None on failure.
            The created ID is automatically tracked via CleanupTracker.
        """
        for attempt in range(retries + 1):
            payload = self.generate_unique_payload(
                employee_data=employee_data,
                name_prefix=name_prefix,
            )

            result = self.client.create_entry(payload)

            if result is not None:
                created_id = result.get("id")
                emp_name = result.get("name", payload.get("name", "unknown"))
                self.tracker.track(
                    id=created_id,
                    employee_name=emp_name,
                    payload_summary=f"Created via API with prefix={name_prefix}",
                )
                log.info(
                    f"[EmployeeAPI] Created employee id={created_id} "
                    f"name='{emp_name}'"
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
                    f"[EmployeeAPI] 'Invalid Name' on attempt {attempt + 1}/{retries + 1}, "
                    f"retrying with new name..."
                )
                import time
                time.sleep(1)
                continue

            log.warning(
                f"[EmployeeAPI] Failed to create employee "
                f"name='{payload.get('name', 'unknown')}'"
            )
            return None

        return None

    def get_employee(self, employee_id: int) -> Optional[Dict]:
        """Fetch a single employee by ID.

        Args:
            employee_id: The employee's database ID.

        Returns:
            Response JSON dict on success, None on failure.
        """
        return self.client.get_entry(SCREEN_NAME, employee_id)

    def update_employee(
        self, employee_id: int, payload: Dict
    ) -> Optional[Dict]:
        """
        Update an existing employee via PUT.

        The Employee screen uses the standard REST pattern —
        PUT for updates (unlike Agent which uses POST).

        Args:
            employee_id:  The employee's database ID.
            payload:      Complete JSON payload with updated fields.
                          Must include "attribute_name": "Employee".

        Returns:
            Response JSON dict on success, None on failure.
        """
        payload.setdefault("attribute_name", SCREEN_NAME)
        payload.setdefault("id", employee_id)
        return self.client.update_entry(employee_id, payload)

    def search_employees(
        self,
        search: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> Optional[Dict]:
        """
        Search/list employees with pagination.

        Args:
            search:    Search string (employee name, email, etc.).
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
        name_prefix: str = "FailEMP",
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
                employee_name=unexpected_name,
            )
            log.warning(
                f"[EmployeeAPI] UNEXPECTED: Invalid payload was accepted! "
                f"id={unexpected_id} prefix='{name_prefix}'. "
                f"This entry must be manually purged. "
                f"No delete endpoint exists."
            )
        else:
            log.info(
                f"[EmployeeAPI] Validation error triggered as expected "
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
        # Also capture the "error" key (used by 500 DB-level errors)
        if "error" in error_body and error_body["error"]:
            all_errors.append({"error_message": error_body["error"]})

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
        name_prefix: str = "DocEMP",
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
                employee_name=unexpected_name,
            )
            status_code = raw_resp.status_code if raw_resp else 201
            log.warning(
                f"[EmployeeAPI] EXPLORATORY: ERP ACCEPTED payload for "
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
                f"[EmployeeAPI] EXPLORATORY: ERP REJECTED payload for "
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
        employee_data: dict = None,
        name_prefix: str = "AutoEMP",
    ) -> Dict:
        """
        Generate a unique Employee API payload.

        Uses format: {FirstName} {LastName} for realistic, unique names.
        Server only accepts letters and spaces in the name field —
        no digits, no special characters (pattern: ^[A-Za-z ]+$).

        EMPLOYEE PAYLOAD STRUCTURE (flat form — no steppers):
          Unlike Agent/Supplier which use children[] stepper arrays,
          Employee is a FLAT form. All fields go at the root level.
          No children[] or details[] arrays needed (both are empty []).

        FIELD KEY MAPPING:
          UI "Employee Name" -> API "name"        (string, REQUIRED, ^[A-Za-z ]+$)
          UI "Email"         -> API "email_id"    (string, REQUIRED)
          UI "Phone Number"  -> API "mobile_no"   (integer, REQUIRED)
          UI "Designation"   -> API "designation" (FK integer, REQUIRED)
          UI "Department"    -> API "department"  (FK integer, optional — null = skip)
          UI "Status"        -> API "status"      (boolean, REQUIRED)

        Args:
            employee_data:  Override data (merged with generated defaults).
            name_prefix:    Prefix for the employee name.

        Returns:
            Complete JSON payload ready for POST.
        """
        # Generate a realistic Indian name with random letters for uniqueness
        # Pattern: {FirstName} {LastName} — matches ^[A-Za-z ]+$
        first_names = [
            "Rajesh", "Amit", "Suresh", "Priya", "Sunita",
            "Vikram", "Meera", "Kiran", "Neha", "Rahul",
            "Swati", "Deepak", "Pooja", "Manoj", "Anita",
        ]
        last_names = [
            "Sharma", "Patel", "Kumar", "Singh", "Gupta",
            "Jain", "Shah", "Reddy", "Nair", "Desai",
            "Kulkarni", "Rao", "Hegde", "Varma", "Naik",
        ]

        # Add random letter suffix for guaranteed uniqueness
        rand_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
        first = random.choice(first_names)
        last = random.choice(last_names)
        employee_name = f"{name_prefix} {first} {last} {rand_suffix}"

        # Pick a random designation from the verified pool
        designation_id = generate_designation_id()

        # Build the flat payload (no children[] stepper structure)
        payload = {
            "id": "",
            "attribute_name": SCREEN_NAME,
            "party_ref_id": None,  # Skip by default — auto-patches name/email/phone
            "name": employee_name,
            "email_id": generate_email(name_prefix.lower()),
            "mobile_no": generate_phone(),
            "designation": designation_id,
            "department": None,  # No options available currently
            "status": True,
            "details": [],
            "children": [],
        }

        # Merge with any overrides
        if employee_data:
            for key, value in employee_data.items():
                if isinstance(value, dict) and isinstance(payload.get(key), dict):
                    payload[key].update(value)
                elif isinstance(value, list) and isinstance(payload.get(key), list):
                    payload[key] = value
                else:
                    payload[key] = value

        return payload
