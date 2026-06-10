"""
customer_cleanup.py
-------------------
No-delete cleanup strategy for Customer module tests.

The ERP has NO delete endpoint, no delete button, and no soft-delete
via status=False. This module provides:

  - CleanupTracker: Tracks all created record IDs + metadata
  - CreatedRecord:  Dataclass for individual records
  - generate_reports(): Exports tracked IDs as JSON + CSV
  - deactivate_all(): Optionally marks records inactive via PUT
                     (only if the ERP supports status=False on update)

NEVER implement delete_customer() or cleanup_all() in this module.
"""

import json
import csv
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict

from common.logger import log


@dataclass
class CreatedRecord:
    """Represents a single created customer record for tracking."""
    id: Optional[int]
    company_name: str
    timestamp: str = ""
    prefix: str = ""
    payload_summary: str = ""
    deactivated: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.prefix and "_" in self.company_name:
            self.prefix = self.company_name.split("_")[0]


class CleanupTracker:
    """
    Tracks all customer records created during a test session.

    Since the ERP has NO delete functionality, this tracker serves as
    the cleanup mechanism by:
      1. Recording every created ID with metadata
      2. Generating cleanup reports (JSON + CSV) for manual DB purging
      3. Optionally marking records as inactive via PUT (if supported)

    Usage:
        tracker = CleanupTracker()
        tracker.track(id=123, company_name="AutoCust_20260609_abc12345")
        ...
        # At session end:
        paths = tracker.generate_reports(output_dir="/tmp/reports/cleanup")
        # Or optionally:
        tracker.deactivate_all(api_client)
    """

    def __init__(self):
        self._records: List[CreatedRecord] = []

    # ================================================================
    # Tracking
    # ================================================================

    def track(
        self,
        id,
        company_name: str,
        payload_summary: str = "",
    ) -> CreatedRecord:
        """
        Record a created customer ID for cleanup reporting.

        Args:
            id:               The database ID returned by the API.
            company_name:     The company name (with timestamp+UUID prefix).
            payload_summary:  Brief description of the payload used.

        Returns:
            The CreatedRecord that was tracked.
        """
        record = CreatedRecord(
            id=id,
            company_name=company_name,
            payload_summary=payload_summary,
        )
        self._records.append(record)
        log.info(
            f"[CleanupTracker] Tracked: id={id} "
            f"name='{company_name}' "
            f"total={len(self._records)}"
        )
        return record

    def track_accidental(
        self,
        id,
        company_name: str,
    ) -> CreatedRecord:
        """
        Track an accidentally created record (from create_and_expect_failure
        where the ERP unexpectedly accepted invalid data).

        Args:
            id:           The database ID.
            company_name: The company name.

        Returns:
            The CreatedRecord marked as requiring manual attention.
        """
        record = CreatedRecord(
            id=id,
            company_name=company_name,
            payload_summary="ACCIDENTAL CREATION — invalid payload was accepted, needs manual purge",
        )
        self._records.append(record)
        log.warning(
            f"[CleanupTracker] ACCIDENTAL: id={id} "
            f"name='{company_name}' — must be manually purged!"
        )
        return record

    # ================================================================
    # Reporting
    # ================================================================

    def generate_reports(
        self,
        output_dir: str = None,
    ) -> Dict[str, str]:
        """
        Generate both JSON and CSV cleanup reports.

        Args:
            output_dir: Directory for report files. If None, auto-generates
                        a path under the customer module's reports/cleanup/ dir.

        Returns:
            Dict with keys "json" and "csv" mapping to the generated file paths.
            Empty dict if no records to report.
        """
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
        json_path = os.path.join(output_dir, f"customer_cleanup_{timestamp}.json")
        csv_path = os.path.join(output_dir, f"customer_cleanup_{timestamp}.csv")

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
                fieldnames=["id", "company_name", "timestamp", "prefix",
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
        """
        Attempt to mark all tracked records as inactive via PUT.

        This is BEST-EFFORT only — the ERP may not support setting
        status=False on update. If it does, deactivated records won't
        appear in active listings but still exist in the database.

        Args:
            api_client: An authenticated RhythmERPAPIClient instance.

        Returns:
            Dict with "deactivated" and "failed" counts.
        """
        deactivated = 0
        failed = 0

        for record in self._records:
            if record.deactivated or record.id is None:
                continue

            try:
                # Fetch current record to get full payload for PUT
                detail = api_client.get_entry("Customer", record.id)
                if detail is None:
                    failed += 1
                    continue

                # Set status to False (inactive)
                detail["status"] = False
                result = api_client.update_entry(record.id, detail)

                if result is not None:
                    record.deactivated = True
                    deactivated += 1
                    log.info(
                        f"[CleanupTracker] Deactivated: id={record.id} "
                        f"name='{record.company_name}'"
                    )
                else:
                    failed += 1
                    log.warning(
                        f"[CleanupTracker] Failed to deactivate: "
                        f"id={record.id} name='{record.company_name}'"
                    )
            except Exception as e:
                failed += 1
                log.error(
                    f"[CleanupTracker] Error deactivating id={record.id}: {e}"
                )

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
