from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    valid_tax_authority_data,
)


class TestTaxAuthorityUI:

    def test_create_smoke(self, ta_page):
        data = valid_tax_authority_data()
        ta_page.open_add_form()
        ta_page.fill_form(data)
        ta_page.submit()
        ta_page.handle_success_alert()
        ta_page.search_tax_authority(data["tax_name"])
        ta_page.verify_tax_authority_exists(data["tax_name"])

        data2 = valid_tax_authority_data()
        ta_page.open_add_form()
        ta_page.fill_form(data2)
        ta_page.submit()
        ta_page.handle_success_alert()
        ta_page.search_tax_authority(data2["tax_name"])
        ta_page.verify_tax_authority_exists(data2["tax_name"])

    def test_form_discard(self, ta_page):
        data = valid_tax_authority_data()
        ta_page.open_add_form()
        ta_page.page.fill(ta_page.NAME_INPUT, data["tax_name"])
        ta_page.close_popup()
        ta_page.search_tax_authority(data["tax_name"])
        assert not ta_page.is_tax_authority_in_table(data["tax_name"])

    def test_validation_sweep(self, ta_page):
        ta_page.open_add_form()
        ta_page.submit()
        ta_page.handle_validation_alert()
        ta_page.close_popup()

    def test_listing_and_search(self, ta_page):
        assert ta_page.get_table_row_count() > 0
        data = valid_tax_authority_data()
        ta_page.open_add_form()
        ta_page.fill_form(data)
        ta_page.submit()
        ta_page.handle_success_alert()
        ta_page.search_tax_authority(data["tax_name"])
        ta_page.verify_tax_authority_exists(data["tax_name"])

    def test_duplicate_name_rejected(self, ta_page):
        existing_name = ta_page.page.locator("td.cdk-column-tax_name").first.inner_text().strip()
        data = valid_tax_authority_data()
        data["tax_name"] = existing_name
        ta_page.open_add_form()
        ta_page.fill_form(data)
        ta_page.submit()
        ta_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (ta_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        ta_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        ta_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        ta_page.close_popup()

    def test_search_nonexistent(self, ta_page):
        ta_page.search_tax_authority("searchNonexitingName")
        assert not ta_page.is_tax_authority_in_table("searchNonexitingName")

    def test_full_row_actions(self, ta_page):
        data = valid_tax_authority_data()
        ta_page.open_add_form()
        ta_page.fill_form(data)
        ta_page.submit()
        ta_page.handle_success_alert()
        ta_page.search_tax_authority(data["tax_name"])
        ta_page.verify_tax_authority_exists(data["tax_name"])

        ta_page.click_view_button(data["tax_name"])
        ta_page.verify_view_popup_read_only()
        ta_page.close_popup()

        updated_name = valid_tax_authority_data()["tax_name"]
        ta_page.click_edit_button(data["tax_name"])
        ta_page.update_name(updated_name)
        ta_page.click_update()
        ta_page.handle_success_alert()

        ta_page.search_tax_authority(updated_name)
        ta_page.click_history_button(updated_name)
        assert ta_page.page.locator(ta_page.CHANGE_LOG).count() > 0
        ta_page.close_popup()
