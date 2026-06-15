import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.erp_api_client import RhythmERPAPIClient


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: Cross-module integration tests")
    config.addinivalue_line("markers", "chain: Full chain tests")


@pytest.fixture(scope="module")
def api_client():
    token = os.environ.get("ERP_TOKEN", "")
    tenant_id = os.environ.get("ERP_TENANT_ID", "711")
    client = RhythmERPAPIClient(tenant_id=tenant_id)
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        client.login()
    return client


@pytest.fixture
def purchase_chain(api_client):
    from pages.private_b2b.scripts.purchase_chain import PurchaseChain
    return PurchaseChain(client=api_client, delay=0.2)
