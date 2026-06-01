#!/usr/bin/env python3
"""
batch_create.py
---------------
Create multiple Season entries via API with realistic Indian season names.

Just paste your Bearer token and go.

Usage:
    python pages/common_settings/modules/season/scripts/batch_create.py
    python pages/common_settings/modules/season/scripts/batch_create.py --count 20
    python pages/common_settings/modules/season/scripts/batch_create.py --token eyJhbGci...
"""

import sys
import os
import time

# Add project root to path (season/scripts → season → modules → common_settings → pages → project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.common_settings.modules.season.data.season_data import generate_season_api_payload

TENANT_ID = "599"
DEFAULT_COUNT = 10


def parse_args():
    args = {"token": None, "count": DEFAULT_COUNT, "dry_run": False}
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--token" and i + 1 < len(sys.argv):
            args["token"] = sys.argv[i + 1]
            i += 2
        elif arg == "--count" and i + 1 < len(sys.argv):
            args["count"] = int(sys.argv[i + 1])
            i += 2
        elif arg == "--dry-run":
            args["dry_run"] = True
            i += 1
        else:
            i += 1
    return args


def batch_create(client, count, dry_run=False):
    success = 0
    fail = 0
    start = time.time()

    print("=" * 70)
    print(f"  SEASON BATCH CREATE — {count} entries")
    print("=" * 70)

    for i in range(count):
        payload = generate_season_api_payload()
        name = payload.get("name", "?")

        if dry_run:
            print(f"  [{i+1:2d}] [DRY] {name:40s}")
            success += 1
            continue

        result = client.create_entry(payload)
        if result:
            rid = result.get("id", "?")
            print(f"  [{i+1:2d}] OK  {name:40s} | ID={rid}")
            success += 1
        else:
            print(f"  [{i+1:2d}] FAIL {name:40s}")
            fail += 1

        time.sleep(0.25)

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Created: {success}/{count} ({fail} failed)")
    if not dry_run:
        print(f"  Time:    {elapsed:.1f}s ({elapsed/count:.2f}s per entry)")
    print("=" * 70)

    return success, fail


def main():
    args = parse_args()
    token = args["token"]
    count = args["count"]
    dry_run = args["dry_run"]

    if not token:
        print("=" * 70)
        print("  SEASON BATCH CREATE")
        print("=" * 70)
        print()
        print("  No token provided. Get it from:")
        print("  1. Open https://rhythmerp.algorhythms.in in Chrome")
        print("  2. DevTools -> Network -> click any page")
        print("  3. Find any /core/ request -> copy Authorization header")
        print("  4. Paste the token value (after 'Bearer ')")
        print()
        token = input("  Token: ").strip()
        if not token:
            print("  No token entered. Exiting.")
            return

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)

    result = client.list_entries("Season", page=1, page_size=1)
    if not result:
        print("  Token invalid or expired. Get a new one from DevTools.")
        client.close()
        return

    batch_create(client, count, dry_run)
    client.close()


if __name__ == "__main__":
    main()
