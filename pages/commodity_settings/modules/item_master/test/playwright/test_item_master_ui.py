import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)


def _unique_data():
    global _counter
    _counter += 1
    return {
        "description": f"Automated item master entry {_counter}",
    }


class TestIMUIGroup1:
    def test_create_smoke(self, im_page):
        data = _unique_data()
        name = im_page.create_record(data)
        if name:
            im_page.search_item(name)
            im_page.verify_item_exists(name)


class TestIMUIGroup2:
    def test_form_discard(self, im_page):
        im_page.open_add_form()
        im_page.close_popup()

    def test_validation_sweep(self, im_page):
        im_page.open_add_form()
        im_page.submit()
        im_page.handle_validation_alert()
        im_page.close_popup()


class TestIMUIGroup3:
    def test_listing_and_search(self, im_page):
        assert im_page.get_table_row_count() > 0


class TestIMUIGroup4:
    def test_full_row_actions(self, im_page):
        data = _unique_data()
        name = im_page.create_record(data)
        if name:
            im_page.search_item(name)
            im_page.verify_item_exists(name)
        im_page.click_view_button(name or "")
        im_page.verify_view_popup_read_only()
        im_page.close_popup()
        if name:
            im_page.search_item(name)
        im_page.click_history_button(name or "")
        assert im_page.page.locator(".popup-footer").count() > 0
        im_page.close_popup()
