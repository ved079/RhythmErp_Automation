"""
api_constituent_documents_utils.py
-----------------------------------
Constituent Documents-specific API wrapper.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from common.erp_api_client import RhythmERPAPIClient
from pages.documents.modules.constituent_documents.api.endpoints import SCREEN_NAME
from pages.documents.modules.constituent_documents.data.constituent_documents_data import (
    build_api_payload,
    generate_valid_data,
    generate_cin_no,
)
from pages.documents.modules.constituent_documents.utils.constituent_documents_cleanup import (
    CleanupTracker,
)


class ConstituentDocumentsAPIUtils:
    def __init__(self, api_client=None, tracker=None):
        self.client = api_client or RhythmERPAPIClient()
        self.tracker = tracker or CleanupTracker()

    def create_entry(self, data=None):
        payload = build_api_payload(data=data)
        result = self.client.create_entry(payload)
        if result is not None:
            created_id = result.get("id")
            self.tracker.track(
                id=created_id,
                cin_no=payload.get("cin_no", ""),
                payload_summary="Created via API",
            )
        return result

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        return self.client.get_entry(SCREEN_NAME, entry_id)

    def search_entries(self, search="", page=1, page_size=10):
        return self.client.list_entries(SCREEN_NAME, page=page, page_size=page_size, search=search)

    def generate_unique_payload(self):
        data = generate_valid_data()
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]
        data["cin_no"] = "L" + ts + uuid_short[:6] + "AB" + uuid_short[6:] + "XYZ000001"
        return build_api_payload(data=data)

    def generate_cleanup_report(self, output_dir=None):
        return self.tracker.generate_reports(output_dir=output_dir)

    @property
    def tracked_count(self) -> int:
        return self.tracker.count
