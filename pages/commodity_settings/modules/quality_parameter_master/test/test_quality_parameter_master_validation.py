"""
Optimized QPM validation suite — 33 tests, 5 classes, 6 bugs.
ZERO wait_seconds() — uses hard_refresh, is_validation_alert_present(timeout=3),
and time.sleep(0.2-0.3) only. Every test uses try/finally with _cleanup(page).

Classes: TestCreateFormValidations(12) TestDuplicateValidations(3)
         TestEditFormValidations(6) TestSearchFilter(5) TestPopupUI(7)
Bugs: BUG-001(spaces) BUG-002(dupes) BUG-003(maxlen) BUG-004(no alert)
      BUG-005(no delete) BUG-006(no history)
Markers: smoke(7) sanity(25) regression(33) bug(13) ui(8)
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By

from pages.commodity_settings.modules.quality_parameter_master.data.quality_parameter_master_data import (
    generate_valid_quality_parameter_data,
    generate_valid_edit_data,
    generate_spaces_only_data,
    generate_duplicate_name_data,
    generate_string_255,
    generate_string_256,
    generate_special_char_data,
    generate_sql_injection_data,
    generate_xss_data,
    generate_unicode_data,
    generate_name_with_leading_trailing_spaces,
    generate_quality_parameter_name,
)
from common.logger import log


# ====================================================================
# Helpers
# ====================================================================

def _cleanup(page):
    """Fast cleanup: cancel any open form, close panels, hard-refresh."""
    try:
        page.cancel()
    except Exception:
        pass
    try:
        page._force_close_panels()
    except Exception:
        pass
    page.hard_refresh()


def _create_qp_fast(page, data=None):
    """Create a QP, close leftover popup, hard-refresh. Returns name."""
    if data is None:
        data = generate_valid_quality_parameter_data("PreReq")
    name = page.create_quality_parameter(data)
    try:
        page.close_popup()
    except Exception:
        pass
    page.hard_refresh()
    return name


# ====================================================================
# PHASE 1: Create Form Validations (12 tests)
# ====================================================================

class TestCreateFormValidations:
    """QPM-C01 to QPM-C12: Validation checks on the Create form.
    QPM has ONLY one form field: Name (text, required).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C01_empty_submit(self, qp_master_page):
        """QPM-C01: Submit with empty Name — should be blocked."""
        log.info("QPM-C01: Empty submit test")
        page = qp_master_page
        try:
            page.open_add_form()
            assert page.is_add_form_open(), "Add form did not open"
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            errors = page.get_mat_error_text()
            form_open = page.is_add_form_open()
            assert form_open or errors or alert, (
                "BUG: Form submitted with empty Name — no validation"
            )
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C02_valid_create(self, qp_master_page):
        """QPM-C02: Create with valid Name — should succeed.
        BUG-004: No success SweetAlert after create.
        """
        log.info("QPM-C02: Valid create test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("ValidC")
            name = page.create_quality_parameter(data)

            # BUG-004: No success alert, just check popup closed
            popup_closed = page.is_form_closed()
            if popup_closed:
                log.info("Form closed after submit (BUG-004: no success alert)")
            else:
                swal_title = page.get_swal_title()
                if swal_title:
                    log.warning(f"Validation alert instead of success: {swal_title}")

            page.hard_refresh()
            found = page.search_qp(name)
            page.clear_search()
            assert found, f"Created QP '{name}' not found in table"
            log.info(f"QP created and found in table: {name}")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason="BUG-001: Spaces-only name accepted — will fail until ERP is fixed",
        strict=False,
    )
    def test_QPM_C03_spaces_only_name(self, qp_master_page):
        """QPM-C03: Spaces-only Name — should be rejected (BUG-001)."""
        log.info("QPM-C03: Spaces-only name test")
        page = qp_master_page
        try:
            data = generate_spaces_only_data(10)
            page.open_add_form()
            page.fill_form(data)
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            form_open = page.is_add_form_open()
            errors = page.get_mat_error_text()
            assert form_open or errors or alert, (
                "BUG-001 CONFIRMED: Spaces-only name was accepted"
            )
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C04_duplicate_name(self, qp_master_page):
        """QPM-C04: Duplicate Name in Create (BUG-002)."""
        log.info("QPM-C04: Duplicate name test")
        page = qp_master_page
        try:
            data1 = generate_valid_quality_parameter_data("Dup1")
            page.create_quality_parameter(data1)
            try:
                page.close_popup()
            except Exception:
                pass
            page.hard_refresh()
            data2 = generate_duplicate_name_data(data1["name"])
            page.open_add_form()
            page.fill_form(data2)
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            form_open = page.is_add_form_open()
            if alert or form_open:
                log.info("Duplicate name rejected — validation working")
            else:
                log.warning("BUG-002 CONFIRMED: Duplicate name allowed in Create")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C05_name_255_chars(self, qp_master_page):
        """QPM-C05: 255-char boundary (BUG-003)."""
        log.info("QPM-C05: 255-char name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form({"name": generate_string_255()})
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("255-char name rejected — maxlength enforced")
            else:
                log.info("255-char name accepted (may be expected if max >= 255)")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C06_name_256_chars(self, qp_master_page):
        """QPM-C06: 256-char exceeds limit (BUG-003)."""
        log.info("QPM-C06: 256-char name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form({"name": generate_string_256()})
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("256-char name rejected — maxlength enforced")
            else:
                log.warning("BUG-003 CONFIRMED: 256-char name accepted")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C07_no_success_popup(self, qp_master_page):
        """QPM-C07: No success SweetAlert after create (BUG-004)."""
        log.info("QPM-C07: No success popup test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form(generate_valid_quality_parameter_data("NoAlert"))
            page.submit()
            swal = page.is_validation_alert_present(timeout=3)
            if not swal:
                log.warning("BUG-004 CONFIRMED: No success SweetAlert after create")
            else:
                log.info(f"SweetAlert appeared: {page.get_swal_title()}")
                page.handle_validation_warning(timeout=3)
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C08_special_chars_name(self, qp_master_page):
        """QPM-C08: Special characters in Name."""
        log.info("QPM-C08: Special chars in name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form(generate_special_char_data())
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("Special chars rejected — validation working")
            else:
                log.info("Special chars accepted (may be expected behavior)")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_C09_sql_injection_name(self, qp_master_page):
        """QPM-C09: SQL injection in Name."""
        log.info("QPM-C09: SQL injection name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form(generate_sql_injection_data())
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("SQL injection rejected — input sanitized")
            else:
                log.info("SQL injection accepted — check server-side sanitization")
        finally:
            _cleanup(page)

    @pytest.mark.regression
    def test_QPM_C10_xss_name(self, qp_master_page):
        """QPM-C10: XSS payload in Name."""
        log.info("QPM-C10: XSS name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form(generate_xss_data())
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("XSS payload rejected — input sanitized")
            else:
                log.info("XSS payload accepted — check if DOM rendering is safe")
        finally:
            _cleanup(page)

    @pytest.mark.regression
    def test_QPM_C11_unicode_name(self, qp_master_page):
        """QPM-C11: Unicode characters in Name."""
        log.info("QPM-C11: Unicode name test")
        page = qp_master_page
        try:
            page.open_add_form()
            page.fill_form(generate_unicode_data())
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("Unicode name rejected")
            else:
                log.info("Unicode name accepted (may be expected for i18n)")
        finally:
            _cleanup(page)

    @pytest.mark.regression
    def test_QPM_C12_leading_trailing_spaces(self, qp_master_page):
        """QPM-C12: Leading/trailing spaces — should be trimmed."""
        log.info("QPM-C12: Leading/trailing spaces test")
        page = qp_master_page
        try:
            spaced_name = generate_name_with_leading_trailing_spaces()
            page.open_add_form()
            page.fill_form({"name": spaced_name})
            page.submit()
            if page.is_form_closed():
                page.hard_refresh()
                names = page.get_all_qp_names()
                trimmed = spaced_name.strip()
                if any(n != n.strip() for n in names if spaced_name in n or trimmed in n):
                    log.warning("BUG: Leading/trailing spaces NOT trimmed")
                else:
                    log.info("Name was trimmed before storage")
            else:
                log.info("Spaced name rejected — validation working")
        finally:
            _cleanup(page)


# ====================================================================
# PHASE 2: Duplicate Validations (3 tests)
# ====================================================================

class TestDuplicateValidations:
    """QPM-D01 to QPM-D03: Duplicate name checks (BUG-002)."""

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_D01_duplicate_create(self, qp_master_page):
        """QPM-D01: Create two QPs with identical names (BUG-002)."""
        log.info("QPM-D01: Duplicate create test")
        page = qp_master_page
        try:
            data1 = generate_valid_quality_parameter_data("DDup1")
            page.create_quality_parameter(data1)
            try:
                page.close_popup()
            except Exception:
                pass
            page.hard_refresh()
            page.open_add_form()
            page.fill_form(generate_duplicate_name_data(data1["name"]))
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("Duplicate name rejected in Create — validation working")
            else:
                log.warning("BUG-002 CONFIRMED: Duplicate name allowed in Create")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_D02_duplicate_case_insensitive(self, qp_master_page):
        """QPM-D02: Same name in different case (BUG-002)."""
        log.info("QPM-D02: Duplicate case-insensitive test")
        page = qp_master_page
        try:
            data1 = generate_valid_quality_parameter_data("CaseDup")
            page.create_quality_parameter(data1)
            try:
                page.close_popup()
            except Exception:
                pass
            page.hard_refresh()
            page.open_add_form()
            page.fill_form({"name": data1["name"].upper()})
            page.submit()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("Case-insensitive duplicate check working — rejected")
            else:
                log.info("Case-insensitive duplicate check NOT enforced")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.regression
    def test_QPM_D03_duplicate_edit(self, qp_master_page):
        """QPM-D03: Edit QP to another QP's name (BUG-002)."""
        log.info("QPM-D03: Duplicate edit test")
        page = qp_master_page
        try:
            data1 = generate_valid_quality_parameter_data("EditDup1")
            _create_qp_fast(page, data1)
            data2 = generate_valid_quality_parameter_data("EditDup2")
            _create_qp_fast(page, data2)
            page.click_edit_button(qp_name=data2["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            page.type_text(page.NAME_INPUT, data1["name"], clear_first=True)
            page.click_update()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            if alert or page.is_add_form_open():
                log.info("Duplicate name rejected in Edit — validation working")
            else:
                log.warning("BUG-002 CONFIRMED: Duplicate name allowed in Edit")
        finally:
            _cleanup(page)


# ====================================================================
# PHASE 3: Edit Form Validations (6 tests)
# ====================================================================

class TestEditFormValidations:
    """QPM-E01 to QPM-E06: Validation checks on the Edit form."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E01_edit_prepopulated(self, qp_master_page):
        """QPM-E01: Edit popup should show Name pre-populated."""
        log.info("QPM-E01: Edit pre-populated fields test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditPre")
            _create_qp_fast(page, data)
            page.click_edit_button(qp_name=data["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            fv = page.get_form_field_values()
            if not fv.get("name"):
                try:
                    fv["name"] = page.driver.execute_script(
                        "var i=document.querySelector("
                        "\"input[name='Name'],input[name='name'],"
                        "input[formcontrolname='name']\");"
                        "return i?i.value:'';"
                    ) or ""
                except Exception:
                    pass
            assert fv.get("name"), "Name field empty in Edit form"
            assert "EditPre" in fv.get("name", ""), (
                f"Edit form Name '{fv.get('name')}' doesn't contain 'EditPre'"
            )
            log.info(f"Edit form pre-populated correctly: {fv}")
        finally:
            _cleanup(page)

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E02_valid_edit(self, qp_master_page):
        """QPM-E02: Edit with valid new Name (BUG-004: no alert)."""
        log.info("QPM-E02: Valid edit test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditOK")
            _create_qp_fast(page, data)
            edit_data = generate_valid_edit_data("Updated")
            page.click_edit_button(qp_name=data["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            page.fill_form(edit_data)
            page.click_update()
            if page.is_form_closed():
                log.info("Edit form closed after update (BUG-004: no success alert)")
            else:
                swal = page.get_swal_title()
                if swal:
                    log.warning(f"Validation alert after edit: {swal}")
            page.hard_refresh()
            found = page.search_qp(edit_data["name"])
            page.clear_search()
            assert found, f"Updated QP '{edit_data['name']}' not found in table"
            log.info(f"QP updated and found in table: {edit_data['name']}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.xfail(
        reason="BUG: Edit form allows empty Name submission — will fail until ERP is fixed",
        strict=False,
    )
    def test_QPM_E03_edit_empty_name(self, qp_master_page):
        """QPM-E03: Edit with empty Name — should be blocked (BUG)."""
        log.info("QPM-E03: Edit empty name test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditEmpty")
            _create_qp_fast(page, data)
            page.click_edit_button(qp_name=data["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            page.driver.execute_script(
                "var i=document.querySelector("
                "\"input[name='Name'],input[name='name'],"
                "input[formcontrolname='name']\");"
                "if(i){var s=Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(i,'');i.dispatchEvent(new Event('input',{bubbles:true}));"
                "i.dispatchEvent(new Event('change',{bubbles:true}));}"
            )
            time.sleep(0.3)
            page.click_update()
            alert = ""
            if page.is_validation_alert_present(timeout=3):
                alert = page.get_swal_title() or ""
                page.handle_validation_warning(timeout=3)
            errors = page.get_mat_error_text()
            assert page.is_add_form_open() or errors or alert, (
                "BUG: Edit form submitted with empty Name — no validation"
            )
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E04_edit_duplicate_name(self, qp_master_page):
        """QPM-E04: Edit QP to another QP's Name (BUG-002)."""
        log.info("QPM-E04: Edit duplicate name test")
        page = qp_master_page
        try:
            data1 = generate_valid_quality_parameter_data("EDup1")
            _create_qp_fast(page, data1)
            data2 = generate_valid_quality_parameter_data("EDup2")
            _create_qp_fast(page, data2)
            page.edit_quality_parameter(data2["name"], {"name": data1["name"]})
            page.hard_refresh()
            if page.is_qp_in_table(data1["name"]):
                log.warning("BUG-002 CONFIRMED: Duplicate name allowed in Edit")
            else:
                log.info("Duplicate name rejected in Edit — validation working")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_E05_edit_no_success_popup(self, qp_master_page):
        """QPM-E05: No success SweetAlert after edit (BUG-004)."""
        log.info("QPM-E05: Edit no success popup test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditNoAlert")
            _create_qp_fast(page, data)
            edit_data = generate_valid_edit_data("UpdNoAlert")
            page.click_edit_button(qp_name=data["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            page.fill_form(edit_data)
            page.click_update()
            swal = page.is_validation_alert_present(timeout=3)
            if not swal:
                log.warning("BUG-004 CONFIRMED: No success SweetAlert after edit")
            else:
                log.info(f"SweetAlert appeared after edit: {page.get_swal_title()}")
                page.handle_validation_warning(timeout=3)
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.regression
    def test_QPM_E06_edit_spaces_only(self, qp_master_page):
        """QPM-E06: Edit Name to spaces-only (BUG-001)."""
        log.info("QPM-E06: Edit spaces-only name test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditSpace")
            _create_qp_fast(page, data)
            page.click_edit_button(qp_name=data["name"])
            assert page.is_edit_mode(), "Edit mode not activated"
            page.fill_form(generate_spaces_only_data(8))
            page.click_update()
            alert = page.is_validation_alert_present(timeout=3)
            if alert:
                page.handle_validation_warning(timeout=3)
            errors = page.get_mat_error_text()
            if page.is_add_form_open() or errors or alert:
                log.info("Spaces-only name rejected in Edit — validation working")
            else:
                log.warning("BUG-001 in Edit: Spaces-only name accepted")
        finally:
            _cleanup(page)


# ====================================================================
# PHASE 4: Search & Filter Edge Cases (5 tests)
# ====================================================================

class TestSearchFilter:
    """QPM-S01 to QPM-S05: Search and Filter edge cases."""

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S01_search_exact(self, qp_master_page):
        """QPM-S01: Search with exact QP name — should find it."""
        log.info("QPM-S01: Search exact name")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("SearchEx")
            _create_qp_fast(page, data)

            found = page.search_qp(data["name"])
            page.clear_search()

            assert found, f"Exact search failed for: {data['name']}"
            log.info(f"Exact search found: {data['name']}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S02_search_partial(self, qp_master_page):
        """QPM-S02: Search with partial QP name — should find it."""
        log.info("QPM-S02: Search partial name")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("SearchPar")
            _create_qp_fast(page, data)

            partial = data["name"][:8]
            found = page.search_qp(partial)
            page.clear_search()

            assert found, f"Partial search failed for: {partial}"
            log.info(f"Partial search found with: {partial}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S03_search_nonexistent(self, qp_master_page):
        """QPM-S03: Search for non-existent name — should return no results."""
        log.info("QPM-S03: Search nonexistent")
        page = qp_master_page
        try:
            fake_name = f"NonExistent_{int(time.time())}"
            found = page.search_qp(fake_name)
            page.clear_search()

            assert not found, (
                f"BUG: Non-existent name '{fake_name}' was found in table"
            )
            log.info(f"Correctly not found: {fake_name}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_S04_filter_panel(self, qp_master_page):
        """QPM-S04: Filter panel should open and close."""
        log.info("QPM-S04: Filter panel test")
        page = qp_master_page
        try:
            page.open_filter_panel()
            filter_open = page.is_filter_panel_open()

            if filter_open:
                log.info("Filter panel opened successfully")
                page.close_filter_panel()
                time.sleep(0.3)
                still_open = page.is_filter_panel_open()
                if not still_open:
                    log.info("Filter panel closed successfully")
                else:
                    log.warning("Filter panel still visible after close")
            else:
                log.info("Filter button/panel not found on this screen")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    def test_QPM_S05_column_sort(self, qp_master_page):
        """QPM-S05: Click Name column header to toggle sort order."""
        log.info("QPM-S05: Column sort test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("Sort")
            _create_qp_fast(page, data)

            names_before = page.get_all_qp_names()
            page.click_name_column_header()
            time.sleep(0.3)
            names_after = page.get_all_qp_names()

            assert names_after, "Table is empty after column sort"
            assert set(names_before) == set(names_after), (
                "Table content changed after sort — data may have been lost"
            )
            log.info(
                f"Column sort passed. Before: {len(names_before)}, "
                f"After: {len(names_after)} rows"
            )
        finally:
            _cleanup(page)


# ====================================================================
# PHASE 5: Popup & UI Behaviors (7 tests)
# ====================================================================

class TestPopupUI:
    """QPM-P01 to QPM-P07: Popup and UI interaction checks.
    Includes documentation of BUG-005 (No Delete) and BUG-006 (No History).
    """

    @pytest.mark.smoke
    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P01_cancel_no_create(self, qp_master_page):
        """QPM-P01: Cancel closes form without creating a QP."""
        log.info("QPM-P01: Cancel no create test")
        page = qp_master_page
        try:
            before_count = page.get_table_row_count()

            page.open_add_form()
            assert page.is_add_form_open(), "Form did not open"

            data = generate_valid_quality_parameter_data("CancelTest")
            page.fill_form(data)
            page.cancel()

            after_count = page.get_table_row_count()
            assert after_count == before_count, (
                f"BUG: Row count changed after Cancel. "
                f"Before: {before_count}, After: {after_count}"
            )
            log.info("Cancel correctly did not create a QP")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P02_close_no_create(self, qp_master_page):
        """QPM-P02: X button closes form without creating a QP."""
        log.info("QPM-P02: Close no create test")
        page = qp_master_page
        try:
            before_count = page.get_table_row_count()

            page.open_add_form()
            assert page.is_add_form_open(), "Form did not open"

            data = generate_valid_quality_parameter_data("CloseTest")
            page.fill_form(data)
            page.close_popup()

            after_count = page.get_table_row_count()
            assert after_count == before_count, (
                f"BUG: Row count changed after X close. "
                f"Before: {before_count}, After: {after_count}"
            )
            log.info("X close correctly did not create a QP")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P03_view_readonly(self, qp_master_page):
        """QPM-P03: View popup shows Name field in read-only mode."""
        log.info("QPM-P03: View read-only test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("ViewTest")
            _create_qp_fast(page, data)

            page.click_view_button(qp_name=data["name"])
            is_readonly = page.verify_view_popup_read_only()

            assert is_readonly, (
                "BUG: View popup Name field is editable (should be read-only)"
            )
            log.info("View popup correctly shows read-only Name field")
            page.close_popup()
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P04_edit_has_update(self, qp_master_page):
        """QPM-P04: Edit popup shows editable Name field with Update button."""
        log.info("QPM-P04: Edit has Update button")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("EditTest")
            _create_qp_fast(page, data)

            page.click_edit_button(qp_name=data["name"])
            is_edit = page.verify_edit_popup_editable()

            assert is_edit, "BUG: Edit popup does not show Update button"
            log.info("Edit popup correctly shows Update button")

            # Verify Name field is editable and pre-populated
            form_values = page.get_form_field_values()
            if not form_values.get("name"):
                try:
                    val = page.driver.execute_script(
                        "var i = document.querySelector("
                        "  \"input[name='Name'], input[name='name'], \""
                        " + \"input[formcontrolname='name']\");"
                        "return i ? i.value : '';"
                    )
                    form_values["name"] = val or ""
                except Exception:
                    pass

            assert form_values.get("name"), "Name field empty in Edit form"
            log.info(f"Edit form Name field pre-populated: {form_values}")
        finally:
            _cleanup(page)

    @pytest.mark.sanity
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P05_add_form_heading(self, qp_master_page):
        """QPM-P05: Add form should show a heading indicating creation mode."""
        log.info("QPM-P05: Add form heading test")
        page = qp_master_page
        try:
            page.open_add_form()
            assert page.is_add_form_open(), "Add form did not open"

            heading = page.get_form_heading()
            log.info(f"Add form heading: '{heading}'")

            if heading:
                log.info(f"Form heading is: {heading}")
            else:
                log.warning("No form heading found — UX issue")

            submit_visible = page.is_displayed(page.SUBMIT_BUTTON, timeout=3)
            update_visible = page.is_displayed(page.UPDATE_BUTTON, timeout=2)

            assert submit_visible, "Submit button not visible in Add form"
            assert not update_visible, (
                "Update button visible in Add form (should be Submit only)"
            )
            log.info("Add form has Submit button (not Update)")
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P06_no_delete_option(self, qp_master_page):
        """QPM-P06: Verify no Delete option exists on the QPM screen.
        BUG-005: No Delete option anywhere on screen.
        """
        log.info("QPM-P06: No Delete option test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("NoDelete")
            _create_qp_fast(page, data)

            # Check for Delete button in table rows
            delete_buttons = page.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table td.cdk-column-delete button, "
                "table#excel-table td.mat-column-delete button, "
                "table#excel-table button[mattooltip='Delete'], "
                "table#excel-table button.delete-btn",
            )

            # Check for Delete in popup footer
            popup_delete_buttons = []
            try:
                popup_delete_buttons = page.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]"
                    "//button[contains(.,'Delete')]",
                )
            except Exception:
                pass

            if not delete_buttons and not popup_delete_buttons:
                log.warning(
                    "BUG-005 CONFIRMED: No Delete option exists on the "
                    "Quality Parameter Master screen."
                )
            else:
                log.info("Delete option found — BUG-005 may be fixed")

            log.info(
                f"Delete buttons in table: {len(delete_buttons)}, "
                f"in popup: {len(popup_delete_buttons)}"
            )
        finally:
            _cleanup(page)

    @pytest.mark.bug
    @pytest.mark.regression
    @pytest.mark.ui
    def test_QPM_P07_no_history_option(self, qp_master_page):
        """QPM-P07: Verify no History/Audit trail feature exists.
        BUG-006: No History / Audit trail feature.
        """
        log.info("QPM-P07: No History option test")
        page = qp_master_page
        try:
            data = generate_valid_quality_parameter_data("NoHistory")
            _create_qp_fast(page, data)

            # Check for History button in table rows
            history_buttons = page.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table td.cdk-column-history button, "
                "table#excel-table td.mat-column-history button, "
                "table#excel-table button[mattooltip='History'], "
                "table#excel-table button.history-btn",
            )

            # Check for History in popup footer
            popup_history_buttons = []
            try:
                popup_history_buttons = page.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]"
                    "//button[contains(.,'History')]",
                )
            except Exception:
                pass

            if not history_buttons and not popup_history_buttons:
                log.warning(
                    "BUG-006 CONFIRMED: No History / Audit trail feature "
                    "exists on the Quality Parameter Master screen."
                )
            else:
                log.info("History option found — BUG-006 may be fixed")

            log.info(
                f"History buttons in table: {len(history_buttons)}, "
                f"in popup: {len(popup_history_buttons)}"
            )
        finally:
            _cleanup(page)
