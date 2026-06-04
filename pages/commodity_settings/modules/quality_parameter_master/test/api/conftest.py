"""
conftest.py — API-only fixtures for Quality Parameter Master fast tests.
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


@pytest.fixture(scope="session")
def api_client():
    """Create an authenticated API client for Quality Parameter Master tests."""
    from common.erp_api_client import RhythmERPAPIClient

    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "599")

    client = RhythmERPAPIClient()
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")

    yield client
    client.close()
