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
    # Format matches ERP validation: F{5d}SE{4d}FTJ{6d}
    cin = f"F{_rng.randint(10000,99999)}SE{_rng.randint(1000,9999)}FTJ{(_ts + _counter) % 900000 + 100000}"
    return {
        "cin_no":   cin,
        "cin_date": "26/01/2026",
    }


class TestConstituentDocumentsUIGroup1:
    def test_create_smoke(self, cd_page):
        data = _unique_data()
        cd_page.create_record(data)
        cd_page.search_document(data["cin_no"])
        cd_page.verify_document_exists(data["cin_no"])


class TestConstituentDocumentsUIGroup2:
    def test_form_discard(self, cd_page):
        data = _unique_data()
        cd_page.open_add_form()
        cd_page.page.locator(cd_page.CIN_NO).first.click(force=True)
        cd_page.page.locator(cd_page.CIN_NO).first.fill(data["cin_no"])
        cd_page.close_popup()
        assert not cd_page.is_document_in_table(data["cin_no"])

    def test_validation_sweep(self, cd_page):
        cd_page.open_add_form()
        cd_page.submit()
        cd_page.handle_validation_alert()
        cd_page.close_popup()


class TestConstituentDocumentsUIGroup3:
    def test_listing_and_search(self, cd_page):
        assert cd_page.get_table_row_count() > 0


class TestConstituentDocumentsUIGroup4:
    def test_full_row_actions(self, cd_page):
        data = _unique_data()
        cd_page.create_record(data)
        cd_page.search_document(data["cin_no"])
        cd_page.verify_document_exists(data["cin_no"])
        cd_page.click_view_button(data["cin_no"])
        cd_page.verify_view_popup_read_only()
        cd_page.close_popup()
        cd_page.search_document(data["cin_no"])
        cd_page.click_history_button(data["cin_no"])
        assert cd_page.page.locator(".popup-footer").count() > 0
        cd_page.close_popup()
