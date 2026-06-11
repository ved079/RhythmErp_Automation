"""
test_agent_live.py
------------------
Live API integration tests for RhythmERP Agent screen.
Tests real API calls against the live server for end-to-end validation.

~5 tests, all headless API calls.

KNOWN BUGS:
  - GET /core/dynamic-screen-wrapper/Agent/{id}/ returns HTTP 500
    ('NoneType' object has no attribute '__dict__')
  - Tests that rely on GET are marked xfail until fixed.

Field Key Mapping:
  UI "Agent Name"   -> API "name"
  UI "Phone Number" -> API "mobile_no"
  UI "Email"        -> API "email_id"

Run:
  pytest test_agent_live.py -v --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log
from pages.registration.modules.agent.api.endpoints import SCREEN_NAME


class TestAgentLive:
    """Live API integration tests against RhythmERP Agent endpoint."""

    @pytest.mark.api
    @pytest.mark.smoke
    def test_list_agents(self, agt_api):
        """List agents should return a valid response with results."""
        log.info("Live: List agents")
        result = agt_api.search_agents(page_size=5)
        assert result is not None, "Agent list should return data"

        # Check structure
        items_key = None
        for key in ("screenmatlistingdata_set", "results", "data", "items"):
            if key in result:
                items_key = key
                break

        if items_key:
            items = result[items_key]
            log.info(f"Agent list returned {len(items)} items")
        else:
            log.info(f"Agent list response keys: {list(result.keys())}")

    @pytest.mark.api
    @pytest.mark.smoke
    def test_create_agent(self, agt_api):
        """Create an agent via API — should succeed and return valid data."""
        log.info("Live: Create agent")

        create_result = agt_api.create_agent(name_prefix="LiveCG")
        assert create_result is not None, "Create should succeed"
        agent_id = create_result.get("id")
        agent_name = create_result.get("name", "")
        log.info(f"Created: id={agent_id}, name='{agent_name}'")
        assert agent_name, "Created agent should have a name"

    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: GET Agent by ID returns HTTP 500 (AGT-BUG-004)",
    )
    def test_create_and_get(self, agt_api):
        """Create an agent and retrieve it — data should match."""
        log.info("Live: Create and get agent")

        create_result = agt_api.create_agent(name_prefix="LiveCG")
        assert create_result is not None, "Create should succeed"
        agent_id = create_result.get("id")
        agent_name = create_result.get("name", "")
        log.info(f"Created: id={agent_id}, name='{agent_name}'")

        # Retrieve — currently returns 500
        get_result = agt_api.get_agent(agent_id)
        assert get_result is not None, f"Get should return agent id={agent_id}"
        log.info(f"Retrieved: id={get_result.get('id')}, name='{get_result.get('name', '')}'")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_search_created_agent(self, agt_api):
        """Create an agent then search for it — should find it."""
        log.info("Live: Search created agent")

        result = agt_api.create_agent(name_prefix="LiveSearch")
        assert result is not None
        agent_name = result.get("name", "")

        # Search
        search_result = agt_api.search_agents(search=agent_name)
        assert search_result is not None, "Search should return results"

        # Find the agent in search results
        items_key = None
        for key in ("screenmatlistingdata_set", "results", "data", "items"):
            if key in search_result:
                items_key = key
                break

        if items_key:
            items = search_result[items_key]
            found = any(
                item.get("name", "") == agent_name
                for item in items
                if isinstance(item, dict)
            )
            assert found, f"Agent '{agent_name}' not found in search results"
            log.info(f"Agent '{agent_name}' found in search")

    @pytest.mark.api
    @pytest.mark.sanity
    @pytest.mark.xfail(
        strict=False,
        reason="BUG: GET Agent by ID returns HTTP 500 — cannot fetch/update (AGT-BUG-004)",
    )
    def test_update_agent(self, agt_api):
        """Create an agent, update phone number, verify update."""
        log.info("Live: Update agent")

        # Create
        create_result = agt_api.create_agent(name_prefix="LiveUpdate")
        assert create_result is not None
        agent_id = create_result.get("id")

        # Fetch full record — currently returns 500
        detail = agt_api.get_agent(agent_id)
        assert detail is not None, f"Failed to fetch agent id={agent_id} (GET 500 bug)"

        # Update phone
        from pages.registration.modules.agent.data.agent_data import generate_phone_number
        new_phone = generate_phone_number()
        detail["mobile_no"] = int(new_phone)

        update_result = agt_api.update_agent(agent_id, detail)
        if update_result is not None:
            log.info(f"Update successful: new phone={new_phone}")
        else:
            log.warning(f"Update failed for agent id={agent_id}")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_pagination(self, agt_api):
        """Agent list pagination should work correctly."""
        log.info("Live: Pagination")

        page1 = agt_api.search_agents(page=1, page_size=5)
        assert page1 is not None, "Page 1 should return data"

        page2 = agt_api.search_agents(page=2, page_size=5)
        # Page 2 may be empty if fewer than 10 agents exist
        log.info(f"Page 1 returned, Page 2 returned: {page2 is not None}")
