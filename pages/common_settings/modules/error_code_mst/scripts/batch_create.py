#!/usr/bin/env python3
"""
Error Code Mst — Batch Create

Screen: "Error Code Mst" (flat, 1 dropdown: error_code_type)
Auto-discovers FK IDs at startup.
"""

import sys
import os
import time

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_error_code_mst_api_payloads,
)

SCREEN_NAME = "Error Code Mst"


def main():
    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE")
    print("=" * 70)

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Resolve FK IDs ────────────────────────────────────────────────
    print()
    print("  Resolving FK IDs...")
    resolver = FkResolver(api)

    # Error Code Type — try multiple screen name variations
    ec_type_ids = {}
    for screen_attempt in ["Error Code Type", "Error Code", "Error Code Master"]:
        ec_type_ids = resolver.resolve(screen_attempt)
        if ec_type_ids:
            print(f"    error_code_type: Found {len(ec_type_ids)} values from '{screen_attempt}'")
            break

    if not ec_type_ids:
        print("    error_code_type: NOT FOUND — will use fallback index values")
        print("    (Entries may fail if the ERP requires valid FK IDs)")

    fk_ids = {"error_code_type": ec_type_ids}

    # ── Generate payloads ─────────────────────────────────────────────
    count = 10
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_error_code_mst_api_payloads(count=count, fk_ids=fk_ids)

    # ── Batch create ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} BATCH CREATE — {count} entries")
    print("=" * 70)

    results = api.batch_create(SCREEN_NAME, payloads)
    api.print_results(results, SCREEN_NAME)
    api.close()


if __name__ == "__main__":
    main()
