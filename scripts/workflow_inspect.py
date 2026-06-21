"""
Universal workflow inspector for Rhythm ERP.

Usage:
    python scripts/workflow_inspect.py --token "eyJ..." --tenant 708 --screen Farmer
    python scripts/workflow_inspect.py --token "eyJ..." --tenant 708 --screen Farmer --entry-id 125
    python scripts/workflow_inspect.py --token "eyJ..." --tenant 708 --screen Farmer --dry-run

Works on ANY tenant, ANY screen, ANY token.
Captures workflow_action structure and tests transitions.
"""

import argparse
import base64
import json
import sys
from collections import Counter
from typing import Optional

import requests


def decode_exec_ref(ref: str) -> str:
    try:
        return base64.b64decode(ref).decode("utf-8")
    except Exception:
        return f"(base64 error: {ref[:50]}...)"


def main():
    parser = argparse.ArgumentParser(description="Inspect workflow structure on any ERP tenant")
    parser.add_argument("--token", required=True, help="Bearer token")
    parser.add_argument("--tenant", required=True, help="X-Tenant-ID")
    parser.add_argument("--base", default="https://rhythmerp.algorhythms.in", help="ERP base URL")
    parser.add_argument("--screen", default="Farmer", help="Screen name (e.g. Farmer, Supplier)")
    parser.add_argument("--entry-id", type=int, help="Specific entry to inspect")
    parser.add_argument("--action", choices=["Verify", "Approve", "SendBack"],
                        help="Try a specific workflow action")
    parser.add_argument("--dry-run", action="store_true", help="Only fetch, don't POST")
    args = parser.parse_args()

    H = {
        "Authorization": f"Bearer {args.token}",
        "X-Tenant-ID": args.tenant,
        "X-Original-Tenant-ID": args.tenant,
        "Content-Type": "application/json",
    }
    BASE = args.base.rstrip("/")
    API = f"{BASE}/core/dynamic-screen-wrapper/"
    WF_API = f"{BASE}/core/dynamic-screen-workflow-action/"

    sep = "=" * 60
    bar = "-" * 60

    print()
    print(sep)
    print(f"  Workflow Inspector")
    print(f"  Screen: {args.screen}  |  Tenant: {args.tenant}")
    print(sep)
    print()

    # Step 1: List entries to find workflow_status
    print(bar)
    print(f"  Step 1: Listing entries to find workflow_status")
    print(bar)
    r = requests.get(f"{API}{args.screen}/?page=1&page_size=200", headers=H, timeout=30)
    if r.status_code != 200:
        print(f"  ERROR: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    data = r.json()
    rows = data.get("screenmatlistingdata_set") or data.get("results") or data.get("data") or data
    if isinstance(rows, dict):
        rows = [rows]

    workflow_applicable = data.get("is_workflow_applicable", None)
    print(f"  is_workflow_applicable: {workflow_applicable}")
    print(f"  Total entries: {len(rows)}")

    statuses = Counter(x.get("workflow_status") for x in rows if isinstance(x, dict))
    wf_ids = [(x.get("id"), x.get("workflow_status"), x.get("workflow_id"))
              for x in rows if isinstance(x, dict) and x.get("workflow_status")]
    print(f"  Workflow statuses: {dict(statuses)}")
    if wf_ids:
        print(f"  Entries with workflow:")
        for eid, ws, wid in wf_ids[:10]:
            print(f"    id={eid:>5}  status={ws or '':20}  wf_id={wid or 'N/A':36}")
    else:
        print(f"  No entries have workflow_status set.")
        print(f"  This screen may not have workflow enabled on this tenant.")

    # Step 2: Inspect entry detail for workflow_action
    entry_id = args.entry_id
    if not entry_id and wf_ids:
        entry_id = wf_ids[0][0]
        print()
        print(f"  No --entry-id given, using first with workflow: id={entry_id}")
    elif not entry_id:
        entry_id = rows[0]["id"] if rows else None
        print()
        print(f"  No workflow entries, using first entry: id={entry_id}")

    detail = {}
    paths = []
    if entry_id:
        print()
        print(bar)
        print(f"  Step 2: Fetching detail for id={entry_id}")
        print(bar)
        r2 = requests.get(f"{API}{args.screen}/{entry_id}/", headers=H, timeout=30)
        if r2.status_code != 200:
            print(f"  ERROR: {r2.status_code} {r2.text[:200]}")
            sys.exit(1)
        detail = r2.json()
        print(f"  workflow_status: {detail.get('workflow_status')}")
        print(f"  workflow_id: {detail.get('workflow_id')}")
        print(f"  created_by: {detail.get('created_by')}")
        print(f"  updated_by: {detail.get('updated_by')}")

        wa = detail.get("workflow_action", {})
        raw = wa.get("rawConditions", {})
        paths = raw.get("paths", [])
        if paths:
            print()
            print(f"  Available workflow transitions ({len(paths)}):")
            for p in paths:
                decoded_ref = decode_exec_ref(p.get("executionReference", ""))
                conds = p.get("conditions", [])
                print(f"    nodeId={p.get('nodeId'):>5}  label={p.get('label'):25}  ref={decoded_ref}")
                for c in conds:
                    print(f"         {c.get('conditionKey')} = {c.get('conditionValue')}")
        else:
            print()
            print(f"  workflow_action: {json.dumps(wa, indent=2)[:1000]}")

    # Step 3: Try workflow action
    action = args.action
    if not action and paths:
        action = paths[0]["label"]
        print()
        print(bar)
        print(f"  Step 3: No --action given, using first: '{action}'")
        print(bar)

    if action and entry_id and not args.dry_run:
        target_path = None
        for p in paths:
            if p["label"] == action:
                target_path = p
                break
        if not target_path:
            print(f"  Action '{action}' not available for this entry!")
            sys.exit(1)

        body = {
            "attribute_name": args.screen,
            "entry_id": entry_id,
            "id": entry_id,
            "workflow_id": detail["workflow_id"],
            "conditions": target_path["conditions"],
            "executionReference": target_path["executionReference"],
        }
        print()
        print(f"  POST body:")
        print(json.dumps(body, indent=4))
        print()

        r3 = requests.post(WF_API, json=body, headers=H, timeout=30)
        print(f"  Response: {r3.status_code}")
        if r3.status_code in (200, 201):
            print(f"  SUCCESS: {r3.text[:500]}")
        else:
            print(f"  {r3.text[:1000]}")
            print()
            if r3.status_code == 400:
                print("  TROUBLESHOOTING:")
                print("    - The token user may not have permission for this action")
                print("    - The entry may be missing required related data")
                print("    - Compare with UI Network panel to find exact body differences")
    elif action and args.dry_run:
        print()
        print(f"  --dry-run: would POST with action: {action}")

    # Summary
    print()
    print(sep)
    print(f"  SUMMARY")
    print(sep)
    print(f"  Screen:              {args.screen}")
    print(f"  Tenant:              {args.tenant}")
    print(f"  Workflow applicable: {workflow_applicable}")
    print(f"  Entries with WF:     {len(wf_ids)}")
    print(f"  Available statuses:  {dict(statuses)}")
    if paths:
        print(f"  Transitions found:   {[p['label'] for p in paths]}")
        top_status = statuses.most_common(1)[0][0] if statuses else "Register"
        print()
        print(f"  To capture exact body from UI:")
        print(f"    1. Open ERP -> List -> Edit a {top_status}-status entry")
        print(f"    2. DevTools -> Network (filter: workflow-action)")
        print(f"    3. Click a transition button in the UI")
        print(f"    4. Right-click the request -> Copy -> Copy as cURL")
    print()


if __name__ == "__main__":
    main()
