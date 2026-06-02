#!/usr/bin/env python3
"""
Tax Rate — Batch Create

Screen: "Tax Rate" (COMPLEX — has stepper "Define Tax Rate Details")
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
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    generate_tax_rate_api_payloads,
)

SCREEN_NAME = "Tax Rate"


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

    # Tax Type
    tax_type_ids = resolver.resolve("Tax Type")
    print(f"    tax_type_ref_id: {len(tax_type_ids)} Tax Types found")

    # Tax Authority (may need to create some first)
    tax_auth_ids = resolver.resolve("Tax Authority")
    print(f"    tax_authority_ref_id: {len(tax_auth_ids)} Tax Authorities found")

    # UOM (for tax detail lines — "Percentage" or "%")
    uom_ids = resolver.resolve("UOM")
    print(f"    uom_ref_id: {len(uom_ids)} UOMs found")

    fk_ids = {
        "tax_type_ref_id": tax_type_ids,
        "tax_authority_ref_id": tax_auth_ids,
        "uom_ref_id": uom_ids,
    }

    # ── Generate payloads ─────────────────────────────────────────────
    count = 10
    print()
    print(f"  Generating {count} payloads...")
    payloads = generate_tax_rate_api_payloads(count=count, fk_ids=fk_ids)

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
