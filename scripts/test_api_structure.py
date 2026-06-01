#!/usr/bin/env python3
"""
test_api_structure.py
---------------------
Quick script to verify the ERP API auth + discover Supplier payload structure.
Run this ONCE to confirm everything works before relying on it in tests.

Usage:
    cd <project_root>
    python scripts/test_api_structure.py

What it does:
    1. Tests login via /auth/login1/
    2. Discovers Supplier screen structure (simple vs complex)
    3. Prints the full payload structure so you can verify field names
    4. Attempts to create ONE test supplier (optional, controlled by flag)
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log


# ============================================================
# CONFIG
# ============================================================
USERNAME = "Assistant@mail.com"
PASSWORD = "Vedant@12345"
TENANT_ID = "599"
SCREEN_NAME = "Supplier"
CREATE_TEST_ENTRY = False  # Set True to attempt creating one test supplier


def main():
    log.separator()
    log.info("ERP API STRUCTURE VERIFICATION")
    log.separator()

    # ── Step 1: Test Login ──
    log.info("Step 1: Testing login via /auth/login1/...")
    client = RhythmERPAPIClient(
        username=USERNAME,
        password=PASSWORD,
        tenant_id=TENANT_ID,
    )

    try:
        token, tenant = client.login()
        log.info(f"Login SUCCESS! Token starts with: {token[:40]}...")
    except Exception as e:
        log.error(f"Login FAILED: {e}")
        log.info("Trying login_from_browser() as fallback...")
        log.info("Open ERP in Chrome DevTools → Network → look for any /core/ request")
        log.info("Copy the Authorization header value (after 'Bearer ') and paste below:")
        manual_token = input("Token (or press Enter to quit): ").strip()
        if not manual_token:
            return
        client.login_from_browser(token=manual_token, tenant_id=TENANT_ID)
        log.info("Manual token set successfully")

    # ── Step 2: Discover Structure ──
    log.info(f"\nStep 2: Discovering '{SCREEN_NAME}' screen structure...")
    structure = client.discover_structure(SCREEN_NAME)

    if structure:
        print("\n" + "=" * 60)
        print("SUPPLIER SCREEN STRUCTURE (from existing entry)")
        print("=" * 60)
        print(json.dumps(structure, indent=2, default=str)[:3000])
        print("=" * 60)

        # Analyze structure
        has_children = "children" in structure and bool(structure["children"])
        if has_children:
            print(f"\nCOMPLEX SCREEN: {len(structure['children'])} stepper(s) found")
            for child in structure["children"]:
                stepper = child.get("stepper_name", "UNKNOWN")
                details = child.get("details", [])
                print(f"  - {stepper}: {len(details)} detail row(s)")
                if details:
                    print(f"    Fields: {list(details[0].keys())[:10]}...")
        else:
            print("\nSIMPLE SCREEN: flat structure (no children/steppers)")

        print(f"\nTop-level keys: {list(structure.keys())}")
    else:
        log.warning("No existing entries found — cannot discover structure")
        log.info("Create one Supplier manually via the UI, then re-run this script")

    # ── Step 3: List Existing Entries ──
    log.info(f"\nStep 3: Listing existing {SCREEN_NAME} entries...")
    entries = client.list_entries(SCREEN_NAME, page=1, page_size=5)
    if entries:
        items = entries.get("screenmatlistingdata_set", [])
        print(f"\nFound {len(items)} entries on first page")
        for item in items[:3]:
            print(f"  ID={item.get('id')}, Name={item.get('name', 'N/A')}")

    # ── Step 4: Test Create (optional) ──
    if CREATE_TEST_ENTRY:
        log.info(f"\nStep 4: Creating test {SCREEN_NAME} entry via API...")
        from pages.registration.modules.supplier.data.supplier_data import (
            generate_supplier_api_payload,
            DEFAULT_SUPPLIER_FK_IDS,
        )

        # Resolve dynamic FK IDs from an existing entry if possible
        resolved_ids = dict(DEFAULT_SUPPLIER_FK_IDS)
        if structure and structure.get("children"):
            for child in structure["children"]:
                stepper = child.get("stepper_name", "")
                details = child.get("details", [])
                if details:
                    if stepper == "Address Details":
                        addr = details[0]
                        if "district_ref_id_id" in addr and addr["district_ref_id_id"]:
                            resolved_ids["district_ref_id_id"] = addr["district_ref_id_id"]
                        if "sub_district_ref_id_id" in addr and addr["sub_district_ref_id_id"]:
                            resolved_ids["sub_district_ref_id_id"] = addr["sub_district_ref_id_id"]
                        if "village_ref_id_id" in addr and addr["village_ref_id_id"]:
                            resolved_ids["village_ref_id_id"] = addr["village_ref_id_id"]
                    elif stepper == "Bank Details":
                        bank = details[0]
                        if "bank_doc_id" in bank and bank["bank_doc_id"]:
                            resolved_ids["bank_doc_id"] = bank["bank_doc_id"]

        payload = generate_supplier_api_payload("VerifyTest", dropdown_ids=resolved_ids)
        print(f"\nPayload structure preview:")
        print(json.dumps(payload, indent=2, default=str)[:1500])

        result = client.create_entry(payload)
        if result:
            print(f"\n✅ Test supplier CREATED! ID: {result.get('id', 'N/A')}")
        else:
            print(f"\n❌ Test supplier creation failed — check error above")
    else:
        print(f"\n(Create test skipped — set CREATE_TEST_ENTRY=True to enable)")

    client.close()
    print("\n✅ Verification complete!")


if __name__ == "__main__":
    main()
