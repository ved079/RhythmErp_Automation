#!/usr/bin/env python3
"""
Agent — Batch Create via API

Screen: "Agent" (3 steppers: Address Details, Payment Details, Bank Details)

Usage:
    python batch_create.py              # Creates 10 entries
    python batch_create.py --count 20   # Creates 20 entries
    python batch_create.py --dry-run    # Preview payloads without sending
"""

import sys
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import ErpApiClient
from common.fk_resolver import FkResolver
from pages.registration.modules.agent.data.agent_data import (
    generate_agent_name,
    generate_phone_number,
    generate_email,
    generate_bank_name,
    generate_branch,
    generate_ifsc_code,
    generate_account_holder_name,
    generate_account_number,
    generate_address,
)
from pages.registration.modules.agent.utils.api_agent_utils import (
    COUNTRY_INDIA_ID,
    ACCOUNT_TYPE_CURRENT_ID,
    ADDRESS_TYPE_SHIPPING_ID,
    ADDRESS_TYPE_BILLING_ID,
    BANK_DOC_CANCELLED_CHEQUE_ID,
    _ADDRESS_CHAINS,
)

SCREEN_NAME = "Agent"


def parse_args():
    parser = argparse.ArgumentParser(description="Batch create Agent entries via API")
    parser.add_argument("--token", default=None, help="ERP Bearer token (omit to prompt)")
    parser.add_argument("--tenant", default=None, help="Tenant ID (omit to prompt)")
    parser.add_argument("--count", type=int, default=None, help="Number of entries to create (omit to prompt)")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending")
    parser.add_argument("--offset", type=int, default=0, help="Start index in data pool")
    return parser.parse_args()


def generate_agent_payload(name_prefix="AGT", offset=0):
    """Generate a single Agent API payload."""
    import random

    rand_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))
    agent_name = f"{name_prefix}{rand_suffix}"

    chain = _ADDRESS_CHAINS[offset % len(_ADDRESS_CHAINS)]

    payload = {
        "id": "",
        "attribute_name": SCREEN_NAME,
        "party_ref_id": None,
        "copy_from_party": False,
        "name": agent_name,
        "mobile_no": int(generate_phone_number()),
        "email_id": generate_email(name_prefix.lower()),
        "status": True,
        "children": [
            {
                "stepper_name": "Address Details",
                "is_stepper": True,
                "details": [
                    {
                        "address_type": ADDRESS_TYPE_SHIPPING_ID,
                        "country_ref_id_id": COUNTRY_INDIA_ID,
                        "state_ref_id_id": chain["state_ref_id_id"],
                        "district_ref_id_id": chain["district_ref_id_id"],
                        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
                        "village_ref_id_id": chain.get("village_ref_id_id"),
                        "address": generate_address(),
                        "pin_code": chain["pin_code"],
                        "same_as_above": None,
                        "details": [],
                    },
                    {
                        "address_type": ADDRESS_TYPE_BILLING_ID,
                        "country_ref_id_id": COUNTRY_INDIA_ID,
                        "state_ref_id_id": chain["state_ref_id_id"],
                        "district_ref_id_id": chain["district_ref_id_id"],
                        "sub_district_ref_id_id": chain["sub_district_ref_id_id"],
                        "village_ref_id_id": chain.get("village_ref_id_id"),
                        "address": generate_address(),
                        "pin_code": chain["pin_code"],
                        "same_as_above": None,
                        "details": [],
                    },
                ],
                "children": [],
            },
            {
                "stepper_name": "Payment Details",
                "is_stepper": True,
                "payment_terms_ref_id": None,
                "preferred_payment_method_ref_id": None,
                "is_gst_set_off": False,
                "details": [],
                "children": [],
            },
            {
                "stepper_name": "Bank Details",
                "is_stepper": True,
                "details": [
                    {
                        "bank_name": generate_bank_name(),
                        "bank_branch_code": generate_branch(),
                        "bank_ifsc_code": generate_ifsc_code(),
                        "account_type": ACCOUNT_TYPE_CURRENT_ID,
                        "bank_account_holder_name": generate_account_holder_name(),
                        "bank_account_no": int(generate_account_number()),
                        "bank_doc_id": BANK_DOC_CANCELLED_CHEQUE_ID,
                        "bank_attachment_path": None,
                        "details": [],
                    }
                ],
                "children": [],
            },
        ],
    }
    return payload


def generate_agent_api_payloads(count=10, offset=0):
    """Generate multiple Agent API payloads."""
    payloads = []
    for i in range(count):
        payloads.append(generate_agent_payload(offset=offset + i))
    return payloads


def prompt_missing_args(args):
    if not args.token:
        print("\n  No token provided. Open DevTools -> Network -> any /core/ request -> Authorization header")
        args.token = input("  Token: ").strip()
        if not args.token:
            print("  No token entered. Exiting.")
            sys.exit(1)
    if not args.tenant:
        args.tenant = input("  Tenant ID (e.g., 711): ").strip()
        if not args.tenant:
            print("  No tenant entered. Exiting.")
            sys.exit(1)
    if not args.count:
        count_str = input("  Count (default 10): ").strip()
        args.count = int(count_str) if count_str else 10
    return args


def main():
    args = parse_args()
    count = args.count if args.count else 10

    print("=" * 70)
    print(f"  {SCREEN_NAME.upper()} — BATCH CREATE (API)")
    print(f"  Screen: {SCREEN_NAME}")
    print(f"  Entries to create: {count}")
    if args.dry_run:
        print("  ** DRY-RUN MODE — no entries will be created **")
    print("=" * 70)

    # ── Generate payloads BEFORE token/auth ────────────────────────────
    print()
    print(f"  Generating {count} payloads...")
    try:
        payloads = generate_agent_api_payloads(count=count, offset=args.offset)
    except Exception as e:
        print(f"  ERROR generating payloads: {e}")
        return

    # ── DRY RUN: print & exit (no token needed) ─────────────────────────
    if args.dry_run:
        print(f"  [DRY-RUN] {len(payloads)} payloads generated")
        for j, p in enumerate(payloads):
            name = p.get("name", "?")[:40]
            print(f"    [{j+1}] {name}")
        return

    # ── Only NOW ask for token ──────────────────────────────────────────
    args = prompt_missing_args(args)

    api = ErpApiClient()
    api.set_session_from_token(args.token, tenant_id=args.tenant)

    # ── Create entries ────────────────────────────────────────────────
    print()
    try:
        results = api.batch_create(SCREEN_NAME, payloads)
    except Exception as e:
        print(f"  ERROR: {e}")
        api.close()
        return

    # ── Summary ────────────────────────────────────────────────────────
    created = sum(1 for r in results if r.get("success"))
    failed = sum(1 for r in results if not r.get("success"))

    print()
    print("=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    status_icon = "OK" if failed == 0 else "!!"
    print(f"  [{status_icon}] {SCREEN_NAME:<35} {created:>3}/{count} created")
    print("-" * 70)
    print(f"  Total: {created} created, {failed} failed out of {count}")
    print("=" * 70)

    api.close()


if __name__ == "__main__":
    main()
