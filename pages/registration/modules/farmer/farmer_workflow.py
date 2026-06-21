"""
farmer_workflow.py
------------------
Selenium script that verifies and approves a list of Farmer records via the ERP UI.

WHY THIS EXISTS:
  The ERP API verify endpoint fails with "Land details are not available" because
  land_classification is a readonly field computed by frontend JS when the Edit form
  loads — not by the API. Opening Edit in the UI triggers that computation, so
  Verify/Approve buttons work immediately after opening Edit.

FLOW PER RECORD (verify_approve):
  1. Search by name → first row appears
  2. more_vert → Edit → popup opens (JS computes land_classification)
  3. Click Verify → swal confirm → popup closes
  4. Row is still in table → more_vert → Edit again
  5. Click Approve → swal confirm → popup closes → next record

USAGE (standalone):
  python -m pages.registration.modules.farmer.farmer_workflow --ids 162 163 164
  python -m pages.registration.modules.farmer.farmer_workflow --run-id <batch_run_id>
  python -m pages.registration.modules.farmer.farmer_workflow --run-id <id> --action verify
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from common.browser_utils import get_driver
from common.logger import log
from config import RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD
from pages.login_screens.Login_Screens_.login_page import LoginPage
from pages.registration.modules.farmer.farmer_page import FarmerPage

BATCH_RESULTS_DIR = Path(PROJECT_ROOT) / "api" / "batch_results"

# ── XPath templates ──────────────────────────────────────────────────────────
_MENU_VISIBLE = "div.mat-mdc-menu-content button, div.mat-menu-content button"
_MENU_ITEM_XPATH = (
    "//div[contains(@class,'mat-mdc-menu-content') or contains(@class,'mat-menu-content')]"
    "//span[contains(@class,'erp-menu-title') and normalize-space(text())='{label}']"
    "/ancestor::button"
)
_FOOTER_BTN_XPATH = (
    "//div[contains(@class,'popup-footer')]"
    "//button[normalize-space(.)='{label}' or contains(normalize-space(.),'{label}')]"
)
_POPUP_FOOTER = (By.CSS_SELECTOR, "div.popup-footer")
_SWAL_BTN = (By.CSS_SELECTOR, ".swal2-confirm, .swal2-ok")
_TABLE_ROW = (By.CSS_SELECTOR, "table tbody tr")


def _w(driver, t=8):
    return WebDriverWait(driver, t)


# ── Atomic UI actions ────────────────────────────────────────────────────────

def _dismiss_swal(driver) -> bool:
    try:
        btn = _w(driver, 4).until(EC.element_to_be_clickable(_SWAL_BTN))
        driver.execute_script("arguments[0].click();", btn)
        # Wait for swal to disappear rather than sleeping
        try:
            _w(driver, 3).until_not(EC.presence_of_element_located(_SWAL_BTN))
        except Exception:
            pass
        return True
    except Exception:
        return False


def _wait_popup_closes(driver):
    try:
        _w(driver, 8).until_not(EC.presence_of_element_located(_POPUP_FOOTER))
    except Exception:
        pass


def _find_first_row(driver):
    try:
        rows = driver.find_elements(*_TABLE_ROW)
        for row in rows:
            try:
                if row.is_displayed():
                    return row
            except Exception:
                continue
    except Exception:
        pass
    return None


def _open_row_menu(driver, row):
    trigger = row.find_element(By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger")
    driver.execute_script("arguments[0].click();", trigger)
    _w(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, _MENU_VISIBLE)))


def _click_menu_edit(driver):
    xpath = _MENU_ITEM_XPATH.format(label="Edit")
    btn = _w(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", btn)
    # Wait for popup footer to confirm it opened
    _w(driver, 10).until(EC.presence_of_element_located(_POPUP_FOOTER))


def _click_footer_btn(driver, label: str, timeout=8) -> bool:
    xpath = _FOOTER_BTN_XPATH.format(label=label)
    try:
        btn = _w(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
        return True
    except TimeoutException:
        return False


# ── Search + get row ─────────────────────────────────────────────────────────

def _search_and_get_row(page: FarmerPage, record_id: int, name: str):
    """Search by name, wait for table to update, return the first row (or None)."""
    driver = page.driver
    _dismiss_swal(driver)  # clear any stray swal before searching

    page.search_farmer(name)

    # Wait for at least one row to appear (up to 6s)
    try:
        _w(driver, 6).until(EC.presence_of_element_located(_TABLE_ROW))
    except TimeoutException:
        log.warning(f"[Workflow] #{record_id}: table empty after search for '{name}'")
        return None

    row = _find_first_row(driver)
    if not row:
        log.warning(f"[Workflow] #{record_id}: no visible row after search for '{name}'")
    return row


# ── Per-record workflow ───────────────────────────────────────────────────────

def _workflow_one(page: FarmerPage, record_id: int, name: str, action: str) -> dict:
    driver = page.driver
    result = {"id": record_id, "status": "skipped", "error": None}

    do_verify = action in ("verify", "verify_approve")
    do_approve = action in ("approve", "verify_approve")

    log.info(f"[Workflow] #{record_id} '{name}' — {action}")

    # ── Search once; reuse row for both Verify and Approve ──
    row = _search_and_get_row(page, record_id, name)
    if not row:
        result["status"] = "failed"
        result["error"] = "Row not found after search"
        return result

    # ── Verify step ──
    if do_verify:
        try:
            _open_row_menu(driver, row)
            _click_menu_edit(driver)
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Could not open Edit for Verify: {e}"
            return result

        # Popup is open; form load computed land_classification
        if not _click_footer_btn(driver, "Verify"):
            # Maybe already verified — Approve button present instead
            if _click_footer_btn(driver, "Approve", timeout=3):
                log.info(f"[Workflow] #{record_id}: already verified → approving directly")
                _dismiss_swal(driver)
                _wait_popup_closes(driver)
                result["status"] = "approved"
                return result
            _click_footer_btn(driver, "Cancel", timeout=3)
            result["status"] = "failed"
            result["error"] = "Verify button not found"
            return result

        _dismiss_swal(driver)
        _wait_popup_closes(driver)
        result["status"] = "verified"
        log.info(f"[Workflow] #{record_id}: VERIFIED ✓")

        # Row is still in the table — re-fetch it (DOM may have refreshed)
        row = _find_first_row(driver)
        if not row:
            # Fallback: re-search
            row = _search_and_get_row(page, record_id, name)
        if not row:
            if do_approve:
                result["status"] = "verified"
                result["error"] = "Row gone after Verify; Approve skipped"
            return result

    # ── Approve step ──
    if do_approve:
        try:
            _open_row_menu(driver, row)
            _click_menu_edit(driver)
        except Exception as e:
            result["status"] = result.get("status", "failed")
            result["error"] = f"Could not open Edit for Approve: {e}"
            return result

        if not _click_footer_btn(driver, "Approve"):
            _click_footer_btn(driver, "Cancel", timeout=3)
            result["status"] = "failed"
            result["error"] = "Approve button not found (not yet verified?)"
            return result

        _dismiss_swal(driver)
        _wait_popup_closes(driver)
        result["status"] = "approved"
        log.info(f"[Workflow] #{record_id}: APPROVED ✓")

    return result


# ── Main entry point ─────────────────────────────────────────────────────────

def run(ids: list, action: str = "verify_approve") -> list[dict]:
    """
    ids: list of (record_id, name) tuples, or list of ints.
    Login once, process all farmers, quit.
    """
    # Normalise to (int, str) tuples
    pairs: list[tuple[int, str]] = []
    for item in ids:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            pairs.append((int(item[0]), str(item[1])))
        else:
            pairs.append((int(item), str(item)))
    total = len(pairs)

    driver = get_driver()
    driver.maximize_window()
    results = []

    try:
        login_page = LoginPage(driver)
        driver.get(RHYTHMERP_LOGIN_URL)
        login_page.wait_seconds(2)
        login_page.enter_email(RHYTHMERP_EMAIL)
        login_page.enter_password(RHYTHMERP_PASSWORD)
        login_page._dismiss_tenant_dropdown()
        login_page.click_login()
        login_page.wait_seconds(3)
        login_page.wait_for_login_complete()
        log.info("[Workflow] Logged in")

        page = FarmerPage(driver)
        page.navigate_to_page()
        # Wait for table to be present before starting
        _w(driver, 10).until(EC.presence_of_element_located(_TABLE_ROW))

        for i, (record_id, name) in enumerate(pairs, 1):
            log.info(f"[Workflow] [{i}/{total}] #{record_id} '{name}'")
            r = _workflow_one(page, record_id, name, action)
            results.append(r)
            err_part = f"  ({r['error']})" if r.get("error") else ""
            icon = "✓" if r["status"] in ("verified", "approved") else "✗"
            print(f"  [{i}/{total}]  #{record_id} '{name}'  {icon}  {r['status']}{err_part}")

    except Exception as e:
        log.error(f"[Workflow] Fatal: {e}")
        print(f"Fatal error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    approved = sum(1 for r in results if r["status"] == "approved")
    verified_only = sum(1 for r in results if r["status"] == "verified")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"\nDone: {approved} approved, {verified_only} verified-only, {failed} failed / {total} total")
    return results


# ── CLI helpers ──────────────────────────────────────────────────────────────

def _load_ids_from_run(run_id: str) -> list[tuple[int, str]]:
    path = BATCH_RESULTS_DIR / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Batch result not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return [
        (int(r["record_id"]), str(r.get("name", r["record_id"])))
        for r in data.get("records", [])
        if r.get("status") in ("created", "verified") and str(r.get("record_id", "")).isdigit()
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify/Approve farmers via ERP UI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", help="Batch run ID (reads api/batch_results/<id>.json)")
    group.add_argument("--ids", nargs="+", type=int, help="Explicit farmer IDs")
    parser.add_argument(
        "--action",
        choices=["verify", "approve", "verify_approve"],
        default="verify_approve",
    )
    args = parser.parse_args()

    if args.run_id:
        farmer_pairs = _load_ids_from_run(args.run_id)
        print(f"Loaded {len(farmer_pairs)} farmers from run {args.run_id}")
    else:
        farmer_pairs = [(fid, str(fid)) for fid in args.ids]

    if not farmer_pairs:
        print("No IDs to process.")
        sys.exit(0)

    run(farmer_pairs, action=args.action)
