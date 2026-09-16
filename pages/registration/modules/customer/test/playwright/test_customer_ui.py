import os
import random
import tempfile
import pytest
import openpyxl
from pages.registration.modules.customer.data.customer_data import (
    generate_company_name,
    generate_email,
    generate_phone_number,
    generate_pan_number,
    generate_address,
    generate_luhn_gstin,
    generate_account_number,
    generate_ifsc_code,
)


def _make_data():
    return {
        # Step 1
        "ownership_status":       "Proprietorship",
        "company_name":           generate_company_name(),
        "sale_type":              "Export",
        "supply_type":            "Both",
        "transaction_currency":   "INR",
        "email":                  generate_email(),
        "phone_number":           generate_phone_number(),
        "pan_number":             generate_pan_number(),
        "contact_person":         "Contact Person",
        "preferred_payment_method": "Cash",
        "tax_registration_status": "Registered",
        "gst_registration_type":  "Regular",
        "payment_terms":          "Immediate",
        "mode_of_delivery":       "Air",
        "delivery_terms":         "Spot",
        "courier_terms":          "Paid",
        # Step 2 — only shipping row needed; billing uses Same as Above
        "address1":               generate_address(),
        # Step 3
        "bank_name":              "HDFC Bank",
        "bank_branch":            "Pune Branch",
        "bank_ifsc":              generate_ifsc_code(),
        "bank_holder":            "Account Holder",
        "bank_account":           generate_account_number(),
        "account_type":           "Saving",
        "bank_proof":             "Cancelled Cheque",
    }


@pytest.mark.smoke
class TestCustomerCreateAndSearch:
    def test_create_search_view(self, customer_page):
        data = _make_data()

        # Create
        customer_page.create_record(data)

        # Search and verify listing
        customer_page.search_customer(data["company_name"])
        customer_page.verify_customer_exists(data["company_name"])

        # View and assert Company Name field
        customer_page.click_view_button(data["company_name"])
        actual = customer_page.page.locator(
            "xpath=//mat-label[contains(.,'Company Name')]"
            "/ancestor::mat-form-field//input"
        ).input_value()
        assert actual == data["company_name"], \
            f"View shows '{actual}', expected '{data['company_name']}'"
        customer_page.force_close_popup()
