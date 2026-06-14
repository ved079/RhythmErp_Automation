"""
conftest.py
-----------
Pytest fixtures for Miscellaneous Documents API tests.
"""

import pytest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common.erp_api_client import ErpApiClient
from pages.registration.modules.miscellaneous_documents.data.miscellaneous_documents_data import (
    generate_batch_payloads,
)


def pytest_addoption(parser):
    parser.addoption("--token", default=None, help="Auth token for ERP")
    parser.addoption("--tenant", default=711, type=int, help="Tenant ID")
    parser.addoption("--base-url", default="https://rhythmerp.algorhythms.in", help="Base ERP URL")


@pytest.fixture(scope="session")
def token(request):
    t = request.config.getoption("--token")
    if not t:
        t = os.environ.get("ERP_TOKEN")
    return t


@pytest.fixture(scope="session")
def tenant(request):
    return request.config.getoption("--tenant")


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def api_client(token, tenant, base_url):
    return ErpApiClient(
        token=token,
        tenant_id=tenant,
        base_url=base_url,
        screen_name="Miscellaneous Documents",
    )


@pytest.fixture(scope="function")
def sample_payload():
    return generate_batch_payloads(1)[0]
