import pytest
from pages.commodity_settings.modules.item_attribute.ia_playwright_page import IAPlaywrightPage
from pages.commodity_settings.modules.item_attribute.test.playwright._ia_names import _unique_data as _ud
_unique_data = lambda: _ud(attr_num=3)


@pytest.fixture(scope="function")
def ia_page(logged_in_page):
    p = IAPlaywrightPage(logged_in_page, attr_num=3)
    p.navigate_to_page()
    yield p
    try:
        p.force_close_popup()
    except Exception:
        pass


class TestIA3UIGroup1:
    def test_create_smoke(self, ia_page):
        data = _unique_data()
        ia_page.create_record(data)
        ia_page.search_attribute(data["name"])
        ia_page.verify_attribute_exists(data["name"])


class TestIA3UIGroup2:
    def test_form_discard(self, ia_page):
        data = _unique_data()
        ia_page.open_add_form()
        ia_page.page.locator(ia_page.NAME).first.click(force=True)
        ia_page.page.locator(ia_page.NAME).first.fill(data["name"])
        ia_page.close_popup()
        assert not ia_page.is_attribute_in_table(data["name"])

    def test_validation_sweep(self, ia_page):
        ia_page.open_add_form()
        ia_page.submit()
        ia_page.handle_validation_alert()
        ia_page.close_popup()


class TestIA3UIGroup3:
    def test_listing_and_search(self, ia_page):
        assert ia_page.get_table_row_count() > 0


class TestIA3UIGroup4:
    def test_full_row_actions(self, ia_page):
        data = _unique_data()
        ia_page.create_record(data)
        ia_page.search_attribute(data["name"])
        ia_page.verify_attribute_exists(data["name"])
        ia_page.click_view_button(data["name"])
        ia_page.verify_view_popup_read_only()
        ia_page.close_popup()
        ia_page.search_attribute(data["name"])
        ia_page.click_history_button(data["name"])
        assert ia_page.page.locator(".popup-footer").count() > 0
        ia_page.close_popup()
