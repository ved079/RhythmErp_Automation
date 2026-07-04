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
    slug = f"{_ts}{_counter}"
    name = _unique_name()
    return {
        "employee_name": name,
        "email":         f"emp{slug}@testmail.com",
        "phone_number":  str(_rng.randint(7000000000, 9999999999)),
    }


class TestEmployeeUIGroup1:
    def test_create_smoke(self, emp_page):
        data = _unique_data()
        emp_page.create_record(data)
        emp_page.search_employee(data["employee_name"])
        emp_page.verify_employee_exists(data["employee_name"])


class TestEmployeeUIGroup2:
    def test_form_discard(self, emp_page):
        data = _unique_data()
        emp_page.open_add_form()
        emp_page.page.locator(emp_page.EMPLOYEE_NAME).first.click(force=True)
        emp_page.page.locator(emp_page.EMPLOYEE_NAME).first.fill(data["employee_name"])
        emp_page.close_popup()
        assert not emp_page.is_employee_in_table(data["employee_name"])

    def test_validation_sweep(self, emp_page):
        emp_page.open_add_form()
        emp_page.submit()
        emp_page.handle_validation_alert()
        emp_page.close_popup()


class TestEmployeeUIGroup3:
    def test_listing_and_search(self, emp_page):
        assert emp_page.get_table_row_count() > 0


class TestEmployeeUIGroup4:
    def test_full_row_actions(self, emp_page):
        data = _unique_data()
        emp_page.create_record(data)
        emp_page.search_employee(data["employee_name"])
        emp_page.verify_employee_exists(data["employee_name"])
        emp_page.click_view_button(data["employee_name"])
        emp_page.verify_view_popup_read_only()
        emp_page.close_popup()
        emp_page.search_employee(data["employee_name"])
        emp_page.click_history_button(data["employee_name"])
        assert emp_page.page.locator(".popup-footer").count() > 0
        emp_page.close_popup()
