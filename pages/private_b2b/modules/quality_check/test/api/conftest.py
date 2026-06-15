import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

import pytest

from common.erp_api_client import RhythmERPAPIClient
from pages.private_b2b.modules.quality_check.utils.api_quality_check_utils import QCAPIUtils
from pages.private_b2b.modules.quality_check.data.quality_check_data import (
    build_qc_payload,
    generate_qc_payload,
)


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
def qc_api(api_client):
    return QCAPIUtils(api_client=api_client)


@pytest.fixture
def build_payload():
    return build_qc_payload


@pytest.fixture
def generate_payload():
    return generate_qc_payload
