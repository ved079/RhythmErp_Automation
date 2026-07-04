import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_CO_FIRST = [
    "Shivaji", "Balaji", "Ganesh", "Laxmi", "Sai", "Vitthal", "Mahalaxmi", "Bhavani",
    "Rajlaxmi", "Samarth", "Omkar", "Siddhivinayak", "Datta", "Renuka", "Ambika",
    "Gurukripa", "Swami", "Kalpana", "Nirmala", "Prathamesh", "Shraddha", "Suvidha",
    "Aarav", "Vedant", "Pranav", "Tanvi", "Shreya", "Siddhi", "Atharva", "Ruturaj",
]

_CO_MIDDLE = [
    "Traders", "Enterprises", "Industries", "Agro", "Foods", "Exports", "Farms",
    "Suppliers", "Distributors", "Associates", "Solutions", "Group", "Services",
    "Products", "Resources", "Networks", "Commodities", "Ventures", "Holdings",
]

_CO_SUFFIX = [
    "Pvt Ltd", "Ltd", "LLP", "& Co", "and Sons", "Brothers", "International",
    "India", "Corporation", "Agency", "Works", "Trading Co", "Impex",
]

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _unique_company_name():
    first  = _rng.choice(_CO_FIRST)
    middle = _rng.choice(_CO_MIDDLE)
    suffix = _rng.choice(_CO_SUFFIX)
    return f"{first} {middle} {suffix}"


def _pan(counter):
    return f"ABC{_LETTERS[(_ts + counter) % 26]}{_LETTERS[(_ts * 3 + counter) % 26]}{(_ts + counter * 7) % 9000 + 1000}F"


def _gstin(counter, state_code="29"):
    return f"{state_code}{_pan(counter)}1Z5"


def _unique_data():
    global _counter
    _counter += 1
    slug = f"{_ts}{_counter}"
    name = _unique_company_name()
    # Company Code: max 4 chars
    code = f"T{_counter % 999:03d}"
    return {
        "company_name":  name,
        "company_code":  code,
        "short_name":    code,
        "contact_name":  name,
        "email":         f"co{slug}@testmail.com",
        "mobile":        str(_rng.randint(7000000000, 9999999999)),
        "pan":           _pan(_counter),
        "tan":           f"PUNE{str(_rng.randint(10000, 99999))}D",
        "gstin":         _gstin(_counter, "29"),
        "cin":           f"U12345MH2024PTC{_counter:06d}",
        "background":    "Automated test company.",
        "address1":      "101 Shivaji Path Pune",
        "address2":      "202 MG Road Kolhapur",
    }


class TestCOUIGroup1:
    def test_create_smoke(self, co_page):
        data = _unique_data()
        co_page.create_record(data)
        co_page.search_company(data["company_name"])
        co_page.verify_company_exists(data["company_name"])


class TestCOUIGroup2:
    def test_form_discard(self, co_page):
        data = _unique_data()
        co_page.open_add_form()
        co_page.page.locator(co_page.COMPANY_NAME).first.click(force=True)
        co_page.page.locator(co_page.COMPANY_NAME).first.fill(data["company_name"])
        co_page.close_popup()
        assert not co_page.is_company_in_table(data["company_name"])

    def test_validation_sweep(self, co_page):
        co_page.open_add_form()
        co_page.submit()
        co_page.handle_validation_alert()
        co_page.close_popup()


class TestCOUIGroup3:
    def test_listing_and_search(self, co_page):
        assert co_page.get_table_row_count() > 0


class TestCOUIGroup4:
    def test_full_row_actions(self, co_page):
        data = _unique_data()
        co_page.create_record(data)
        co_page.search_company(data["company_name"])
        co_page.verify_company_exists(data["company_name"])
        co_page.click_view_button(data["company_name"])
        co_page.verify_view_popup_read_only()
        co_page.close_popup()
        co_page.search_company(data["company_name"])
        co_page.click_history_button(data["company_name"])
        assert co_page.page.locator(".popup-footer").count() > 0
        co_page.close_popup()
