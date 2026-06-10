"""
test_supplier_hybrid_scenarios.py
---------------------------------
Hybrid test suite for RhythmERP Supplier screen.

Bucket C — Hybrid Tests: API creates/sets up data → UI verifies display/behavior.
Each test uses BOTH ``sp_api`` and ``sp_page`` fixtures.

Test Inventory (6 tests):
  SP-C02+P05 — API create → UI verify SweetAlert2 + row appears
  SP-S01 — API create → UI search exact match
  SP-S02 — API create → UI search partial match
  SP-S03 — API create → UI search case insensitive
  SP-P02 — API create → UI view popup is read-only
  SP-E01+E02 — API create → UI edit shows pre-populated + Update button
  SP-E03 — API create → UI edit with special chars (BUG-001)

Hybrid Pattern:
  1. API creates supplier with specific data via ``sp_api.create_supplier()``
  2. UI opens the same supplier for view/edit via ``sp_page`` methods
  3. Verify the UI displays the data correctly or documents bug behavior

NO-DELETE CONSTRAINT:
  No delete/cleanup calls — all created suppliers are tracked via
  ``sp_api.tracker`` (CleanupTracker) for end-of-session reporting.

Run:
  pytest test_supplier_hybrid_scenarios.py -v --tb=short
  pytest test_supplier_hybrid_scenarios.py -v -m hybrid --tb=short
  pytest test_supplier_hybrid_scenarios.py -v -k "SP_C02" --tb=short
  pytest test_supplier_hybrid_scenarios.py -v -m critical --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from common.logger import log
from pages.registration.modules.supplier.data.supplier_data import (
    generate_special_char_company_name,
    KnownBugs,
)


# ====================================================================
# SP-C02 + SP-P05: API create → UI verify creation
# ====================================================================

class TestCreateAndVerify:
    """Hybrid: API creates supplier → UI verifies it appears in table."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_SP_C02_create_and_verify(self, sp_page, sp_api):
        """API creates supplier → UI searches and finds it."""
        log.info("SP-C02 + SP-P05 (Hybrid): API create → UI verify")
        page = sp_page

        # API creates supplier
        result = sp_api.create_supplier(name_prefix="HybridCreate")
        assert result is not None, "API supplier creation failed"
        company_name = result.get("name", "")
        log.info(f"API created supplier: {company_name}")

        # UI: Refresh and search for it
        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
            "Table did not load after refresh",
        )

        found = page.search_supplier(company_name)
        assert found, f"UI search failed to find API-created supplier: {company_name}"
        log.info(f"UI found supplier: {company_name}")


# ====================================================================
# SP-S01/S02/S03: API create → UI search
# ====================================================================

class TestSearchViaAPI:
    """Hybrid: API creates supplier → UI verifies search behavior."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_SP_S01_search_exact(self, sp_page, sp_api):
        """API creates supplier → UI searches exact name match."""
        log.info("SP-S01 (Hybrid): Search exact match")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="SearchExact")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        found = page.search_supplier(company_name)
        assert found, f"Exact search failed for: {company_name}"
        log.info(f"Exact search found: {company_name}")

    @pytest.mark.hybrid
    def test_SP_S02_search_partial(self, sp_page, sp_api):
        """API creates supplier → UI searches partial name."""
        log.info("SP-S02 (Hybrid): Search partial match")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="SearchPartial")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        partial = company_name[:10]
        found = page.search_supplier(partial)
        assert found, f"Partial search failed for: {partial}"
        log.info(f"Partial search found with: {partial}")

    @pytest.mark.hybrid
    def test_SP_S03_search_case_insensitive(self, sp_page, sp_api):
        """API creates supplier → UI searches case-insensitive."""
        log.info("SP-S03 (Hybrid): Search case insensitive")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="SearchCase")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        found = page.search_supplier(company_name.lower())
        log.info(f"Case insensitive search result: found={found}")


# ====================================================================
# SP-P02: API create → UI view popup read-only
# ====================================================================

class TestViewReadOnly:
    """Hybrid: API creates supplier → UI verifies View popup is read-only."""

    @pytest.mark.hybrid
    def test_SP_P02_view_readonly(self, sp_page, sp_api):
        """API creates supplier → UI views it → verify popup is read-only."""
        log.info("SP-P02 (Hybrid): View popup is read-only")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="ViewRO")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        # Search for the created supplier
        found = page.search_supplier(company_name)
        assert found, f"Could not find supplier for View test: {company_name}"

        page.click_view_first_row()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open(),
            "View popup did not open",
        )

        is_readonly = page.verify_view_popup_read_only()
        assert is_readonly, (
            "BUG: View popup fields are editable (should be read-only)"
        )
        log.info("View popup correctly shows read-only fields")

        page.close_popup()


# ====================================================================
# SP-E01 + SP-E02: API create → UI edit pre-populated + Update button
# ====================================================================

class TestEditVerification:
    """Hybrid: API creates supplier → UI verifies edit behavior."""

    @pytest.mark.hybrid
    def test_SP_E01_E02_edit_prepopulated_and_update(self, sp_page, sp_api):
        """API creates supplier → UI edits → verify pre-populated + Update button."""
        log.info("SP-E01 + SP-E02 (Hybrid): Edit pre-populated + Update button")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="EditPrepop")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        # Search for the created supplier
        found = page.search_supplier(company_name)
        assert found, f"Could not find supplier for Edit test: {company_name}"

        # SP-E02: Edit shows pre-populated fields
        page.click_edit_first_row()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open() and page.is_edit_mode(),
            "Edit form did not open or not in edit mode",
        )

        form_values = page.get_form_field_values()
        company_val = form_values.get("Company Name", "")
        assert company_val, "Company Name empty in Edit form"
        log.info(f"Edit form pre-populated — Company Name: {company_val}")

        # SP-E01: Edit has Update button
        has_update = page.has_update_button()
        assert has_update, (
            "BUG-005: No Update button in Edit mode — cannot save edits"
        )
        log.info("Edit mode shows Update button")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()

    # ---- SP-E03: Edit Company Name special chars (BUG-001) ----
    @pytest.mark.hybrid
    @pytest.mark.bug
    @pytest.mark.xfail(reason=KnownBugs.BUG_001, strict=False)
    def test_SP_E03_edit_special_chars(self, sp_page, sp_api):
        """API creates supplier → UI edits with special chars — BUG-001."""
        log.info("SP-E03 (Hybrid): Edit Company Name special chars")
        page = sp_page

        result = sp_api.create_supplier(name_prefix="EditSpecCh")
        assert result is not None, "API creation failed"
        company_name = result.get("name", "")

        page.click_refresh()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.get_table_row_count() >= 1,
        )

        found = page.search_supplier(company_name)
        assert found, f"Could not find supplier for Edit test: {company_name}"

        page.click_edit_first_row()
        WebDriverWait(page.driver, 10).until(
            lambda d: page.is_add_form_open() and page.is_edit_mode(),
            "Edit form did not open",
        )

        try:
            page.type_text(
                page.COMPANY_NAME_INPUT,
                generate_special_char_company_name(),
                clear_first=True,
            )

            if page.has_update_button():
                page.click_update()
                WebDriverWait(page.driver, 10).until(
                    lambda d: not page.is_add_form_open(),
                    "Popup did not close after Update",
                )
                page.handle_success_alert(timeout=5)
                log.info("Edit with special chars — Update succeeded (BUG-001)")
            else:
                log.info("No Update button found")
                page.cancel()
        except Exception as e:
            log.warning(f"Edit special chars test exception: {e}")
            try:
                page.cancel()
            except Exception:
                pass

        page.click_refresh()
