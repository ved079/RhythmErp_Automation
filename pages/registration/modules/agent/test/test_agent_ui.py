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
        "agent_name":   f"Rajesh {_encode(_ts % 1000)}{_encode(_counter)}",
        "phone_number": str(_rng.randint(7000000000, 9999999999)),
        "email":        f"agent{tag}@testmail.com",
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
