"""
api_register_of_loan_utils.py
-------------------------------
Register of Loan-specific API wrapper.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Optional

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.register_of_loan.api.endpoints import SCREEN_NAME
from pages.registration.modules.register_of_loan.data.register_of_loan_data import (
    build_api_payload,
    generate_valid_data,
)
from pages.registration.modules.register_of_loan.utils.register_of_loan_cleanup import (
    CleanupTracker,
)


class RegisterOfLoanAPIUtils:
    """Register of Loan API utility for batch creation and testing."""

    def __init__(self, api_client=None, tracker=None):
        self.client = api_client or RhythmERPAPIClient()
        self.tracker = tracker or CleanupTracker()

    def create_entry(self, data=None, fk_overrides=None):
        if fk_overrides is None:
            fk_overrides = {}
        payload = build_api_payload(data=data, fk_overrides=fk_overrides)
        result = self.client.create_entry(payload)
        if result is not None:
            created_id = result.get("id")
            self.tracker.track(
                id=created_id,
                bank_name=payload.get("bank_name", ""),
                payload_summary="Created via API",
            )
        return result

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        return self.client.get_entry(SCREEN_NAME, entry_id)

    def search_entries(self, search="", page=1, page_size=10):
        return self.client.list_entries(SCREEN_NAME, page=page, page_size=page_size, search=search)

    def generate_unique_payload(self):
        data = generate_valid_data()
        ts = datetime.now().strftime("%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]
        data["bank_name"] = f"Bank {ts}{uuid_short[:4]}"
        return build_api_payload(data=data)

    def generate_cleanup_report(self, output_dir=None):
        return self.tracker.generate_reports(output_dir=output_dir)

    @property
    def tracked_count(self) -> int:
        return self.tracker.count
