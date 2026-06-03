#!/usr/bin/env python3
"""
discover_all.py
---------------
Discover the API structure for ALL 10 Common Settings screens.

For each screen:
  1. Calls discover_structure() on the RhythmERPAPIClient
  2. Saves the full JSON structure to pages/common_settings/data/discovered/<screen>.json
  3. Prints a summary: field keys, children/steppers, dropdown fields with FK options

Usage:
    python pages/common_settings/scripts/discover_all.py
    python pages/common_settings/scripts/discover_all.py --token eyJhbGci...
"""

import sys
import os
import json
import time

# common_settings/scripts -> common_settings -> pages -> project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from common.logger import log

TENANT_ID = "599"

# The 10 Common Settings screens to discover
SCREENS = [
    "Designation",
    "Season",
    "UOM",
    "Error Code Mst",
    "HSN SAC",
    "Tax Authority",
    "Vehicle Master",
    "Bank",
    "Tax Rate",
    "UOM Conversion",
]

# Output directory for discovered JSON files
DATA_DIR = os.path.join(
    PROJECT_ROOT, "pages", "common_settings", "data", "discovered"
)


# ────────────────────────────────────────────────────────────────
# Argument parsing (same pattern as customer/batch_create.py)
# ────────────────────────────────────────────────────────────────

def parse_args():
    """Parse --token flag from sys.argv."""
    token = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--token" and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    return token


def prompt_token():
    """Prompt the user for a Bearer token if not provided via --token."""
    print("=" * 70)
    print("  COMMON SETTINGS — DISCOVER ALL (10 screens)")
    print("=" * 70)
    print()
    print("  No --token flag provided. Get your Bearer token from:")
    print("  1. Open https://rhythmerp.algorhythms.in in Chrome")
    print("  2. DevTools -> Network -> click any page")
    print("  3. Find any /core/ request -> copy Authorization header")
    print("  4. Paste the token value (after 'Bearer ')")
    print()
    token = input("  Token: ").strip()
    if not token:
        print("  No token entered. Exiting.")
        sys.exit(1)
    return token


# ────────────────────────────────────────────────────────────────
# Analysis helpers
# ────────────────────────────────────────────────────────────────

def extract_top_level_keys(detail: dict) -> list:
    """Return the top-level keys of a discovered entry."""
    return list(detail.keys())


def extract_children_info(detail: dict) -> dict:
    """
    Return info about children / steppers.

    Returns:
        {
            "has_children": bool,
            "stepper_count": int,
            "stepper_names": [str, ...],
        }
    """
    children = detail.get("children", [])
    if not children or not isinstance(children, list):
        return {"has_children": False, "stepper_count": 0, "stepper_names": []}

    stepper_names = [c.get("stepper_name", "<unnamed>") for c in children]
    return {
        "has_children": True,
        "stepper_count": len(children),
        "stepper_names": stepper_names,
    }


def extract_dropdown_fields(client: RhythmERPAPIClient, screen_name: str) -> list:
    """
    Return a list of dropdown field descriptors for a screen.

    Each descriptor:
        {
            "field_key": str,
            "field_label": str,
            "field_type": str,
            "filter_dropdown_raw_query": [...] | None,
            "options_count": int,
            "option_ids": [int, ...],
        }
    """
    schema = client.get_screen_schema(screen_name)
    if not schema:
        return []

    all_fields = client._flatten_fields(schema.get("screendefinition_set", []))
    dropdown_fields = []

    for field in all_fields:
        field_key = field.get("field_key", "")
        fdrq = field.get("filter_dropdown_raw_query")
        drq = field.get("dropdown_raw_query")

        # A field is considered a "dropdown" if it has either
        # filter_dropdown_raw_query or dropdown_raw_query
        is_dropdown = False
        options_source = None

        if fdrq is not None and fdrq:
            is_dropdown = True
            options_source = fdrq
        elif drq is not None and drq:
            is_dropdown = True
            options_source = drq

        if not is_dropdown:
            continue

        # Extract option IDs and keys
        option_ids = []
        if isinstance(options_source, list):
            for opt in options_source:
                if isinstance(opt, dict):
                    oid = opt.get("id")
                    if oid is not None:
                        option_ids.append(oid)

        dropdown_fields.append({
            "field_key": field_key,
            "field_label": field.get("field_label", field.get("label", "")),
            "field_type": field.get("field_type", field.get("type", "")),
            "filter_dropdown_raw_query": fdrq if fdrq else None,
            "options_count": len(option_ids) if isinstance(options_source, list) else 0,
            "option_ids": option_ids,
        })

    return dropdown_fields


