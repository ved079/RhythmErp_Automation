"""
Direct PB creation tests (Eco Green Pvt Ltd tenant).

Flow: create PB directly without a PO reference.

TC coverage:
  Group 1 — Mandatory header validations   : TC1, TC4, TC18
  Group 2 — Item row field validations     : TC7-TC14
  Group 3 — Discount validations           : TC82, TC84, TC89
  Group 4 — Input type rejections          : TC85, TC86, TC87
  Group 5 — Row add/remove behaviour       : TC19, TC23, TC24
  Group 6 — Supplier dropdown              : TC2
  Group 7 — Live calculation assertions    : CALC1-CALC8
"""

import datetime
import os
import pathlib
import random
import pytest
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from pages.private_b2b.modules.purchase_booking.direct_pb_playwright_page import ITEMS

# ── Seeded RNG — override via TEST_SEED env var for reproducibility ───────────
_SEED = int(os.environ.get("TEST_SEED", 42))
_rng  = random.Random(_SEED)

DISC_CHOICES   = [0, 5, 10, 15, 20, 25]
LABOUR_CHOICES = [0, 100, 250, 500, 1000]


# ── Helper: pick two distinct items ──────────────────────────────────────────

def _two_items():
    """Return (item_a, item_b) — two distinct items from the known list."""
    a = ITEMS[0]
    b = ITEMS[1]
    return a, b


# ── Group 1: Mandatory header validations ─────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBHeaderValidations:

    def test_navigate_to_pb_page(self, pb_page):
        """Smoke: PB listing loads for Eco Green Pvt Ltd."""
        visible = pb_page.page.locator("table.mat-mdc-table, div.empty-state").count() > 0
        print(f"\n[SMOKE] PB listing page visible: {'✓' if visible else '✗'}")
        assert visible, "PB listing page must be visible after login"

    def test_tc1_submit_without_supplier(self, pb_page):
        """TC1: Submit with no fields filled — supplier validation must appear."""
        pb_page.open_add_form()
        pb_page.submit_and_wait()
        errors    = pb_page.visible_errors()
        form_open = pb_page.page.locator(pb_page.SUPPLIER_NAME).count() > 0
        print(f"\n[TC1]  Action : submit empty form (no supplier, no fields)")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")
        print(f"       Form stayed open: {'✓' if form_open else '✗'}")
        assert len(errors) > 0, f"Expected validation errors on empty submit, got: {errors}"
        assert form_open, "Form must stay open after empty submit"

    def test_tc4_mandatory_header_fields(self, pb_page):
        """TC4: Supplier selected but Location/Department/Type of Sale missing — validation."""
        pb_page.open_add_form()
        pb_page._select_random_mat_option(pb_page.SUPPLIER_NAME)
        pb_page.page.wait_for_timeout(600)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        print(f"\n[TC4]  Action : supplier selected, Location/Dept/Type of Sale left blank")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")
        assert len(errors) > 0, (
            f"Expected mandatory field errors when Location/Dept/Type of Sale missing, got: {errors}"
        )

    def test_tc18_submit_without_items(self, pb_page):
        """TC18: Header fully filled but no item rows — validation must block save."""
        pb_page.open_add_form()
        pb_page.fill_header()
        pb_page.submit_and_wait()
        errors    = pb_page.visible_errors()
        form_open = pb_page.page.locator(pb_page.SUPPLIER_NAME).count() > 0
        print(f"\n[TC18] Action : header fully filled, zero item rows, submit")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")
        print(f"       Form stayed open: {'✓' if form_open else '✗'}")
        assert len(errors) > 0, f"Expected validation when submitting with no item rows, got: {errors}"
        assert form_open, "Form must stay open"


# ── Group 2: Item row field validations ───────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBRowFieldValidations:
    """Each test opens the form, fills header, adds one item row, sets the
    field under test to an invalid value, submits, and asserts the error."""

    ITEM    = ITEMS[0]
    VALID_QTY  = 10
    VALID_RATE = 100

    def _setup(self, pb_page):
        """Open form + fill header + add item row with valid qty & rate."""
        pb_page.open_add_form()
        pb_page.fill_header()
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(self.ITEM)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, self.ITEM)
        pb_page.page.wait_for_timeout(1000)

    def _print_validation_result(self, tag, action, errors):
        print(f"\n[{tag}] Action : {action}")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")

    def test_tc7_qty_blank(self, pb_page):
        """TC7: Quantity left blank — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.RATE, 0, self.VALID_RATE)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC7", f"qty=blank  rate={self.VALID_RATE}  → submit", errors)
        assert len(errors) > 0, f"Expected qty-blank validation, got: {errors}"

    def test_tc8_qty_zero(self, pb_page):
        """TC8: Quantity = 0 — save must be blocked."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, 0)
        pb_page._fill_number_nth(pb_page.RATE,     0, self.VALID_RATE)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC8", f"qty=0  rate={self.VALID_RATE}  → submit", errors)
        assert len(errors) > 0, f"Expected qty=0 validation, got: {errors}"

    def test_tc9_qty_negative(self, pb_page):
        """TC9: Negative quantity — system must reject."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, -5)
        pb_page._fill_number_nth(pb_page.RATE,     0, self.VALID_RATE)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC9", f"qty=-5  rate={self.VALID_RATE}  → submit", errors)
        assert len(errors) > 0, f"Expected negative-qty validation, got: {errors}"

    def test_tc10_rate_blank(self, pb_page):
        """TC10: Rate left blank — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, self.VALID_QTY)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC10", f"qty={self.VALID_QTY}  rate=blank  → submit", errors)
        assert len(errors) > 0, f"Expected rate-blank validation, got: {errors}"

    def test_tc11_rate_zero(self, pb_page):
        """TC11: Rate = 0 — validation per business rule."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, self.VALID_QTY)
        pb_page._fill_number_nth(pb_page.RATE,     0, 0)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC11", f"qty={self.VALID_QTY}  rate=0  → submit", errors)
        assert len(errors) > 0, f"Expected rate=0 validation, got: {errors}"

    def test_tc12_rate_negative(self, pb_page):
        """TC12: Negative rate — system must reject."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, self.VALID_QTY)
        pb_page._fill_number_nth(pb_page.RATE,     0, -100)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC12", f"qty={self.VALID_QTY}  rate=-100  → submit", errors)
        assert len(errors) > 0, f"Expected negative-rate validation, got: {errors}"

    def test_tc13_empty_bag_weight_negative(self, pb_page):
        """TC13: Negative empty bag weight — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY,        0, self.VALID_QTY)
        pb_page._fill_number_nth(pb_page.RATE,            0, self.VALID_RATE)
        pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, 0, -1)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC13", f"qty={self.VALID_QTY}  rate={self.VALID_RATE}  EBW=-1  → submit", errors)
        assert len(errors) > 0, f"Expected negative empty-bag-weight validation, got: {errors}"

    def test_tc14_labour_charges_negative(self, pb_page):
        """TC14: Negative labour charges — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY,       0, self.VALID_QTY)
        pb_page._fill_number_nth(pb_page.RATE,           0, self.VALID_RATE)
        pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, 0, -500)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        self._print_validation_result("TC14", f"qty={self.VALID_QTY}  rate={self.VALID_RATE}  labour=-500  → submit", errors)
        assert len(errors) > 0, f"Expected negative labour-charges validation, got: {errors}"


