import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_FIRST_NAMES = [
    "Ramesh", "Suresh", "Mahesh", "Dinesh", "Ganesh", "Rajesh", "Naresh", "Umesh", "Yogesh", "Lokesh",
    "Anil", "Sunil", "Pankaj", "Sanjay", "Vijay", "Ajay", "Manoj", "Ravi", "Vinod", "Pramod",
    "Santosh", "Rakesh", "Mukesh", "Devendra", "Narendra", "Hemant", "Prasad", "Nitin", "Sachin", "Rohit",
    "Amol", "Vishal", "Nikhil", "Rahul", "Abhijit", "Deepak", "Vivek", "Prashant", "Nilesh", "Tushar",
    "Kiran", "Shubham", "Abhishek", "Aniket", "Akash", "Omkar", "Siddhesh", "Pratik", "Gaurav", "Swapnil",
]

_MIDDLE_NAMES = [
    "Baburao", "Shankar", "Sitaram", "Govind", "Dattatray", "Pandurang", "Vitthal", "Narayan", "Bhimrao", "Kondiba",
    "Krishnarao", "Vishwanath", "Laxmanrao", "Bhalchandra", "Trimbakrao", "Anandrao", "Madhavrao", "Shivaji", "Bajirao", "Tatya",
]

_LAST_NAMES = [
    "Patil", "Shinde", "Jadhav", "Deshmukh", "More", "Pawar", "Kulkarni", "Bhosale", "Mane", "Gaikwad",
    "Yadav", "Chavan", "Salunke", "Kadam", "Sawant", "Thorat", "Waghmare", "Bandal", "Kale", "Doke",
    "Mohite", "Bhoir", "Lokhande", "Deshpande", "Joshi", "Nair", "Iyer", "Reddy", "Sharma", "Verma",
    "Kumar", "Singh", "Gupta", "Shah", "Mehta", "Patel", "Rao", "Naik", "Nayak", "Pillai",
    "Wagh", "Borse", "Gholap", "Gavhane", "Sonawane", "Nimbalkar", "Zende", "Kshirsagar", "Bagal", "Mulik",
]


def _unique_name():
    first  = _rng.choice(_FIRST_NAMES)
    middle = _rng.choice(_MIDDLE_NAMES)
    last   = _rng.choice(_LAST_NAMES)
    return f"{first} {middle} {last}"


def _unique_data():
    global _counter
    _counter += 1
    name = _unique_name()
    slug = f"{_ts}{_counter}"
    return {
        "farmer_name":  name,
        "email":        f"farmer{slug}@testmail.com",
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "address1":     "101 Shivaji Path Pune",
        "address2":     "202 MG Road Kolhapur",
        "bank_name":    "HDFC Bank",
        "bank_branch":  "Pune Branch",
        "bank_ifsc":    "BARB0696379",
        "bank_holder":  name,
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


class TestFarmerFPCCreate:
    def test_create_fpc_member(self, farmer_page):
        data = _unique_data()
        farmer_page.create_record(data, category="FPC Member")
        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        # Verify workflow
        farmer_page.click_edit_button(data["farmer_name"])
        farmer_page.click_workflow_btn(farmer_page.VERIFY_BTN)
        farmer_page.search_farmer(data["farmer_name"])
        assert farmer_page.get_workflow_status(data["farmer_name"]) == "Verify"

        # Approve workflow
        farmer_page.click_edit_button(data["farmer_name"])
        farmer_page.click_workflow_btn(farmer_page.APPROVE_BTN)
        farmer_page.search_farmer(data["farmer_name"])
        assert farmer_page.get_workflow_status(data["farmer_name"]) == "Approve"


class TestFarmerBorrowerCreate:
    def test_create_borrower_farmer(self, farmer_page):
        data = _unique_data()
        farmer_page.create_record(data, category="Borrower Farmer")
        farmer_page.search_farmer(data["farmer_name"])
        farmer_page.verify_farmer_exists(data["farmer_name"])

        # Verify workflow
        farmer_page.click_edit_button(data["farmer_name"])
        farmer_page.click_workflow_btn(farmer_page.VERIFY_BTN)
        farmer_page.search_farmer(data["farmer_name"])
        assert farmer_page.get_workflow_status(data["farmer_name"]) == "Verify"

        # Approve workflow
        farmer_page.click_edit_button(data["farmer_name"])
        farmer_page.click_workflow_btn(farmer_page.APPROVE_BTN)
        farmer_page.search_farmer(data["farmer_name"])
        assert farmer_page.get_workflow_status(data["farmer_name"]) == "Approve"
