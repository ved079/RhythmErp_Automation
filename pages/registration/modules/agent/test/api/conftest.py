"""
conftest.py — Agent API test fixtures (deep API sub-directory)
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log
from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.agent.utils.api_agent_utils import AgentAPIUtils


@pytest.fixture(scope="session")
def agt_api():
    """Authenticated Agent API utility — session scoped for deep API tests."""
    client = RhythmERPAPIClient()
    client.login()
    api = AgentAPIUtils(api_client=client)
    yield api
    try:
        api.tracker.generate_reports()
    except Exception as e:
        log.warning(f"Failed to generate cleanup report: {e}")
