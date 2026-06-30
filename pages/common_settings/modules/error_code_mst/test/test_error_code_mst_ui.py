import time
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_valid_error_code_mst_data,
    generate_create_without_description,
)


_ts = int(time.time() * 1000) % 1000000
_ucounter = 0


def _unique_code():
    global _ucounter
    _ucounter += 1
    return f"EC-{_ts}-{_ucounter:04d}"


class TestErrorCodeMstUI:

    def test_validation_sweep(self, ecm_page):
        ecm_page.open_add_form()
        ecm_page.submit()
        ecm_page.handle_validation_alert()
        ecm_page.close_popup()

    def test_form_discard(self, ecm_page):
        code = _unique_code()
        ecm_page.open_add_form()
        ecm_page.page.fill(ecm_page.CODE_INPUT, code)
        ecm_page.close_popup()
        ecm_page.search_record(code)
        assert not ecm_page.is_code_in_table(code), \
            "Cancelled record must not appear in table"

    def test_create_smoke(self, ecm_page):
        data = generate_valid_error_code_mst_data()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        found = ecm_page.is_code_in_table(data["code"])
        assert found, f"Error code '{data['code']}' not found in table after create"

    def test_listing_and_search(self, ecm_page):
        data = generate_valid_error_code_mst_data()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        ecm_page.search_record(data["code"])
        assert ecm_page.is_code_in_table(data["code"]), \
            f"Error code '{data['code']}' must appear in search results"

    def test_description_is_optional(self, ecm_page):
        data = generate_create_without_description()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        found = ecm_page.is_code_in_table(data["code"])
        assert found, f"Error code '{data['code']}' not found in table after create (no description)"
