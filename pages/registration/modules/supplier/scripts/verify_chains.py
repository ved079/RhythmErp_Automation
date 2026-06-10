#!/usr/bin/env python3
"""
verify_chains.py
----------------
Test unverified address chains by creating a throwaway Supplier entry
with each chain. If the API accepts it, the chain is marked verified.

Usage:
    python pages/registration/modules/supplier/scripts/verify_chains.py --token <YOUR_TOKEN>
    python pages/registration/modules/supplier/scripts/verify_chains.py --token <YOUR_TOKEN> --all
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.registration.modules.supplier.data.supplier_data import (
    _ADDRESS_CHAINS,
    generate_supplier_api_payload,
    add_address_chain,
)


def verify_chains(client: RhythmERPAPIClient, test_all: bool = False) -> dict:
    """Test address chains by creating a minimal Supplier entry with each."""
    results = {}
    chains_to_test = []

    for i, chain in enumerate(_ADDRESS_CHAINS):
        if test_all or not chain.get("_verified", False):
            chains_to_test.append((i, chain))

    if not chains_to_test:
        print("All chains are already verified! Use --all to re-verify.")
        return {}

    print(f"\nTesting {len(chains_to_test)} unverified chain(s)...")
    print("=" * 60)

    for idx, chain in chains_to_test:
        clean_chain = {k: v for k, v in chain.items() if k != "_verified"}
        state_id = clean_chain["state_ref_id_id"]
        district_id = clean_chain["district_ref_id_id"]

        payload = generate_supplier_api_payload(dropdown_ids={**clean_chain})
        payload["name"] = f"ChainTest_S{state_id}_D{district_id}"

        print(f"\n  [{idx}] State={state_id}, District={district_id}...", end=" ")

        result = client.create_entry(payload)

        if result:
            print("VERIFIED")
            chain["_verified"] = True
            results[idx] = {"success": True, "error": None}
        else:
            print("FAILED")
            chain["_verified"] = False
            results[idx] = {"success": False, "error": "API rejected"}

    return results


def main():
    token = None
    test_all = False

    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
        if arg == "--all":
            test_all = True

    if not token:
        print("=" * 60)
        print("USAGE: python verify_chains.py --token <YOUR_TOKEN>")
        print("")
        print("OPTIONS:")
        print("  --token TOKEN   Bearer token from DevTools (required)")
        print("  --all           Re-verify ALL chains (default: unverified only)")
        print("=" * 60)
        sys.exit(1)

    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id="681")

    results = verify_chains(client, test_all)
    client.close()

    if not results:
        return

    verified = sum(1 for r in results.values() if r["success"])
    failed = sum(1 for r in results.values() if not r["success"])

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {verified} verified, {failed} failed out of {len(results)} tested")
    print(f"{'=' * 60}")

    total_verified = sum(1 for c in _ADDRESS_CHAINS if c.get("_verified", False))
    total_unverified = sum(1 for c in _ADDRESS_CHAINS if not c.get("_verified", False))
    print(f"\nPool status: {total_verified} verified, {total_unverified} unverified")


if __name__ == "__main__":
    main()
