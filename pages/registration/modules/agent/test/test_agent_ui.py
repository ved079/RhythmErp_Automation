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
        "agent_name":   name,
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "email":        f"agent{slug}@testmail.com",
        "address":      "405 MG Road Solapur",
        "pin_code":     "411001",
        "bank_name":    "HDFC Bank",
        "bank_branch":  "Mumbai Main Branch",
        "bank_ifsc":    "SBIN0179242",
        "bank_holder":  "Meera Desai",
        "bank_account": str(_rng.randint(100000000000, 999999999999)),
    }


class TestAgentUIGroup1:
    def test_create_smoke(self, agent_page):
        data = _unique_data()
        agent_page.create_record(data)
        agent_page.search_agent(data["agent_name"])
        agent_page.verify_agent_exists(data["agent_name"])


class TestAgentUIGroup2:
    def test_form_discard(self, agent_page):
        data = _unique_data()
        agent_page.open_add_form()
        agent_page.page.locator(agent_page.AGENT_NAME).first.click(force=True)
        agent_page.page.locator(agent_page.AGENT_NAME).first.fill(data["agent_name"])
        agent_page.close_popup()
        assert not agent_page.is_agent_in_table(data["agent_name"])

    def test_validation_sweep(self, agent_page):
        agent_page.open_add_form()
        agent_page.submit()
        agent_page.handle_validation_alert()
        agent_page.close_popup()


class TestAgentUIGroup3:
    def test_listing_and_search(self, agent_page):
        assert agent_page.get_table_row_count() > 0


class TestAgentUIGroup4:
    def test_full_row_actions(self, agent_page):
        data = _unique_data()
        agent_page.create_record(data)
        agent_page.search_agent(data["agent_name"])
        agent_page.verify_agent_exists(data["agent_name"])
        agent_page.click_view_button(data["agent_name"])
        agent_page.verify_view_popup_read_only()
        agent_page.close_popup()
        agent_page.search_agent(data["agent_name"])
        agent_page.click_history_button(data["agent_name"])
        assert agent_page.page.locator(".popup-footer").count() > 0
        agent_page.close_popup()
