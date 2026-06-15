"""
batch_create.py — Goods Receipt Note batch creation script.

Usage:
    python batch_create.py --token <jwt> --tenant 711 --count 5
    python batch_create.py --token <jwt> --tenant 711 --supplier 1 --count 3 --dry-run

Uses RhythmERPAPIClient + GRNAPIUtils (shared auth pattern).
"""

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.private_b2b.modules.goods_receipt_note.data.goods_receipt_note_data import (
    generate_grn_payload,
    compute_expected_results,
)
from pages.private_b2b.modules.goods_receipt_note.utils.api_goods_receipt_note_utils import (
    GRNAPIUtils,
)


def main():
    parser = argparse.ArgumentParser(description="Batch create GRN entries")
    parser.add_argument("--token", default="", help="ERP JWT token")
    parser.add_argument("--tenant", default="711", help="Tenant ID")
    parser.add_argument("--count", type=int, default=5, help="Number of GRNs to create")
    parser.add_argument("--supplier", type=int, default=None, help="Supplier ref ID (random if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without creating")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between creates (seconds)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    api = GRNAPIUtils(client)

    fk_overrides = {}
    if args.supplier is not None:
        fk_overrides["supplier_ref_id"] = args.supplier

    payloads = []
    for _ in range(args.count):
        payloads.append(generate_grn_payload(fk_overrides=fk_overrides or None))

    if args.dry_run:
        print(f"\n{'=' * 60}")
        print(f"DRY RUN: {args.count} GRN payload(s) generated")
        print(f"{'=' * 60}")
        for i, p in enumerate(payloads):
            expected = compute_expected_results(p)
            print(f"\n--- GRN [{i + 1}/{args.count}] ---")
            print(json.dumps(p, indent=2, default=str))
            print(f"  Expected master total: {expected['master_total']}")
        print(f"\nDry run complete. No entries created.")
        return

    print(f"\n{'=' * 60}")
    print(f"Creating {args.count} GRN(s)...")
    print(f"{'=' * 60}")

    successes = 0
    for i, payload in enumerate(payloads, 1):
        try:
            data = api.create_grn(payload)
            if data:
                successes += 1
                entry_id = data.get("id") or data.get("entry_id")
                ref_no = data.get("transaction_ref_no", str(entry_id))
                print(f"  [{i}/{args.count}] Created GRN ID={entry_id}, ref={ref_no}")
            else:
                print(f"  [{i}/{args.count}] FAILED (status {api._last_status})")
        except Exception as e:
            print(f"  [{i}/{args.count}] ERROR: {e}")

        if args.delay and i < args.count:
            time.sleep(args.delay)

    print(f"\n{'=' * 60}")
    print(f"Batch complete: {successes}/{args.count} succeeded")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
