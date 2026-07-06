from pages.common_settings.modules.season.data.season_data import (
    valid_season_with_description,
    valid_season_name_only,
)


class TestSeasonUI:

    def test_create_smoke(self, season_page):
        data = valid_season_with_description()
        season_page.open_add_form()
        season_page.fill_form(data)
        season_page.submit()
        season_page.handle_success_alert()
        season_page.search_season(data["Name"])
        season_page.verify_season_exists(data["Name"])

        data2 = valid_season_name_only()
        season_page.open_add_form()
        season_page.page.fill(season_page.NAME_INPUT, data2["Name"])
        season_page.submit()
        season_page.handle_success_alert()
        season_page.search_season(data2["Name"])
        season_page.verify_season_exists(data2["Name"])

    def test_form_discard(self, season_page):
        data = valid_season_with_description()
        season_page.open_add_form()
        season_page.fill_form(data)
        season_page.close_popup()
        season_page.search_season(data["Name"])
        assert not season_page.is_season_in_table(data["Name"])

    def test_validation_sweep(self, season_page):
        season_page.open_add_form()
        season_page.submit()
        season_page.handle_validation_alert()
        season_page.close_popup()

    def test_listing_and_search(self, season_page):
        assert season_page.get_table_row_count() > 0
        data = valid_season_with_description()
        season_page.open_add_form()
        season_page.fill_form(data)
        season_page.submit()
        season_page.handle_success_alert()
        season_page.search_season(data["Name"])
        season_page.verify_season_exists(data["Name"])

    def test_duplicate_name_rejected(self, season_page):
        existing_name = season_page.page.locator("td.cdk-column-name").first.inner_text().strip()
        season_page.open_add_form()
        season_page.page.fill(season_page.NAME_INPUT, existing_name)
        season_page.submit()
        season_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (season_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        season_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        season_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        season_page.close_popup()

    def test_search_nonexistent(self, season_page):
        season_page.search_season("searchNonexitingName")
        assert not season_page.is_season_in_table("searchNonexitingName")

    def test_full_row_actions(self, season_page):
        data = valid_season_with_description()
        season_page.open_add_form()
        season_page.fill_form(data)
        season_page.submit()
        season_page.handle_success_alert()
        season_page.search_season(data["Name"])
        season_page.verify_season_exists(data["Name"])

        season_page.click_view_button(data["Name"])
        season_page.verify_view_popup_read_only()
        season_page.close_popup()

        updated_name = data["Name"] + "UPD"
        season_page.click_edit_button(data["Name"])
        season_page.update_name(updated_name)
        season_page.click_update()
        season_page.handle_success_alert()

        season_page.search_season(updated_name)
        season_page.click_history_button(updated_name)
        assert season_page.page.locator(season_page.CHANGE_LOG).count() > 0
        season_page.close_popup()
