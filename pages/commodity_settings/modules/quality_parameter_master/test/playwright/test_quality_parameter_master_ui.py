import time
import random

_ts = int(time.time())
_counter = 0
_rng = random.Random(_ts)

_QPM_PARAMS = [
    # Physical parameters
    "Moisture Content", "Bulk Density", "Test Weight", "Grain Size", "Grain Length",
    "Grain Width", "Kernel Weight", "Broken Percentage", "Foreign Matter", "Shrivelled Grain",
    "Immature Grain", "Damaged Grain", "Discoloured Grain", "Chalky Grain", "Weevilled Grain",
    # Chemical parameters
    "Protein Content", "Fat Content", "Fibre Content", "Ash Content", "Starch Content",
    "Gluten Content", "Oil Content", "Fatty Acid Value", "Aflatoxin Level", "Pesticide Residue",
    "Heavy Metal Content", "Moisture Absorption", "Water Activity", "pH Level", "Acidity",
    # Sensory parameters
    "Colour Value", "Texture Score", "Aroma Score", "Taste Score", "Hardness",
    "Particle Size", "Viscosity", "Clarity", "Turbidity", "Brightness",
    # Milling parameters
    "Milling Recovery", "Head Rice Recovery", "Hulling Efficiency", "Whiteness Index",
    "Degree of Milling", "Bran Content", "Polish Degree",
    # Purity parameters
    "Purity Percentage", "Admixture Level", "Weed Seed Count", "Germination Rate",
    "Viability Percentage", "Vigour Index",
]

_QPM_QUALIFIERS = [
    "Index", "Score", "Level", "Value", "Rating",
    "Percentage", "Grade", "Parameter", "Measure", "Standard",
]


def _unique_data():
    global _counter
    _counter += 1
    param     = _rng.choice(_QPM_PARAMS)
    qualifier = _rng.choice(_QPM_QUALIFIERS)
    return {"name": f"{param} {qualifier} {_counter}"}


class TestQPMUIGroup1:
    def test_create_smoke(self, qpm_page):
        data = _unique_data()
        qpm_page.create_record(data)
        qpm_page.search_parameter(data["name"])
        qpm_page.verify_parameter_exists(data["name"])


class TestQPMUIGroup2:
    def test_form_discard(self, qpm_page):
        data = _unique_data()
        qpm_page.open_add_form()
        qpm_page.page.locator(qpm_page.NAME).first.click(force=True)
        qpm_page.page.locator(qpm_page.NAME).first.fill(data["name"])
        qpm_page.close_popup()
        assert not qpm_page.is_parameter_in_table(data["name"])

    def test_validation_sweep(self, qpm_page):
        qpm_page.open_add_form()
        qpm_page.submit()
        qpm_page.handle_validation_alert()
        qpm_page.close_popup()


class TestQPMUIGroup3:
    def test_listing_and_search(self, qpm_page):
        assert qpm_page.get_table_row_count() > 0


class TestQPMUIGroup4:
    def test_full_row_actions(self, qpm_page):
        data = _unique_data()
        qpm_page.create_record(data)
        qpm_page.search_parameter(data["name"])
        qpm_page.verify_parameter_exists(data["name"])
        qpm_page.click_view_button(data["name"])
        qpm_page.verify_view_popup_read_only()
        qpm_page.close_popup()
        qpm_page.search_parameter(data["name"])
        qpm_page.click_history_button(data["name"])
        assert qpm_page.page.locator(".popup-footer").count() > 0
        qpm_page.close_popup()