def sanitize_filename(screen_name: str) -> str:
    """Convert a screen name to a safe filename (lowercase, underscores)."""
    return screen_name.lower().replace(" ", "_")


# ────────────────────────────────────────────────────────────────
# Per-screen discovery
# ────────────────────────────────────────────────────────────────

def discover_screen(client: RhythmERPAPIClient, screen_name: str, index: int, total: int):
    """
    Discover one screen's API structure.

    Returns:
        dict with keys: screen_name, success, detail, top_keys,
        children_info, dropdown_fields, error (if any)
    """
    label = f"[{index}/{total}]"
    print()
    print("=" * 70)
    print(f"  {label} {screen_name}")
    print("=" * 70)

    result = {
        "screen_name": screen_name,
        "success": False,
        "detail": None,
        "top_keys": [],
        "children_info": {},
        "dropdown_fields": [],
        "error": None,
    }

    try:
        # ── Step 1: Discover structure (list + get detail) ──
        log.info(f"{label} Discovering structure for '{screen_name}'...")
        detail = client.discover_structure(screen_name)

        if detail is None:
            result["error"] = "No existing entries found (create one via UI first)"
            log.warning(f"{label} {result['error']}")
            _print_failure(screen_name, result["error"])
            return result

        result["detail"] = detail
        result["success"] = True

        # ── Step 2: Extract top-level keys ──
        result["top_keys"] = extract_top_level_keys(detail)

        # ── Step 3: Extract children / stepper info ──
        result["children_info"] = extract_children_info(detail)

        # ── Step 4: Extract dropdown fields from schema ──
        log.info(f"{label} Fetching screen schema for dropdown analysis...")
        result["dropdown_fields"] = extract_dropdown_fields(client, screen_name)

        # ── Step 5: Save full JSON ──
        filename = sanitize_filename(screen_name) + ".json"
        filepath = os.path.join(DATA_DIR, filename)
        os.makedirs(DATA_DIR, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(detail, f, indent=2, default=str, ensure_ascii=False)
        log.info(f"{label} Saved to {filepath}")

        # ── Step 6: Print summary ──
        _print_summary(screen_name, result)

    except Exception as exc:
        result["error"] = str(exc)
        log.error(f"{label} Error discovering '{screen_name}': {exc}")
        _print_failure(screen_name, str(exc))

    return result


# ────────────────────────────────────────────────────────────────
# Print helpers
# ────────────────────────────────────────────────────────────────

def _print_summary(screen_name: str, result: dict):
    """Print a formatted summary for one screen."""
    top_keys = result["top_keys"]
    ci = result["children_info"]
    dd_fields = result["dropdown_fields"]

    print(f"\n  SCREEN: {screen_name}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Top-level keys ({len(top_keys)}): {top_keys}")

    if ci.get("has_children"):
        print(f"  Children/Steppers: YES ({ci['stepper_count']} stepper(s))")
        for sname in ci["stepper_names"]:
            print(f"    - {sname}")
    else:
        print(f"  Children/Steppers: NO (flat structure)")

    if dd_fields:
        print(f"  Dropdown fields ({len(dd_fields)}):")
        for df in dd_fields:
            fkey = df["field_key"]
            opt_count = df["options_count"]
            opt_ids = df.get("option_ids", [])
            print(f"    - {fkey}  ({opt_count} option(s), IDs: {opt_ids})")
            # Show full filter_dropdown_raw_query options if available
            fdrq = df.get("filter_dropdown_raw_query")
            if fdrq and isinstance(fdrq, list):
                for opt in fdrq:
                    if isinstance(opt, dict):
                        oid = opt.get("id", "?")
                        okey = opt.get("key", "?")
                        print(f"        ID={oid}  key={okey}")
    else:
        print(f"  Dropdown fields: None")

    print()


def _print_failure(screen_name: str, error_msg: str):
    """Print a failure notice for one screen."""
    print(f"\n  SCREEN: {screen_name}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  FAILED: {error_msg}")
    print()


def print_final_report(results: list):
    """Print a final summary table of all screens."""
    print()
    print("=" * 70)
    print("  FINAL DISCOVERY REPORT — Common Settings (10 screens)")
    print("=" * 70)
    print()

    success_count = 0
    fail_count = 0

    for r in results:
        name = r["screen_name"]
        if r["success"]:
            success_count += 1
            ci = r["children_info"]
            has_children = "YES" if ci.get("has_children") else "NO"
            dd_count = len(r["dropdown_fields"])
            dd_keys = [df["field_key"] for df in r["dropdown_fields"]]
            status_line = (
                f"  OK  | {name:20s} | children={has_children:3s} | "
                f"dropdowns={dd_count} | keys={dd_keys}"
            )
        else:
            fail_count += 1
            status_line = f"  FAIL| {name:20s} | {r['error']}"

        print(status_line)

    print()
    print(f"  Total: {len(results)} | Success: {success_count} | Failed: {fail_count}")
    print(f"  Output dir: {DATA_DIR}")
    print("=" * 70)


# ────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────

def main():
    token = parse_args()

    if not token:
        token = prompt_token()

    # ── Authenticate ──
    client = RhythmERPAPIClient()
    client.login_from_browser(token=token, tenant_id=TENANT_ID)
    log.info("[DISCOVER] Client authenticated. Starting discovery...")

    # Quick validation: try listing one screen
    test_result = client.list_entries("Designation", page=1, page_size=1)
    if not test_result:
        print("\n  Token appears invalid or expired. Get a new one from DevTools.")
        client.close()
        sys.exit(1)

    log.info("[DISCOVER] Token validated. Proceeding with all 10 screens...")

    # ── Discover all screens ──
    results = []
    total = len(SCREENS)

    for i, screen_name in enumerate(SCREENS, 1):
        result = discover_screen(client, screen_name, i, total)
        results.append(result)
        # Small delay between screens to be respectful
        if i < total:
            time.sleep(0.5)

    # ── Final report ──
    print_final_report(results)

    # ── Save combined summary JSON ──
    summary_path = os.path.join(DATA_DIR, "_summary.json")
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tenant_id": TENANT_ID,
        "total_screens": total,
        "success_count": sum(1 for r in results if r["success"]),
        "fail_count": sum(1 for r in results if not r["success"]),
        "screens": [],
    }
    for r in results:
        entry = {
            "screen_name": r["screen_name"],
            "success": r["success"],
            "error": r["error"],
            "top_keys": r["top_keys"],
            "has_children": r["children_info"].get("has_children", False),
            "stepper_count": r["children_info"].get("stepper_count", 0),
            "stepper_names": r["children_info"].get("stepper_names", []),
            "dropdown_fields": [
                {
                    "field_key": df["field_key"],
                    "options_count": df["options_count"],
                    "option_ids": df["option_ids"],
                }
                for df in r["dropdown_fields"]
            ],
        }
        summary["screens"].append(entry)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log.info(f"[DISCOVER] Combined summary saved to {summary_path}")

    client.close()
    log.info("[DISCOVER] Done. Session closed.")


if __name__ == "__main__":
    main()
