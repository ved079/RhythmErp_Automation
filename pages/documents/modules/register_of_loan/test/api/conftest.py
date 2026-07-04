"""
conftest.py — API-only fixtures for Register of Loan tests.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient, ErpApiClient


@pytest.fixture(scope="module")
def api_client():
    client = RhythmERPAPIClient()
    token = os.environ.get("ERP_TOKEN")
    tenant = os.environ.get("ERP_TENANT", "711")
    if token:
        client.login_from_browser(token=token, tenant_id=tenant)
    else:
        client.login()
    result = client.list_entries("Register of Loan", page=1, page_size=1)
    if not result:
        pytest.skip("Register of Loan screen not accessible")
    yield client
    client.close()


@pytest.fixture(scope="module")
def erp_client():
    client = ErpApiClient()
    token = os.environ.get("ERP_TOKEN")
    if token:
        tenant = os.environ.get("ERP_TENANT", "711")
        client.set_session_from_token(token, tenant_id=tenant)
    else:
        client.login()
    yield client
    client.close()
