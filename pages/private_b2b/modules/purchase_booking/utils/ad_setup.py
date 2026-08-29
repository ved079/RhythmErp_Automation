"""
ad_setup.py — Universal Purchase Booking Accounting Definition setup script.

For any RhythmERP tenant, this script:
  1. Resolves all required account IDs from the Chart of Account Definition by name.
  2. Resolves Type of Sale IDs from the PB screen's parameter6 dropdown.
  3. Builds the canonical Purchase Booking AD structure.
  4. Creates the AD if none exists, or PUTs the corrected one if it does.

Canonical AD structure (Purchase Booking, transaction_type=5):
  CR  Payable                   val=9   always        sub_ledger=True
  DR  Purchase @gst             val=10  supplier only (supplier_ref_type=Supplier)
  DR  Purchase exempt           val=10  farmer only   (supplier_ref_type=Farmer)
  DR  Input IGST                val=11  always
  DR  Input CGST                val=12  always
  DR  Input SGST                val=13  always
  CR  Round Off                 val=38  always
  DR  Round Off                 val=37  always

param5 in conditions = supplier_ref_type field ("Supplier" / "Farmer")
param6 in conditions = parameter6 field (Type of Sale FK IDs, tenant-specific)

Usage:
    python ad_setup.py --token <jwt> --tenant <id>
    python ad_setup.py --token <jwt> --tenant <id> --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient

# ── Constants ─────────────────────────────────────────────────────────────────

_PB_TRANSACTION_TYPE = "5"
_PB_AD_NAME = "Purchase Booking"

# ERP-global transaction value codes (same on every tenant)
_VAL_PAYABLE        = "9"
_VAL_PURCHASE       = "10"
_VAL_IGST           = "11"
_VAL_CGST           = "12"
_VAL_SGST           = "13"
_VAL_ROUNDOFF_DR    = "37"
_VAL_ROUNDOFF_CR    = "38"

# AD condition parameter IDs (ERP-global)
_PARAM_SUPPLIER_TYPE = 5   # maps to supplier_ref_type field
_PARAM_TYPE_OF_SALE  = 6   # maps to parameter6 field (Type of Sale)

# Operator codes
_OP_IN     = 1704
_OP_NOT_IN = 1705
_OP_AND    = 1710

# Required CoA account names → looked up by exact name on each tenant
# Value: (name_candidates, sub_ledger, description)
_REQUIRED_ACCOUNTS: list[tuple[list[str], bool, str]] = [
    (["Payable"],                             True,  "Creditors / AP"),
    (["Purchase @gst"],                       False, "Purchase (taxable)"),
    (["Purchase exempt"],                     False, "Purchase (exempt)"),
    (["Input IGST"],                          False, "Input IGST"),
    (["Input CGST"],                          False, "Input CGST"),
    (["Input SGST"],                          False, "Input SGST"),
    (["Expense Round Off", "Round Off"],      False, "Round-off"),
]


# ── CoA resolution ────────────────────────────────────────────────────────────

def fetch_coa(client: RhythmERPAPIClient) -> dict[str, int]:
    """Return {account_name: id} for the tenant's Chart of Account Definition."""
    r = client.session.get(
        f"{client.BASE_URL}/core/dynamic-screen-wrapper/Chart%20Of%20Account%20Definition/",
        params={"page_number": 1, "page_size": 500},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"CoA fetch failed: HTTP {r.status_code}")
    rows = r.json().get("screenmatlistingdata_set") or []
    return {row["name"]: row["id"] for row in rows if row.get("id") and row.get("name")}


