"""
purchase_chain_jv.py
--------------------
Full Purchase Flow with JV Check.

Runs the standard PO → GP → GRN → QC → PB chain, then verifies the
Journal Voucher report to confirm accounting entries are balanced
(Σ Debit == Σ |Credit|) for the Purchase Booking account.

Usage:
    python -m pages.private_b2b.scripts.purchase_chain_jv --token <TOKEN> --tenant 666
    python -m pages.private_b2b.scripts.purchase_chain_jv --token <TOKEN> --tenant 666 --count 2

The existing purchase_chain.py is untouched.
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log
from pages.private_b2b.scripts.purchase_chain import PurchaseChain, setup_argparse
from pages.private_b2b.modules.journal_voucher.utils.api_jv_utils import JVAPIUtils


class PurchaseChainWithJV:
    """
    Thin wrapper around PurchaseChain that adds a JV verification step
    after each PB is created.

    The chain logic is fully delegated to PurchaseChain — no duplication.
    """

    def __init__(self, token: str, tenant: str = "666", delay: float = 0.0):
        self.client = RhythmERPAPIClient()
        self.client.login_from_browser(token=token, tenant_id=tenant)

        self.chain = PurchaseChain(token=token, tenant=tenant, delay=delay)
        self.jv = JVAPIUtils(self.chain.client)

    def run(self, supplier_ref_id: int = 1, **overrides) -> dict:
        """
        Run one full chain then verify the JV for its PB.

        Returns the standard chain result dict extended with:
            result["jv"] = JVVerificationResult  (or None if no PB)
        """
        result = self.chain.run(supplier_ref_id=supplier_ref_id, **overrides)
        result["jv"] = self._verify_jv(result)
        return result

    def run_multiple(self, count: int, supplier_ref_id: int = 1, **overrides) -> list:
        results = []
        for i in range(count):
            log.info(f"\nChain [{i + 1}/{count}] — supplier={supplier_ref_id}")
            results.append(self.run(supplier_ref_id=supplier_ref_id, **overrides))
        return results

    # ── Private ───────────────────────────────────────────────────────────

    def _verify_jv(self, chain_result: dict):
        pb = chain_result.get("pb")
        if not pb:
            log.info("[JV] No PB in chain result — skipping JV check")
            return None

        pb_ref_no = pb.get("ref")
        if not pb_ref_no:
            log.warning("[JV] PB has no ref_no — skipping JV check")
            return None

        # Use chain context IDs for the JV report filter
        ctx = chain_result.get("ctx") or self.chain.last_ctx
        if ctx is None:
            log.warning("[JV] No chain context available — skipping JV check")
            return None

        return self.jv.verify_pb(
            pb_ref_no=pb_ref_no,
            division_id=ctx.parameter1,
            department_id=ctx.parameter2,
            type_of_sale_id=ctx.parameter5,
            location_id=ctx.parameter6,
        )


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    token = args.token or os.environ.get("ERP_TOKEN", "")
    if not token:
        print("ERROR: No token provided. Use --token or set ERP_TOKEN env var.")
        sys.exit(1)

    runner = PurchaseChainWithJV(
        token=token,
        tenant=args.tenant,
        delay=args.delay,
    )

    print(f"\n{'=' * 60}")
    print(f"Full Purchase Flow + JV Check — {args.count} chain(s), supplier={args.supplier}")
    print(f"{'=' * 60}")

    start = time.time()
    results = runner.run_multiple(
        count=args.count,
        supplier_ref_id=args.supplier,
        num_items=args.num_items,
        item_ref_id=args.item_ref_id,
    )
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    for i, r in enumerate(results):
        po  = r.get("po") or {}
        gp  = r.get("gp") or {}
        grn = r.get("grn") or {}
        qc  = r.get("qc") or {}
        pb  = r.get("pb") or {}
        jv  = r.get("jv")

        pb_str = f"PB {pb.get('id', '?')} ({pb.get('ref', '?')})" if pb else "PB (skipped)"
        jv_str = jv.summary() if jv else "JV (skipped)"
        jv_ok  = "✓" if (jv and jv.ok()) else ("✕" if jv else "—")

        print(
            f"  Chain [{i + 1}]:  "
            f"PO {po.get('id','?')}  →  GP {gp.get('id','?')}  →  "
            f"GRN {grn.get('id','?')}  →  QC {qc.get('id','?')}  →  "
            f"{pb_str}"
        )
        print(f"            JV {jv_ok}  {jv_str}")

    print(f"\n  Total time: {elapsed:.1f}s  ({elapsed / max(args.count,1):.1f}s per chain)")

    failed_jv = [r for r in results if r.get("jv") and not r["jv"].ok()]
    if failed_jv:
        print(f"\n  WARNING: {len(failed_jv)} JV check(s) failed.")
        sys.exit(1)
    else:
        print(f"\n  All {args.count} chain(s) + JV checks passed.")


if __name__ == "__main__":
    main()
