#!/usr/bin/env python3
"""
discover_dropdowns.py
---------------------
Discover how the Supplier screen schema provides cascading dropdown queries.
Shows field definitions for State, District, Taluka, Village.

Usage:
    python pages/registration/modules/supplier/scripts/discover_dropdowns.py --token eyJhbGci...
"""

import os
import sys
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient


def main():
    token = None
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            break

    if not token:
        print("USAGE: python discover_dropdowns.py --token <YOUR_TOKEN>")
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id="681")

    # Fetch screen schema
    print("Fetching Supplier screen schema...\n")
    schema = client.get_screen_schema("Supplier")

    if not schema:
        print("FAILED: Could not fetch schema")
        return

    all_fields = client._flatten_fields(schema.get("screendefinition_set", []))

    address_keys = [
        "state_ref_id_id", "district_ref_id_id",
        "sub_district_ref_id_id", "village_ref_id_id",
        "country_ref_id_id", "address_type",
    ]

    print("=" * 70)
    print("ADDRESS FIELD DEFINITIONS FROM SCHEMA")
    print("=" * 70)

    for field in all_fields:
        field_key = field.get("field_key", "")
        if field_key in address_keys:
            print(f"\n--- {field_key} ---")
            print(json.dumps(field, indent=2, default=str))

    print("\n" + "=" * 70)
    print("ALL FIELDS WITH dropdown_raw_query (type check)")
    print("=" * 70)
    for field in all_fields:
        drq = field.get("dropdown_raw_query")
        fdrq = field.get("filter_dropdown_raw_query")
        field_key = field.get("field_key", "?")
        if drq is not None or fdrq is not None:
            drq_type = type(drq).__name__ if drq is not None else "None"
            fdrq_type = type(fdrq).__name__ if fdrq is not None else "None"
            drq_preview = str(drq)[:120] if drq is not None else "None"
            fdrq_preview = str(fdrq)[:120] if fdrq is not None else "None"
            print(f"\n  field_key: {field_key}")
            print(f"  dropdown_raw_query ({drq_type}): {drq_preview}")
            print(f"  filter_dropdown_raw_query ({fdrq_type}): {fdrq_preview}")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
