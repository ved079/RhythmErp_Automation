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


class TestCMUIGroup4:
    def test_full_row_actions(self, cm_page):
        data = _unique_data()
        cm_page.create_record(data)
        cm_page.search_crop(data["name"])
        cm_page.verify_crop_exists(data["name"])
        cm_page.click_view_button(data["name"])
        cm_page.verify_view_popup_read_only()
        cm_page.close_popup()
        cm_page.search_crop(data["name"])
        cm_page.click_history_button(data["name"])
        assert cm_page.page.locator(".popup-footer").count() > 0
        cm_page.close_popup()
