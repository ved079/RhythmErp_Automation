"""
batch_create.py — Purchase Order batch creation script.

Usage:
    python batch_create.py --token <jwt> --tenant 711 --count 3
    python batch_create.py --token <jwt> --tenant 711 --dry-run
    python batch_create.py --token <jwt> --tenant 711 --supplier 1 --count 5

Uses RhythmERPAPIClient + POAPIUtils (shared auth pattern).
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
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payload,
    compute_expected_results,
)
from pages.private_b2b.modules.purchase_order.utils.api_purchase_order_utils import (
    POAPIUtils,
)


def main():
    parser = argparse.ArgumentParser(description="Batch create Purchase Orders")
    parser.add_argument("--token", default="", help="ERP JWT token")
    parser.add_argument("--tenant", default="711", help="Tenant ID")
    parser.add_argument("--count", type=int, default=1, help="Number of POs to create")
    parser.add_argument("--supplier", type=int, default=None, help="Supplier ref ID (random if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without creating")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between creates (seconds)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=args.tenant)
    api = POAPIUtils(client)

    fk_overrides = {}
    if args.supplier is not None:
        fk_overrides["supplier_ref_id"] = args.supplier

    payloads = []
    for _ in range(args.count):
        payloads.append(generate_po_payload(fk_overrides=fk_overrides or None))

    if args.dry_run:
        print(f"\n{'=' * 60}")
        print(f"DRY RUN: {args.count} PO payload(s) generated")
        print(f"{'=' * 60}")
        for i, p in enumerate(payloads):
            expected = compute_expected_results(p)
            print(f"\n--- PO [{i + 1}/{args.count}] ---")
            print(json.dumps(p, indent=2, default=str))
            print(f"  Expected totals: amount={expected['txn_currency_total_amount']}, "
                  f"discount={expected['txn_currency_discount_amount']}, "
                  f"interest={expected['txn_currency_interest_amount']}")
        print(f"\nDry run complete. No entries created.")
        return

    print(f"\n{'=' * 60}")
    print(f"Creating {args.count} Purchase Order(s)...")
    print(f"{'=' * 60}")

    results = []
    for i, payload in enumerate(payloads):
        try:
            data = api.create_po(payload)
            if data:
                entry_id = data.get("id") or data.get("entry_id")
                ref_no = data.get("transaction_ref_no", str(entry_id))
                results.append({"success": True, "id": entry_id, "ref": ref_no})
                print(f"  [{i + 1}/{args.count}] Created PO ID={entry_id}, ref={ref_no}")
            else:
                results.append({"success": False, "status": api._last_status,
                                "error": getattr(api._last_response, 'text', 'N/A')[:300]})
                print(f"  [{i + 1}/{args.count}] FAILED (status {api._last_status})")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"  [{i + 1}/{args.count}] ERROR: {e}")

        if args.delay and i < len(payloads) - 1:
            time.sleep(args.delay)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n{'=' * 60}")
    print(f"Batch complete: {success_count}/{args.count} succeeded")
    print(f"{'=' * 60}")

    return results


if __name__ == "__main__":
    main()
