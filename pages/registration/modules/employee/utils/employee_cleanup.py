"""
employee_cleanup.py
-------------------
No-delete cleanup strategy for Employee module tests.

The ERP has NO delete endpoint, no delete button, and no soft-delete
via status=False. This module provides:

  - CleanupTracker: Tracks all created record IDs + metadata
  - CreatedRecord:  Dataclass for individual records
  - generate_reports(): Exports tracked IDs as JSON + CSV

NEVER implement delete_employee() or cleanup_all() in this module.
"""

import json
import csv
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict

from common.logger import log


@dataclass
class CreatedRecord:
    """Represents a single created employee record for tracking."""
    id: Optional[int]
    employee_name: str
    timestamp: str = ""
    prefix: str = ""
    payload_summary: str = ""
    deactivated: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        # Derive prefix from name (first word before space or the whole name)
        if not self.prefix and self.employee_name:
            if " " in self.employee_name:
                self.prefix = self.employee_name.split(" ")[0]
            else:
                self.prefix = self.employee_name[:10]
        elif not self.employee_name:
            self.employee_name = "<null>"


class CleanupTracker:
    """
    Tracks all employee records created during a test session.

    Since the ERP has NO delete functionality, this tracker serves as
    the cleanup mechanism by:
      1. Recording every created ID with metadata
      2. Generating cleanup reports (JSON + CSV) for manual DB purging
      3. Optionally marking records as inactive via PUT (if supported)

    Usage:
        tracker = CleanupTracker()
        tracker.track(id=123, employee_name="Rajesh Sharma")
        ...
        # At session end:
        paths = tracker.generate_reports(output_dir="/tmp/reports/cleanup")
    """

    def __init__(self):
        self._records: List[CreatedRecord] = []

    # ================================================================
    # Tracking
    # ================================================================

    def track(
        self,
        id,
        employee_name: str,
        payload_summary: str = "",
    ) -> CreatedRecord:
        """Record a created employee ID for cleanup reporting."""
        record = CreatedRecord(
            id=id,
            employee_name=employee_name,
            payload_summary=payload_summary,
        )
        self._records.append(record)
        log.info(
            f"[CleanupTracker] Tracked: id={id} "
            f"name='{employee_name}' "
            f"total={len(self._records)}"
        )
        return record

    def track_accidental(
        self,
        id,
        employee_name: str,
    ) -> CreatedRecord:
        """Track an accidentally created record (invalid payload accepted)."""
        record = CreatedRecord(
            id=id,
            employee_name=employee_name,
            payload_summary="ACCIDENTAL CREATION — invalid payload was accepted, needs manual purge",
        )
        self._records.append(record)
        log.warning(
            f"[CleanupTracker] ACCIDENTAL: id={id} "
            f"name='{employee_name}' — must be manually purged!"
        )
        return record

    # ================================================================
    # Reporting
    # ================================================================

    def generate_reports(
        self,
        output_dir: str = None,
    ) -> Dict[str, str]:
        """Generate both JSON and CSV cleanup reports."""
        if not self._records:
            log.info("[CleanupTracker] No tracked records to report.")
            return {}

        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "reports", "cleanup",
            )
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(output_dir, f"employee_cleanup_{timestamp}.json")
        csv_path = os.path.join(output_dir, f"employee_cleanup_{timestamp}.csv")

        # Generate JSON report
        json_data = {
            "generated_at": datetime.now().isoformat(),
            "total_tracked": len(self._records),
            "accidental_count": sum(1 for r in self._records if "ACCIDENTAL" in r.payload_summary),
            "note": (
                "NO-DELETE CONSTRAINT: The ERP has no delete endpoint. "
                "These IDs must be manually purged from the database."
            ),
            "records": [asdict(r) for r in self._records],
        }
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)
        log.info(f"[CleanupTracker] JSON report: {json_path}")

        # Generate CSV report
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "employee_name", "timestamp", "prefix",
                            "payload_summary", "deactivated"],
            )
            writer.writeheader()
            for record in self._records:
                writer.writerow(asdict(record))
        log.info(f"[CleanupTracker] CSV report: {csv_path}")

        return {"json": json_path, "csv": csv_path}

    # ================================================================
    # Optional Deactivation (if PUT supports status=False)
    # ================================================================

    def deactivate_all(self, api_client) -> Dict[str, int]:
        """Attempt to mark all tracked records as inactive via PUT."""
        from pages.registration.modules.employee.api.endpoints import SCREEN_NAME

        deactivated = 0
        failed = 0

        for record in self._records:
            if record.deactivated or record.id is None:
                continue

            try:
                detail = api_client.get_entry(SCREEN_NAME, record.id)
                if detail is None:
                    failed += 1
                    continue

                detail["status"] = False
                result = api_client.update_entry(record.id, detail)

                if result is not None:
                    record.deactivated = True
                    deactivated += 1
                    log.info(
                        f"[CleanupTracker] Deactivated: id={record.id} "
                        f"name='{record.employee_name}'"
                    )
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                log.error(f"[CleanupTracker] Error deactivating id={record.id}: {e}")

        log.info(
            f"[CleanupTracker] Deactivation complete: "
            f"{deactivated} deactivated, {failed} failed"
        )
        return {"deactivated": deactivated, "failed": failed}

    # ================================================================
    # Properties
    # ================================================================

    @property
    def count(self) -> int:
        """Number of tracked records."""
        return len(self._records)

    @property
    def records(self) -> List[CreatedRecord]:
        """Copy of the tracked records list."""
        return list(self._records)

    @property
    def accidental_count(self) -> int:
        """Number of accidentally created records."""
        return sum(1 for r in self._records if "ACCIDENTAL" in r.payload_summary)
