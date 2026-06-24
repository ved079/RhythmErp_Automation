import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    config.addinivalue_line("markers", "calculation: Computed field verification (no network)")
    config.addinivalue_line("markers", "live: Tests that require a live ERP token (ERP_TOKEN env var)")
    config.addinivalue_line("markers", "integrity: Data consistency and mutation tests")
    config.addinivalue_line("markers", "performance: Speed and benchmark tests")
    config.addinivalue_line("markers", "schema: Schema and structure verification")


@pytest.fixture(scope="session")
def pb_api():
    token = os.environ.get("ERP_TOKEN", "")
    tenant = os.environ.get("ERP_TENANT_ID", "751")
    if not token:
        pytest.skip("ERP_TOKEN not set — skipping live tests")

    from common.erp_api_client import RhythmERPAPIClient
    from pages.private_b2b.modules.purchase_booking.utils.api_purchase_booking_utils import PBAPIUtils

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=tenant)
    return PBAPIUtils(client)