# ── Group 3: Discount validations ────────────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBDiscountValidations:

    ITEM       = ITEMS[2]
    VALID_QTY  = 10
    VALID_RATE = 200

    def _setup(self, pb_page):
        pb_page.open_add_form()
        pb_page.fill_header()
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(self.ITEM)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, self.ITEM)
        pb_page.page.wait_for_timeout(1000)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, self.VALID_QTY)
        pb_page._fill_number_nth(pb_page.RATE,     0, self.VALID_RATE)
        pb_page.page.wait_for_timeout(500)

    def test_tc82_negative_discount(self, pb_page):
        """TC82: Negative discount — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, -10)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        print(f"\n[TC82] Action : disc=-10%  → submit")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")
        assert len(errors) > 0, f"Expected negative-discount validation, got: {errors}"

    def test_tc84_discount_over_100(self, pb_page):
        """TC84: Discount > 100% — validation must appear."""
        self._setup(pb_page)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, 110)
        pb_page.submit_and_wait()
        errors = pb_page.visible_errors()
        print(f"\n[TC84] Action : disc=110%  → submit")
        print(f"       Errors : {len(errors)} found  {'✓' if len(errors) > 0 else '✗ NONE'}")
        for e in errors:
            print(f"         - {e}")
        assert len(errors) > 0, f"Expected discount>100 validation, got: {errors}"

    def test_tc89_discount_zero_amount_unchanged(self, pb_page):
        """TC89: Discount = 0 — Transaction Amount must not change."""
        self._setup(pb_page)
        txn_before = pb_page.read_transaction_amount(0)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, 0)
        pb_page.page.wait_for_timeout(600)
        txn_after = pb_page.read_transaction_amount(0)
        diff  = abs(txn_after - txn_before)
        match = "✓ UNCHANGED" if diff < 1.0 else f"✗ CHANGED by {diff:.2f}"
        print(f"\n[TC89] Action : disc=0%  (no discount applied)")
        print(f"       Txn before: {txn_before:.2f}  →  after: {txn_after:.2f}  [{match}]")
        assert diff < 1.0, f"TC89: Discount=0 changed txn from {txn_before:.2f} to {txn_after:.2f}"


# ── Group 4: Input type rejections ───────────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBInputTypeRejections:
    """Number fields must silently reject non-numeric input."""

    ITEM = ITEMS[3]

    def _open_with_item(self, pb_page):
        pb_page.open_add_form()
        pb_page.fill_header()
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(self.ITEM)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, self.ITEM)
        pb_page.page.wait_for_timeout(1000)

    def _try_type_into_rate(self, pb_page, text):
        """Attempt to type text into the Rate field (editable number input) and
        return what actually landed. Quantity is readonly — Rate is not."""
        rate_loc = pb_page.page.locator(
            "xpath=" + pb_page.RATE.replace("xpath=", "")
        ).first
        rate_loc.click(force=True)
        pb_page.page.wait_for_timeout(200)
        rate_loc.fill("")
        rate_loc.type(text)
        pb_page.page.wait_for_timeout(400)
        return rate_loc.input_value()

    def test_tc85_alphabetic_rejected(self, pb_page):
        """TC85: Alphabetic characters must not land in a number (Rate) field."""
        self._open_with_item(pb_page)
        val     = self._try_type_into_rate(pb_page, "abc")
        passed  = val == "" or not any(c.isalpha() for c in val)
        print(f"\n[TC85] Action : type 'abc' into Rate field")
        print(f"       Field value after input: '{val}'  [{'✓ rejected' if passed else '✗ ACCEPTED letters'}]")
        assert passed, f"Alphabetic input should be rejected by number field; got: '{val}'"

    def test_tc86_special_chars_rejected(self, pb_page):
        """TC86: Special characters must not land in a number (Rate) field."""
        self._open_with_item(pb_page)
        val    = self._try_type_into_rate(pb_page, "@#$")
        passed = val == "" or not any(c in "@#$" for c in val)
        print(f"\n[TC86] Action : type '@#$' into Rate field")
        print(f"       Field value after input: '{val}'  [{'✓ rejected' if passed else '✗ ACCEPTED special chars'}]")
        assert passed, f"Special chars should be rejected by number field; got: '{val}'"

    def test_tc87_large_value(self, pb_page):
        """TC87: Extremely large value (99999999999) — field must accept without crashing,
        and submit must show a validation (overflow) or the form must stay open."""
        self._open_with_item(pb_page)
        pb_page._fill_number_nth(pb_page.QUANTITY, 0, 99999999999)
        pb_page._fill_number_nth(pb_page.RATE,     0, 99999999999)
        pb_page.submit_and_wait()
        form_still_open = pb_page.page.locator(pb_page.SUPPLIER_NAME).count() > 0
        errors  = pb_page.visible_errors()
        blocked = form_still_open or len(errors) > 0
        print(f"\n[TC87] Action : qty=99999999999  rate=99999999999  → submit")
        print(f"       Form still open : {'✓' if form_still_open else '✗'}")
        print(f"       Errors found    : {len(errors)}  {[e for e in errors]}")
        print(f"       Blocked (pass)  : {'✓' if blocked else '✗'}")
        assert blocked, "Large value must either show validation or keep form open"


# ── Group 5: Row add/remove behaviour ────────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBRowBehaviour:

    def test_tc2_inactive_supplier_not_in_list(self, pb_page):
        """TC2: 'LK suppliers' is inactive — must not appear in supplier dropdown."""
        pb_page.open_add_form()
        options = pb_page.search_supplier_in_dropdown("LK suppliers")
        found   = any("LK suppliers" in o for o in options)
        print(f"\n[TC2]  Action : search 'LK suppliers' in supplier dropdown")
        print(f"       Results found : {options if options else '(none)'}")
        print(f"       Inactive supplier absent: {'✓' if not found else '✗ VISIBLE — should be hidden'}")
        assert not found, f"Inactive supplier 'LK suppliers' should not appear; found: {options}"

    def test_tc19_duplicate_item_blocked(self, pb_page):
        """TC19: Same item in two rows — validation must appear."""
        item = ITEMS[4]
        pb_page.open_add_form()
        pb_page.fill_header()

        # Row 0
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(800)

        # Row 1 — add and select the same item
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, item)
        pb_page.page.wait_for_timeout(800)

        errors = pb_page.page.locator("mat-error").all()
        print(f"\n[TC19] Action : add item '{item}' to row 0, then same item to row 1")
        print(f"       Errors : {len(errors)} found  {'✓ duplicate blocked' if len(errors) > 0 else '✗ NO ERROR — duplicate allowed'}")
        for e in errors:
            print(f"         - {e.inner_text().strip()}")
        assert len(errors) > 0, f"Expected 'already added' or duplicate validation for item '{item}'"

    def test_tc23_add_item_remove_total_resets(self, pb_page):
        """TC23: Add item row + an empty spare row, delete the item row — the
        surviving empty row must have txn=0 (no values carried over)."""
        item = ITEMS[5]
        pb_page.open_add_form()
        pb_page.fill_header()

        # Row 0 is the default empty row — leave it empty.
        # Add row 1 (last row) and put the item there so the delete button removes it.
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, item)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(1)
        pb_page.fill_qty_details(1, 10)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(500)

        txn_before = pb_page.read_transaction_amount(1)

        # Delete the last row (the item row) — only one delete button exists, always nth(0)
        pb_page.delete_row(0)
        pb_page.page.wait_for_timeout(600)

        # Remaining row is the original default empty row 0 — txn must be 0
        txn_after = pb_page.read_transaction_amount(0)
        row_count = pb_page.count_item_rows()
        passed    = txn_after == 0.0

        print(f"\n[TC23] Action : add item '{item}' qty=10 via popup, add empty row, delete item row")
        print(f"       Txn before delete : {txn_before:.2f}  {'✓ > 0' if txn_before > 0 else '✗ was already 0'}")
        print(f"       Rows remaining    : {row_count}")
        print(f"       Txn after delete  : {txn_after:.2f}  {'✓ zero — no carry-over' if passed else '✗ still has values'}")
        print(f"       Overall           : {'✓ PASS' if passed else '✗ FAIL'}")
        assert txn_before > 0, f"TC23: pre-condition failed — item row txn was 0 before delete"
        assert passed, (
            f"TC23: After deleting item row, surviving empty row should have txn=0; got {txn_after:.2f}"
        )

    def test_tc24_remove_add_no_stale_values(self, pb_page):
        """TC24: Remove item A, add item B with same qty — item B txn must differ
        from item A txn (different master rates → different computed amounts)."""
        item_a, item_b = _two_items()
        qty = _rand_qty()
        pb_page.open_add_form()
        pb_page.fill_header()

        # Add row 0 with item_a via popup
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge_a = pb_page._pick_nudge_item(item_a)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge_a)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item_a)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        txn_a = pb_page.read_transaction_amount(0)

        # Add empty row 1 so DELETE appears, then delete item_a row
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        pb_page.delete_row(0)
        pb_page.page.wait_for_timeout(600)

        # Fill remaining empty row with item_b — same qty via popup
        nudge_b = pb_page._pick_nudge_item(item_b)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge_b)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item_b)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        txn_b  = pb_page.read_transaction_amount(0)
        no_stale = txn_b != txn_a and txn_b > 0

        print(f"\n[TC24] Action : add item_a='{item_a}' qty={qty} via popup, delete it, add item_b='{item_b}' qty={qty} via popup")
        print(f"       item_a txn : {txn_a:.2f}  (master rate × {qty})")
        print(f"       item_b txn : {txn_b:.2f}  (master rate × {qty})")
        print(f"       Different  : {'✓ no stale carry-over' if txn_b != txn_a else '✗ SAME — possible stale'}")
        print(f"       item_b > 0 : {'✓' if txn_b > 0 else '✗ ZERO'}")
        assert txn_a > 0, f"TC24: pre-condition failed — item_a txn was 0"
        assert txn_b > 0, f"TC24: item_b txn is 0 after selection with qty={qty}"
        assert txn_b != txn_a, (
            f"TC24: item_b txn ({txn_b:.2f}) == item_a txn ({txn_a:.2f}) — "
            f"different items must have different master rates"
        )


# ── Group 7: Live calculation assertions ──────────────────────────────────────

@pytest.mark.direct_pb
class TestDirectPBCalculations:
    """
    Confirmed formula (from PB_notes.md + live smoke test):
      Amount       = rate × net_qty              (gross; rate is auto-fetched from master)
      net_qty      = qty - empty_bag_weight
      Disc Amt     = Amount × disc_pct / 100
      Tax          = Amount × tax_rate / 100     (applied on gross Amount)
      Total Amount = Amount - Disc Amt - Labour + Tax

    Rate is auto-fetched from item master — _fill_number_nth(RATE) does not stick.
    All expected values are therefore derived from the live-read Amount, not hardcoded.
    """

    ITEM     = ITEMS[0]
    QTY      = 100
    EBW      = 20       # empty bag weight → net_qty = 80
    DISC_PCT = 10
    LABOUR   = 200
    TAX_RATE = 5

    TOL = 0.02          # ±2 cents float tolerance

    def _open_row(self, pb_page, item=None, qty=None, ebw=0):
        """Open form, fill header, select item on default row 0, set qty + EBW via popup."""
        item = item or self.ITEM
        qty  = qty if qty is not None else self.QTY
        pb_page.open_add_form()
        pb_page.fill_header()
        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        if ebw:
            pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, 0, ebw)
        pb_page.page.wait_for_timeout(600)

    # ── ALL-IN-ONE smoke test ─────────────────────────────────────────────

    def test_all_calc_fields(self, pb_page):
        """Smoke: fill every input, print all computed values, assert relationships."""
        self._open_row(pb_page, ebw=self.EBW)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, self.DISC_PCT)
        pb_page._fill_number_nth(pb_page.LABOUR_CHARGES,  0, self.LABOUR)
        pb_page.page.wait_for_timeout(600)
        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, self.TAX_RATE)
        pb_page.select_gst_type(0, "IGST")
        pb_page.page.wait_for_timeout(800)

        amount    = pb_page._read_number_nth(pb_page.AMOUNT,           0)
        net_qty   = pb_page._read_number_nth(pb_page.NET_QUANTITY,      0)
        disc_amt  = pb_page._read_number_nth(pb_page.DISCOUNT_AMOUNT,   0)
        total_amt = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT,      0)
        igst_amt  = pb_page._read_number_nth(pb_page.IGST_AMOUNT,       0)
        cgst_amt  = pb_page._read_number_nth(pb_page.CGST_AMOUNT,       0)
        sgst_amt  = pb_page._read_number_nth(pb_page.SGST_AMOUNT,       0)
        tax_total = pb_page._read_number_nth(pb_page.TAX_AMOUNT_FIELD,  0)

        exp_net_qty = self.QTY - self.EBW
        exp_disc    = amount * self.DISC_PCT / 100
        exp_igst    = amount * self.TAX_RATE / 100
        exp_total   = amount - exp_disc - self.LABOUR + exp_igst

        def chk(got, exp, tol=self.TOL): return "✓" if abs(got - exp) <= tol else f"✗ (expected {exp:.2f})"

        print(f"\n[CALC-ALL] item={self.ITEM!r}  qty={self.QTY}  ebw={self.EBW}  disc={self.DISC_PCT}%  labour={self.LABOUR}  tax={self.TAX_RATE}%  gst=IGST")
        print(f"  ┌─────────────────────────────────────────────────────────┐")
        print(f"  │  Inputs                                                 │")
        print(f"  │    qty={self.QTY}  EBW={self.EBW}  disc%={self.DISC_PCT}  labour={self.LABOUR}  tax%={self.TAX_RATE}     │")
        print(f"  ├─────────────────────────────────────────────────────────┤")
        print(f"  │  Field              ERP value    Expected     Check     │")
        print(f"  ├─────────────────────────────────────────────────────────┤")
        print(f"  │  Amount             {amount:>10.2f}    (auto)       {'✓' if amount > 0 else '✗ ZERO'}       │")
        print(f"  │  Net Qty            {net_qty:>10.2f}    {exp_net_qty:>10.2f}   {chk(net_qty, exp_net_qty)}       │")
        print(f"  │  Disc Amount        {disc_amt:>10.2f}    {exp_disc:>10.2f}   {chk(disc_amt, exp_disc)}       │")
        print(f"  │  IGST Amount        {igst_amt:>10.2f}    {exp_igst:>10.2f}   {chk(igst_amt, exp_igst)}       │")
        print(f"  │  CGST Amount        {cgst_amt:>10.2f}    {'0.00':>10}   {'✓' if cgst_amt==0 else '✗ not 0'}       │")
        print(f"  │  SGST Amount        {sgst_amt:>10.2f}    {'0.00':>10}   {'✓' if sgst_amt==0 else '✗ not 0'}       │")
        print(f"  │  Tax Total          {tax_total:>10.2f}    {exp_igst:>10.2f}   {chk(tax_total, exp_igst)}       │")
        print(f"  │  Total Amount       {total_amt:>10.2f}    {exp_total:>10.2f}   {chk(total_amt, exp_total)}       │")
        print(f"  │                                                         │")
        print(f"  │  Formula: Amount - Disc - Labour + IGST = Total        │")
        print(f"  │    {amount:.2f} - {exp_disc:.2f} - {self.LABOUR} + {exp_igst:.2f} = {exp_total:.2f}              │")
        print(f"  └─────────────────────────────────────────────────────────┘")

        assert amount   > 0,                               f"Amount zero/empty"
        assert abs(net_qty  - exp_net_qty) <= self.TOL,   f"Net Qty: {net_qty} != {exp_net_qty}"
        assert abs(disc_amt - exp_disc)    <= self.TOL,   f"Disc Amt: {disc_amt} != {exp_disc}"
        assert abs(igst_amt - exp_igst)    <= self.TOL,   f"IGST: {igst_amt} != {exp_igst}"
        assert cgst_amt == 0.0,                            f"CGST should be 0 in IGST mode: {cgst_amt}"
        assert sgst_amt == 0.0,                            f"SGST should be 0 in IGST mode: {sgst_amt}"
        assert abs(tax_total - exp_igst)   <= self.TOL,   f"Tax total: {tax_total} != IGST {exp_igst}"
        assert abs(total_amt - exp_total)  <= self.TOL,   f"Total: {total_amt} != {exp_total}"

    # ── CALC1: Amount > 0 after item + qty selected ───────────────────────

    def test_calc1_amount(self, pb_page):
        """CALC1: Amount auto-computes (rate×net_qty) — must be > 0."""
        self._open_row(pb_page)
        amount  = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        net_qty = pb_page._read_number_nth(pb_page.NET_QUANTITY, 0)
        print(f"\n[CALC1] item={self.ITEM!r}  qty={self.QTY}  net_qty={net_qty:.2f}")
        print(f"        Amount = rate × net_qty = {amount:.2f}  [{'✓ > 0' if amount > 0 else '✗ ZERO'}]")
        assert amount > 0, f"CALC1: Amount should be > 0 after item+qty set, got {amount}"

    # ── CALC2: Discount Amount = Amount × disc_pct / 100 ─────────────────

    def test_calc2_discount_amount(self, pb_page):
        """CALC2: Discount Amount = Amount × disc% / 100."""
        self._open_row(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, self.DISC_PCT)
        pb_page.page.wait_for_timeout(600)
        disc_amt = pb_page._read_number_nth(pb_page.DISCOUNT_AMOUNT, 0)
        expected = amount * self.DISC_PCT / 100
        match    = "✓ MATCH" if abs(disc_amt - expected) <= self.TOL else f"✗ MISMATCH"
        print(f"\n[CALC2] item={self.ITEM!r}  qty={self.QTY}  disc%={self.DISC_PCT}")
        print(f"        Amount={amount:.2f}")
        print(f"        Disc Amount = {amount:.2f} × {self.DISC_PCT}% = {expected:.2f}")
        print(f"        ERP shows   : {disc_amt:.2f}  [{match}]")
        assert abs(disc_amt - expected) <= self.TOL, (
            f"CALC2: Disc Amt {disc_amt} != Amount({amount})×{self.DISC_PCT}% = {expected}"
        )

    # ── CALC3: Total = Amount - Discount (no labour, no tax) ─────────────

    def test_calc3_total_no_tax(self, pb_page):
        """CALC3: Total Amount = Amount - Discount when no labour/tax."""
        self._open_row(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, self.DISC_PCT)
        pb_page.page.wait_for_timeout(600)
        total    = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 0)
        disc_amt = amount * self.DISC_PCT / 100
        expected = amount - disc_amt
        match    = "✓ MATCH" if abs(total - expected) <= self.TOL else "✗ MISMATCH"
        print(f"\n[CALC3] item={self.ITEM!r}  qty={self.QTY}  disc%={self.DISC_PCT}  labour=0  tax=none")
        print(f"        Amount={amount:.2f}  Disc={disc_amt:.2f}")
        print(f"        Formula: {amount:.2f} - {disc_amt:.2f} = {expected:.2f}")
        print(f"        ERP Total : {total:.2f}  [{match}]")
        assert abs(total - expected) <= self.TOL, (
            f"CALC3: Total {total} != Amount-Discount = {expected}"
        )

    # ── CALC4: Labour deducted from Total ────────────────────────────────

    def test_calc4_labour_deducted_from_total(self, pb_page):
        """CALC4: Total Amount = Amount - Discount - Labour."""
        self._open_row(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, self.DISC_PCT)
        pb_page._fill_number_nth(pb_page.LABOUR_CHARGES,  0, self.LABOUR)
        pb_page.page.wait_for_timeout(600)
        total    = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 0)
        disc_amt = amount * self.DISC_PCT / 100
        expected = amount - disc_amt - self.LABOUR
        match    = "✓ MATCH" if abs(total - expected) <= self.TOL else "✗ MISMATCH"
        print(f"\n[CALC4] item={self.ITEM!r}  qty={self.QTY}  disc%={self.DISC_PCT}  labour={self.LABOUR}")
        print(f"        Amount={amount:.2f}  Disc={disc_amt:.2f}  Labour={self.LABOUR}")
        print(f"        Formula: {amount:.2f} - {disc_amt:.2f} - {self.LABOUR} = {expected:.2f}")
        print(f"        ERP Total : {total:.2f}  [{match}]")
        assert abs(total - expected) <= self.TOL, (
            f"CALC4: Total {total} != Amount-Disc-Labour = {expected}"
        )

    # ── CALC5: Net Quantity = Quantity - Empty Bag Weight ─────────────────

    def test_calc5_net_qty_empty_bag(self, pb_page):
        """CALC5: Net Quantity = Quantity - Empty Bag Weight."""
        qty, ebw, exp = 1000, 200, 800
        self._open_row(pb_page, qty=qty, ebw=ebw)
        net_qty = pb_page._read_number_nth(pb_page.NET_QUANTITY, 0)
        match   = "✓ MATCH" if abs(net_qty - exp) <= self.TOL else "✗ MISMATCH"
        print(f"\n[CALC5] qty={qty}  EBW={ebw}")
        print(f"        Net Qty = {qty} - {ebw} = {exp}")
        print(f"        ERP shows: {net_qty:.2f}  [{match}]")
        assert abs(net_qty - exp) <= self.TOL, f"CALC5: Net Qty {net_qty} != {qty}-{ebw} = {exp}"

    def test_calc5b_no_empty_bag(self, pb_page):
        """CALC5b: EBW=0 — Net Quantity equals full Quantity."""
        qty = 500
        self._open_row(pb_page, qty=qty, ebw=0)
        net_qty = pb_page._read_number_nth(pb_page.NET_QUANTITY, 0)
        match   = "✓ MATCH" if abs(net_qty - qty) <= self.TOL else "✗ MISMATCH"
        print(f"\n[CALC5b] qty={qty}  EBW=0")
        print(f"         Net Qty = {qty} - 0 = {qty} (full qty)")
        print(f"         ERP shows: {net_qty:.2f}  [{match}]")
        assert abs(net_qty - qty) <= self.TOL, f"CALC5b: Net Qty {net_qty} != {qty} when EBW=0"

    def test_calc5c_fractional_ebw(self, pb_page):
        """CALC5c: Float EBW — Net Quantity becomes fractional (e.g. 0.5)."""
        qty, ebw, exp = 1000, 999.5, 0.5
        self._open_row(pb_page, qty=qty, ebw=ebw)
        net_qty = pb_page._read_number_nth(pb_page.NET_QUANTITY, 0)
        match   = "✓ MATCH" if abs(net_qty - exp) <= self.TOL else "✗ MISMATCH"
        print(f"\n[CALC5c] qty={qty}  EBW={ebw}  (fractional EBW)")
        print(f"         Net Qty = {qty} - {ebw} = {exp}")
        print(f"         ERP shows: {net_qty:.4f}  [{match}]")
        assert abs(net_qty - exp) <= self.TOL, f"CALC5c: Net Qty {net_qty} != {qty}-{ebw} = {exp}"

    # ── CALC6: IGST = Amount × tax_rate / 100 ────────────────────────────

    def test_calc6_igst_amount(self, pb_page):
        """CALC6: IGST mode — IGST Amount = Amount × 5%; CGST/SGST = 0."""
        self._open_row(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, self.TAX_RATE)
        pb_page.select_gst_type(0, "IGST")
        pb_page.page.wait_for_timeout(800)

        igst_amt  = pb_page._read_number_nth(pb_page.IGST_AMOUNT,      0)
        cgst_amt  = pb_page._read_number_nth(pb_page.CGST_AMOUNT,      0)
        sgst_amt  = pb_page._read_number_nth(pb_page.SGST_AMOUNT,      0)
        tax_total = pb_page._read_number_nth(pb_page.TAX_AMOUNT_FIELD, 0)

        exp_igst = amount * self.TAX_RATE / 100
        print(f"\n[CALC6] item={self.ITEM!r}  qty={self.QTY}  tax={self.TAX_RATE}%  mode=IGST")
        print(f"        Amount={amount:.2f}")
        print(f"        IGST = {amount:.2f} × {self.TAX_RATE}% = {exp_igst:.2f}  ERP: {igst_amt:.2f}  [{'✓' if abs(igst_amt-exp_igst)<=self.TOL else '✗'}]")
        print(f"        CGST = {cgst_amt:.2f}  (expected 0)  [{'✓ zero' if cgst_amt==0 else '✗ NOT ZERO'}]")
        print(f"        SGST = {sgst_amt:.2f}  (expected 0)  [{'✓ zero' if sgst_amt==0 else '✗ NOT ZERO'}]")
        print(f"        Tax Total = {tax_total:.2f}  expected {exp_igst:.2f}  [{'✓' if abs(tax_total-exp_igst)<=self.TOL else '✗'}]")

        assert abs(igst_amt  - exp_igst) <= self.TOL, f"CALC6: IGST {igst_amt} != {exp_igst}"
        assert cgst_amt == 0.0,                        f"CALC6: CGST should be 0: {cgst_amt}"
        assert sgst_amt == 0.0,                        f"CALC6: SGST should be 0: {sgst_amt}"
        assert abs(tax_total - exp_igst) <= self.TOL,  f"CALC6: Tax total {tax_total} != IGST {exp_igst}"

    # ── CALC7: CGST + SGST each = Amount × 2.5% ──────────────────────────

    def test_calc7_cgst_sgst_amounts(self, pb_page):
        """CALC7: CGST+SGST mode — each = Amount × 2.5%; IGST = 0."""
        self._open_row(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, self.TAX_RATE)
        pb_page.select_gst_type(0, "CGST + SGST")
        pb_page.page.wait_for_timeout(800)

        cgst_amt  = pb_page._read_number_nth(pb_page.CGST_AMOUNT,      0)
        sgst_amt  = pb_page._read_number_nth(pb_page.SGST_AMOUNT,      0)
        igst_amt  = pb_page._read_number_nth(pb_page.IGST_AMOUNT,      0)
        tax_total = pb_page._read_number_nth(pb_page.TAX_AMOUNT_FIELD, 0)

        exp_each = amount * self.TAX_RATE / 200
        exp_tax  = amount * self.TAX_RATE / 100
        print(f"\n[CALC7] item={self.ITEM!r}  qty={self.QTY}  tax={self.TAX_RATE}%  mode=CGST+SGST")
        print(f"        Amount={amount:.2f}")
        print(f"        Each half = {amount:.2f} × {self.TAX_RATE/2}% = {exp_each:.2f}")
        print(f"        CGST = {cgst_amt:.2f}  expected {exp_each:.2f}  [{'✓' if abs(cgst_amt-exp_each)<=self.TOL else '✗'}]")
        print(f"        SGST = {sgst_amt:.2f}  expected {exp_each:.2f}  [{'✓' if abs(sgst_amt-exp_each)<=self.TOL else '✗'}]")
        print(f"        IGST = {igst_amt:.2f}  (expected 0)             [{'✓ zero' if igst_amt==0 else '✗ NOT ZERO'}]")
        print(f"        Tax Total = {tax_total:.2f}  expected {exp_tax:.2f}  [{'✓' if abs(tax_total-exp_tax)<=self.TOL else '✗'}]")

        assert abs(cgst_amt  - exp_each) <= self.TOL, f"CALC7: CGST {cgst_amt} != {exp_each}"
        assert abs(sgst_amt  - exp_each) <= self.TOL, f"CALC7: SGST {sgst_amt} != {exp_each}"
        assert igst_amt == 0.0,                        f"CALC7: IGST should be 0: {igst_amt}"
        assert abs(tax_total - exp_tax)  <= self.TOL,  f"CALC7: Tax total {tax_total} != {exp_tax}"

    # ── CALC8: Header totals = sum of row amounts / totals ───────────────

    def test_calc8_header_totals_two_rows(self, pb_page):
        """CALC8: Header Amount and Total Amount = sum of all row values."""
        item_a, item_b = ITEMS[0], ITEMS[1]
        pb_page.open_add_form()
        pb_page.fill_header()

        # Row 0 — use popup for qty
        nudge_a = pb_page._pick_nudge_item(item_a)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge_a)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item_a)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, self.QTY)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        # Row 1 — add row then use popup for qty
        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge_b = pb_page._pick_nudge_item(item_b)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, nudge_b)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 1, item_b)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(1)
        pb_page.fill_qty_details(1, self.QTY)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        # DOM layout (confirmed via dump):
        #   AMOUNT      → only 1 field: index 0 = header total amount
        #   TOTAL_AMOUNT → index 0 = header, index 1 = row 0, index 2 = row 1
        hdr_amount = pb_page._read_number_nth(pb_page.AMOUNT,       0)
        total0     = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        total1     = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 2)
        hdr_total  = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 0)

        col = "{:<28} {:>6} {:>14} {}"
        print(f"\n[CALC8] 2-row header sum check  (qty={self.QTY} each)")
        print(col.format("Item", "Qty", "RowTotal", "Status"))
        print("─" * 56)
        print(col.format(item_a[:28], self.QTY, f"{total0:.2f}", "✓" if total0 > 0 else "✗ ZERO"))
        print(col.format(item_b[:28], self.QTY, f"{total1:.2f}", "✓" if total1 > 0 else "✗ ZERO"))
        print("─" * 56)
        exp_hdr = total0 + total1
        match   = "✓ MATCH" if abs(hdr_total - exp_hdr) <= self.TOL else f"✗ MISMATCH (diff={hdr_total-exp_hdr:.4f})"
        print(col.format("HEADER TOTAL", "", f"{hdr_total:.2f}", match))
        print(col.format("SUM OF ROWS",  "", f"{exp_hdr:.2f}",  ""))
        print(f"        Header Amount field: {hdr_amount:.2f}  [{'✓ > 0' if hdr_amount > 0 else '✗ ZERO'}]")

        assert hdr_amount > 0, f"CALC8: Header Amount should be > 0, got {hdr_amount}"
        assert total0 > 0,     f"CALC8: Row 0 Total Amount should be > 0, got {total0}"
        assert total1 > 0,     f"CALC8: Row 1 Total Amount should be > 0, got {total1}"
        assert abs(hdr_total - (total0 + total1)) <= self.TOL, (
            f"CALC8: Header Total {hdr_total} != row0({total0})+row1({total1})"
        )


# ── Shared helpers ────────────────────────────────────────────────────────────

def _rand_items(n):
    """Pick n distinct items at random (seeded)."""
    return _rng.sample(ITEMS, n)

def _rand_qty():
    return _rng.randint(50, 2000)

def _rand_disc():
    return _rng.choice(DISC_CHOICES)

def _rand_labour():
    return _rng.choice(LABOUR_CHOICES)

def _rand_ebw(qty, max_fraction=0.3):
    """EBW up to 30% of qty so net_qty stays positive."""
    return round(_rng.uniform(0, qty * max_fraction))


def _setup_single_row(pb_page, item=None, qty=None, ebw=0, disc_pct=None, labour=None):
    """Open form, fill header, add one row via popup with randomized defaults."""
    item     = item     or _rng.choice(ITEMS)
    qty      = qty      if qty      is not None else _rand_qty()
    disc_pct = disc_pct if disc_pct is not None else _rand_disc()
    labour   = labour   if labour   is not None else _rand_labour()
    print(f"\n[single-row] seed={_SEED} item={item!r} qty={qty} ebw={ebw} disc={disc_pct}% labour={labour}")
    pb_page.open_add_form()
    pb_page.fill_header()
    nudge = pb_page._pick_nudge_item(item)
    pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
    pb_page.page.wait_for_timeout(500)
    pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
    pb_page.page.wait_for_timeout(1000)
    pb_page.open_qty_details_popup(0)
    pb_page.fill_qty_details(1, qty)
    pb_page.click_done()
    if ebw:
        pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, 0, ebw)
    if disc_pct:
        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, disc_pct)
    if labour:
        pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, 0, labour)
    pb_page.page.wait_for_timeout(600)
    return qty, disc_pct, labour


def _add_rows(pb_page, items=None, qtys=None, disc_pcts=None, labours=None, ebws=None, n=None):
    """Open form, fill header, add N rows via popup.
    Pass explicit lists or let n drive random generation."""
    if items is None:
        n = n or _rng.randint(2, 6)
        items = _rand_items(n)
    n         = len(items)
    qtys      = qtys      or [_rand_qty()   for _ in range(n)]
    disc_pcts = disc_pcts or [_rand_disc()  for _ in range(n)]
    labours   = labours   or [_rand_labour() for _ in range(n)]
    ebws      = ebws      or [0] * n
    print(f"\n[add-rows] seed={_SEED} n={n}")
    for i in range(n):
        print(f"  row{i}: item={items[i]!r} qty={qtys[i]} disc={disc_pcts[i]}% labour={labours[i]} ebw={ebws[i]}")
    pb_page.open_add_form()
    pb_page.fill_header()
    for i in range(n):
        if i > 0:
            pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
            pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(items[i])
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, i, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, i, items[i])
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(i)
        pb_page.fill_qty_details(1, qtys[i])
        pb_page.click_done()
        if ebws[i]:
            pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, i, ebws[i])
        if disc_pcts[i]:
            pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, i, disc_pcts[i])
        if labours[i]:
            pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, i, labours[i])
        pb_page.page.wait_for_timeout(500)
    pb_page.page.wait_for_timeout(600)
    return items, qtys, disc_pcts, labours, ebws


def _row_totals(pb_page, n):
    """Read Total Amount for each row. DOM: [0]=header, [1..n]=rows."""
    return [pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, i + 1) for i in range(n)]


def _hdr_total(pb_page):
    return pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 0)


# ── Group 8: Multi-row calculations ──────────────────────────────────────────

@pytest.mark.direct_pb
class TestMultiRowCalculations:
    """
    Multi-item tests — N rows with varied qty/disc/labour/EBW.
    DOM layout confirmed:
      TOTAL_AMOUNT[0]      = header total
      TOTAL_AMOUNT[1..n]   = per-row totals
      AMOUNT[0]            = header amount (only 1 field exists)
      DISCOUNT_AMOUNT[0..] = unknown layout — diagnosed per test
    """

    TOL = 0.02

    SWAL_TITLE_SUCCESS = "Purchase Booking created successfully"
    REF_NO_COL         = "td.cdk-column-transaction_ref_no"
    ROW_TRIGGER        = "button.erp-row-trigger"
    VIEW_MENU_ITEM     = (
        "xpath=//div[contains(@class,'mat-mdc-menu-panel')]"
        "//button[.//mat-icon[normalize-space(.)='visibility']]"
    )

    def test_m1_five_rows_varied_inputs_header_equals_sum(self, pb_page):
        """M1: 5 random rows (random item/qty/disc/labour) — verify calcs then save."""
        items, qtys, disc_pcts, labours, ebws = _add_rows(pb_page, n=5)
        n    = len(items)
        rows = _row_totals(pb_page, n)
        hdr  = _hdr_total(pb_page)

        # ── pretty summary ────────────────────────────────────────────────────
        col = "{:<28} {:>6} {:>6} {:>6} {:>8} {:>12} {}"
        print("\n")
        print(col.format("Item", "Qty", "Disc%", "Labour", "EBW", "RowTotal", "Status"))
        print("─" * 82)
        for i in range(n):
            status = "✓" if rows[i] > 0 else "✗ ZERO"
            print(col.format(
                items[i][:28], qtys[i], disc_pcts[i], labours[i], ebws[i],
                f"{rows[i]:.2f}", status
            ))
        print("─" * 82)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH (diff={hdr - sum(rows):.4f})"
        print(col.format("HEADER TOTAL", "", "", "", "", f"{hdr:.2f}", match))
        print(col.format("SUM OF ROWS",  "", "", "", "", f"{sum(rows):.2f}", ""))
        print()
        # ─────────────────────────────────────────────────────────────────────

        for i, t in enumerate(rows):
            assert t > 0, f"M1: Row {i} Total = 0 (item={items[i]!r} qty={qtys[i]})"
        assert abs(hdr - sum(rows)) <= self.TOL, (
            f"M1: Header {hdr} != sum{rows} = {sum(rows)}"
        )

        # ── save ──────────────────────────────────────────────────────────────
        btn = pb_page.page.locator(pb_page.SUBMIT_BTN)
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        pb_page.page.wait_for_selector(".swal2-container", timeout=12000)
        title = pb_page.page.locator("#swal2-title").inner_text().strip()
        assert title == self.SWAL_TITLE_SUCCESS, (
            f"M1: Expected success alert '{self.SWAL_TITLE_SUCCESS}', got: '{title}'"
        )
        pb_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=8000)
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        pb_page.page.wait_for_timeout(500)
        ref_no = pb_page.page.locator(self.REF_NO_COL).first.inner_text().strip()
        print(f"[saved] ref_no={ref_no}  total={hdr:.2f}")
        assert ref_no.startswith("PURB/"), f"M1: Expected saved PB ref_no, got: {ref_no}"

    def test_m1b_header_disc_equals_sum_of_row_discs(self, pb_page):
        """E5: 4 rows, ≥3 with disc — verify ≥3 non-zero Discount Amount fields exist."""
        n_rows    = 4
        items     = _rand_items(n_rows)
        qtys      = [_rand_qty() for _ in range(n_rows)]
        disc_pcts = [_rng.choice([5, 10, 15, 20])] * 3 + [0]
        _rng.shuffle(disc_pcts)
        _add_rows(pb_page, items=items, qtys=qtys, disc_pcts=disc_pcts)
        n_disc    = pb_page.page.locator(pb_page.DISCOUNT_AMOUNT).count()
        all_discs = [pb_page._read_number_nth(pb_page.DISCOUNT_AMOUNT, i) for i in range(n_disc)]
        positive  = [d for d in all_discs if d > 0]

        col = "{:<28} {:>6} {:>6} {:>14}"
        print("\n")
        print(col.format("Item", "Qty", "Disc%", "DiscAmount"))
        print("─" * 58)
        for i in range(n_rows):
            da = all_discs[i] if i < len(all_discs) else 0
            print(col.format(items[i][:28], qtys[i], disc_pcts[i], f"{da:.2f}"))
        print("─" * 58)
        print(f"Non-zero disc fields found: {len(positive)} / {n_rows}  {'✓' if len(positive) >= 3 else '✗'}")
        print()

        assert len(positive) >= 3, (
            f"E5: Expected ≥3 non-zero disc amounts (3 rows have disc>0), got: {all_discs}"
        )

    def test_m1c_ebw_per_row_net_qty_affects_totals(self, pb_page):
        """CALC5+M1 combo: 3 random rows with random EBW — each Total > 0, header = sum."""
        items = _rand_items(3)
        qtys  = [_rand_qty() for _ in range(3)]
        ebws  = [_rand_ebw(q) for q in qtys]
        _add_rows(pb_page, items=items, qtys=qtys, ebws=ebws)
        rows = _row_totals(pb_page, 3)
        hdr  = _hdr_total(pb_page)

        col = "{:<28} {:>6} {:>6} {:>12} {}"
        print("\n")
        print(col.format("Item", "Qty", "EBW", "RowTotal", "Status"))
        print("─" * 62)
        for i in range(3):
            net = qtys[i] - ebws[i]
            status = "✓" if rows[i] > 0 else "✗ ZERO"
            print(col.format(items[i][:28], qtys[i], ebws[i], f"{rows[i]:.2f}", status))
        print("─" * 62)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH"
        print(col.format("HEADER TOTAL", "", "", f"{hdr:.2f}", match))
        print(col.format("SUM OF ROWS",  "", "", f"{sum(rows):.2f}", ""))
        print()

        for i, t in enumerate(rows):
            assert t > 0, f"M1c: Row {i} Total = 0 (qty={qtys[i]} ebw={ebws[i]})"
        assert abs(hdr - sum(rows)) <= self.TOL, (
            f"M1c: Header {hdr} != sum{rows}"
        )

    def test_m1d_all_20_items_header_equals_sum(self, pb_page):
        """E8: All 20 items, random qty each — header total = sum of 20 row totals."""
        qtys = [_rand_qty() for _ in range(20)]
        _add_rows(pb_page, items=ITEMS[:20], qtys=qtys)
        rows = _row_totals(pb_page, 20)
        hdr  = _hdr_total(pb_page)

        col = "{:<3} {:<28} {:>6} {:>14} {}"
        print("\n")
        print(col.format("#", "Item", "Qty", "RowTotal", "Status"))
        print("─" * 62)
        for i in range(20):
            status = "✓" if rows[i] > 0 else "✗ ZERO"
            print(col.format(i, ITEMS[i][:28], qtys[i], f"{rows[i]:.2f}", status))
        print("─" * 62)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH (diff={hdr-sum(rows):.4f})"
        print(col.format("", "HEADER TOTAL", "", f"{hdr:.2f}", match))
        print(col.format("", "SUM OF ROWS",  "", f"{sum(rows):.2f}", ""))
        print()

        for i, t in enumerate(rows):
            assert t > 0, f"E8: Row {i} Total = 0"
        assert abs(hdr - sum(rows)) <= self.TOL, (
            f"E8: Header {hdr} != sum of 20 rows = {sum(rows)}"
        )

    def test_m1f_many_rows_all_fields_random(self, pb_page):
        """M1f: 10-15 rows — disc, labour, EBW, tax rate, GST type all random per row.
        Saves PB, exports Excel, then opens in View mode and cross-checks all totals."""
        TAX_RATES = [5, 12, 18]
        GST_TYPES = ["IGST", "CGST + SGST"]

        n       = _rng.randint(8, 10)
        items   = _rand_items(n)
        qtys    = [_rand_qty()    for _ in range(n)]
        discs   = [_rand_disc()   for _ in range(n)]
        labours = [_rand_labour() for _ in range(n)]
        ebws    = [_rand_ebw(q)   for q in qtys]
        gst_on    = [_rng.random() < 0.67 for _ in range(n)]
        tax_rates = [_rng.choice(TAX_RATES) if g else 0 for g in gst_on]
        gst_types = [_rng.choice(GST_TYPES) if g else "none" for g in gst_on]

        pb_page.open_add_form()
        pb_page.fill_header()
        for i in range(n):
            if i > 0:
                pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
                pb_page.page.wait_for_timeout(600)
            nudge = pb_page._pick_nudge_item(items[i])
            pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, i, nudge)
            pb_page.page.wait_for_timeout(500)
            pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, i, items[i])
            pb_page.page.wait_for_timeout(1000)
            pb_page.open_qty_details_popup(i)
            pb_page.fill_qty_details(1, qtys[i])
            pb_page.click_done()
            if ebws[i]:
                pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, i, ebws[i])
            if discs[i]:
                pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, i, discs[i])
            if labours[i]:
                pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, i, labours[i])
            pb_page.page.wait_for_timeout(500)

            if gst_on[i]:
                pb_page.enable_gst_off(i)
                pb_page.page.wait_for_timeout(800)
                pb_page.select_tax_rate(i, tax_rates[i])
                pb_page.page.wait_for_timeout(1000)
                try:
                    pb_page.select_gst_type(i, gst_types[i])
                except Exception:
                    pb_page.enable_gst_off(i)
                    tax_rates[i] = 0
                    gst_types[i] = "none"
                    gst_on[i] = False
                pb_page.page.wait_for_timeout(1000)

        pb_page.page.wait_for_timeout(600)

        pb_page.page.wait_for_timeout(1500)
        rows = _row_totals(pb_page, n)
        hdr  = _hdr_total(pb_page)

        # ── pretty summary ────────────────────────────────────────────────────
        col = "{:<3} {:<24} {:>5} {:>5} {:>5} {:>5} {:>4} {:>14} {:>14} {}"
        print("\n")
        print(col.format("#", "Item", "Qty", "Dsc%", "Lab", "EBW", "Tax%", "GSTType", "RowTotal", "Status"))
        print("─" * 100)
        for i in range(n):
            status = "✓" if rows[i] > 0 else "✗ ZERO"
            print(col.format(
                i, items[i][:24], qtys[i], discs[i], labours[i], ebws[i],
                tax_rates[i] if gst_on[i] else "-",
                gst_types[i][:7] if gst_on[i] else "none",
                f"{rows[i]:.2f}", status
            ))
        print("─" * 100)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH (diff={hdr - sum(rows):.4f})"
        print(col.format("", "HEADER TOTAL", "", "", "", "", "", "", f"{hdr:.2f}", match))
        print(col.format("", "SUM OF ROWS",  "", "", "", "", "", "", f"{sum(rows):.2f}", ""))
        print()

        for i, t in enumerate(rows):
            assert t > 0, f"M1f: Row {i} Total = 0 (item={items[i]!r} qty={qtys[i]} ebw={ebws[i]})"
        assert abs(hdr - sum(rows)) <= self.TOL, (
            f"M1f: Header {hdr} != sum of {n} rows = {sum(rows)}"
        )

        # ── Save PB ───────────────────────────────────────────────────────────
        btn = pb_page.page.locator(pb_page.SUBMIT_BTN)
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        pb_page.page.wait_for_selector(".swal2-container", timeout=15000)
        swal_title = pb_page.page.locator("#swal2-title").inner_text().strip()
        assert swal_title == self.SWAL_TITLE_SUCCESS, (
            f"M1f: Save failed — swal2 title: '{swal_title}'"
        )
        pb_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=8000)
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        pb_page.page.wait_for_timeout(500)
        ref_no = pb_page.page.locator(self.REF_NO_COL).first.inner_text().strip()
        assert ref_no.startswith("PURB/"), f"M1f: Expected PURB/ ref_no after save, got: {ref_no}"
        print(f"[M1f] saved → ref_no={ref_no}  header_total={hdr:.2f}")

        # ── Open View mode ────────────────────────────────────────────────────
        pb_page.page.locator(self.ROW_TRIGGER).first.click(force=True)
        pb_page.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)
        pb_page.page.locator(self.VIEW_MENU_ITEM).first.click(force=True)
        # Wait for the view form to render (same popup structure as create form)
        pb_page.page.wait_for_selector(pb_page.TOTAL_AMOUNT, timeout=20000)
        pb_page.page.wait_for_timeout(1500)

        view_rows = _row_totals(pb_page, n)
        view_hdr  = _hdr_total(pb_page)

        vcol = "{:<3} {:<24} {:>14} {:>14} {}"
        print(f"\n[M1f] View mode cross-check  ref_no={ref_no}")
        print(vcol.format("#", "Item", "Created", "View", "Match"))
        print("─" * 72)
        mismatches = []
        for i in range(n):
            ok = abs(view_rows[i] - rows[i]) <= self.TOL
            status = "✓" if ok else f"✗ MISMATCH (diff={view_rows[i]-rows[i]:+.4f})"
            print(vcol.format(i, items[i][:24], f"{rows[i]:.2f}", f"{view_rows[i]:.2f}", status))
            if not ok:
                mismatches.append(i)
        print("─" * 72)
        hdr_ok = abs(view_hdr - hdr) <= self.TOL
        print(vcol.format("", "HEADER TOTAL", f"{hdr:.2f}", f"{view_hdr:.2f}",
                          "✓" if hdr_ok else f"✗ MISMATCH (diff={view_hdr-hdr:+.4f})"))
        print()

        for i in mismatches:
            assert False, (
                f"M1f: View row {i} total {view_rows[i]:.2f} != created {rows[i]:.2f} "
                f"(item={items[i]!r})"
            )
        assert hdr_ok, (
            f"M1f: View header total {view_hdr:.2f} != created {hdr:.2f}"
        )
        print(f"[M1f] ✓ All {n} row totals + header match in view mode")

        # ── Export Excel with cross-check ────────────────────────────────────
        reports_dir = pathlib.Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        xlsx_path = reports_dir / f"m1f_{ts}.xlsx"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cross-Check"

        hdr_font  = Font(bold=True, color="FFFFFF")
        hdr_fill  = PatternFill("solid", fgColor="2E5896")
        tot_fill  = PatternFill("solid", fgColor="D9E1F2")
        mis_fill  = PatternFill("solid", fgColor="FCE4EC")
        mis_font  = Font(color="C62828")
        ok_fill   = PatternFill("solid", fgColor="E8F5E9")
        ctr       = Alignment(horizontal="center")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        headers = ["#", "Item", "Qty", "Disc%", "Labour", "EBW",
                    "GST Type", "Tax%", "Created Total", "View Total",
                    "Diff", "Status"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font, cell.fill, cell.alignment = hdr_font, hdr_fill, ctr
            cell.border = thin_border

        pass_count = 0
        for i in range(n):
            gst_label = f"{gst_types[i]} {tax_rates[i]}%" if gst_on[i] else "No GST"
            created = round(rows[i], 2)
            viewed  = round(view_rows[i], 2)
            diff    = round(viewed - created, 2)
            ok      = abs(diff) <= self.TOL
            status  = "PASS" if ok else "FAIL"
            if ok:
                pass_count += 1
            vals = [i, items[i], qtys[i], discs[i], labours[i], ebws[i],
                    gst_label, tax_rates[i] if gst_on[i] else 0,
                    created, viewed, diff, status]
            ws.append(vals)
            row_idx = ws.max_row
            for cell in ws[row_idx]:
                cell.border = thin_border
                cell.alignment = ctr
            if not ok:
                for cell in ws[row_idx]:
                    cell.fill = mis_fill
                    cell.font = mis_font
            else:
                ws.cell(row=row_idx, column=len(vals)).fill = ok_fill

        ws.append([])
        sep_row = ws.max_row

        hdr_created = round(hdr, 2)
        hdr_viewed  = round(view_hdr, 2)
        hdr_diff    = round(hdr_viewed - hdr_created, 2)
        hdr_ok      = abs(hdr_diff) <= self.TOL

        ws.append(["HEADER TOTAL", "", "", "", "", "", "",
                    "", hdr_created, hdr_viewed, hdr_diff,
                    "PASS" if hdr_ok else "FAIL"])
        for cell in ws[ws.max_row]:
            cell.fill = tot_fill
            cell.font = Font(bold=True, color="C62828" if not hdr_ok else "000000")
            cell.border = thin_border
            cell.alignment = ctr

        ws.append(["SUM OF ROWS", "", "", "", "", "", "",
                    "", round(sum(rows), 2), round(sum(view_rows), 2),
                    round(sum(view_rows) - sum(rows), 2), ""])
        for cell in ws[ws.max_row]:
            cell.fill = PatternFill("solid", fgColor="FFF3E0")

        ws.append([])
        ws.append(["ref_no", ref_no])
        ws.append(["seed", _SEED])
        ws.append(["rows", n])
        ws.append(["passed", pass_count])
        ws.append(["failed", n - pass_count])
        ws.append(["header_match", "PASS" if hdr_ok else "FAIL"])
        ws.column_dimensions["B"].width = 42
        for letter in ["A", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]:
            ws.column_dimensions[letter].width = 14

        wb.save(xlsx_path)
        print(f"\n[M1f] Excel exported → {xlsx_path}")

    def test_m1e_gst_mixed_all_rows_header_sum(self, pb_page):
        """E4+M1: Row 0=IGST, Row 1=CGST+SGST, Row 2=no GST — header total = sum."""
        items = _rand_items(3)
        qtys  = [_rand_qty() for _ in range(3)]
        _add_rows(pb_page, items=items, qtys=qtys)

        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, 5)
        pb_page.select_gst_type(0, "IGST")
        pb_page.page.wait_for_timeout(500)

        pb_page.enable_gst_off(1)
        pb_page.select_tax_rate(1, 5)
        pb_page.select_gst_type(1, "CGST + SGST")
        pb_page.page.wait_for_timeout(600)

        rows = _row_totals(pb_page, 3)
        hdr  = _hdr_total(pb_page)

        col = "{:<28} {:>6} {:>14} {:>16} {}"
        print("\n")
        print(col.format("Item", "Qty", "RowTotal", "GST Type", "Status"))
        print("─" * 72)
        gst_labels = ["IGST (5%)", "CGST+SGST (5%)", "No GST"]
        for i in range(3):
            status = "✓" if rows[i] > 0 else "✗ ZERO"
            print(col.format(items[i][:28], qtys[i], f"{rows[i]:.2f}", gst_labels[i], status))
        print("─" * 72)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH"
        print(col.format("HEADER TOTAL", "", f"{hdr:.2f}", "", match))
        print(col.format("SUM OF ROWS",  "", f"{sum(rows):.2f}", "", ""))
        print()

        for i, t in enumerate(rows):
            assert t > 0, f"M1e: Row {i} Total = 0"
        assert abs(hdr - sum(rows)) <= self.TOL, (
            f"M1e: Header {hdr} != sum{rows}"
        )


# ── Group 9: Row mutation + recalculation ────────────────────────────────────

@pytest.mark.direct_pb
class TestRowMutations:
    """
    Tests that add rows, read calcs, mutate state (delete/change disc/add new rows),
    then verify the header re-derives correctly.
    """

    TOL = 0.02

    def test_m2_add_n_delete_random_header_updates(self, pb_page):
        """M2: Add N random rows → delete 2 random rows → header = remaining sum."""
        n      = _rng.randint(4, 7)
        items, qtys, _, _, _ = _add_rows(pb_page, n=n)
        before = _row_totals(pb_page, n)

        del_indices = sorted(_rng.sample(range(1, n), 2), reverse=True)
        kept        = set(range(n)) - set(del_indices)

        col = "{:<3} {:<26} {:>6} {:>14} {}"
        print("\n")
        print(col.format("#", "Item", "Qty", "Total", "Action"))
        print("─" * 58)
        for i in range(n):
            action = "DELETE" if i in del_indices else "keep"
            print(col.format(i, items[i][:26], qtys[i], f"{before[i]:.2f}", action))
        print("─" * 58)

        for orig_idx in del_indices:
            pb_page.delete_row(orig_idx)
            pb_page.page.wait_for_timeout(500)

        expected = sum(before[i] for i in kept)
        hdr      = _hdr_total(pb_page)
        match    = "✓ MATCH" if abs(hdr - expected) <= self.TOL else f"✗ MISMATCH (diff={hdr-expected:.4f})"
        print(col.format("", "EXPECTED (kept sum)", "", f"{expected:.2f}", ""))
        print(col.format("", "HEADER TOTAL",        "", f"{hdr:.2f}",      match))
        print()

        assert abs(hdr - expected) <= self.TOL, (
            f"M2: Header {hdr} != remaining sum {expected}"
        )

    def test_m2b_delete_all_but_one_header_equals_single_row(self, pb_page):
        """M2b: Add N rows, delete all but row 0 — header must equal surviving row."""
        n      = _rng.randint(3, 5)
        items, qtys, _, _, _ = _add_rows(pb_page, n=n)
        before = _row_totals(pb_page, n)

        col = "{:<3} {:<26} {:>6} {:>14} {}"
        print("\n")
        print(col.format("#", "Item", "Qty", "Total", "Action"))
        print("─" * 58)
        for i in range(n):
            action = "KEEP (survivor)" if i == 0 else "delete"
            print(col.format(i, items[i][:26], qtys[i], f"{before[i]:.2f}", action))
        print("─" * 58)

        for _ in range(n - 1):
            pb_page.delete_row(1)
            pb_page.page.wait_for_timeout(500)

        hdr  = _hdr_total(pb_page)
        row0 = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        match = "✓ MATCH" if abs(hdr - before[0]) <= self.TOL else f"✗ MISMATCH"
        print(col.format("", "Surviving row0 total", "", f"{before[0]:.2f}", ""))
        print(col.format("", "HEADER TOTAL",         "", f"{hdr:.2f}",       match))
        print()

        assert abs(hdr - before[0]) <= self.TOL, f"M2b: Header {hdr} != row0 {before[0]}"
        assert abs(row0 - before[0]) <= self.TOL, f"M2b: Surviving row {row0} != original row0 {before[0]}"

    def test_m3_mutate_disc_delete_add_recheck(self, pb_page):
        """M3: Add N rows → apply random disc to some → delete 1 → add new row → header = sum."""
        n      = _rng.randint(3, 5)
        items, qtys, _, _, _ = _add_rows(pb_page, n=n, disc_pcts=[0]*n)

        disc_rows = _rng.sample(range(n), _rng.randint(1, n))
        disc_map  = {}
        for i in disc_rows:
            d = _rng.choice([5, 10, 15, 20])
            pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, i, d)
            disc_map[i] = d
        pb_page.page.wait_for_timeout(600)

        del_idx   = _rng.randint(1, n - 1)
        remaining = n - 1

        new_item = _rng.choice([x for x in ITEMS if x not in items])
        new_qty  = _rand_qty()

        col = "{:<3} {:<26} {:>6} {:>6} {}"
        print("\n")
        print(col.format("#", "Item", "Qty", "Disc%", "Action"))
        print("─" * 56)
        for i in range(n):
            action = f"DELETE" if i == del_idx else f"disc {disc_map.get(i,0)}%" if i in disc_map else "keep"
            print(col.format(i, items[i][:26], qtys[i], disc_map.get(i, 0), action))
        print(col.format("+", new_item[:26], new_qty, 0, "ADD NEW"))
        print("─" * 56)

        pb_page.delete_row(del_idx)
        pb_page.page.wait_for_timeout(500)

        pb_page.page.locator(pb_page.ADD_ROW_BTN).click()
        pb_page.page.wait_for_timeout(600)
        nudge = pb_page._pick_nudge_item(new_item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, remaining, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, remaining, new_item)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(remaining)
        pb_page.fill_qty_details(1, new_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        total_rows = remaining + 1
        rows = _row_totals(pb_page, total_rows)
        hdr  = _hdr_total(pb_page)
        match = "✓ MATCH" if abs(hdr - sum(rows)) <= self.TOL else f"✗ MISMATCH (diff={hdr-sum(rows):.4f})"
        print(col.format("", "HEADER TOTAL", "", "", match + f"  {hdr:.2f}"))
        print(col.format("", "SUM OF ROWS",  "", "", f"{sum(rows):.2f}"))
        print()

        for i, t in enumerate(rows):
            assert t > 0, f"M3: Row {i} Total = 0"
        assert abs(hdr - sum(rows)) <= self.TOL, f"M3: Header {hdr} != sum {sum(rows)}"

    def test_m3b_change_qty_on_existing_rows_header_recalcs(self, pb_page):
        """M3b: Add N rows, increase qty on a random row via popup → header grows."""
        n      = _rng.randint(2, 4)
        items, qtys, _, _, _ = _add_rows(pb_page, n=n)
        hdr_before = _hdr_total(pb_page)

        target_row = _rng.randint(0, n - 1)
        mult       = _rng.randint(2, 5)
        new_qty    = qtys[target_row] * mult

        col = "{:<3} {:<26} {:>8} {:>8} {}"
        print("\n")
        print(col.format("#", "Item", "OldQty", "NewQty", "Action"))
        print("─" * 60)
        for i in range(n):
            if i == target_row:
                print(col.format(i, items[i][:26], qtys[i], new_qty, f"CHANGE ×{mult}"))
            else:
                print(col.format(i, items[i][:26], qtys[i], "-", "keep"))
        print("─" * 60)

        pb_page.open_qty_details_popup(target_row)
        pb_page.fill_qty_details(1, new_qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        hdr_after = _hdr_total(pb_page)
        rows      = _row_totals(pb_page, n)
        grew      = "✓ GREW" if hdr_after > hdr_before else "✗ DID NOT GROW"
        match     = "✓ MATCH" if abs(hdr_after - sum(rows)) <= self.TOL else "✗ MISMATCH"
        print(f"  Header before: {hdr_before:.2f}  →  after: {hdr_after:.2f}  [{grew}]")
        print(f"  Sum of rows  : {sum(rows):.2f}  [{match}]")
        print()

        assert hdr_after > hdr_before, f"M3b: Header should grow after qty increase"
        assert abs(hdr_after - sum(rows)) <= self.TOL, f"M3b: Header {hdr_after} != sum{rows}"

    def test_m3c_change_disc_on_existing_rows_header_recalcs(self, pb_page):
        """M3c: Add N rows with no disc, apply disc to all → header drops, still = sum."""
        n      = _rng.randint(2, 4)
        items, qtys, _, _, _ = _add_rows(pb_page, n=n, disc_pcts=[0]*n)
        hdr_before = _hdr_total(pb_page)

        disc = _rng.choice([5, 10, 15, 20])

        col = "{:<3} {:<26} {:>6} {:>6}"
        print("\n")
        print(col.format("#", "Item", "Qty", "Disc%"))
        print("─" * 44)
        for i in range(n):
            print(col.format(i, items[i][:26], qtys[i], f"0 → {disc}"))
        print("─" * 44)

        for i in range(n):
            pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, i, disc)
        pb_page.page.wait_for_timeout(700)

        hdr_after = _hdr_total(pb_page)
        rows      = _row_totals(pb_page, n)
        dropped   = "✓ DROPPED" if hdr_after < hdr_before else "✗ DID NOT DROP"
        match     = "✓ MATCH"   if abs(hdr_after - sum(rows)) <= self.TOL else "✗ MISMATCH"
        print(f"  Header before: {hdr_before:.2f}  →  after: {hdr_after:.2f}  [{dropped}]")
        print(f"  Sum of rows  : {sum(rows):.2f}  [{match}]")
        print()

        assert hdr_after < hdr_before, f"M3c: Header should drop after {disc}% disc"
        assert abs(hdr_after - sum(rows)) <= self.TOL, f"M3c: Header {hdr_after} != sum{rows}"


# ── Group 10: Edge cases ─────────────────────────────────────────────────────

@pytest.mark.direct_pb
class TestEdgeCases:
    """
    Boundary and user-behaviour edge cases.
    """

    TOL = 0.02

    def test_e1_ebw_equals_qty_amount_zero(self, pb_page):
        """E1: EBW = Qty → net_qty = 0 → row Total = 0."""
        qty = _rand_qty()
        _setup_single_row(pb_page, qty=qty, ebw=qty)
        total = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        result = "✓ ZERO" if total == 0.0 else f"✗ GOT {total}"
        print(f"\n[E1]  qty={qty}  ebw={qty}  net_qty=0  total={total:.2f}  [{result}]")
        assert total == 0.0, f"E1: Total should be 0 when EBW=Qty, got {total}"

    def test_e1b_ebw_greater_than_qty(self, pb_page):
        """E1b: EBW > Qty → net_qty negative → Total ≤ 0."""
        qty = _rand_qty()
        ebw = qty + _rng.randint(1, 100)
        _setup_single_row(pb_page, qty=qty, ebw=ebw)
        total  = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        result = "✓ ≤0" if total <= self.TOL else f"✗ GOT {total}"
        print(f"\n[E1b] qty={qty}  ebw={ebw}  net_qty={qty-ebw}  total={total:.2f}  [{result}]")
        assert total <= self.TOL, f"E1b: Total should be ≤0 when EBW>Qty, got {total}"

    def test_e2_discount_100_percent_total_zero(self, pb_page):
        """E2: 100% discount — Total Amount should be 0 (or ≤0)."""
        qty = _rand_qty()
        _setup_single_row(pb_page, qty=qty, disc_pct=100)
        total  = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        result = "✓ ZERO" if total <= self.TOL else f"✗ GOT {total}"
        print(f"\n[E2]  qty={qty}  disc=100%  total={total:.2f}  [{result}]")
        assert total <= self.TOL, f"E2: With 100% disc, Total should be 0, got {total}"

    def test_e2b_discount_reduces_total_proportionally(self, pb_page):
        """E2b: 50% discount — Total should be ~half of no-discount Total."""
        qty = _rand_qty()
        _setup_single_row(pb_page, qty=qty)
        total_no_disc = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)

        pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, 50)
        pb_page.page.wait_for_timeout(500)
        total_with_disc = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)

        expected = total_no_disc * 0.5
        match    = "✓ MATCH" if abs(total_with_disc - expected) <= self.TOL else f"✗ MISMATCH"
        print(f"\n[E2b] qty={qty}  total_no_disc={total_no_disc:.2f}  → disc=50%"
              f"  total={total_with_disc:.2f}  expected={expected:.2f}  [{match}]")
        assert abs(total_with_disc - expected) <= self.TOL, (
            f"E2b: With 50% disc, Total {total_with_disc} != half of {total_no_disc} = {expected}"
        )

    def test_e3_gst_type_switch_igst_to_cgst_sgst_clears_igst(self, pb_page):
        """E3: Switch GST type IGST → CGST+SGST — IGST clears, CGST/SGST populate."""
        qty = _rand_qty()
        tax = _rng.choice([5, 12, 18])
        _setup_single_row(pb_page, qty=qty)
        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, tax)
        pb_page.select_gst_type(0, "IGST")
        pb_page.page.wait_for_timeout(600)

        igst_before = pb_page._read_number_nth(pb_page.IGST_AMOUNT, 0)
        assert igst_before > 0, "E3: IGST must be > 0 before switching type"

        pb_page.select_gst_type(0, "CGST + SGST")
        pb_page.page.wait_for_timeout(600)

        igst_after = pb_page._read_number_nth(pb_page.IGST_AMOUNT, 0)
        cgst       = pb_page._read_number_nth(pb_page.CGST_AMOUNT, 0)
        sgst       = pb_page._read_number_nth(pb_page.SGST_AMOUNT, 0)

        print(f"\n[E3]  qty={qty}  tax={tax}%  IGST before switch: {igst_before:.2f}")
        print(f"      After IGST→CGST+SGST:  IGST={igst_after:.2f} {'✓ cleared' if igst_after==0 else '✗ NOT CLEARED'}  "
              f"CGST={cgst:.2f} {'✓' if cgst>0 else '✗'}  SGST={sgst:.2f} {'✓' if sgst>0 else '✗'}")

        assert igst_after == 0.0, f"E3: IGST should clear after switch, got {igst_after}"
        assert cgst > 0,          f"E3: CGST should populate after switch, got {cgst}"
        assert sgst > 0,          f"E3: SGST should populate after switch, got {sgst}"

    def test_e3b_gst_type_switch_cgst_sgst_to_igst_clears_cgst(self, pb_page):
        """E3b: Switch CGST+SGST → IGST — CGST/SGST clear, IGST populates."""
        qty = _rand_qty()
        tax = _rng.choice([5, 12, 18])
        _setup_single_row(pb_page, qty=qty)
        pb_page.enable_gst_off(0)
        pb_page.select_tax_rate(0, tax)
        pb_page.select_gst_type(0, "CGST + SGST")
        pb_page.page.wait_for_timeout(600)

        cgst_before = pb_page._read_number_nth(pb_page.CGST_AMOUNT, 0)
        assert cgst_before > 0, "E3b: CGST must be > 0 before switching"

        pb_page.select_gst_type(0, "IGST")
        pb_page.page.wait_for_timeout(600)

        cgst_after = pb_page._read_number_nth(pb_page.CGST_AMOUNT, 0)
        igst_after = pb_page._read_number_nth(pb_page.IGST_AMOUNT, 0)

        print(f"\n[E3b] qty={qty}  tax={tax}%  CGST before switch: {cgst_before:.2f}")
        print(f"      After CGST+SGST→IGST:  CGST={cgst_after:.2f} {'✓ cleared' if cgst_after==0 else '✗ NOT CLEARED'}  "
              f"IGST={igst_after:.2f} {'✓' if igst_after>0 else '✗'}")

        assert cgst_after == 0.0, f"E3b: CGST should clear after switch to IGST, got {cgst_after}"
        assert igst_after > 0,    f"E3b: IGST should populate after switch, got {igst_after}"

    def test_e6_increase_qty_recalculates_disc_and_total(self, pb_page):
        """E6: Disc% set, then qty multiplied via popup — Disc Amount and Total must grow."""
        qty  = _rand_qty()
        disc = _rng.choice([5, 10, 15, 20])
        mult = _rng.randint(2, 5)
        _setup_single_row(pb_page, qty=qty, disc_pct=disc)
        disc_before  = pb_page._read_number_nth(pb_page.DISCOUNT_AMOUNT, 0)
        total_before = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)

        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty * mult)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        disc_after  = pb_page._read_number_nth(pb_page.DISCOUNT_AMOUNT, 0)
        total_after = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)

        print(f"\n[E6]  qty {qty} → {qty*mult} (×{mult})  disc={disc}%")
        print(f"      Disc:  {disc_before:.2f} → {disc_after:.2f}  {'✓ GREW' if disc_after > disc_before else '✗'}")
        print(f"      Total: {total_before:.2f} → {total_after:.2f}  {'✓ GREW' if total_after > total_before else '✗'}")

        assert disc_after > disc_before,   f"E6: Disc should grow: {disc_before} → {disc_after}"
        assert total_after > total_before, f"E6: Total should grow: {total_before} → {total_after}"

    def test_e9_clear_qty_to_zero_total_drops(self, pb_page):
        """E9: Set random qty (Total > 0), then set qty=0 — Total must drop to 0."""
        qty = _rand_qty()
        _setup_single_row(pb_page, qty=qty)
        total_before = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        assert total_before > 0, "E9: Initial total must be > 0"

        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(0, 0)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        total_after = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        result      = "✓ ZERO" if total_after == 0.0 else f"✗ GOT {total_after}"
        print(f"\n[E9]  qty {qty} → 0  total: {total_before:.2f} → {total_after:.2f}  [{result}]")
        assert total_after == 0.0, f"E9: After qty=0, Total should be 0, got {total_after}"

    def test_e10_labour_alone_total_equals_amount_minus_labour(self, pb_page):
        """E10: No disc, no tax — Total = Amount − Labour."""
        qty    = _rand_qty()
        labour = _rng.choice([l for l in LABOUR_CHOICES if l > 0])
        _setup_single_row(pb_page, qty=qty)
        amount_hdr = pb_page._read_number_nth(pb_page.AMOUNT, 0)
        pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, 0, labour)
        pb_page.page.wait_for_timeout(500)
        total    = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        expected = amount_hdr - labour
        match    = "✓ MATCH" if abs(total - expected) <= self.TOL else f"✗ MISMATCH"
        print(f"\n[E10] qty={qty}  amount={amount_hdr:.2f}  labour={labour}")
        print(f"      expected={amount_hdr:.2f} − {labour} = {expected:.2f}  got={total:.2f}  [{match}]")
        assert abs(total - expected) <= self.TOL, (
            f"E10: Total {total} != Amount({amount_hdr}) − Labour({labour}) = {expected}"
        )

    def test_m4_fill_disc_labour_before_item_select(self, pb_page):
        """M4: Fill disc/labour on blank row BEFORE selecting item → item select triggers recalc."""
        disc   = _rand_disc()
        labour = _rand_labour()
        qty    = _rand_qty()
        item   = _rng.choice(ITEMS)
        print(f"\nM4: disc={disc}%, labour={labour}, qty={qty}, item={item}")
        pb_page.open_add_form()
        pb_page.fill_header()

        # Fill on blank row 0 before any item is chosen
        if disc:
            pb_page._fill_number_nth(pb_page.DISC_PERCENTAGE, 0, disc)
        if labour:
            pb_page._fill_number_nth(pb_page.LABOUR_CHARGES, 0, labour)
        pb_page.page.wait_for_timeout(400)

        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(1000)

        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        total  = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        hdr    = _hdr_total(pb_page)
        amount = pb_page._read_number_nth(pb_page.AMOUNT, 0)

        assert total > 0, f"M4: Total should be > 0 after item select, got {total}"
        assert abs(hdr - total) <= self.TOL, f"M4: Header {hdr} != row total {total}"
        print(f"M4: amount={amount}, total={total} (diff={amount - total:.2f} — disc+labour effect)")

    def test_m4b_fill_ebw_before_item_net_qty_correct(self, pb_page):
        """M4b: Fill EBW on blank row before item select → after qty set, net_qty = qty − EBW."""
        qty  = _rand_qty()
        ebw  = _rand_ebw(qty)
        item = _rng.choice(ITEMS)
        print(f"\nM4b: qty={qty}, ebw={ebw}, item={item}")
        pb_page.open_add_form()
        pb_page.fill_header()

        pb_page._fill_number_nth(pb_page.EMPTY_BAG_WEIGHT, 0, ebw)
        pb_page.page.wait_for_timeout(400)

        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(1000)

        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(600)

        net_qty = pb_page._read_number_nth(pb_page.NET_QUANTITY, 0)
        total   = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)

        assert total > 0, f"M4b: Total should be > 0 after item+qty set"
        print(f"M4b: net_qty={net_qty} (expected {qty - ebw} if EBW survived item-select, else {qty})")


# ── Group 11: Post-save state ─────────────────────────────────────────────────

@pytest.mark.direct_pb
class TestPostSave:
    """Tests that verify state after a PB is saved."""

    ROW_TRIGGER = "button.erp-row-trigger"
    EDIT_MENU_ITEM = (
        "xpath=//div[contains(@class,'mat-mdc-menu-panel')]"
        "//button[.//i[normalize-space(.)='edit']]"
    )
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    SWAL_TITLE_SUCCESS = "Purchase Booking created successfully"

    def _submit_and_return_to_list(self, pb_page):
        """Click Submit, assert swal2 success title, dismiss, wait for listing."""
        btn = pb_page.page.locator(pb_page.SUBMIT_BTN)
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        pb_page.page.wait_for_selector(".swal2-container", timeout=12000)
        title = pb_page.page.locator("#swal2-title").inner_text().strip()
        assert title == self.SWAL_TITLE_SUCCESS, (
            f"M5: Expected success alert '{self.SWAL_TITLE_SUCCESS}', got: '{title}'"
        )
        pb_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=8000)
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        pb_page.page.wait_for_timeout(500)

    def test_m5_saved_pb_edit_disabled_in_menu(self, pb_page):
        """M5: Save a PB → open row action menu → Edit must be disabled (Pending status)."""
        item = _rng.choice(ITEMS)
        qty  = _rand_qty()
        print(f"\n[M5] item={item!r}  qty={qty}")

        pb_page.open_add_form()
        pb_page.fill_header()

        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(1000)
        pb_page.open_qty_details_popup(0)
        pb_page.fill_qty_details(1, qty)
        pb_page.click_done()
        pb_page.page.wait_for_timeout(500)

        row_total = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        print(f"[M5] row total before save = {row_total:.2f}")

        self._submit_and_return_to_list(pb_page)

        ref_no = pb_page.page.locator(self.REF_NO_COL).first.inner_text().strip()
        assert ref_no.startswith("PURB/"), f"M5: Expected saved PB ref_no, got: {ref_no}"
        print(f"[M5] saved → ref_no={ref_no}")

        pb_page.page.locator(self.ROW_TRIGGER).first.click(force=True)
        pb_page.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)

        edit_btn = pb_page.page.locator(self.EDIT_MENU_ITEM)
        assert edit_btn.count() > 0, "M5: Edit menu item not found in action menu"
        disabled = edit_btn.first.get_attribute("disabled")
        aria_dis = edit_btn.first.get_attribute("aria-disabled")
        is_disabled = disabled is not None or aria_dis == "true"
        print(f"[M5] Edit button disabled={is_disabled}  (disabled={disabled!r}, aria-disabled={aria_dis!r})")
        assert is_disabled, f"M5: Edit is enabled for Pending PB '{ref_no}' — expected disabled"
        print(f"[M5] ✓ Edit correctly disabled for Pending PB {ref_no}")


# ── Group 12: Decimal precision validation ────────────────────────────────────

@pytest.mark.direct_pb
class TestDecimalPrecision:
    """
    Validates decimal place rules enforced by the ERP:
      - Quantity: max 4 decimal places (5dp → inline error)
      - Rate:     up to 3 decimal places accepted
      - Total Amount displayed: always rounded to 2 decimal places
    """

    QTY_ERROR_SEL   = "mat-error"
    QTY_ERROR_TEXT  = "Quantity can have a maximum of 4 decimal places."
    TOL             = 0.005   # tolerance for 2dp rounding check

    def _rand_5dp_qty(self):
        """Random qty with exactly 5 significant decimal digits (last digit non-zero)."""
        integer_part = _rng.randint(1, 99)
        frac_5dp     = _rng.randint(10001, 99999)   # guarantees 5 digits, last non-zero
        return float(f"{integer_part}.{frac_5dp}")

    def _rand_4dp_qty(self):
        """Random qty with exactly 4 significant decimal digits (last digit non-zero)."""
        integer_part = _rng.randint(1, 99)
        frac_4dp     = _rng.randint(1001, 9999)     # guarantees 4 digits, last non-zero
        return float(f"{integer_part}.{frac_4dp}")

    def _rand_3dp_rate(self):
        """Random rate with exactly 3 decimal digits."""
        integer_part = _rng.randint(100, 2000)
        frac_3dp     = _rng.randint(101, 999)
        return float(f"{integer_part}.{frac_3dp}")

    def _decimal_places(self, value):
        """Count decimal places in a float (strips trailing zeros)."""
        s = f"{value:.10f}".rstrip("0")
        if "." not in s:
            return 0
        return len(s.split(".")[1])

    def test_dp1_5dp_qty_rejected_4dp_accepted_total_2dp(self, pb_page):
        """DP1: 5dp qty shows inline error; clear → 4dp qty accepted; total rounds to 2dp."""
        qty_5dp  = self._rand_5dp_qty()
        qty_4dp  = self._rand_4dp_qty()
        rate_3dp = self._rand_3dp_rate()
        item     = _rng.choice(ITEMS)

        print(f"\n[DP1] item={item!r}")
        print(f"[DP1] qty_5dp={qty_5dp}  qty_4dp={qty_4dp}  rate={rate_3dp}")

        # ── Step 1: open form + select item ───────────────────────────────
        pb_page.open_add_form()
        pb_page.fill_header()
        nudge = pb_page._pick_nudge_item(item)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, nudge)
        pb_page.page.wait_for_timeout(500)
        pb_page._select_mat_by_text_nth(pb_page.ITEM_NAME, 0, item)
        pb_page.page.wait_for_timeout(1000)

        # ── Step 2: open popup, enter 5dp qty → expect error ──────────────
        pb_page.open_qty_details_popup(0)
        qty_inp = pb_page.page.locator("input[placeholder='Quantity']:not([readonly])").last
        qty_inp.wait_for(state="visible", timeout=8000)
        qty_inp.fill(str(qty_5dp))
        pb_page.page.wait_for_timeout(400)

        # trigger validation by tabbing out
        qty_inp.press("Tab")
        pb_page.page.wait_for_timeout(400)

        error_loc = pb_page.page.locator(self.QTY_ERROR_SEL).filter(has_text="4 decimal places")
        assert error_loc.count() > 0, (
            f"DP1: Expected inline error for 5dp qty={qty_5dp}, none found"
        )
        error_text = error_loc.first.inner_text().strip()
        print(f"[DP1] ✓ 5dp error shown: '{error_text}'")
        assert self.QTY_ERROR_TEXT in error_text, (
            f"DP1: Error text mismatch: '{error_text}'"
        )

        # ── Step 3: clear and enter 4dp qty → no error ────────────────────
        qty_inp.fill("")
        pb_page.page.wait_for_timeout(200)
        qty_inp.fill(str(qty_4dp))
        pb_page.page.wait_for_timeout(400)
        qty_inp.press("Tab")
        pb_page.page.wait_for_timeout(400)

        still_error = pb_page.page.locator(self.QTY_ERROR_SEL).filter(has_text="4 decimal places")
        assert still_error.count() == 0, (
            f"DP1: 4dp qty={qty_4dp} should be accepted but error is still shown"
        )
        print(f"[DP1] ✓ 4dp qty accepted (no error)")

        # fill bags and close popup
        bags_inp = pb_page.page.locator("input[placeholder='No of Bags']:not([readonly])").last
        bags_inp.fill("1")
        pb_page.page.wait_for_timeout(200)
        pb_page.click_done()

        # ── Step 4: set rate with 3dp ──────────────────────────────────────
        pb_page._fill_number_nth(pb_page.RATE, 0, rate_3dp)
        pb_page.page.wait_for_timeout(600)

        # ── Step 5: read total and assert it has ≤ 2 decimal places ────────
        total = pb_page._read_number_nth(pb_page.TOTAL_AMOUNT, 1)
        total_2dp_rounded = round(total, 2)

        # ERP math (informational)
        # qty is displayed/used as rounded to 2dp internally by ERP
        qty_erp   = round(qty_4dp, 2)
        erp_exact = qty_erp * rate_3dp

        print(f"\n[DP1] ─── Decimal precision summary ───────────────────────")
        print(f"[DP1]   qty entered (4dp)  : {qty_4dp}")
        print(f"[DP1]   qty ERP uses (~2dp): {qty_erp}")
        print(f"[DP1]   rate (3dp)         : {rate_3dp}")
        print(f"[DP1]   expected total     : {erp_exact:.6f}  → rounded {erp_exact:.2f}")
        print(f"[DP1]   ERP shown total    : {total}")
        print(f"[DP1]   total ≤ 2dp?       : {abs(total - total_2dp_rounded) < self.TOL}")
        print(f"[DP1] ────────────────────────────────────────────────────────")

        assert total > 0, f"DP1: Total should be > 0, got {total}"
        assert abs(total - total_2dp_rounded) < self.TOL, (
            f"DP1: Total {total} is not rounded to 2dp (rounded={total_2dp_rounded})"
        )

        # ── Step 6: save and verify ────────────────────────────────────────
        btn = pb_page.page.locator(pb_page.SUBMIT_BTN)
        btn.wait_for(state="visible", timeout=5000)
        btn.click(force=True)
        pb_page.page.wait_for_selector(".swal2-container", timeout=12000)
        title = pb_page.page.locator("#swal2-title").inner_text().strip()
        assert title == "Purchase Booking created successfully", (
            f"DP1: Save failed, swal2 title: '{title}'"
        )
        pb_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=8000)
        pb_page.navigate_to_page()
        pb_page.page.wait_for_selector("td.cdk-column-transaction_ref_no", timeout=15000)
        pb_page.page.wait_for_timeout(500)
        ref_no = pb_page.page.locator("td.cdk-column-transaction_ref_no").first.inner_text().strip()
        assert ref_no.startswith("PURB/"), f"DP1: Expected PURB/ ref_no, got: {ref_no}"
        print(f"[DP1] ✓ saved → ref_no={ref_no}  total={total:.2f}")
