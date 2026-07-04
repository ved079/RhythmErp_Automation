"""
test_live.py
------------
Live API tests for Constituent Documents — requires --token and --tenant.
"""

import pytest
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


pytestmark = pytest.mark.skipif(
    not os.environ.get("ERP_TOKEN"),
    reason="ERP_TOKEN not set; skipping live API tests",
)


class TestConstituentDocumentsLive:
    def test_create_entry(self, api_client, sample_payload):
        result = api_client.create_entry_with_defaults(endpoint_slug="", payload=sample_payload)
        assert result is not None
        assert "id" in result
        assert result.get("cin_no") == sample_payload["cin_no"]
        assert result.get("cin_date") == sample_payload["cin_date"]

    def test_get_entry(self, api_client):
        import uuid
        cin = "L" + uuid.uuid4().hex[:12].upper() + "AB" + uuid.uuid4().hex[:6].upper() + "XYZ000001"
        payload = {
            "id": "",
            "attribute_name": "Constituent Documents",
            "cin_no": cin,
            "cin_date": "2025-03-15T18:30:00Z",
            "details": [],
        }
        result = api_client.create_entry_with_defaults(endpoint_slug="", payload=payload)
        if result and "id" in result:
            entry_id = result["id"]
            fetched = api_client.get_entry("Constituent Documents", entry_id)
            assert fetched is not None
            assert fetched.get("cin_no") == result.get("cin_no")

    def test_list_entries(self, api_client):
        result = api_client.list_entries("Constituent Documents", page=1, page_size=5)
        assert result is not None
        data = result.get("screenmatlistingdata_set", [])
        assert isinstance(data, list)
