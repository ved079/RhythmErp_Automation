import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_CROPS = [
    # Cereals
    "Paddy", "Wheat", "Maize", "Sorghum", "Bajra", "Barley", "Ragi",
    "Jowar", "Triticale", "Oats", "Buckwheat", "Quinoa",
    # Millets
    "Foxtail Millet", "Kodo Millet", "Proso Millet", "Little Millet",
    "Barnyard Millet", "Brown Top Millet",
    # Pulses
    "Chickpea", "Pigeon Pea", "Green Gram", "Black Gram", "Lentil",
    "Kidney Bean", "Cowpea", "Horse Gram", "Moth Bean", "Field Pea",
    # Oilseeds
    "Groundnut", "Soybean", "Mustard", "Sunflower", "Sesame",
    "Linseed", "Castor", "Safflower", "Niger", "Rapeseed",
    # Cash crops
    "Cotton", "Sugarcane", "Jute", "Tobacco", "Rubber",
    # Horticulture
    "Tomato", "Potato", "Onion", "Garlic", "Ginger",
    "Turmeric", "Chilli", "Coriander", "Cumin", "Fenugreek",
    "Banana", "Mango", "Papaya", "Guava", "Pomegranate",
    # Plantation
    "Coconut", "Arecanut", "Coffee", "Tea", "Cardamom",
    "Pepper", "Vanilla", "Cashew",
]

_QUALIFIERS = [
    "Kharif", "Rabi", "Summer", "Zaid", "Annual",
    "Perennial", "Hybrid", "Desi", "HYV", "OPV",
    "Irrigated", "Rainfed", "Organic", "Traditional", "Improved",
]


def _unique_data():
    global _counter
    _counter += 1
    crop      = _rng.choice(_CROPS)
    qualifier = _rng.choice(_QUALIFIERS)
    return {"name": f"{crop} {qualifier} {_counter}"}


class TestCMUIGroup1:
    def test_create_smoke(self, cm_page):
        data = _unique_data()
        cm_page.create_record(data)
        cm_page.search_crop(data["name"])
        cm_page.verify_crop_exists(data["name"])


class TestCMUIGroup2:
    def test_form_discard(self, cm_page):
        data = _unique_data()
        cm_page.open_add_form()
        cm_page.page.locator(cm_page.NAME).first.click(force=True)
        cm_page.page.locator(cm_page.NAME).first.fill(data["name"])
        cm_page.close_popup()
        assert not cm_page.is_crop_in_table(data["name"])

    def test_validation_sweep(self, cm_page):
        cm_page.open_add_form()
        cm_page.submit()
        cm_page.handle_validation_alert()
        cm_page.close_popup()


class TestCMUIGroup3:
    def test_listing_and_search(self, cm_page):
        assert cm_page.get_table_row_count() > 0

    def test_search_nonexistent(self, cm_page):
        cm_page.search_crop("searchNonexitingCode")
        assert not cm_page.is_crop_in_table("searchNonexitingCode")


class TestCMUIGroup4:
    def test_full_row_actions(self, cm_page):
        data = _unique_data()
        cm_page.create_record(data)
        cm_page.search_crop(data["name"])
        cm_page.verify_crop_exists(data["name"])

        # View
        cm_page.click_view_button(data["name"])
        cm_page.verify_view_popup_read_only()
        cm_page.close_popup()

        # Edit — update name
        cm_page.search_crop(data["name"])
        updated_name = data["name"] + " Edited"
        cm_page.click_edit_button(data["name"])
        cm_page.update_name(updated_name)
        cm_page.click_update()
        cm_page.handle_success_alert()
        cm_page.navigate_to_page()

        # History
        cm_page.search_crop(updated_name)
        cm_page.click_history_button(updated_name)
        assert cm_page.page.locator(".popup-footer").count() > 0
        cm_page.close_popup()


class TestCMUIGroup5:
    def test_duplicate_name_rejected(self, cm_page):
        existing_name = cm_page.page.locator("td.cdk-column-name").first.inner_text().strip()
        cm_page.open_add_form()
        cm_page.fill_form({"name": existing_name})
        cm_page.submit()
        cm_page.page.wait_for_selector(".swal2-container", timeout=5000)
        title = (cm_page.page.locator("#swal2-title").text_content() or "").strip().lower()
        assert any(w in title for w in ("validation", "already", "exists", "duplicate", "error")), \
            f"Expected duplicate rejection alert, got: '{title}'"
        cm_page.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        cm_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        cm_page.close_popup()
