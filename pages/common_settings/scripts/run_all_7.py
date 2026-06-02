#!/usr/bin/env python3
"""
Run All 7 Remaining Common Settings Batch Creates

Runs all 7 screens in sequence, sharing the same token.
Shows a summary at the end.
"""

import sys
import os
import time
from datetime import datetime

# ── Path setup ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver

# ── Import all data generators ────────────────────────────────────────
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_error_code_mst_api_payloads,
)
from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import (
    generate_hsn_sac_api_payloads,
)
from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    generate_tax_authority_api_payloads,
)
from pages.common_settings.modules.vehicle_master.data.vehicle_master_data import (
    generate_vehicle_master_api_payloads,
)
from pages.common_settings.modules.bank.data.bank_data import (
    generate_bank_api_payloads,
)
from pages.common_settings.modules.tax_rate.data.tax_rate_data import (
    generate_tax_rate_api_payloads,
)
from pages.common_settings.modules.uom_conversion.data.uom_conversion_data import (
    generate_uom_conversion_api_payloads,
)


# ── Screen definitions ────────────────────────────────────────────────
SCREENS = [
    {
        "name": "Tax Authority",
        "generator": generate_tax_authority_api_payloads,
        "fk_screens": {"tax_type_ref_id": "Tax Type", "country_ref_id": "Country"},
    },
    {
        "name": "Error Code Mst",
        "generator": generate_error_code_mst_api_payloads,
        "fk_screens": {"error_code_type": "Error Code Type"},
    },
    {
        "name": "HSN SAC",
        "generator": generate_hsn_sac_api_payloads,
        "fk_screens": {"hsn_sac_type": "HSN SAC Type"},
    },
    {
        "name": "Vehicle Master",
        "generator": generate_vehicle_master_api_payloads,
        "fk_screens": {"vehicle_type_id": "Vehicle Type", "fuel_type_ref_id": "Fuel Type"},
    },
    {
        "name": "Bank",
        "generator": generate_bank_api_payloads,
        "fk_screens": {"account_type": "Account Type", "account_ref_id": "Account"},
    },
    {
        "name": "UOM Conversion",
        "generator": generate_uom_conversion_api_payloads,
        "fk_screens": {"source_uom_code": "UOM", "target_uom_code": "UOM"},
    },
    {
        "name": "Tax Rate",
        "generator": generate_tax_rate_api_payloads,
        "fk_screens": {"tax_type_ref_id": "Tax Type", "tax_authority_ref_id": "Tax Authority", "uom_ref_id": "UOM"},
    },
]

COUNT = 10


def resolve_fk_for_screen(resolver, fk_screens):
    """Resolve all FK IDs for a screen's dropdown fields."""
    fk_ids = {}
    for field_name, screen_name in fk_screens.items():
        # Try the primary screen name, then variations
        ids = resolver.resolve(screen_name)
        if not ids:
            # Try some variations
            for alt in [screen_name + " Master", screen_name + " Type", screen_name.replace(" ", "")]:
                ids = resolver.resolve(alt)
                if ids:
                    break
        fk_ids[field_name] = ids
    return fk_ids


def main():
    print("=" * 70)
    print("  COMMON SETTINGS — RUN ALL 7 BATCH CREATES")
    print("=" * 70)
    print()

    api = ErpApiClient()
    token = api.prompt_for_token()
    api.set_session_from_token(token)

    # ── Pre-resolve all FK IDs ────────────────────────────────────────
    print()
    print("  Phase 1: Resolving FK IDs for all screens...")
    print("-" * 70)

    resolver = FkResolver(api)
    all_fk_ids = {}

    for screen in SCREENS:
        screen_name = screen["name"]
        fk_screens = screen["fk_screens"]
        fk_ids = resolve_fk_for_screen(resolver, fk_screens)
        all_fk_ids[screen_name] = fk_ids

        # Show resolution status
        for field_name, ids in fk_ids.items():
            status = f"{len(ids)} IDs" if ids else "NOT FOUND (will use fallback)"
            print(f"    {screen_name}: {field_name} → {status}")

    # ── Run batch creates ─────────────────────────────────────────────
    print()
    print("  Phase 2: Creating entries for all screens...")
    print("=" * 70)

    all_results = {}

    for screen in SCREENS:
        screen_name = screen["name"]
        generator = screen["generator"]
        fk_ids = all_fk_ids[screen_name]

        print()
        print(f"  ── {screen_name} ──")
        print("-" * 70)

        try:
            payloads = generator(count=COUNT, fk_ids=fk_ids)
            results = api.batch_create(screen_name, payloads)
            all_results[screen_name] = results

            created = sum(1 for r in results if r.get("success"))
            failed = sum(1 for r in results if not r.get("success"))
            print(f"  Result: {created}/{COUNT} created, {failed} failed")

        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[screen_name] = []

    # ── Summary ────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)

    total_created = 0
    total_failed = 0

    for screen_name, results in all_results.items():
        created = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))
        total_created += created
        total_failed += failed
        status_icon = "OK" if failed == 0 else "!!"
        print(f"  [{status_icon}] {screen_name:<25} {created:>3}/{COUNT} created")

    print("-" * 70)
    print(f"  Total: {total_created} created, {total_failed} failed out of {COUNT * len(SCREENS)}")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()
