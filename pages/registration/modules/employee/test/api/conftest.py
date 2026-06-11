"""
conftest.py — API-only fixtures for Employee fast tests.
No browser needed. All tests run via HTTP requests.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log


def pytest_configure(config):
    """Register custom markers for API test categorization."""
    config.addinivalue_line("markers", "api: API payload and CRUD tests")
    config.addinivalue_line("markers", "schema: Schema and structure verification")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "validation: Field validation boundary tests")
    config.addinivalue_line("markers", "bug: Test documenting a known bug")
    config.addinivalue_line("markers", "regression: Regression test suite")


@pytest.fixture(scope="session")
def api_client():
    """Create an authenticated API client for Employee tests."""
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

    # Verify auth works by listing Employee entries
    from pages.registration.modules.employee.api.endpoints import SCREEN_NAME
    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        pytest.skip("ERP authentication failed. Check token/credentials.")

    yield client
    client.close()


@pytest.fixture(scope="session")
def emp_api():
    """EmployeeAPIUtils — authenticated API client + cleanup tracker.

    Session-scoped so the tracker accumulates all created IDs across
    the entire test session. Cleanup report is generated at session end.
    """
    from common.erp_api_client import RhythmERPAPIClient
    from pages.registration.modules.employee.utils.api_employee_utils import EmployeeAPIUtils
    from pages.registration.modules.employee.utils.employee_cleanup import CleanupTracker
    from pages.registration.modules.employee.api.endpoints import SCREEN_NAME

    tracker = CleanupTracker()
    client = RhythmERPAPIClient()

    # Authenticate — try token first, then login
    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "681")

    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")

    # Verify auth works
    result = client.list_entries(SCREEN_NAME, page=1, page_size=1)
    if not result:
        pytest.skip("ERP authentication failed. Check token/credentials.")

    api = EmployeeAPIUtils(api_client=client, tracker=tracker)

    yield api

    # Generate cleanup report at session end
    if tracker.count > 0:
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "reports", "cleanup"
        )
        try:
            paths = tracker.generate_reports(output_dir=output_dir)
            if paths:
                log.info(f"[EmployeeAPI] Cleanup report generated: {paths}")
        except Exception as e:
            log.warning(f"[EmployeeAPI] Cleanup report generation failed: {e}")

    client.close()
