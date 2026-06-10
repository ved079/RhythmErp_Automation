"""
conftest.py — API-only fixtures for Bank fast tests.
No browser needed. All tests validate in-memory payload generation.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    """Register custom markers for API test categorization."""
    config.addinivalue_line("markers", "api: API payload and CRUD tests")
    config.addinivalue_line("markers", "schema: Schema and structure verification")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "live_api: Live API CRUD tests against real ERP")


@pytest.fixture(scope="session")
def api_client():
    """Create an authenticated API client for Bank tests.
    Uses token from environment variable or tries login.
    """
    from common.erp_api_client import RhythmERPAPIClient

    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "681")

    client = RhythmERPAPIClient()
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")

    # Verify auth works
    result = client.list_entries("Bank", page=1, page_size=1)
    if not result:
        pytest.skip("ERP authentication failed. Check token/credentials.")

    yield client
    client.close()
