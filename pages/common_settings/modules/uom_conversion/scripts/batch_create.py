#!/usr/bin/env python3
"""
UOM Conversion — Batch Create

Screen: "UOM Conversion" (flat, 2 FK dropdowns: source_uom_code, target_uom_code)
Auto-discovers FK IDs at startup (both use UOM screen).
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
from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_api_payloads,
)

SCREEN_NAME = "UOM Conversion"


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

    # Both source and target use UOM IDs
    uom_ids = resolver.resolve("UOM")
    print(f"    UOM IDs: {len(uom_ids)} found")

    # Also try "UOM Code" as an alternative
    uom_code_ids = resolver.resolve("UOM Code")
    if uom_code_ids and len(uom_code_ids) > len(uom_ids):
        uom_ids = uom_code_ids
        print(f"    UOM Code IDs: {len(uom_code_ids)} found (using these — better match)")

    # Show some sample UOM IDs for verification
    if uom_ids:
        sample = list(uom_ids.items())[:5]
        for name, uid in sample:
            print(f"      {name}: {uid}")
        if len(uom_ids) > 5:
            print(f"      ... and {len(uom_ids) - 5} more")

    fk_ids = {
        "source_uom_code": uom_ids,
        "target_uom_code": uom_ids,  # Same UOM screen for both
    }

    # ── Generate payloads ─────────────────────────────────────────────
    count = 10
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_uom_conversion_api_payloads(count=count, fk_ids=fk_ids)

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
