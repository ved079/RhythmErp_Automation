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
    tag = f"{_encode(_ts % 100000)}{_encode(_counter)}"
    # Name must be letters + spaces only
    return {
        "farmer_name":  f"Ramesh {tag}",
        "email":        f"farmer{tag.lower()}@testmail.com",
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "address1":     "101 Shivaji Path Pune",
        "address2":     "202 MG Road Kolhapur",
        "bank_name":    "HDFC Bank",
        "bank_branch":  "Pune Branch",
        "bank_ifsc":    "BARB0696379",
        "bank_holder":  f"Ramesh {tag}",
        "bank_account": str(_rng.randint(100000000000, 999999999999)),
    }


class TestFarmerUIGroup1:
    def test_create_smoke(self, farmer_page):
        data = _unique_data()
        farmer_page.create_record(data)
        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])


class TestFarmerUIGroup2:
    def test_form_discard(self, farmer_page):
        data = _unique_data()
        farmer_page.open_add_form()
        farmer_page.page.locator(farmer_page.FARMER_NAME).first.click(force=True)
        farmer_page.page.locator(farmer_page.FARMER_NAME).first.fill(data["farmer_name"])
        farmer_page.close_popup()
        assert not farmer_page.is_farmer_in_table(data["farmer_name"])

    def test_validation_sweep(self, farmer_page):
        farmer_page.open_add_form()
        farmer_page.submit()
        farmer_page.handle_validation_alert()
        farmer_page.close_popup()


class TestFarmerUIGroup3:
    def test_listing_and_search(self, farmer_page):
        assert farmer_page.get_table_row_count() > 0


class TestFarmerUIGroup4:
    def test_full_row_actions(self, farmer_page):
        data = _unique_data()
        farmer_page.create_record(data)
        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])
        farmer_page.click_view_button(data["farmer_name"])
        farmer_page.verify_view_popup_read_only()
        farmer_page.close_popup()
        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.click_history_button(data["farmer_name"])
        assert farmer_page.page.locator(".popup-footer").count() > 0
        farmer_page.close_popup()
