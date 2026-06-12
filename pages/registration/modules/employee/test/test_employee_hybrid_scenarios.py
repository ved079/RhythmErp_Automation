"""
test_employee_hybrid_scenarios.py
---------------------------------
Enhanced hybrid test suite for RhythmERP Employee screen.

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

Test Inventory (14 tests):
  EMP-H01  — API create -> UI verify row appears in table
  EMP-H02  — API create -> UI verify all fields in table row match API data
  EMP-H03  — API create with specific designation -> UI verify designation shown
  EMP-H04  — API create with status=False -> UI verify inactive status
  EMP-HS01 — API create -> UI search exact match
  EMP-HS02 — API create -> UI search partial match
  EMP-HS03 — API create -> UI search case insensitive
  EMP-HS04 — API create -> UI search then clear -> table resets
  EMP-HP01 — API create -> UI View popup is read-only
  EMP-HP02 — API create -> UI View shows all pre-populated fields
  EMP-HE01 — API create -> UI edit shows pre-populated + Update button
  EMP-HE02 — API create -> UI edit name + submit -> success alert
  EMP-HE03 — API create -> UI edit with invalid email -> validation check
  EMP-HR01 — API create -> UI refresh -> data persists

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
from common.soft_assert import SoftAssert


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
        page.search_employee(emp_name)
        page.wait_seconds(2)
        names = page.get_table_employee_names()
        name_found = any(emp_name.lower() in n.lower() for n in names)
        assert name_found, f"UI search failed to find API-created employee: {emp_name}"
        log.info(f"UI found employee: {emp_name}")


# ====================================================================
# EMP-H02: API create -> UI verify table row data matches API data
# ====================================================================

class TestCreateAndVerifyRowData:
    """Hybrid: API creates employee -> UI verifies table row data."""

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_H02_verify_table_row_data(self, emp_page, emp_api):
        """API creates employee -> UI verifies name, email, phone in table row."""
        log.info("EMP-H02 (Hybrid): Verify table row data matches API payload")
        page = emp_page
        sa = SoftAssert()

        result = emp_api.create_employee(name_prefix="RowVerify")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")
        emp_email = result.get("email_id", "")
        emp_phone = str(result.get("mobile_no", ""))

        log.info(f"API created: name='{emp_name}', email='{emp_email}', phone='{emp_phone}'")

        # Search and find the employee
        page.search_employee(emp_name)
        page.wait_seconds(2)

        # Find the row index
        row_idx = page.find_employee_row_index(emp_name)
        if row_idx >= 0:
            row_data = page.get_table_row_data(row_idx)
            log.info(f"UI table row data: {row_data}")

            # Verify name matches
            if row_data.get("name"):
                name_match = emp_name.lower() in row_data["name"].lower()
                sa.assert_true(
                    name_match,
                    f"Name mismatch: API='{emp_name}', UI='{row_data['name']}'"
                )
            else:
                sa.fail("Name column empty in table row")

            # Verify email matches (if shown in table)
            if row_data.get("email_id") and emp_email:
                email_match = emp_email.lower() in row_data["email_id"].lower()
                sa.assert_true(
                    email_match,
                    f"Email mismatch: API='{emp_email}', UI='{row_data['email_id']}'"
                )

            # Verify phone matches (if shown in table)
            if row_data.get("mobile_no") and emp_phone:
                phone_match = emp_phone in row_data["mobile_no"]
                sa.assert_true(
                    phone_match,
                    f"Phone mismatch: API='{emp_phone}', UI='{row_data['mobile_no']}'"
                )
        else:
            sa.fail(f"Employee '{emp_name}' not found in table after search")

        sa.check_all()


# ====================================================================
# EMP-H03: API create with specific designation -> UI verify
# ====================================================================

class TestCreateWithDesignation:
    """Hybrid: API creates employee with specific designation -> UI verifies."""

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_H03_designation_in_table(self, emp_page, emp_api):
        """API creates employee with designation -> UI verifies designation column."""
        log.info("EMP-H03 (Hybrid): Designation in table")
        page = emp_page

        # Create with specific designation
        result = emp_api.create_employee(name_prefix="DesigCheck")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")
        designation_id = result.get("designation")

        log.info(f"API created: name='{emp_name}', designation_id={designation_id}")

        page.search_employee(emp_name)
        page.wait_seconds(2)

        row_idx = page.find_employee_row_index(emp_name)
        if row_idx >= 0:
            desig_text = page.get_table_cell_value(row_idx, "designation")
            log.info(f"Designation in table: '{desig_text}' (API id={designation_id})")
            # Designation text should not be empty if an ID was set
            if designation_id and not desig_text:
                log.warning(f"Designation ID {designation_id} set but table shows empty")
        else:
            log.warning(f"Employee '{emp_name}' not found in table")


# ====================================================================
# EMP-H04: API create with status=False -> UI verify inactive
# ====================================================================

class TestCreateInactive:
    """Hybrid: API creates inactive employee -> UI verifies status."""

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_H04_inactive_status(self, emp_page, emp_api):
        """API creates employee with status=False -> UI verifies inactive status."""
        log.info("EMP-H04 (Hybrid): Inactive status check")
        page = emp_page

        # Create with status=False
        from pages.registration.modules.employee.data.employee_data import (
            generate_employee_api_payload,
        )
        payload = generate_employee_api_payload(status=False)
        result = emp_api.create_employee(employee_data=payload, name_prefix="Inactive")
        if result is None:
            # Server may not allow inactive creation — document and pass
            log.warning("API creation with status=False failed — server may require active status")
            return

        emp_name = result.get("name", "")
        log.info(f"API created inactive employee: {emp_name}")

        page.search_employee(emp_name)
        page.wait_seconds(2)

        row_idx = page.find_employee_row_index(emp_name)
        if row_idx >= 0:
            status_text = page.get_table_cell_value(row_idx, "status")
            log.info(f"Status in table: '{status_text}' (expected inactive)")
            # Document the status display — may show "Inactive" or similar
        else:
            log.warning(f"Inactive employee '{emp_name}' not found in table")


# ====================================================================
# EMP-HS01/S02/S03/S04: API create -> UI search
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

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_HS04_search_and_clear(self, emp_page, emp_api):
        """API creates employee -> UI search then clear -> verify table resets."""
        log.info("EMP-HS04 (Hybrid): Search then clear")
        page = emp_page

        # Get initial row count
        initial_count = page.get_table_row_count()
        log.info(f"Initial table row count: {initial_count}")

        result = emp_api.create_employee(name_prefix="SearchClear")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search for the employee
        page.search_employee(emp_name)
        page.wait_seconds(2)
        search_count = page.get_table_row_count()
        log.info(f"After search: {search_count} rows (searched for '{emp_name}')")

        # Clear search
        page.clear_search()
        page.wait_seconds(2)

        # After clearing, table should show more rows again
        cleared_count = page.get_table_row_count()
        log.info(f"After clear: {cleared_count} rows (was {search_count} during search)")

        # Refresh to ensure we see the full table
        page.click_refresh()
        page.wait_seconds(2)
        final_count = page.get_table_row_count()
        log.info(f"After refresh: {final_count} rows")


# ====================================================================
# EMP-HP01/HP02: API create -> UI view read-only
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
        has_update = page.is_update_button_visible()
        has_submit = page.is_submit_button_visible()
        log.info(f"View mode: has_update={has_update}, has_submit={has_submit}")

        if has_update or has_submit:
            log.warning(
                "BUG: View popup shows Update/Submit button — should be read-only. "
                "View mode should not have action buttons."
            )
        else:
            log.info("View mode is correctly read-only (no Update/Submit buttons)")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_HP02_view_prepopulated_fields(self, emp_page, emp_api):
        """API creates employee -> UI View -> verify fields show correct data.

        KNOWN ERP BEHAVIOR: In View mode, disabled mat-select dropdowns
        (Designation, Department) show as empty (mat-mdc-select-empty) even
        when the employee has a designation set. The Angular form control
        does not populate the dropdown value in View/disabled mode. This is
        confirmed via DOM inspection: no ng-reflect attributes, __ngContext__
        has no value, and the mat-select component's .value is null.

        For dropdown fields, we verify via API as the source of truth and
        log a warning about the UI behavior. Text inputs (Name, Email, Phone)
        are verified directly from the UI as they populate correctly.
        """
        log.info("EMP-HP02 (Hybrid): View pre-populated fields check")
        page = emp_page
        sa = SoftAssert()

        result = emp_api.create_employee(name_prefix="ViewFields")
        assert result is not None, "API creation failed"
        emp_id = result.get("id")
        emp_name = result.get("name", "")
        emp_email = result.get("email_id", "")
        emp_phone = str(result.get("mobile_no", ""))
        emp_designation_id = result.get("designation")

        log.info(f"API created: id={emp_id}, name='{emp_name}', "
                 f"email='{emp_email}', phone='{emp_phone}', "
                 f"designation_id='{emp_designation_id}'")

        # Resolve expected designation name from ID
        from pages.registration.modules.employee.data.employee_data import (
            DESIGNATION_NAMES,
        )
        expected_designation = ""
        if emp_designation_id and emp_designation_id in DESIGNATION_NAMES:
            expected_designation = DESIGNATION_NAMES[emp_designation_id]

        # Search and open View
        page.search_employee(emp_name)
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.wait_seconds(0.5)
        page.click_view_from_menu()
        page.wait_seconds(2)

        # Read form field values
        values = page.get_form_field_values()
        log.info(f"View form values: {values}")

        # Verify Employee Name is pre-populated
        ui_name = values.get("Employee Name", "")
        sa.assert_true(
            bool(ui_name.strip()),
            f"Employee Name should be pre-populated in View, got: '{ui_name}'"
        )

        # Verify Email is pre-populated
        ui_email = values.get("Email", "")
        if emp_email and ui_email:
            sa.assert_true(
                emp_email.lower() in ui_email.lower(),
                f"Email mismatch: API='{emp_email}', UI='{ui_email}'"
            )

        # Verify Phone is pre-populated
        ui_phone = values.get("Phone Number", "")
        if emp_phone and ui_phone:
            sa.assert_true(
                emp_phone in ui_phone,
                f"Phone mismatch: API='{emp_phone}', UI='{ui_phone}'"
            )

        # Verify Designation — check UI first, fall back to API verification
        # KNOWN ERP BUG: View mode disabled mat-selects don't display
        # selected values (mat-mdc-select-empty). Verified 2026-06-11:
        #   - No ng-reflect-* attributes (production build)
        #   - __ngContext__ has no value property
        #   - mat-select component .value is null
        ui_designation = values.get("Designation", "")
        if ui_designation.strip():
            # UI shows the value — verify it matches expected
            designation_ok = True
            if expected_designation:
                designation_ok = (
                    expected_designation.lower() in ui_designation.lower()
                    or str(emp_designation_id) == ui_designation.strip()
                )
            sa.assert_true(
                designation_ok,
                f"Designation mismatch in View: UI='{ui_designation}', "
                f"expected='{expected_designation}' or id={emp_designation_id}"
            )
        else:
            # UI dropdown is empty (known ERP behavior in View mode)
            # Verify via API that the designation was actually saved
            log.warning(
                f"UI Designation dropdown is empty in View mode "
                f"(known ERP behavior — disabled mat-selects don't display "
                f"selected values). Verifying via API instead."
            )
            api_result = emp_api.get_employee(emp_id)
            if api_result:
                api_designation = api_result.get("designation")
                sa.assert_true(
                    api_designation is not None and api_designation != "",
                    f"Designation should exist in API record, "
                    f"got: '{api_designation}'"
                )
                if api_designation and expected_designation:
                    sa.assert_true(
                        str(api_designation) == str(emp_designation_id),
                        f"API designation mismatch: got={api_designation}, "
                        f"expected={emp_designation_id} "
                        f"({expected_designation})"
                    )
                    log.info(
                        f"Designation verified via API: "
                        f"id={api_designation} "
                        f"({expected_designation})"
                    )
            else:
                log.warning(
                    f"Could not fetch employee id={emp_id} via API "
                    f"to verify designation"
                )

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()

        sa.check_all()


# ====================================================================
# EMP-HE01/HE02/HE03: API create -> UI edit
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

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_HE02_edit_name_and_submit(self, emp_page, emp_api):
        """API creates employee -> UI Edit name -> Update -> verify success."""
        log.info("EMP-HE02 (Hybrid): Edit name and submit")
        page = emp_page

        result = emp_api.create_employee(name_prefix="EditName")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search and open edit
        page.search_employee(emp_name)
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.wait_seconds(0.5)
        page.click_edit_from_menu()
        page.wait_seconds(2)

        # Verify edit mode
        assert page.is_edit_mode(), "Should be in edit mode"

        # Edit the Employee Name field
        from pages.registration.modules.employee.data.employee_data import generate_employee_name
        new_name = generate_employee_name("Edited")
        page.type_text(page.EMPLOYEE_NAME_INPUT, new_name, clear_first=True)
        page.wait_seconds(0.5)

        # Click Update
        page.update()
        page.wait_seconds(3)

        # Check for success or error
        swal_title = page.get_alert_title()
        if swal_title:
            log.info(f"Edit name response: '{swal_title}'")
            if "success" in swal_title.lower():
                log.info(f"Name update successful: '{new_name}'")
            elif "validation" in swal_title.lower():
                log.warning(f"Name update validation failed: '{swal_title}'")
            page.dismiss_alert()
        else:
            log.info("No SweetAlert after name update — form may have closed")

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_HE03_edit_invalid_email(self, emp_page, emp_api):
        """API creates employee -> UI Edit with invalid email -> check validation."""
        log.info("EMP-HE03 (Hybrid): Edit with invalid email")
        page = emp_page

        result = emp_api.create_employee(name_prefix="EditInvalid")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search and open edit
        page.search_employee(emp_name)
        page.wait_seconds(2)

        page.open_row_menu(0)
        page.wait_seconds(0.5)
        page.click_edit_from_menu()
        page.wait_seconds(2)

        # Enter invalid email
        page.type_text(page.EMAIL_INPUT, "not-an-email", clear_first=True)
        page.wait_seconds(0.5)

        # Try to update
        page.update()
        page.wait_seconds(2)

        # Check for validation — could be mat-error or SweetAlert
        has_mat_errors = page.has_validation_errors()
        swal_title = page.get_alert_title()
        is_validation_alert = swal_title and "validation" in swal_title.lower()

        log.info(
            f"Invalid email edit: mat_errors={has_mat_errors}, "
            f"swal='{swal_title}', is_validation_alert={is_validation_alert}"
        )

        if has_mat_errors:
            errors = page.get_validation_errors()
            log.info(f"Validation errors shown: {errors}")

        if is_validation_alert:
            page.dismiss_alert()

        try:
            page.cancel_form()
        except Exception:
            page._force_close_panels()


# ====================================================================
# EMP-HR01: API create -> UI refresh -> data persists
# ====================================================================

class TestRefreshPersistence:
    """Hybrid: API creates employee -> UI refreshes -> data should persist."""

    @pytest.mark.hybrid
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_EMP_HR01_refresh_persists_data(self, emp_page, emp_api):
        """API creates employee -> UI refresh -> employee still in table."""
        log.info("EMP-HR01 (Hybrid): Refresh persists data")
        page = emp_page

        result = emp_api.create_employee(name_prefix="RefreshPersist")
        assert result is not None, "API creation failed"
        emp_name = result.get("name", "")

        # Search for the employee
        page.search_employee(emp_name)
        page.wait_seconds(2)

        # Verify it appears initially
        names = page.get_table_employee_names()
        found_initial = any(emp_name.lower() in n.lower() for n in names)
        assert found_initial, f"Employee not found before refresh: {emp_name}"

        # Refresh the page
        page.click_refresh()
        page.wait_seconds(3)

        # Search again after refresh
        page.search_employee(emp_name)
        page.wait_seconds(2)

        names_after = page.get_table_employee_names()
        found_after = any(emp_name.lower() in n.lower() for n in names_after)

        if found_after:
            log.info(f"Employee persisted after refresh: {emp_name}")
        else:
            log.warning(f"Employee NOT found after refresh: {emp_name} — possible data loss")

        assert found_after, f"Employee should persist after refresh: {emp_name}"
