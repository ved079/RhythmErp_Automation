import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.logger import log


@pytest.fixture(scope="module")
def api_client():
    from common.erp_api_client import RhythmERPAPIClient
    token = os.environ.get("ERP_TOKEN", "").strip()
    tenant_id = os.environ.get("ERP_TENANT_ID", "711")
    client = RhythmERPAPIClient(tenant_id=tenant_id)
    if token:
        client.login_from_browser(token=token, tenant_id=tenant_id)
    else:
        try:
            client.login()
        except Exception:
            pytest.skip("No ERP token available. Set ERP_TOKEN env var.")
    yield client
    try:
        client.close()
    except Exception:
        pass


@pytest.fixture
def grn_api(api_client):
    from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import GRNAPIUtils
    return GRNAPIUtils(api_client=api_client)


@pytest.fixture
def build_payload():
    from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import build_grn_payload
    return build_grn_payload


@pytest.fixture
def generate_payload():
    from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import generate_grn_payload
    return generate_grn_payload
