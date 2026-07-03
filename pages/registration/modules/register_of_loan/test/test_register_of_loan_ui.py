import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _encode(n):
    result = ""
    n = max(n, 1)
    while n > 0:
        result = _LETTERS[(n - 1) % 26] + result
        n = (n - 1) // 26
    return result


def _unique_data():
    global _counter
    _counter += 1
    return {
        "sanction_date":       "09/09/2024",
        "bank_name":           f"HDFC Bank {_encode(_ts % 100000)}{_encode(_counter)}",
        "sanction_amount":     str(_rng.randint(500000, 99999999)),
        "disbursement_amount": str(_rng.randint(100000, 49999999)),
        "emi_servicing_date":  "15/10/2024",
        "instalment_amount":   str(_rng.randint(5000, 99999)),
        "reminder_days":       str(_rng.randint(1, 30)),
        "outstanding_date":    "01/01/2025",
        "outstanding_amount":  str(_rng.randint(50000, 9999999)),
    }


class TestRegisterOfLoanUIGroup1:
    def test_create_smoke(self, loan_page):
        data = _unique_data()
        loan_page.create_record(data)
        loan_page.search_loan(data["bank_name"])
        loan_page.verify_loan_exists(data["bank_name"])


class TestRegisterOfLoanUIGroup2:
    def test_form_discard(self, loan_page):
        data = _unique_data()
        loan_page.open_add_form()
        loan_page.page.locator(loan_page.BANK_NAME).first.click(force=True)
        loan_page.page.locator(loan_page.BANK_NAME).first.fill(data["bank_name"])
        loan_page.close_popup()
        assert not loan_page.is_loan_in_table(data["bank_name"])

    def test_validation_sweep(self, loan_page):
        loan_page.open_add_form()
        loan_page.submit()
        loan_page.handle_validation_alert()
        loan_page.close_popup()


class TestRegisterOfLoanUIGroup3:
    def test_listing_and_search(self, loan_page):
        assert loan_page.get_table_row_count() > 0


class TestRegisterOfLoanUIGroup4:
    def test_full_row_actions(self, loan_page):
        data = _unique_data()
        loan_page.create_record(data)
        loan_page.search_loan(data["bank_name"])
        loan_page.verify_loan_exists(data["bank_name"])
        loan_page.click_view_button(data["bank_name"])
        loan_page.verify_view_popup_read_only()
        loan_page.close_popup()
        loan_page.search_loan(data["bank_name"])
        loan_page.click_history_button(data["bank_name"])
        assert loan_page.page.locator(".popup-footer").count() > 0
        loan_page.close_popup()
