"""
test_live.py
------------
Live API tests for Miscellaneous Documents — requires --token and --tenant.
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


class TestMiscellaneousDocumentsLive:
    def test_create_entry(self, api_client, sample_payload):
        result = api_client.create_entry_with_defaults(endpoint_slug="", payload=sample_payload)
        assert result is not None
        assert "id" in result
        assert result.get("name") == sample_payload["name"]
        assert result.get("document_no") == sample_payload["document_no"]

    def test_get_entry(self, api_client):
        import uuid
        payload = {
            "id": "",
            "attribute_name": "Miscellaneous Documents",
            "name": f"Test Entry {uuid.uuid4().hex[:8]}",
            "document_no": int(uuid.uuid4().hex[:8], 16) % 90000 + 10000,
            "registered_date": "2025-03-15T18:30:00Z",
            "brief_details": "Integration test entry",
        }
        result = api_client.create_entry_with_defaults(endpoint_slug="", payload=payload)
        if result and "id" in result:
            entry_id = result["id"]
            fetched = api_client.get_entry("Miscellaneous Documents", entry_id)
            assert fetched is not None
            assert fetched.get("name") == result.get("name")

    def test_list_entries(self, api_client):
        result = api_client.list_entries("Miscellaneous Documents", page=1, page_size=5)
        assert result is not None
        data = result.get("screenmatlistingdata_set", [])
        assert isinstance(data, list)
