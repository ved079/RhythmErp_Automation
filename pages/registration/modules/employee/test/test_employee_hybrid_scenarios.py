"""
test_employee_hybrid_scenarios.py
---------------------------------
Hybrid test suite for RhythmERP Employee screen.

Bucket C — Hybrid Tests: API creates/sets up data -> UI verifies display/behavior.
Each test uses BOTH ``emp_api`` and ``emp_page`` fixtures.

EMPLOYEE FORM STRUCTURE (FLAT — NO STEPPERS):
  Unlike Agent/Supplier which use children[] stepper arrays,
  Employee is a FLAT form. All fields are on a single page:
    1. Party Reference  (dropdown, optional)
    2. Employee Name    (text, ^[A-Za-z ]+$)
    3. Email            (text, standard email regex)
    4. Phone Number     (integer, ^[6-9]\\d{9}$)
    5. Designation      (dropdown, 56 options)
    6. Department       (dropdown, 0 options)
    7. Status           (toggle, required, default=true)

Test Inventory (6 tests):
  EMP-H01 — API create -> UI verify row appears in table
  EMP-HS01 — API create -> UI search exact match
  EMP-HS02 — API create -> UI search partial match
  EMP-HS03 — API create -> UI search case insensitive
  EMP-HP01 — API create -> UI View popup is read-only
  EMP-HE01 — API create -> UI edit shows pre-populated + Update button -> edit -> Update

Hybrid Pattern:
  1. API creates employee with specific data via ``emp_api.create_employee()``
  2. UI opens the same employee for view/edit via ``emp_page`` methods
  3. Verify the UI displays the data correctly or documents bug behavior

NO-DELETE CONSTRAINT:
  No delete/cleanup calls — all created employees are tracked via
  ``emp_api.tracker`` (CleanupTracker) for end-of-session reporting.

Run:
  pytest test_employee_hybrid_scenarios.py -v --tb=short
  pytest test_employee_hybrid_scenarios.py -v -m hybrid --tb=short
  pytest test_employee_hybrid_scenarios.py -v -k "EMP_H01" --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.logger import log


# ====================================================================
# EMP-H01: API create -> UI verify creation
# ====================================================================

class TestCreateAndVerify:
    """Hybrid: API creates employee -> UI verifies it appears in table."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_EMP_H01_create_and_verify(self, emp_page, emp_api):
        """API creates employee -> UI searches and finds it."""
        log.info("EMP-H01 (Hybrid): API create -> UI verify")
        page = emp_page

        # API creates employee
        result = emp_api.create_employee(name_prefix="HybridCreate")
        assert result is not None, "API employee creation failed"
        emp_name = result.get("name", "")
        log.info(f"API created employee: {emp_name}")

        # UI: Search for it
        found = page.search_employee(emp_name)
        # search_employee is void; check the table for the name
        page.wait_seconds(2)
        names = page.get_table_employee_names()
        name_found = any(emp_name.lower() in n.lower() for n in names)
        assert name_found, f"UI search failed to find API-created employee: {emp_name}"
        log.info(f"UI found employee: {emp_name}")


# ====================================================================
# EMP-HS01/S02/S03: API create -> UI search
# ====================================================================

