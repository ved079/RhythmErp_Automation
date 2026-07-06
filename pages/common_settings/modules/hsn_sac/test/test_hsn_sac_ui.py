from pages.common_settings.modules.hsn_sac.data.hsn_sac_data import generate_valid_hsn_sac_data


class TestHsnSacUI:

    def test_create_smoke(self, hsn_page):
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        found = hsn_page.is_hsn_in_table(data["hsn_sac_number"])
        assert found, f"HSN SAC '{data['hsn_sac_number']}' not found in table after create"

    def test_validation_sweep(self, hsn_page):
        hsn_page.open_add_form()
        hsn_page.submit()
        hsn_page.handle_validation_alert()
        hsn_page.close_popup()

    def test_listing_and_search(self, hsn_page):
        assert hsn_page.get_table_row_count() > 0
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.verify_hsn_exists(data["hsn_sac_number"])

    def test_duplicate_number_rejected(self, hsn_page):
        existing_no = hsn_page.page.locator("td.cdk-column-hsn_sac_no").first.inner_text().strip()
        hsn_page.open_add_form()
        hsn_page.page.fill(hsn_page.NUMBER_INPUT, existing_no)
        hsn_page.submit()
        hsn_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (hsn_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        hsn_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        hsn_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        hsn_page.close_popup()

    def test_search_nonexistent(self, hsn_page):
        hsn_page.search_hsn_sac("searchNonexitingCode")
        assert not hsn_page.is_hsn_in_table("searchNonexitingCode")

    def test_full_row_actions(self, hsn_page):
        data = generate_valid_hsn_sac_data()
        hsn_page.open_add_form()
        hsn_page.fill_form(data)
        hsn_page.submit()
        hsn_page.handle_success_alert()
        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.verify_hsn_exists(data["hsn_sac_number"])

        hsn_page.click_view_button(data["hsn_sac_number"])
        hsn_page.verify_view_popup_read_only()
        hsn_page.close_popup()

        hsn_page.click_edit_button(data["hsn_sac_number"])
        hsn_page.update_description("Updated description by automation")
        hsn_page.click_update()
        hsn_page.handle_success_alert()

        hsn_page.search_hsn_sac(data["hsn_sac_number"])
        hsn_page.click_history_button(data["hsn_sac_number"])
        assert hsn_page.page.locator(hsn_page.CHANGE_LOG).count() > 0
        hsn_page.close_popup()
