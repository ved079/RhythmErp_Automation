import time
from pages.common_settings.modules.bank.data.bank_data import generate_valid_bank_data

# bank_name must be alpha-only — encode timestamp as letters to ensure uniqueness across runs
_ts = int(time.time())


def _encode_ts(ts):
    result = ""
    while ts > 0:
        result = chr(ord('A') + (ts % 26)) + result
        ts //= 26
    return result


_ts_letters = _encode_ts(_ts)
_counter = 0


def _unique_data():
    global _counter
    _counter += 1
    data = generate_valid_bank_data()
    suffix = f"{_ts_letters}{_encode_ts(_counter)}"
    base = data["bank_name"].rstrip()
    data["bank_name"] = (base[:20] + suffix)[:255]
    return data


class TestBankUI:

    def test_create_smoke(self, bank_page):
        data = _unique_data()
        bank_page.open_add_form()
        bank_page.fill_form(data)
        bank_page.submit()
        bank_page.handle_success_alert()
        bank_page.go_to_first_page()
        bank_page.verify_bank_exists(data["bank_name"])

        data2 = _unique_data()
        bank_page.open_add_form()
        bank_page.fill_form(data2)
        bank_page.submit()
        bank_page.handle_success_alert()
        bank_page.go_to_first_page()
        bank_page.verify_bank_exists(data2["bank_name"])

    def test_form_discard(self, bank_page):
        data = _unique_data()
        bank_page.open_add_form()
        bank_page.page.fill(bank_page.NAME_INPUT, data["bank_name"])
        bank_page.close_popup()
        bank_page.go_to_first_page()
        assert not bank_page.is_bank_in_table(data["bank_name"])

    def test_validation_sweep(self, bank_page):
        bank_page.open_add_form()
        bank_page.submit()
        bank_page.handle_validation_alert()
        bank_page.close_popup()

    def test_listing_and_search(self, bank_page):
        assert bank_page.get_table_row_count() > 0
        data = _unique_data()
        bank_page.open_add_form()
        bank_page.fill_form(data)
        bank_page.submit()
        bank_page.handle_success_alert()
        bank_page.go_to_first_page()
        bank_page.verify_bank_exists(data["bank_name"])

    def test_full_row_actions(self, bank_page):
        data = _unique_data()
        bank_page.open_add_form()
        bank_page.fill_form(data)
        bank_page.submit()
        bank_page.handle_success_alert()
        bank_page.go_to_first_page()
        bank_page.verify_bank_exists(data["bank_name"])

        bank_page.click_view_button(data["bank_name"])
        bank_page.verify_view_popup_read_only()
        bank_page.close_popup()

        updated_name = (data["bank_name"][:18] + _encode_ts(_counter) + "UP")[:255]
        bank_page.click_edit_button(data["bank_name"])
        bank_page.update_name(updated_name)
        bank_page.click_update()
        bank_page.handle_success_alert()
        bank_page.go_to_first_page()
        bank_page.verify_bank_exists(updated_name)

        bank_page.click_history_button(updated_name)
        assert bank_page.page.locator(".popup-footer").count() > 0
        bank_page.close_popup()
