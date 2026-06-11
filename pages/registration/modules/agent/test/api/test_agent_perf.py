"""
test_agent_perf.py
------------------
Performance baseline tests for RhythmERP Agent API.
Measures response times for key Agent API operations.

~5 tests, all headless API calls.

Run:
  pytest test_agent_perf.py -v --tb=short
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.logger import log


class TestAgentPerformance:
    """Verify Agent API response times meet baseline expectations."""

    CREATE_BASELINE_S = 3.0  # Create should complete within 3s
    LIST_BASELINE_S = 2.0    # List should complete within 2s
    GET_BASELINE_S = 2.0     # Get detail should complete within 2s
    SCHEMA_BASELINE_S = 2.0  # Schema should complete within 2s

    @pytest.mark.api
    @pytest.mark.sanity
    def test_create_response_time(self, agt_api):
        """Agent create should respond within baseline time."""
        log.info("Perf: Create response time")
        start = time.time()
        result = agt_api.create_agent(name_prefix="PerfCreate")
        elapsed = time.time() - start
        log.info(f"Create response time: {elapsed:.2f}s (baseline: {self.CREATE_BASELINE_S}s)")

        if result is not None:
            assert elapsed < self.CREATE_BASELINE_S, \
                f"Create took {elapsed:.2f}s — exceeds baseline {self.CREATE_BASELINE_S}s"
        else:
            log.warning(f"Create failed but took {elapsed:.2f}s")

    @pytest.mark.api
    @pytest.mark.sanity
    def test_list_response_time(self, agt_api):
        """Agent list should respond within baseline time."""
        log.info("Perf: List response time")
        start = time.time()
        result = agt_api.search_agents(page_size=10)
        elapsed = time.time() - start
        log.info(f"List response time: {elapsed:.2f}s (baseline: {self.LIST_BASELINE_S}s)")

        assert result is not None, "List should return results"
        assert elapsed < self.LIST_BASELINE_S, \
            f"List took {elapsed:.2f}s — exceeds baseline {self.LIST_BASELINE_S}s"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_get_response_time(self, agt_api):
        """Agent get-detail should respond within baseline time."""
        log.info("Perf: Get response time")

        # Create an agent first to get its ID
        create_result = agt_api.create_agent(name_prefix="PerfGet")
        assert create_result is not None, "Need to create agent for get test"
        agent_id = create_result.get("id")

        start = time.time()
        result = agt_api.get_agent(agent_id)
        elapsed = time.time() - start
        log.info(f"Get response time: {elapsed:.2f}s (baseline: {self.GET_BASELINE_S}s)")

        assert result is not None, f"Get for id={agent_id} should return data"
        assert elapsed < self.GET_BASELINE_S, \
            f"Get took {elapsed:.2f}s — exceeds baseline {self.GET_BASELINE_S}s"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_schema_response_time(self, agt_api):
        """Agent schema should respond within baseline time."""
        log.info("Perf: Schema response time")
        from pages.registration.modules.agent.api.endpoints import SCREEN_NAME

        start = time.time()
        result = agt_api.client.get_screen_schema(SCREEN_NAME)
        elapsed = time.time() - start
        log.info(f"Schema response time: {elapsed:.2f}s (baseline: {self.SCHEMA_BASELINE_S}s)")

        assert result is not None, "Schema should return data"
        assert elapsed < self.SCHEMA_BASELINE_S, \
            f"Schema took {elapsed:.2f}s — exceeds baseline {self.SCHEMA_BASELINE_S}s"

    @pytest.mark.api
    @pytest.mark.sanity
    def test_search_response_time(self, agt_api):
        """Agent search with query should respond within baseline time."""
        log.info("Perf: Search response time")

        # Create an agent to search for
        create_result = agt_api.create_agent(name_prefix="PerfSearch")
        agent_name = create_result.get("agent_name", "") if create_result else ""

        start = time.time()
        result = agt_api.search_agents(search=agent_name)
        elapsed = time.time() - start
        log.info(f"Search response time: {elapsed:.2f}s (baseline: {self.LIST_BASELINE_S}s)")

        assert result is not None, "Search should return results"
        assert elapsed < self.LIST_BASELINE_S, \
            f"Search took {elapsed:.2f}s — exceeds baseline {self.LIST_BASELINE_S}s"
