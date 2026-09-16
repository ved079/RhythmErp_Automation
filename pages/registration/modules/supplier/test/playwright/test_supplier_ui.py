import pytest
from pages.registration.modules.supplier.data.supplier_data import (
    generate_company_name,
    generate_email,
    generate_phone,
    generate_pan,
    generate_address,
    generate_registration_number,
    generate_ifsc,
    generate_account_number,
    generate_contact_person,
)


def _make_data():
    return {
        "ownership_status": "Proprietorship",
        "company_name":     generate_company_name(),
        "po_type":          "Domestic",
        "email":            generate_email(),
        "phone_number":     generate_phone(),
        "default_currency": "INR",
        "pan_number":       generate_pan(),
        "contact_person":   generate_contact_person(),
        "tax_reg_status":   "Registered",
        "gst_reg_type":     "Regular",
        "state":            "Maharashtra",
        "address":          generate_address(),
        "registration_number": generate_registration_number(),
        "bank_name":        "HDFC Bank",
        "bank_branch":      "Pune Branch",
        "bank_ifsc":        generate_ifsc(),
        "account_type":     "Saving",
        "bank_holder":      generate_contact_person(),
        "bank_account":     generate_account_number(),
        "bank_proof":       "Passbook",
    }


@pytest.mark.smoke
class TestSupplierCreateAndSearch:
    def test_create_and_search(self, supplier_page):
        data = _make_data()
        supplier_page.create_record(data)
        supplier_page.search_supplier(data["company_name"])
        supplier_page.verify_supplier_exists(data["company_name"])


@pytest.mark.validation
class TestSupplierSubmitExistingPan:
    def test_submit_existing_pan(self, supplier_page):
        existing_pan = supplier_page.get_first_supplier_pan()
        data = _make_data()
        data["pan_number"] = existing_pan
        supplier_page.open_add_form()
        supplier_page.fill_form(data)
        supplier_page.submit()
        supplier_page.page.wait_for_selector(".swal2-container", timeout=10000)
        assert supplier_page.page.locator(".swal2-title").text_content().strip() == "Validation Failed"
        supplier_page.page.evaluate("document.querySelector('.swal2-cancel')?.click()")
        supplier_page.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)


@pytest.mark.regression
class TestSupplierEditAndHistory:
    def test_create_edit_view_history(self, supplier_page):
        data = _make_data()

        # 1. Create
        supplier_page.create_record(data)
        supplier_page.search_supplier(data["company_name"])
        supplier_page.verify_supplier_exists(data["company_name"])

        # 2. History after create — must be empty
        history_before = supplier_page.get_history_entry_count(data["company_name"])
        assert history_before == 0, f"Expected empty history after create, got {history_before} rows"

        # 3. Edit contact person
        updated_contact = "Updated Contact Person"
        supplier_page.edit_field_and_update(data["company_name"], "Contact Person Name", updated_contact)
        supplier_page.search_supplier(data["company_name"])

        # 4. View — field must reflect the update
        actual = supplier_page.get_view_field_value(data["company_name"], "Contact Person Name")
        assert actual == updated_contact, f"Expected '{updated_contact}', got '{actual}'"

        # 5. History after edit — must have at least one entry
        history_after = supplier_page.get_history_entry_count(data["company_name"])
        assert history_after > 0, "Expected history entries after edit, got none"
