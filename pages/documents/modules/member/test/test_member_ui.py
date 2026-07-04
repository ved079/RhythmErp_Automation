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
    return f"{_rng.choice(_FIRST_NAMES)} {_rng.choice(_MIDDLE_NAMES)} {_rng.choice(_LAST_NAMES)}"


# ── Verhoeff tables for Aadhaar generation ────────────────
_V_D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],
        [3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
        [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],
        [9,8,7,6,5,4,3,2,1,0]]
_V_P = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],
        [8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
        [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
_V_INV = [0,4,3,2,1,9,8,7,6,5]

def _verhoeff_digit(s):
    c = 0
    for i, n in enumerate(reversed("0" + s)):
        c = _V_D[c][_V_P[i % 8][int(n)]]
    return str(_V_INV[c])

def _aadhaar(counter):
    base = f"{2 + counter % 7}{(counter * 137 + 1000000000) % 10000000000:010d}"
    return base + _verhoeff_digit(base)


def _encode_ts(ts):
    result = ""
    while ts > 0:
        result = chr(ord('A') + (ts % 26)) + result
        ts //= 26
    return result or "A"


_ts_letters = _encode_ts(_ts)


def _unique_data():
    global _counter
    _counter += 1
    return {
        "member_name": _unique_name(),
        "member_address": "Test Address Pune",
        "pan_no": f"ABC{chr(ord('A') + (_ts + _counter) % 26)}{chr(ord('A') + (_ts * 3 + _counter) % 26)}{(_ts + _counter * 7) % 9000 + 1000}F",
        "phone": "9876543210",
        "distinctive_number": str(1000 + _counter),
        "folio_number": f"FOL{_counter:04d}",
        "registration_date": "01/01/2024",
        "date_of_allotment": "01/01/2024",
        "no_class_shares": "10 Class A",
        "amount_paid": "1000",
        "percentage": "10",
        "kyc_number": _aadhaar(_ts + _counter),
    }


class TestMemberUIGroup1:
    def test_create_smoke(self, mb_page):
        data = _unique_data()
        mb_page.create_record(data)
        mb_page.search_member(data["member_name"])
        mb_page.verify_member_exists(data["member_name"])


class TestMemberUIGroup2:
    def test_form_discard(self, mb_page):
        data = _unique_data()
        mb_page.open_add_form()
        mb_page.page.fill(mb_page.NAME_INPUT, data["member_name"])
        mb_page.close_popup()
        assert not mb_page.is_member_in_table(data["member_name"])

    def test_validation_sweep(self, mb_page):
        mb_page.open_add_form()
        mb_page.submit()
        mb_page.handle_validation_alert()
        mb_page.close_popup()


class TestMemberUIGroup3:
    def test_listing_and_search(self, mb_page):
        assert mb_page.get_table_row_count() > 0


class TestMemberUIGroup4:
    def test_full_row_actions(self, mb_page):
        data = _unique_data()
        mb_page.create_record(data)
        mb_page.search_member(data["member_name"])
        mb_page.verify_member_exists(data["member_name"])
        mb_page.click_view_button(data["member_name"])
        mb_page.verify_view_popup_read_only()
        mb_page.close_popup()
        mb_page.search_member(data["member_name"])
        mb_page.click_history_button(data["member_name"])
        assert mb_page.page.locator(".popup-footer").count() > 0
        mb_page.close_popup()
