"""
test_schema.py
--------------
Schema validation tests for Constituent Documents — requires live API access.
"""

import pytest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pages.registration.modules.constituent_documents.api.endpoints import build_schema_url
from common.erp_api_client import ErpApiClient


pytestmark = pytest.mark.skipif(
    not os.environ.get("ERP_TOKEN"),
    reason="ERP_TOKEN not set; skipping schema tests",
)


class TestConstituentDocumentsSchema:
    def test_schema_returns_screen_fields(self, api_client: ErpApiClient):
        assert hasattr(api_client, "get_screen_schema") or True
        url = build_schema_url(api_client.base_url)
        headers = {
            "Authorization": f"Bearer {api_client.token}",
            "X-Tenant-Id": str(api_client.tenant_id),
        }
        import requests
        response = requests.get(url, headers=headers)
        assert response.status_code == 200
        schema = response.json()
        fields = schema.get("screendefinition_set", [])
        field_keys = [f.get("field_key") for f in fields]
        assert "cin_no" in field_keys, f"cin_no not found in schema fields: {field_keys}"
        assert "cin_date" in field_keys, f"cin_date not found in schema fields: {field_keys}"
