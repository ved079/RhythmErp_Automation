#!/usr/bin/env python3
"""
quick_test.py
-------------
One-shot: verify API auth + discover Supplier structure + create 1 test entry.

Usage (from project root):
    python scripts/quick_test.py

No interactive prompts — token is hardcoded below.
Replace the TOKEN value if it expires (check DevTools → Network → any /core/ request).
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


# ============================================================
# CONFIG — UPDATE TOKEN IF EXPIRED
# ============================================================
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwMzQyNDIxLCJpYXQiOjE3ODAzMjgwMjEsImp0aSI6ImM2Zjc5ZjAwOGIwODQxNDRiMzQyMGRiMzg3YmU2N2E2IiwidXNlcl9pZCI6IjE0NiJ9.qFjlwOlQWhbVFGoQSvuy8FWkEnoKo92qtvJ6fCpkd3Y"
TENANT_ID = "599"
SCREEN_NAME = "Supplier"
CREATE_TEST = True  # Set False to skip creation, only discover


def main():
    log.separator()
    log.info("ERP API QUICK TEST")
    log.separator()

    # ── Step 1: Set auth from browser token ──
    client = RhythmERPAPIClient()
    client.login_from_browser(token=TOKEN, tenant_id=TENANT_ID)
    log.info("Token set successfully")

    # ── Step 2: Discover Supplier structure ──
    log.info(f"\nDiscovering '{SCREEN_NAME}' structure...")
    structure = client.discover_structure(SCREEN_NAME)

    if structure:
        print("\n" + "=" * 70)
        print("SUPPLIER STRUCTURE (from live API)")
        print("=" * 70)
        print(json.dumps(structure, indent=2, default=str)[:5000])
        print("=" * 70)

        has_children = "children" in structure and bool(structure["children"])
        if has_children:
            print(f"\nCOMPLEX SCREEN: {len(structure['children'])} stepper(s)")
            for child in structure["children"]:
                stepper = child.get("stepper_name", "UNKNOWN")
                details = child.get("details", [])
                print(f"  Stepper: {stepper} — {len(details)} row(s)")
                if details:
                    print(f"    Field keys: {list(details[0].keys())}")
        else:
            print("\nSIMPLE SCREEN: flat, no children/steppers")

        print(f"\nTop-level keys: {list(structure.keys())}")
    else:
        log.warning("No existing entries found — cannot discover structure")

    # ── Step 3: List existing entries ──
    log.info(f"\nListing existing {SCREEN_NAME} entries...")
    entries = client.list_entries(SCREEN_NAME, page=1, page_size=5)
    if entries:
        items = entries.get("screenmatlistingdata_set", [])
        print(f"\nFound {len(items)} entries on page 1")
        for item in items[:3]:
            print(f"  ID={item.get('id')}, Name={item.get('name', 'N/A')}")

    # ── Step 4: Create test entry ──
    if CREATE_TEST:
        log.info(f"\nCreating test {SCREEN_NAME} entry via API...")
        from pages.registration.modules.supplier.data.supplier_data import (
            generate_supplier_api_payload,
            DEFAULT_SUPPLIER_FK_IDS,
        )

        # Resolve dynamic FK IDs from existing entry
        resolved_ids = dict(DEFAULT_SUPPLIER_FK_IDS)
        if structure and structure.get("children"):
            for child in structure["children"]:
                stepper = child.get("stepper_name", "")
                details = child.get("details", [])
                if details:
                    if stepper == "Address Details":
                        addr = details[0]
                        for key in ["district_ref_id_id", "sub_district_ref_id_id", "village_ref_id_id"]:
                            if key in addr and addr[key]:
                                resolved_ids[key] = addr[key]
                    elif stepper == "Bank Details":
                        bank = details[0]
                        if "bank_doc_id" in bank and bank["bank_doc_id"]:
                            resolved_ids["bank_doc_id"] = bank["bank_doc_id"]

        payload = generate_supplier_api_payload(dropdown_ids=resolved_ids)
        print(f"\nPayload preview:")
        print(json.dumps(payload, indent=2, default=str)[:2000])

        result = client.create_entry(payload)
        if result:
            print(f"\n[OK] Test supplier CREATED! ID={result.get('id', 'N/A')}")
        else:
            print(f"\n[FAIL] Test supplier creation failed — see error above")
    else:
        print(f"\n(Create test skipped — set CREATE_TEST=True to enable)")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
