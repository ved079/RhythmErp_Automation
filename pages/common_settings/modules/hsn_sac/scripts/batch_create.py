#!/usr/bin/env python3
"""
HSN SAC — Batch Create

Screen: "HSN SAC" (flat, 1 dropdown: hsn_sac_type)
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
from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    generate_hsn_sac_api_payloads,
)

SCREEN_NAME = "HSN SAC"


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

    # HSN SAC Type — try multiple screen name variations
    hsn_type_ids = {}
    for screen_attempt in ["HSN SAC Type", "HSN Type", "SAC Type", "HSN/SAC Type"]:
        hsn_type_ids = resolver.resolve(screen_attempt)
        if hsn_type_ids:
            print(f"    hsn_sac_type: Found {len(hsn_type_ids)} values from '{screen_attempt}'")
            break

    if not hsn_type_ids:
        print("    hsn_sac_type: NOT FOUND — will use fallback (Goods=1, Services=2)")

    fk_ids = {"hsn_sac_type": hsn_type_ids}

    # ── Generate payloads ─────────────────────────────────────────────
    count = 10
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_hsn_sac_api_payloads(count=count, fk_ids=fk_ids)

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
