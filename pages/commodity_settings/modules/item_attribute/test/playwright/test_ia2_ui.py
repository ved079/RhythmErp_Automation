import pytest
from pages.commodity_settings.modules.item_attribute.ia_playwright_page import IAPlaywrightPage
from pages.commodity_settings.modules.item_attribute.test.playwright._ia_names import _unique_data as _ud
_unique_data = lambda: _ud(attr_num=2)


@pytest.fixture(scope="function")
def ia_page(logged_in_page):
    p = IAPlaywrightPage(logged_in_page, attr_num=2)
    p.navigate_to_page()
    yield p
    try:
        p.close_popup()
    except Exception:
        pass


class TestIA2UIGroup1:
    def test_create_smoke(self, ia_page):
        data = _unique_data()
        ia_page.create_record(data)
        ia_page.search_attribute(data["name"])
        ia_page.verify_attribute_exists(data["name"])


class TestIA2UIGroup2:
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


class TestIA2UIGroup3:
    def test_listing_and_search(self, ia_page):
        assert ia_page.get_table_row_count() > 0


class TestIA2UIGroup5:
    def test_duplicate_name_rejected(self, ia_page):
        existing_name = ia_page.page.locator("td.cdk-column-name").first.inner_text().strip()
        data = {"name": existing_name, "description": "dup test"}
        ia_page.open_add_form()
        ia_page.fill_form(data)
        ia_page.submit()
        ia_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (ia_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        ia_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        ia_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        ia_page.close_popup()

    def test_search_nonexistent(self, ia_page):
        ia_page.search_attribute("searchNonexitingName")
        assert not ia_page.is_attribute_in_table("searchNonexitingName")


class TestIA2UIGroup4:
    def test_full_row_actions(self, ia_page):
        data = _unique_data()
        ia_page.create_record(data)
        ia_page.search_attribute(data["name"])
        ia_page.verify_attribute_exists(data["name"])

        # View
        ia_page.click_view_button(data["name"])
        ia_page.verify_view_popup_read_only()
        ia_page.close_popup()

        # Edit — update description
        ia_page.search_attribute(data["name"])
        ia_page.click_edit_button(data["name"])
        ia_page.update_description("Updated desc after edit")
        ia_page.click_update()
        ia_page.handle_success_alert()

        # History
        ia_page.search_attribute(data["name"])
        ia_page.click_history_button(data["name"])
        assert ia_page.page.locator(".popup-footer").count() > 0
        ia_page.close_popup()
