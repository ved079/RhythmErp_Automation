"""
test_uom_full_flow.py
---------------------
Full end-to-end test for UOM: Create -> View -> History(empty) -> Edit -> Update -> History(with data).
"""

import sys
import os
import pytest
from common.logger import log

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pages.common_settings.modules.uom.uom_page import UOMPage
from pages.common_settings.modules.uom.data.uom_data import generate_uom_data, generate_updated_description


class TestUOMFullFlow:
    """Test suite for complete UOM lifecycle: Create -> View -> History -> Edit -> Verify."""

    def test_uom_create_view_edit_history(self, logged_in_driver):
        driver = logged_in_driver
        uom_page = UOMPage(driver)

        uom_data = generate_uom_data()
        uom_code = uom_data["uom_code"]
        original_description = uom_data["uom_description"]

        log.info("========== UOM FULL FLOW TEST ==========")
        log.info("UOM Code: " + uom_code)
        log.info("Original Description: " + original_description)

        # ============================================================
        # STEP 1: CREATE UOM
        # ============================================================
        log.info(">>> STEP 1: CREATE UOM")
        uom_page.navigate_to_page()
        uom_page.open_add_form()
        uom_page.fill_uom_form(uom_data)
        uom_page.submit()
        uom_page.handle_success_alert()

        uom_page.navigate_to_page()
        uom_page.search_uom(uom_code)
        uom_page.verify_uom_exists(uom_code)
        log.info(">>> STEP 1 PASSED: UOM created and verified")

        # ============================================================
        # STEP 2: VIEW UOM (verify read-only)
        # ============================================================
        log.info(">>> STEP 2: VIEW UOM")
        uom_page.click_view_button(uom_code)
        uom_page.verify_view_popup_read_only()

        code_value = uom_page.get_view_field_value(uom_page.UOM_CODE_INPUT)
        desc_value = uom_page.get_view_field_value(uom_page.UOM_DESCRIPTION_INPUT)
        log.info("  View - UOM Code: " + str(code_value))
        log.info("  View - Description: " + str(desc_value))
        assert code_value == uom_code, \
            "View: UOM Code mismatch. Expected '" + uom_code + "', got '" + str(code_value) + "'"
        assert original_description in str(desc_value), \
            "View: Description mismatch. Expected '" + original_description + "' in '" + str(desc_value) + "'"
        log.info(">>> STEP 2 PASSED: View popup is read-only and shows correct data")

        uom_page.close_popup()

        # ============================================================
        # STEP 3: HISTORY (should be empty for newly created UOM)
        # ============================================================
        log.info(">>> STEP 3: CHECK HISTORY (expect empty)")
        uom_page.click_history_button(uom_code)
        is_empty = uom_page.is_history_empty()
        assert is_empty, "History should be empty for a newly created UOM"
        row_count = uom_page.get_history_row_count()
        log.info("  History row count: " + str(row_count))
        assert row_count == 0, "Expected 0 history rows for new UOM, found " + str(row_count)
        log.info(">>> STEP 3 PASSED: History is empty as expected")

        uom_page.close_history_popup()

        # ============================================================
        # STEP 4: EDIT UOM (keep Active so Step 5 can find it)
        # ============================================================
        log.info(">>> STEP 4: EDIT UOM")
        uom_page.click_edit_button(uom_code)
        uom_page.verify_edit_popup_editable()

        new_description = generate_updated_description()
        uom_page.update_uom_description(new_description)
        log.info("  New description: " + str(new_description))

        # NOTE: Status intentionally NOT toggled - keeping Active so the
        # record remains visible in the default table view for Step 5.
        current_status = uom_page.get_toggle_status()
        log.info("  Status kept as: " + str(current_status))

        uom_page.click_update()
        uom_page.handle_success_alert()
        log.info(">>> STEP 4 PASSED: UOM edited and updated")

        # ============================================================
        # STEP 5: VERIFY HISTORY after edit
        # ============================================================
        log.info(">>> STEP 5: VERIFY HISTORY (expect data)")

        uom_page.navigate_to_page()
        uom_page.search_uom(uom_code)
        uom_page.verify_uom_exists(uom_code)

        uom_page.click_history_button(uom_code)

        is_empty = uom_page.is_history_empty()
        assert not is_empty, "History should have data after UOM was updated"

        history_records = uom_page.get_history_data()
        row_count = len(history_records)
        log.info("  History row count: " + str(row_count))
        assert row_count > 0, "Expected at least 1 history row after edit, found " + str(row_count)

        latest_record = history_records[0]
        log.info("  Latest history record: " + str(latest_record))

        assert latest_record["uom_code"] == uom_code, \
            "History: UOM Code mismatch. Expected '" + uom_code + "', got '" + latest_record["uom_code"] + "'"
        assert latest_record["updated_time"] != "", \
            "History: Updated Time should be populated after edit"
        assert latest_record["created_time"] != "", \
            "History: Creation Time should be populated"

        log.info("  Creation Time: " + latest_record["created_time"])
        log.info("  Updated Time: " + latest_record["updated_time"])
        log.info("  UOM Code: " + latest_record["uom_code"])
        log.info("  Description: " + latest_record["description"])
        log.info("  Status: " + latest_record["status"])

        uom_page.close_history_popup()

        log.info(">>> STEP 5 PASSED: History verified with updated data")
        log.info("========== ALL STEPS PASSED ==========")