def resolve_accounts(coa: dict[str, int]) -> dict[str, int]:
    """
    For each required account, try each candidate name in order.
    Returns {canonical_name: id}.  Raises if any account is missing.
    """
    resolved: dict[str, int] = {}
    missing: list[str] = []
    for candidates, _, desc in _REQUIRED_ACCOUNTS:
        found_id = None
        for name in candidates:
            if name in coa:
                found_id = coa[name]
                resolved[candidates[0]] = found_id  # key by first (canonical) name
                break
        if found_id is None:
            missing.append(f"{desc} (tried: {candidates})")
    if missing:
        raise RuntimeError(
            "Missing accounts in CoA — create them first:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )
    return resolved


# ── Type of Sale resolution ───────────────────────────────────────────────────

def fetch_type_of_sale_ids(client: RhythmERPAPIClient) -> list[int]:
    """Return all parameter6 (Type of Sale) IDs from the PB screen dropdown."""
    opts = client.get_dropdown_options("Purchase Booking", "parameter6") or []
    ids = [int(o["id"]) for o in opts if o.get("id") is not None]
    return ids


# ── AD payload builder ────────────────────────────────────────────────────────

def _param_block() -> dict:
    return {
        "parameter1": ["All"],
        "parameter2": ["All"],
        "parameter5": ["All"],
        "parameter6": ["All"],
    }


def _condition(param_id: int, operator: int, options: list, logical_op=None) -> dict:
    return {
        "parameter": param_id,
        "operator": operator,
        "options": options,
        "logical_operator": logical_op,
        "parent_id": 0,
    }


def build_ad_payload(accounts: dict[str, int], tos_ids: list[int]) -> dict:
    """
    Build the canonical Purchase Booking AD payload.

    Purchase @gst  fires when supplier_ref_type = Supplier (any Type of Sale).
    Purchase exempt fires when supplier_ref_type = Farmer  (any Type of Sale).
    All other entries are unconditional.
    """
    payable_id    = accounts["Payable"]
    purchase_gst  = accounts["Purchase @gst"]
    purchase_ex   = accounts["Purchase exempt"]
    igst_id       = accounts["Input IGST"]
    cgst_id       = accounts["Input CGST"]
    sgst_id       = accounts["Input SGST"]
    roundoff_id   = accounts["Expense Round Off"]

    # supplier_ref_type conditions
    cond_supplier = [
        _condition(_PARAM_SUPPLIER_TYPE, _OP_IN, ["Supplier"], None),
    ]
    cond_farmer = [
        _condition(_PARAM_SUPPLIER_TYPE, _OP_IN, ["Farmer"], None),
    ]

    def entry(dr_cr, account_id, value_name, conditions=None, sub_ledger=False):
        return {
            "account_ref_id": account_id,
            "dr_cr": dr_cr,
            "value_name": value_name,
            "inter_company": "",
            "is_sub_ledger_applicable": sub_ledger,
            "parameter": _param_block(),
            "conditions": conditions or [],
            "is_screen_coa_applicable": False,
        }

    details = [
        # Creditors / AP — always, sub-ledger enabled
        entry("Credit", payable_id,   _VAL_PAYABLE,  sub_ledger=True),
        # Purchase debit — Supplier
        entry("Debit",  purchase_gst, _VAL_PURCHASE, conditions=cond_supplier),
        # Purchase debit — Farmer (exempt)
        entry("Debit",  purchase_ex,  _VAL_PURCHASE, conditions=cond_farmer),
        # Tax entries — always
        entry("Debit",  igst_id,      _VAL_IGST),
        entry("Debit",  cgst_id,      _VAL_CGST),
        entry("Debit",  sgst_id,      _VAL_SGST),
        # Round-off — always
        entry("Credit", roundoff_id,  _VAL_ROUNDOFF_CR),
        entry("Debit",  roundoff_id,  _VAL_ROUNDOFF_DR),
    ]

    return {
        "name": _PB_AD_NAME,
        "transaction_type": _PB_TRANSACTION_TYPE,
        "accounting_definition_detail": details,
    }


# ── AD create / update ────────────────────────────────────────────────────────

def find_existing_pb_ad(client: RhythmERPAPIClient) -> dict | None:
    """Return the existing Purchase Booking AD record or None."""
    r = client.session.get(
        f"{client.BASE_URL}/core/accounting-definition/",
        params={"page_number": 1, "page_size": 100},
        timeout=15,
    )
    if r.status_code != 200:
        raise RuntimeError(f"AD listing failed: HTTP {r.status_code}")
    listing = r.json()
    rows = listing if isinstance(listing, list) else (
        listing.get("results") or listing.get("screenmatlistingdata_set") or []
    )
    return next(
        (r for r in rows if str(r.get("transaction_type", "")) == _PB_TRANSACTION_TYPE),
        None,
    )


def _fetch_existing_details(client: RhythmERPAPIClient, ad_id: int) -> list[dict]:
    """Fetch the full detail list for an existing AD."""
    r = client.session.get(
        f"{client.BASE_URL}/core/accounting-definition/{ad_id}/",
        timeout=15,
    )
    if r.status_code == 200:
        return r.json().get("accounting_definition_detail") or []
    return []


def _assign_existing_ids(new_details: list[dict], existing_details: list[dict]) -> None:
    """
    Match each new detail entry to an existing one by (dr_cr, value_name, account_ref_id)
    and assign its id.  Matched entries are removed from the pool so each id is used once.
    Unmatched new entries get no id (backend creates them).
    Condition ids are also re-assigned from matched existing conditions (by parameter+operator).
    """
    pool = list(existing_details)  # consume as we match

    for new_d in new_details:
        key = (new_d.get("dr_cr"), str(new_d.get("value_name")), new_d.get("account_ref_id"))
        match = next(
            (e for e in pool
             if e.get("dr_cr") == key[0]
             and str(e.get("value_name", "")) == key[1]
             and e.get("account_ref_id") == key[2]),
            None,
        )
        if match:
            new_d["id"] = match["id"]
            pool.remove(match)
            # Re-assign condition ids by (parameter, operator) match
            existing_conds = list(match.get("conditions") or [])
            for new_c in new_d.get("conditions", []):
                cmatch = next(
                    (c for c in existing_conds
                     if c.get("parameter") == new_c.get("parameter")
                     and c.get("operator") == new_c.get("operator")),
                    None,
                )
                if cmatch:
                    new_c["id"] = cmatch["id"]
                    existing_conds.remove(cmatch)


def apply_ad(client: RhythmERPAPIClient, payload: dict, existing_id: int | None, dry_run: bool) -> None:
    import copy
    send_payload = copy.deepcopy(payload)

    if existing_id:
        send_payload["id"] = existing_id
        # Fetch existing sub-records and reuse their ids so the ERP serializer is happy
        existing_details = _fetch_existing_details(client, existing_id)
        _assign_existing_ids(send_payload.get("accounting_definition_detail", []), existing_details)

    if dry_run:
        action = f"PUT /core/accounting-definition/{existing_id}/" if existing_id else "POST /core/accounting-definition/"
        print(f"\n[DRY RUN] Would {action}")
        print(json.dumps(send_payload, indent=2))
        return

    if existing_id:
        url = f"{client.BASE_URL}/core/accounting-definition/{existing_id}/"
        r = client.session.put(url, json=send_payload, timeout=30)
        verb = "Updated"
    else:
        url = f"{client.BASE_URL}/core/accounting-definition/"
        r = client.session.post(url, json=send_payload, timeout=30)
        verb = "Created"

    if r.status_code in (200, 201):
        result = r.json()
        print(f"\n  {verb} AD id={result.get('id') or existing_id} '{payload['name']}'")
    else:
        print(f"\n  ERROR: HTTP {r.status_code}")
        print(f"  {r.text[:500]}")
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Set up Purchase Booking Accounting Definition")
    parser.add_argument("--token",   required=True, help="ERP JWT token")
    parser.add_argument("--tenant",  required=True, help="Tenant ID")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, do not write")
    args = parser.parse_args()

    client = RhythmERPAPIClient()
    client.login_from_browser(token=args.token, tenant_id=args.tenant)

    sep = "-" * 60
    print(f"\n{sep}")
    print(f"  AD Setup — tenant {args.tenant}")
    print(sep)

    # ── Resolve accounts
    print("\nResolving Chart of Accounts...")
    coa = fetch_coa(client)
    print(f"  {len(coa)} accounts found")
    accounts = resolve_accounts(coa)
    for name, aid in accounts.items():
        print(f"    {name:30s} -> id={aid}")

    # ── Type of Sale IDs
    print("\nResolving Type of Sale options (parameter6)...")
    tos_ids = fetch_type_of_sale_ids(client)
    print(f"  IDs: {tos_ids}")

    # ── Find existing AD
    print("\nChecking existing Accounting Definition...")
    existing = find_existing_pb_ad(client)
    if existing:
        print(f"  Found: id={existing['id']} name='{existing.get('name')}' — will replace")
    else:
        print("  Not found — will create new")

    existing_id = existing["id"] if existing else None

    # ── Build payload
    payload = build_ad_payload(accounts, tos_ids)

    # ── Apply
    apply_ad(client, payload, existing_id, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n{sep}")
        print("  Done. Run batch_create.py --dry-run to verify AD filter passes.")
        print(sep)


if __name__ == "__main__":
    main()
