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


def _pan(counter):
    return f"ABC{_LETTERS[(_ts + counter) % 26]}{_LETTERS[(_ts * 3 + counter) % 26]}{(_ts + counter * 7) % 9000 + 1000}F"


def _gstin(counter, state_code="29"):
    pan = _pan(counter)
    return f"{state_code}{pan}1Z5"


def _unique_data():
    global _counter
    _counter += 1
    tag = f"{_encode(_ts % 100000)}{_encode(_counter)}"
    return {
        "company_name": f"High Street {tag}",
        "email":        f"cust{tag.lower()}@testmail.com",
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "pan_number":   _pan(_counter),
        "address1":     "101 Shivaji Path Pune",
        "gstin1":       _gstin(_counter, "29"),
        "address2":     "123 Laxmi Nagar Kolhapur",
        "gstin2":       _gstin(_counter + 100, "27"),
        "bank_name":    "HDFC Bank",
        "bank_branch":  "Pune Branch",
        "bank_ifsc":    "BARB0696379",
        "bank_holder":  f"High Street {tag}",
        "bank_account": str(_rng.randint(100000000000, 999999999999)),
    }


class TestCustomerUIGroup1:
    def test_create_smoke(self, cust_page):
        data = _unique_data()
        cust_page.create_record(data)
        cust_page.search_customer(data["company_name"])
        cust_page.verify_customer_exists(data["company_name"])


class TestCustomerUIGroup2:
    def test_form_discard(self, cust_page):
        data = _unique_data()
        cust_page.open_add_form()
        cust_page.page.locator(cust_page.COMPANY_NAME).first.click(force=True)
        cust_page.page.locator(cust_page.COMPANY_NAME).first.fill(data["company_name"])
        cust_page.close_popup()
        assert not cust_page.is_customer_in_table(data["company_name"])

    def test_validation_sweep(self, cust_page):
        cust_page.open_add_form()
        cust_page.submit()
        cust_page.handle_validation_alert()
        cust_page.close_popup()


class TestCustomerUIGroup3:
    def test_listing_and_search(self, cust_page):
        assert cust_page.get_table_row_count() > 0


class TestCustomerUIGroup4:
    def test_full_row_actions(self, cust_page):
        data = _unique_data()
        cust_page.create_record(data)
        cust_page.search_customer(data["company_name"])
        cust_page.verify_customer_exists(data["company_name"])
        cust_page.click_view_button(data["company_name"])
        cust_page.verify_view_popup_read_only()
        cust_page.close_popup()
        cust_page.search_customer(data["company_name"])
        cust_page.click_history_button(data["company_name"])
        assert cust_page.page.locator(".popup-footer").count() > 0
        cust_page.close_popup()
