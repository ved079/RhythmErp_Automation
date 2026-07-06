import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

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


def _unique_company_name():
    first  = _rng.choice(_CO_FIRST)
    middle = _rng.choice(_CO_MIDDLE)
    suffix = _rng.choice(_CO_SUFFIX)
    return f"{first} {middle} {suffix}"


def _pan(counter):
    return f"ABC{_LETTERS[(_ts + counter) % 26]}{_LETTERS[(_ts * 3 + counter) % 26]}{(_ts + counter * 7) % 9000 + 1000}F"


def _gstin(counter, state_code="29"):
    pan = _pan(counter)
    return f"{state_code}{pan}1Z5"


def _unique_data():
    global _counter
    _counter += 1
    slug = f"{_ts}{_counter}"
    name = _unique_company_name()
    return {
        "company_name": name,
        "email":        f"cust{slug}@testmail.com",
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "pan_number":   _pan(_counter),
        "address1":     "101 Shivaji Path Pune",
        "gstin1":       _gstin(_counter, "29"),
        "address2":     "123 Laxmi Nagar Kolhapur",
        "gstin2":       _gstin(_counter + 100, "27"),
        "bank_name":    "HDFC Bank",
        "bank_branch":  "Pune Branch",
        "bank_ifsc":    "BARB0696379",
        "bank_holder":  name,
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

        updated_name = data["company_name"] + " U"
        cust_page.search_customer(data["company_name"])
        cust_page.click_edit_button(data["company_name"])
        cust_page.update_company_name(updated_name)
        cust_page.click_update()
        cust_page.handle_success_alert()

        cust_page.search_customer(updated_name)
        cust_page.click_history_button(updated_name)
        assert cust_page.page.locator(".popup-footer").count() > 0
        cust_page.close_popup()
