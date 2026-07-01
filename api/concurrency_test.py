"""
concurrency_test.py
-------------------
Fire the same ERP operation from two sessions simultaneously and report results.

Usage:
    python api/concurrency_test.py

Tokens and tenant IDs are hard-coded below for this run.
"""

import asyncio
import json
import time
import sys
import os

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pages.registration.modules.supplier.data.supplier_data import generate_supplier_api_payload

# ── Config ─────────────────────────────────────────────────────────

BASE_URL = "https://rhythmerp.algorhythms.in"
ENDPOINT = "/core/dynamic-screen-wrapper/"

SESSIONS = [
    {
        "label": "PC-1  Tenant A",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgyODk5NzgxLCJpYXQiOjE3ODI4ODUzODEsImp0aSI6ImFkYTU4ZTgwOTQzODQ5MmJiMmMzZTgxM2ZkODE1MjI1IiwidXNlcl9pZCI6IjIwMCJ9.rTBVnnh-kDvEgQIR-y3nbVGNEM8djvdXKAG8iuI6wT4",
        "tenant_id": "751",
    },
    {
        "label": "PC-2  Tenant A",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgyODk5ODk1LCJpYXQiOjE3ODI4ODU0OTUsImp0aSI6IjAwYzEwMTRhMzQyZjRjMTJhY2Q3ZGMxNTdhMTJlOGZmIiwidXNlcl9pZCI6IjIwMCJ9.WOB40CvQPcj8V9LMk2izSPTXjaboFDwMQDwvDJL5yAQ",
        "tenant_id": "751",
    },
]

# ── Core ────────────────────────────────────────────────────────────

async def create_supplier(session: dict, payload: dict, barrier: asyncio.Barrier) -> dict:
    headers = {
        "Authorization": f"Bearer {session['token']}",
        "Content-Type": "application/json",
        "X-Tenant-ID": session["tenant_id"],
    }
    url = BASE_URL + ENDPOINT

    # Wait at the barrier so both requests fire at the same instant
    await barrier.wait()
    t0 = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
        elapsed = round((time.monotonic() - t0) * 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        return {
            "label": session["label"],
            "status": resp.status_code,
            "ok": resp.status_code in (200, 201),
            "elapsed_ms": elapsed,
            "body": body,
        }
    except Exception as exc:
        elapsed = round((time.monotonic() - t0) * 1000)
        return {
            "label": session["label"],
            "status": None,
            "ok": False,
            "elapsed_ms": elapsed,
            "body": str(exc),
        }


async def run_concurrency_test(runs: int = 3):
    print(f"\n{'='*60}")
    print(f"  Concurrent Supplier Creation - {runs} round(s)")
    print(f"{'='*60}\n")

    all_conflicts = 0

    for i in range(1, runs + 1):
        print(f"-- Round {i}/{runs} --")

        # Both PCs use the same payload (same company name) to maximise conflict chance
        payload = generate_supplier_api_payload()
        company = payload.get("name") or payload.get("company_name", "?")
        print(f"  Payload: {company}")

        barrier = asyncio.Barrier(len(SESSIONS))
        tasks = [create_supplier(s, payload, barrier) for s in SESSIONS]
        results = await asyncio.gather(*tasks)

        statuses = [r["status"] for r in results]
        conflict = len(set(statuses)) > 1 or any(r["status"] not in (200, 201) for r in results)

        for r in results:
            icon = "OK" if r["ok"] else "FAIL"
            print(f"  [{icon}]  {r['label']}  ->  HTTP {r['status']}  ({r['elapsed_ms']} ms)")
            if not r["ok"]:
                # Print first 300 chars of error
                body_str = json.dumps(r["body"]) if not isinstance(r["body"], str) else r["body"]
                print(f"       {body_str[:300]}")

        if conflict:
            all_conflicts += 1
            print("  [CONFLICT] Responses diverged")
        else:
            print("  [PASS] Both succeeded consistently")
        print()

    print(f"{'='*60}")
    print(f"  Done. Conflicts: {all_conflicts}/{runs}")
    print("="*60)


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    asyncio.run(run_concurrency_test(runs))
