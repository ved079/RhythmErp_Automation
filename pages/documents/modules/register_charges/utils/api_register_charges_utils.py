"""
api_register_charges_utils.py
------------------------------
Register Charges-specific API wrapper.

Wraps RhythmERPAPIClient with Register Charges helpers.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from common.erp_api_client import RhythmERPAPIClient
from pages.documents.modules.register_charges.api.endpoints import SCREEN_NAME
from pages.documents.modules.register_charges.data.register_charges_data import (
    build_api_payload,
    generate_valid_data,
    generate_roc_charge_id,
    TYPE_OF_CHARGE_IDS,
)
from pages.documents.modules.register_charges.utils.register_charges_cleanup import (
    CleanupTracker,
    CreatedRecord,
)


class RegisterChargesAPIUtils:
    """Register Charges API utility for batch creation and testing."""

    def __init__(self, api_client=None, tracker=None):
        self.client = api_client or RhythmERPAPIClient()
        self.tracker = tracker or CleanupTracker()

    def create_entry(self, data=None, fk_overrides=None, roc_prefix="1"):
        """Create a Register Charges entry via API and track the ID.

        Args:
            data: Override data dict. If None, auto-generates.
            fk_overrides: FK ID overrides (e.g. type_of_charge_ref_id).
            roc_prefix: Prefix for ROC charge ID.

        Returns:
            Response JSON dict on success, None on failure.
        """
        if fk_overrides is None:
            fk_overrides = {}

        payload = build_api_payload(data=data, fk_overrides=fk_overrides)
        payload["roc_charge_id"] = generate_roc_charge_id(prefix=roc_prefix)

        result = self.client.create_entry(payload)

        if result is not None:
            created_id = result.get("id")
            self.tracker.track(
                id=created_id,
                roc_charge_id=payload.get("roc_charge_id", ""),
                payload_summary=f"Created via API",
            )
        return result

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Fetch a single entry by ID."""
        return self.client.get_entry(SCREEN_NAME, entry_id)

    def search_entries(self, search="", page=1, page_size=10):
        """Search/list entries with pagination."""
        return self.client.list_entries(SCREEN_NAME, page=page, page_size=page_size, search=search)

    def generate_unique_payload(self, roc_prefix="1"):
        """Generate a unique payload with timestamped ROC ID."""
        data = generate_valid_data()
        payload = build_api_payload(data)
        ts = datetime.now().strftime("%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]
        payload["roc_charge_id"] = f"{roc_prefix}{ts}{uuid_short[:4]}"
        return payload

    def generate_cleanup_report(self, output_dir=None):
        return self.tracker.generate_reports(output_dir=output_dir)

    @property
    def tracked_count(self) -> int:
        return self.tracker.count
