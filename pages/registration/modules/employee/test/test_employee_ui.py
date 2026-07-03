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
    tag = f"{_encode(_ts % 100000)}{_encode(_counter)}".lower()
    return {
        "employee_name": f"Geeta {_encode(_ts % 1000)}{_encode(_counter)}",
        "email":         f"emp{tag}@testmail.com",
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
