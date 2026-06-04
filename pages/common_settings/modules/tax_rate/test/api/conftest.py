"""conftest.py — API-only fixtures for Tax Rate fast tests."""
import os, sys, pytest
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

def pytest_configure(config):
    config.addinivalue_line("markers", "api: API payload and CRUD tests")
    config.addinivalue_line("markers", "schema: Schema and structure verification")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")

@pytest.fixture(scope="session")
def api_client():
    from common.erp_api_client import RhythmERPAPIClient
    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "599")
    client = RhythmERPAPIClient()
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try: client.login()
        except: pytest.skip("No ERP token available.")
    yield client
    client.close()
