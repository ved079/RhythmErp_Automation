import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_IG_MAIN = [
    # Grains
    "Rice Group", "Wheat Group", "Maize Group", "Sorghum Group", "Millet Group",
    "Barley Group", "Oats Group",
    # Pulses
    "Gram Group", "Lentil Group", "Pea Group", "Bean Group", "Soybean Group",
    # Oilseeds
    "Groundnut Group", "Mustard Group", "Sunflower Group", "Sesame Group",
    "Linseed Group", "Castor Group",
    # Cash crops
    "Cotton Group", "Sugarcane Group", "Tobacco Group", "Jute Group",
    # Horticulture
    "Vegetable Group", "Fruit Group", "Spice Group", "Flower Group",
    "Tuber Group", "Leafy Greens Group",
    # Processed
    "Flour Group", "Oil Group", "Feed Group", "Starch Group",
    "Bran Group", "Cake Group",
]

_IG_QUALIFIER = [
    "Kharif", "Rabi", "Summer", "Annual", "Hybrid",
    "Organic", "Export", "Domestic", "Certified", "Traditional",
    "Commercial", "Local", "Premium", "Standard", "Bulk",
]


def _unique_data():
    global _counter
    _counter += 1
    main      = _rng.choice(_IG_MAIN)
    qualifier = _rng.choice(_IG_QUALIFIER)
    name      = f"{main} {qualifier} {_counter}"
    return {
        "item_group":  name,
        "description": f"Automated group entry {_counter}",
    }


class TestIGUIGroup1:
    def test_create_smoke(self, ig_page):
        data = _unique_data()
        ig_page.create_record(data)
        ig_page.search_group(data["item_group"])
        ig_page.verify_group_exists(data["item_group"])


class TestIGUIGroup2:
    def test_form_discard(self, ig_page):
        data = _unique_data()
        ig_page.open_add_form()
        ig_page.page.locator(ig_page.ITEM_GROUP).first.click(force=True)
        ig_page.page.locator(ig_page.ITEM_GROUP).first.fill(data["item_group"])
        ig_page.close_popup()
        assert not ig_page.is_group_in_table(data["item_group"])

    def test_validation_sweep(self, ig_page):
        ig_page.open_add_form()
        ig_page.submit()
        ig_page.handle_validation_alert()
        ig_page.close_popup()


class TestIGUIGroup3:
    def test_listing_and_search(self, ig_page):
        assert ig_page.get_table_row_count() > 0

    def test_search_nonexistent(self, ig_page):
        ig_page.search_group("searchNonexitingCode")
        assert not ig_page.is_group_in_table("searchNonexitingCode")


class TestIGUIGroup4:
    def test_full_row_actions(self, ig_page):
        data = _unique_data()
        ig_page.create_record(data)
        ig_page.search_group(data["item_group"])
        ig_page.verify_group_exists(data["item_group"])

        # View
        ig_page.click_view_button(data["item_group"])
        ig_page.verify_view_popup_read_only()
        ig_page.close_popup()

        # Edit — update description
        ig_page.search_group(data["item_group"])
        ig_page.click_edit_button(data["item_group"])
        ig_page.update_description("Updated description after edit")
        ig_page.click_update()
        ig_page.handle_success_alert()

        # History
        ig_page.search_group(data["item_group"])
        ig_page.click_history_button(data["item_group"])
        assert ig_page.page.locator(".popup-footer").count() > 0
        ig_page.close_popup()


class TestIGUIGroup5:
    def test_duplicate_name_rejected(self, ig_page):
        existing_name = ig_page.page.locator("td.cdk-column-code").first.inner_text().strip()
        data = {"item_group": existing_name, "description": "dup test"}
        ig_page.open_add_form()
        ig_page.fill_form(data)
        ig_page.submit()
        ig_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (ig_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        ig_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        ig_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        ig_page.close_popup()