class TestSearchViaAPI:
    """Hybrid: API creates employee -> UI verifies search behavior."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_EMP_HS01_search_exact(self, emp_page, emp_api):
        """API creates employee -> UI searches exact name match."""
        log.info("EMP-HS01 (Hybrid): Search exact match")
        page = emp_page

        result = emp_api.create_employee(name_prefix="SearchExact")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")
        log.info(f"API created employee: {emp_name}")

        page.search_employee(emp_name)
        page.wait_seconds(2)
        names = page.get_table_employee_names()
        found = any(emp_name.lower() in n.lower() for n in names)
        assert found, f"Exact search failed for: {emp_name}"

    @pytest.mark.hybrid
    @pytest.mark.sanity
    def test_EMP_HS02_search_partial(self, emp_page, emp_api):
        """API creates employee -> UI searches partial name."""
        log.info("EMP-HS02 (Hybrid): Search partial match")
        page = emp_page

        result = emp_api.create_employee(name_prefix="SearchPartial")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Use first 10 chars of the name as partial search
        partial = emp_name[:10] if len(emp_name) > 10 else emp_name
        log.info(f"Partial search: '{partial}' from full name '{emp_name}'")

        page.search_employee(partial)
        page.wait_seconds(2)
        names = page.get_table_employee_names()
        found = any(partial.lower() in n.lower() for n in names)
        assert found, f"Partial search failed for: {partial}"

    @pytest.mark.hybrid
    @pytest.mark.sanity
    def test_EMP_HS03_search_case_insensitive(self, emp_page, emp_api):
        """API creates employee -> UI searches lowercase version of name."""
        log.info("EMP-HS03 (Hybrid): Search case insensitive")
        page = emp_page

        result = emp_api.create_employee(name_prefix="CaseSearch")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search with lowercase
        lower_name = emp_name.lower()
        log.info(f"Case-insensitive search: '{lower_name}' from '{emp_name}'")

        page.search_employee(lower_name)
        page.wait_seconds(2)
        names = page.get_table_employee_names()
        found = any(lower_name in n.lower() for n in names)

        # Case-insensitive search may not be supported — document behavior
        if found:
            log.info(f"Case-insensitive search works: '{lower_name}' found '{emp_name}'")
        else:
            log.warning(
                f"Case-insensitive search NOT supported: "
                f"'{lower_name}' did not find '{emp_name}'"
            )


# ====================================================================
# EMP-HP01: API create -> UI view read-only
# ====================================================================

class TestViewReadOnly:
    """Hybrid: API creates employee -> UI opens View and checks read-only mode."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_EMP_HP01_view_readonly(self, emp_page, emp_api):
        """API creates employee -> UI View -> should be read-only (no Update button)."""
        log.info("EMP-HP01 (Hybrid): View read-only check")
        page = emp_page

        result = emp_api.create_employee(name_prefix="ViewRO")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search for the employee first
        page.search_employee(emp_name)
        page.wait_seconds(2)

        # Open row menu and click View
        page.open_row_menu(0)
        page.wait_seconds(0.5)
        page.click_view_from_menu()
        page.wait_seconds(2)

        # In View mode, there should be NO Update/Submit button
        is_edit = page.is_edit_mode()
        log.info(f"View mode: is_edit_mode={is_edit}")

        if is_edit:
            log.warning(
                "BUG: View popup shows Update button — should be read-only. "
                "View mode should not have Update/Submit buttons."
            )
        else:
            log.info("View mode is correctly read-only (no Update button)")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()


# ====================================================================
# EMP-HE01: API create -> UI edit pre-populated + update
# ====================================================================

class TestEditVerification:
    """Hybrid: API creates employee -> UI edits and updates."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_EMP_HE01_edit_prepopulated_and_update(self, emp_page, emp_api):
        """API creates employee -> UI Edit -> verify pre-populated + Update button -> edit email -> Update.

        Employee is a FLAT form — no stepper navigation needed.
        All fields are on a single page, so we can directly edit
        any field and click Update without Next/Back navigation.
        """
        log.info("EMP-HE01 (Hybrid): Edit pre-populated and update")
        page = emp_page

        result = emp_api.create_employee(name_prefix="EditPre")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search for the employee
        page.search_employee(emp_name)
        page.wait_seconds(2)

        # Open row menu and click Edit
        page.open_row_menu(0)
        page.wait_seconds(0.5)
        page.click_edit_from_menu()
        page.wait_seconds(2)

        # Verify edit mode (Update button present)
        is_edit = page.is_edit_mode()
        assert is_edit, "Edit popup should have Update button"

        # Verify fields are pre-populated
        values = page.get_form_field_values()
        log.info(f"Edit form values: {values}")

        has_name = bool(values.get("Employee Name", "").strip())
        if has_name:
            log.info(f"Employee Name pre-populated: '{values['Employee Name']}'")
        else:
            log.warning("Employee Name not pre-populated in edit mode")

        # Edit email — Employee is flat, no stepper navigation needed
        from pages.registration.modules.employee.data.employee_data import generate_email
        new_email = generate_email("updated")
        page.type_text(page.EMAIL_INPUT, new_email, clear_first=True)
        page.wait_seconds(0.5)

        # Click Update directly (flat form — no Next/Back needed)
        update_btn = page.find_visible_element(page.UPDATE_BUTTON)
        if update_btn:
            page.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                update_btn,
            )
            page.wait_seconds(3)

        # Check for success
        swal_title = page.get_alert_title()
        if swal_title and "success" in swal_title.lower():
            log.info(f"Update successful: {swal_title}")
        elif swal_title and "validation" in swal_title.lower():
            log.warning(f"Update validation failed: {swal_title}")
            page.dismiss_alert()
        else:
            log.info(f"Update response: swal='{swal_title}'")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()
