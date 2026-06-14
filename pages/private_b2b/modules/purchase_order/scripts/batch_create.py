"""
batch_create.py — Purchase Order batch creation script.

Usage:
    python batch_create.py --token <jwt> --tenant 711 --count 3
    python batch_create.py --token <jwt> --tenant 711 --dry-run

Without --dry-run, creates real Purchase Orders via the ERP API.
With --dry-run, generates and prints payloads without hitting the API.
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

from common.logger import log
from pages.private_b2b.modules.purchase_order.data.purchase_order_data import (
    generate_po_payload,
    generate_po_payloads,
    compute_expected_results,
)


def setup_api(token, tenant):
    from common.erp_api_client import RhythmERPAPIClient
    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=tenant)
    return client


def main():
    parser = argparse.ArgumentParser(description="Batch create Purchase Orders")
    parser.add_argument("--token", default="", help="ERP JWT token")
    parser.add_argument("--tenant", default="711", help="Tenant ID")
    parser.add_argument("--count", type=int, default=1, help="Number of POs to create")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without creating")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between creates (seconds)")
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    api = setup_api(token, args.tenant)

    payloads = generate_po_payloads(args.count)

    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN: {args.count} PO payload(s) generated")
        print(f"{'='*60}")
        for i, p in enumerate(payloads):
            expected = compute_expected_results(p)
            print(f"\n--- PO [{i+1}/{args.count}] ---")
            print(json.dumps(p, indent=2, default=str))
            print(f"  Expected totals: amount={expected['txn_currency_total_amount']}, "
                  f"discount={expected['txn_currency_discount_amount']}, "
                  f"interest={expected['txn_currency_interest_amount']}")
        print(f"\nDry run complete. No entries created.")
        return

    print(f"\n{'='*60}")
    print(f"Creating {args.count} Purchase Order(s)...")
    print(f"{'='*60}")

    results = []
    for i, payload in enumerate(payloads):
        try:
            url = api.BASE_URL.rstrip("/") + "/procure_to_pay/purchase_order/"
            resp = api.session.post(url, headers=api.session.headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                data = resp.json()
                entry_id = data.get("id") or data.get("entry_id")
                results.append({"success": True, "id": entry_id, "status": resp.status_code})
                print(f"  [{i+1}/{args.count}] Created PO ID={entry_id}")
            else:
                results.append({"success": False, "status": resp.status_code, "error": resp.text[:300]})
                print(f"  [{i+1}/{args.count}] FAILED (status {resp.status_code})")
        except Exception as e:
            results.append({"success": False, "error": str(e)})
            print(f"  [{i+1}/{args.count}] ERROR: {e}")

        if args.delay and i < len(payloads) - 1:
            time.sleep(args.delay)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n{'='*60}")
    print(f"Batch complete: {success_count}/{args.count} succeeded")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    main()
