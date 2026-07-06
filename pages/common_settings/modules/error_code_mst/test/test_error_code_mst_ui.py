import time
from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    generate_valid_error_code_mst_data,
)

_ts = int(time.time() * 1000) % 1000000
_ucounter = 0


def _unique_code():
    global _ucounter
    _ucounter += 1
    return f"EC-{_ts}-{_ucounter:04d}"


class TestErrorCodeMstUI:

    def test_create_smoke(self, ecm_page):
        data = generate_valid_error_code_mst_data()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        assert ecm_page.is_code_in_table(data["code"]), \
            f"Error code '{data['code']}' not found after create"

        data2 = generate_valid_error_code_mst_data()
        data2["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data2)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        assert ecm_page.is_code_in_table(data2["code"]), \
            f"Error code '{data2['code']}' not found after second create"

    def test_form_discard(self, ecm_page):
        code = _unique_code()
        ecm_page.open_add_form()
        ecm_page.page.fill(ecm_page.CODE_INPUT, code)
        ecm_page.close_popup()
        ecm_page.search_record(code)
        assert not ecm_page.is_code_in_table(code), \
            "Cancelled record must not appear in table"

    def test_validation_sweep(self, ecm_page):
        ecm_page.open_add_form()
        ecm_page.submit()
        ecm_page.handle_validation_alert()
        ecm_page.close_popup()

    def test_listing_and_search(self, ecm_page):
        assert ecm_page.get_table_row_count() > 0
        data = generate_valid_error_code_mst_data()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        ecm_page.search_record(data["code"])
        assert ecm_page.is_code_in_table(data["code"]), \
            f"Error code '{data['code']}' must appear in search results"

    def test_duplicate_code_rejected(self, ecm_page):
        existing_code = ecm_page.page.locator("td.cdk-column-code").first.inner_text().strip()
        ecm_page.open_add_form()
        ecm_page.page.fill(ecm_page.CODE_INPUT, existing_code)
        ecm_page.submit()
        ecm_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (ecm_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        ecm_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        ecm_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        ecm_page.close_popup()

    def test_search_nonexistent(self, ecm_page):
        ecm_page.search_record("searchNonexitingCode")
        assert not ecm_page.is_code_in_table("searchNonexitingCode")

    def test_full_row_actions(self, ecm_page):
        data = generate_valid_error_code_mst_data()
        data["code"] = _unique_code()
        ecm_page.open_add_form()
        ecm_page.fill_form(data)
        ecm_page.submit()
        ecm_page.handle_success_alert()
        ecm_page.search_record(data["code"])
        assert ecm_page.is_code_in_table(data["code"])

        ecm_page.click_view_button(data["code"])
        ecm_page.verify_view_popup_read_only()
        ecm_page.close_popup()

        updated_code = _unique_code()
        ecm_page.click_edit_button(data["code"])
        ecm_page.update_code(updated_code)
        ecm_page.click_update()
        ecm_page.handle_success_alert()

        ecm_page.search_record(updated_code)
        ecm_page.click_history_button(updated_code)
        assert ecm_page.page.locator(ecm_page.CHANGE_LOG).count() > 0
        ecm_page.close_popup()
