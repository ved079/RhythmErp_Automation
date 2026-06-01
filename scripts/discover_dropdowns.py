#!/usr/bin/env python3
"""
discover_dropdowns.py
---------------------
Discover how the Supplier screen schema provides cascading dropdown queries.
We need to understand the field definitions for State, District, Taluka, Village
to build a dynamic cascade resolver.

Usage:
    python scripts/discover_dropdowns.py
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwMzQyNDIxLCJpYXQiOjE3ODAzMjgwMjEsImp0aSI6ImM2Zjc5ZjAwOGIwODQxNDRiMzQyMGRiMzg3YmU2N2E2IiwidXNlcl9pZCI6IjE0NiJ9.qFjlwOlQWhbVFGoQSvuy8FWkEnoKo92qtvJ6fCpkd3Y"
TENANT_ID = "599"


def main():
    client = RhythmERPAPIClient()
    client.login_from_browser(token=TOKEN, tenant_id=TENANT_ID)

    # ── 1. Fetch screen schema ──
    print("Fetching Supplier screen schema...\n")
    schema = client.get_screen_schema("Supplier")

    if not schema:
        print("FAILED: Could not fetch schema")
        return

    # Dump all field definitions
    all_fields = client._flatten_fields(schema.get("screendefinition_set", []))

    # Address-related field keys we care about
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
            # Print the full field definition (this is the goldmine)
            print(json.dumps(field, indent=2, default=str))

    # Also check: do any fields have 'dropdown_raw_query' as a STRING (encrypted query)?
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

    # ── 2. Try the execute-query endpoint directly ──
    print("\n" + "=" * 70)
    print("TESTING: Can we call execute-query for State dropdown?")
    print("=" * 70)

    # Find the state field's query string from schema
    for field in all_fields:
        if field.get("field_key") == "state_ref_id_id":
            # Check all possible properties that might contain the query
            for key in sorted(field.keys()):
                val = field[key]
                if val and isinstance(val, str) and len(val) > 20:
                    # Could be an encrypted query string
                    print(f"\n  Candidate key: {key}")
                    print(f"  Value: {str(val)[:200]}")

                    # Try calling execute-query with it
                    try:
                        resp = client.session.get(
                            f"{client.BASE_URL}/core/execute-query/",
                            params={"query": val},
                            timeout=15,
                        )
                        print(f"  Response status: {resp.status_code}")
                        if resp.status_code == 200:
                            data = resp.json()
                            if isinstance(data, list):
                                print(f"  Got {len(data)} options!")
                                for opt in data[:5]:
                                    print(f"    {opt}")
                                if len(data) > 5:
                                    print(f"    ... and {len(data)-5} more")
                            else:
                                print(f"  Response: {str(data)[:200]}")
                    except Exception as e:
                        print(f"  Error: {e}")
            break

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
