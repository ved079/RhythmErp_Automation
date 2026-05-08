"""
test_uom.py
-----------
Create-only test for UOM (existing test from Phase 1).
Kept separate for quick smoke testing.
"""

import sys
import os
import pytest
from common.logger import log

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from pages.common_settings.Common_Settings.uom_page import UOMPage
from pages.common_settings.data.uom_data import generate_uom_data


class TestUOMCreate:
    """Test suite for UOM creation and verification via search."""

    def test_create_and_verify_uom(self, logged_in_driver):
        """
        Create a new UOM and verify it appears in the table via search.

        Flow:
        1. Navigate to Common Settings > UOM
        2. Click Add, fill form, submit
        3. Handle success alert
        4. Search for the created UOM
        5. Verify it exists in the table
        """
        driver = logged_in_driver
        uom_page = UOMPage(driver)
        uom_data = generate_uom_data()

        log.info(f"=== Creating UOM: {uom_data['uom_code']} ===")

        # Step 1: Navigate to UOM page
        uom_page.navigate_to_page()

        # Step 2: Open Add form, fill, submit
        uom_page.open_add_form()
        uom_page.fill_uom_form(uom_data)
        uom_page.submit()

        # Step 3: Handle success alert
        uom_page.handle_success_alert()

        # Step 4: Search and verify
        uom_page.refresh_page()
        uom_page.search_uom(uom_data["uom_code"])
        uom_page.verify_uom_exists(uom_data["uom_code"])

        log.info(f"=== UOM '{uom_data['uom_code']}' created and verified successfully ===")
