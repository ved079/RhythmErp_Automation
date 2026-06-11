"""
test_agent_hybrid_scenarios.py
------------------------------
Hybrid test suite for RhythmERP Agent screen.

Bucket C — Hybrid Tests: API creates/sets up data → UI verifies display/behavior.
Each test uses BOTH ``agt_api`` and ``agt_page`` fixtures.

Test Inventory (6 tests):
  AGT-H01 — API create → UI verify row appears in table
  AGT-HS01 — API create → UI search exact match
  AGT-HS02 — API create → UI search partial match
  AGT-HS03 — API create → UI search case insensitive
  AGT-HP01 — API create → UI View popup is read-only
  AGT-HE01 — API create → UI edit shows pre-populated + Update button → edit → Update

Hybrid Pattern:
  1. API creates agent with specific data via ``agt_api.create_agent()``
  2. UI opens the same agent for view/edit via ``agt_page`` methods
  3. Verify the UI displays the data correctly or documents bug behavior

NO-DELETE CONSTRAINT:
  No delete/cleanup calls — all created agents are tracked via
  ``agt_api.tracker`` (CleanupTracker) for end-of-session reporting.

Run:
  pytest test_agent_hybrid_scenarios.py -v --tb=short
  pytest test_agent_hybrid_scenarios.py -v -m hybrid --tb=short
  pytest test_agent_hybrid_scenarios.py -v -k "AGT_H01" --tb=short
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
from pages.registration.modules.agent.data.agent_data import (
    generate_valid_edit_data,
)


# ====================================================================
# AGT-H01: API create → UI verify creation
# ====================================================================

class TestCreateAndVerify:
    """Hybrid: API creates agent → UI verifies it appears in table."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_AGT_H01_create_and_verify(self, agt_page, agt_api):
        """API creates agent → UI searches and finds it."""
        log.info("AGT-H01 (Hybrid): API create → UI verify")
        page = agt_page

        # API creates agent
        result = agt_api.create_agent(name_prefix="HybridCreate")
        assert result is not None, "API agent creation failed"
        agent_name = result.get("agent_name", "")
        log.info(f"API created agent: {agent_name}")

        # UI: Search for it
        found = page.search_agent(agent_name)
        assert found, f"UI search failed to find API-created agent: {agent_name}"
        log.info(f"UI found agent: {agent_name}")


# ====================================================================
# AGT-HS01/S02/S03: API create → UI search
# ====================================================================

class TestSearchViaAPI:
    """Hybrid: API creates agent → UI verifies search behavior."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_AGT_HS01_search_exact(self, agt_page, agt_api):
        """API creates agent → UI searches exact name match."""
        log.info("AGT-HS01 (Hybrid): Search exact match")
        page = agt_page

        result = agt_api.create_agent(name_prefix="SearchExact")
        assert result is not None, "API creation failed"
        agent_name = result.get("agent_name", "")
        log.info(f"API created agent: {agent_name}")

        found = page.search_agent(agent_name)
        assert found, f"Exact search failed for: {agent_name}"

    @pytest.mark.hybrid
    @pytest.mark.sanity
    def test_AGT_HS02_search_partial(self, agt_page, agt_api):
        """API creates agent → UI searches partial name."""
        log.info("AGT-HS02 (Hybrid): Search partial match")
        page = agt_page

        result = agt_api.create_agent(name_prefix="SearchPartial")
        assert result is not None, "API creation failed"
        agent_name = result.get("agent_name", "")

        # Use first 15 chars of the name as partial search
        partial = agent_name[:15] if len(agent_name) > 15 else agent_name
        log.info(f"Partial search: '{partial}' from full name '{agent_name}'")

        found = page.search_agent(partial)
        assert found, f"Partial search failed for: {partial}"

    @pytest.mark.hybrid
    @pytest.mark.sanity
    def test_AGT_HS03_search_case_insensitive(self, agt_page, agt_api):
        """API creates agent → UI searches lowercase version of name."""
        log.info("AGT-HS03 (Hybrid): Search case insensitive")
        page = agt_page

        result = agt_api.create_agent(name_prefix="CaseSearch")
        assert result is not None, "API creation failed"
        agent_name = result.get("agent_name", "")

        # Search with lowercase
        lower_name = agent_name.lower()
        log.info(f"Case-insensitive search: '{lower_name}' from '{agent_name}'")

        found = page.search_agent(lower_name)
        # Case-insensitive search may not be supported — document behavior
        if found:
            log.info(f"Case-insensitive search works: '{lower_name}' found '{agent_name}'")
        else:
            log.warning(
                f"Case-insensitive search NOT supported: "
                f"'{lower_name}' did not find '{agent_name}'"
            )


# ====================================================================
# AGT-HP01: API create → UI view read-only
# ====================================================================

class TestViewReadOnly:
    """Hybrid: API creates agent → UI opens View and checks read-only mode."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_AGT_HP01_view_readonly(self, agt_page, agt_api):
        """API creates agent → UI View → should be read-only (no Update button)."""
        log.info("AGT-HP01 (Hybrid): View read-only check")
        page = agt_page

        result = agt_api.create_agent(name_prefix="ViewRO")
        assert result is not None, "API creation failed"
        agent_name = result.get("agent_name", "")

        # Search and click View
        page.search_agent(agent_name)
        page.wait_seconds(1)
        page.click_view_button(agent_name)
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
            page.cancel()
        except Exception:
            page.force_close_form_popup()


# ====================================================================
# AGT-HE01: API create → UI edit pre-populated + update
# ====================================================================

class TestEditVerification:
    """Hybrid: API creates agent → UI edits and updates."""

    @pytest.mark.hybrid
    @pytest.mark.smoke
    def test_AGT_HE01_edit_prepopulated_and_update(self, agt_page, agt_api):
        """API creates agent → UI Edit → verify pre-populated + Update button → edit phone → Update."""
        log.info("AGT-HE01 (Hybrid): Edit pre-populated and update")
        page = agt_page

        result = agt_api.create_agent(name_prefix="EditPre")
        assert result is not None, "API creation failed"
        agent_name = result.get("agent_name", "")

        # Search and click Edit
        page.search_agent(agent_name)
        page.wait_seconds(1)
        page.click_edit_button(agent_name)
        page.wait_seconds(2)

        # Verify edit mode (Update button present)
        is_edit = page.is_edit_mode()
        assert is_edit, "Edit popup should have Update button"

        # Verify fields are pre-populated
        values = page.get_form_field_values()
        log.info(f"Edit form values: {values}")
        has_name = bool(values.get("Agent Name", "").strip())
        if has_name:
            log.info(f"Agent Name pre-populated: '{values['Agent Name']}'")
        else:
            log.warning("Agent Name not pre-populated in edit mode")

        # Edit phone number
        from pages.registration.modules.agent.data.agent_data import generate_phone_number
        new_phone = generate_phone_number()
        page._fill_input_by_name("Phone Number", new_phone)
        page.wait_seconds(0.5)

        # Click through steps and Update
        page.click_next()
        page.wait_seconds(1.5)
        page.click_next()
        page.wait_seconds(1.5)
        page.click_next()
        page.wait_seconds(1.5)

        page.update()
        page.wait_seconds(3)

        # Check for success
        swal_title = page.get_swal_title()
        if swal_title and "success" in swal_title.lower():
            log.info(f"Update successful: {swal_title}")
        elif swal_title and "validation" in swal_title.lower():
            log.warning(f"Update validation failed: {swal_title}")
            page._dismiss_swal()
        else:
            log.info(f"Update response: swal='{swal_title}'")

        try:
            page.cancel()
        except Exception:
            page.force_close_form_popup()
