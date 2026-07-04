"""
register_of_loan_cleanup.py
----------------------------
Cleanup tracker for Register of Loan batch creation.
"""

import json
import csv
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List


@dataclass
class CreatedRecord:
    id: int
    bank_name: str = ""
    timestamp: str = ""
    payload_summary: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CleanupTracker:
    """Tracks created entry IDs for cleanup reporting."""

    def __init__(self):
        self.records: List[CreatedRecord] = []
        self._accidental: List[CreatedRecord] = []

    def track(self, id, bank_name="", payload_summary=""):
        self.records.append(CreatedRecord(
            id=id, bank_name=str(bank_name), payload_summary=payload_summary,
        ))

    def track_accidental(self, id, bank_name="", payload_summary=""):
        self._accidental.append(CreatedRecord(
            id=id, bank_name=str(bank_name), payload_summary=payload_summary,
        ))

    @property
    def count(self) -> int:
        return len(self.records)

    def generate_reports(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "..", "reports", "cleanup"
            )
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(output_dir, f"register_of_loan_cleanup_{timestamp}")

        paths = {}
        json_path = f"{base}.json"
        with open(json_path, "w") as f:
            json.dump({
                "created": [
                    {"id": r.id, "bank_name": r.bank_name,
                     "timestamp": r.timestamp, "summary": r.payload_summary}
                    for r in self.records
                ],
                "accidental": [
                    {"id": r.id, "bank_name": r.bank_name,
                     "timestamp": r.timestamp, "summary": r.payload_summary}
                    for r in self._accidental
                ],
            }, f, indent=2)
        paths["json"] = json_path

        csv_path = f"{base}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "bank_name", "timestamp", "summary"])
            for r in self.records:
                writer.writerow([r.id, r.bank_name, r.timestamp, r.payload_summary])
        paths["csv"] = csv_path

        return paths
