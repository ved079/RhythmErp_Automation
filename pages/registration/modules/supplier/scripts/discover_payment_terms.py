#!/usr/bin/env python3
"""
Quick script to discover the correct Payment Terms FK IDs for the Supplier screen.
Also dumps all dropdown options for verification.

Usage:
    python pages/registration/modules/supplier/scripts/discover_payment_terms.py
"""
import os, sys, json

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
        print("No token provided. Paste it:")
        token = input("  Token: ").strip()
        if not token:
            print("No token. Exiting.")
            return

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id="681")

    # 1. Check screen schema for payment_terms_ref_id
    print("\n" + "=" * 70)
    print("PAYMENT TERMS DROPDOWN OPTIONS FROM SCHEMA")
    print("=" * 70)
    options = client.get_dropdown_options("Supplier", "payment_terms_ref_id")
    if options:
        print(f"Found {len(options)} options:")
        for opt in options:
            print(f"  id={opt.get('id'):>5}  key={opt.get('key', '?')}")
    else:
        print("No options found via get_dropdown_options()")

    # 2. Check an existing supplier entry's Additional Details
    print("\n" + "=" * 70)
    print("EXISTING SUPPLIER ENTRY — ADDITIONAL DETAILS")
    print("=" * 70)
    data = client.list_entries("Supplier", page=1, page_size=5)
    if data:
        items = data.get("screenmatlistingdata_set", [])
        for item in items[:3]:
            entry_id = item.get("id")
            detail = client.get_entry("Supplier", entry_id)
            if detail and detail.get("children"):
                ad = detail["children"][0]
                name = detail.get("name", "?")
                pt = ad.get("payment_terms_ref_id", "NOT_FOUND")
                dt = ad.get("delivery_terms_ref_id", "NOT_FOUND")
                md = ad.get("mode_of_delivery_ref_id", "NOT_FOUND")
                cp = ad.get("display_name_as", "NOT_FOUND")
                print(f"  Supplier: {name[:40]}")
                print(f"    payment_terms_ref_id = {pt}")
                print(f"    delivery_terms_ref_id = {dt}")
                print(f"    mode_of_delivery_ref_id = {md}")
                print(f"    display_name_as = {cp}")
                print()

    # 3. Also dump all Additional Details keys from first entry
    print("=" * 70)
    print("FULL ADDITIONAL DETAILS KEYS (first entry)")
    print("=" * 70)
    if data:
        items = data.get("screenmatlistingdata_set", [])
        if items:
            detail = client.get_entry("Supplier", items[0].get("id"))
            if detail and detail.get("children"):
                ad = detail["children"][0]
                for k, v in sorted(ad.items()):
                    print(f"  {k}: {v}")

    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
