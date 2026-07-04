"""
miscellaneous_documents_cleanup.py
-----------------------------------
Cleanup tracker for Miscellaneous Documents batch creation.
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
    name: str = ""
    document_no: str = ""
    timestamp: str = ""
    payload_summary: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CleanupTracker:
    def __init__(self):
        self.records: List[CreatedRecord] = []
        self._accidental: List[CreatedRecord] = []

    def track(self, id, name="", document_no="", payload_summary=""):
        self.records.append(CreatedRecord(
            id=id, name=str(name), document_no=str(document_no),
            payload_summary=payload_summary,
        ))

    def track_accidental(self, id, name="", document_no="", payload_summary=""):
        self._accidental.append(CreatedRecord(
            id=id, name=str(name), document_no=str(document_no),
            payload_summary=payload_summary,
        ))

    @property
    def count(self) -> int:
        return len(self.records)

    def generate_reports(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "reports", "cleanup"
            )
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(output_dir, f"miscellaneous_documents_cleanup_{timestamp}")

        paths = {}
        json_path = f"{base}.json"
        with open(json_path, "w") as f:
            json.dump({
                "created": [
                    {"id": r.id, "name": r.name, "document_no": r.document_no,
                     "timestamp": r.timestamp, "summary": r.payload_summary}
                    for r in self.records
                ],
                "accidental": [
                    {"id": r.id, "name": r.name, "document_no": r.document_no,
                     "timestamp": r.timestamp, "summary": r.payload_summary}
                    for r in self._accidental
                ],
            }, f, indent=2)
        paths["json"] = json_path

        csv_path = f"{base}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "document_no", "timestamp", "summary"])
            for r in self.records:
                writer.writerow([r.id, r.name, r.document_no, r.timestamp, r.payload_summary])
        paths["csv"] = csv_path

        return paths
