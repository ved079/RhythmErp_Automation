"""Scan pages/ directory to discover modules, sub-modules, and test functions."""

import ast
import os
import re

from api.models import Module, SubModule, TestFunction, ModuleListResponse


# Map folder names → display names
DISPLAY_NAMES = {
    # Top-level modules
    "login_screens": "Login Screens",
    "access": "Access",
    "access_screen": "Access Screen",
    "company_onboarding": "Company Onboarding",
    "common_settings": "Common Settings",
    "commodity_settings": "Commodity Settings",
    "registration": "Registration",

    # Common Settings sub-modules
    "bank": "Bank",
    "designation": "Designation",
    "error_code_mst": "Error Code Master",
    "hsn_sac": "HSN/SAC",
    "season": "Season",
    "tax_authority": "Tax Authority",
    "tax_rate": "Tax Rate",
    "uom": "UOM",
    "uom_conversion": "UOM Conversion",
    "vehicle_master": "Vehicle Master",

    # Commodity Settings sub-modules
    "crop_master": "Crop Master",
    "item_master": "Item Master",
    "quality_parameter_master": "Quality Parameter Master",
    "services_master": "Services Master",
    "item_category": "Item Category",
    "item_group": "Item Group",
    "commodity_quality_parameter": "Commodity Quality Parameter",
    "commodity_base_rate": "Commodity Base Rate",
    "item_attribute": "Item Attribute",

    # Access sub-modules
    "entity_group_definition": "Entity Group Definition",
    "user_creation_screen": "User Creation",
    "role_creation_screen": "Role Creation",

    # Registration sub-modules
    "agent": "Agent",
    "supplier": "Supplier",
    "customer": "Customer",
    "farmer": "Farmer",
    "member": "Member",

    # Document sub-modules

    # Private (B2B) modules
    "private_b2b": "Private (B2B)",
    "purchase_order": "Purchase Order",
    "goods_receipt_note": "Goods Receipt Note",
    "gate_pass": "Gate Pass",
    "quality_check": "Quality Check",
}

# Curated display names per test function for BA/QA readability.
# Key = exact function name, Value = human-readable description.
# Only functions with non-obvious names need to be listed here;
# the fallback auto-generates from the function name.
FUNCTION_DISPLAY_NAMES: dict[str, str] = {
    # ── Supplier / SP — Create ──
    "test_SP_C01_empty_submit": "Empty Submit",
    "test_SP_C02_create_and_verify": "Create & Verify",
    "test_SP_C03_spaces_only_company_name": "Spaces Only Company Name",
    "test_SP_C03_to_C06_company_name_create_attempts": "Company Name Create Attempts",
    "test_SP_C04_special_chars_company_name": "Special Chars Company Name",
    "test_SP_C05_sql_injection_company_name": "SQL Injection Company Name",
    "test_SP_C06_xss_company_name": "XSS Company Name",
    "test_SP_C07_255_chars_company_name": "255 Chars Company Name",
    "test_SP_C07_C08_company_name_boundary": "Company Name Boundary",
    "test_SP_C08_256_chars_company_name": "256 Chars Company Name",
    "test_SP_C09_invalid_email": "Invalid Email",
    "test_SP_C10_invalid_pan": "Invalid PAN",
    "test_SP_C11_phone_alpha_chars": "Phone Alpha Chars",
    "test_SP_C13_to_C17_all_dropdowns": "All Dropdowns",
    "test_SP_C18_stepper_navigation": "Stepper Navigation",
    "test_SP_C01_C11_C18_form_interactions": "Form Interactions",
    "test_crud_workflow": "CRUD Workflow",
    "test_create_single_supplier": "Create Single Supplier",
    "test_create_supplier_with_partnership": "Create With Partnership",
    "test_create_supplier_inactive": "Create Inactive Supplier",
    # ── Supplier / SP — Edit ──
    "test_SP_E01_E02_edit_prepopulated_and_update": "Edit Prepopulated & Update",
    "test_SP_E03_edit_special_chars": "Edit Special Chars",
    "test_SP_E03_edit_company_name_special_chars": "Edit Company Name Special Chars",
    "test_SP_E04_edit_invalid_email": "Edit Invalid Email",
    # ── Supplier / SP — Search ──
    "test_SP_S01_search_exact": "Search Exact",
    "test_SP_S02_search_partial": "Search Partial",
    "test_SP_S03_search_case_insensitive": "Search Case Insensitive",
    "test_search_validation": "Search Validation",
    "test_list_suppliers": "List Suppliers",
    "test_get_supplier_detail": "Get Supplier Detail",
    "test_discover_supplier_structure": "Discover Supplier Structure",
    # ── Supplier / SP — Duplicate ──
    "test_SP_D01_duplicate_company_name": "Duplicate Company Name",
    "test_SP_D02_duplicate_email": "Duplicate Email",
    "test_SP_D03_duplicate_phone": "Duplicate Phone",
    "test_duplicate_validation": "Duplicate Validation",
    # ── Supplier / SP — Popup ──
    "test_SP_P01_add_form_opens": "Add Form Opens",
    "test_SP_P02_view_readonly": "View Read-Only",
    "test_SP_P03_cancel_closes_popup": "Cancel Closes Popup",
    "test_SP_P04_close_x_closes_popup": "Close X Closes Popup",
    "test_SP_P06_phone_spinner_controls": "Phone Spinner Controls",
    "test_SP_P07_toggle_defaults": "Toggle Defaults",
    "test_popup_workflow": "Popup Workflow",
    # ── Supplier — API Schema ──
    "test_field_validation_rules_has_root_fields": "Field Rules: Root Fields",
    "test_field_validation_rules_has_additional_details": "Field Rules: Additional Details",
    "test_field_validation_rules_has_address_fields": "Field Rules: Address Fields",
    "test_field_validation_rules_has_bank_fields": "Field Rules: Bank Fields",
    "test_pan_pattern_matches_schema": "PAN Pattern Matches Schema",
    "test_ownership_status_has_6_options": "Ownership Status Has 6 Options",
    "test_payment_terms_has_6_options": "Payment Terms Has 6 Options",
    "test_bank_doc_has_3_options": "Bank Doc Has 3 Options",
    "test_pan_is_unique": "PAN Is Unique",
    "test_status_is_required": "Status Is Required",
    "test_default_fk_ids_valid": "Default FK IDs Valid",
    "test_ownership_status_names_complete": "Ownership Status Names Complete",
    "test_bank_doc_names_complete": "Bank Doc Names Complete",
    "test_payment_terms_names_complete": "Payment Terms Names Complete",
    "test_fk_pool_lengths_match_rules": "FK Pool Lengths Match Rules",
    "test_address_type_has_dual_requirement_note": "Address Type: Dual Requirement Note",
    "test_default_fk_ids_has_both_address_types": "Default FK IDs: Both Address Types",
    # ── Supplier — API Payload ──
    "test_payload_has_required_keys": "Payload: Required Keys",
    "test_payload_has_3_children_steppers": "Payload: 3 Children Steppers",
    "test_payload_additional_details_on_stepper": "Payload: Additional Details On Stepper",
    "test_payload_address_in_details_array": "Payload: Address In Details Array",
    "test_payload_shipping_billing_have_different_types": "Payload: Shipping/Billing Different Types",
    "test_payload_both_addresses_share_cascading_chain": "Payload: Both Addresses Share Cascading Chain",
    "test_generate_valid_supplier_data_has_step2_addresses": "Generate Valid Data: Step 2 Addresses",
    "test_payload_bank_in_details_array": "Payload: Bank In Details Array",
    "test_payload_company_name_is_string": "Payload: Company Name Is String",
    "test_payload_email_is_valid_format": "Payload: Email Is Valid Format",
    "test_payload_phone_is_10_digits": "Payload: Phone Is 10 Digits",
    "test_payload_pan_format": "Payload: PAN Format",
    "test_payload_gstin_valid_checksum": "Payload: GSTIN Valid Checksum",
    "test_payload_fk_ids_in_valid_pools": "Payload: FK IDs In Valid Pools",
    "test_payload_status_is_boolean": "Payload: Status Is Boolean",
    "test_build_with_explicit_data": "Build With Explicit Data",
    "test_build_with_fk_overrides": "Build With FK Overrides",
    "test_batch_generates_correct_count": "Batch: Generates Correct Count",
    "test_batch_names_are_unique": "Batch: Names Are Unique",
    "test_batch_emails_are_unique": "Batch: Emails Are Unique",
    "test_batch_pans_are_unique": "Batch: PANs Are Unique",
    # ── Supplier — API Live ──
    "test_supplier_has_3_steppers": "Supplier Has 3 Steppers",
    "test_missing_billing_address_rejected": "Missing Billing Address Rejected",
    "test_missing_shipping_address_rejected": "Missing Shipping Address Rejected",
    # ── Supplier — API Perf ──
    "test_batch_create_5_suppliers": "Batch Create 5 Suppliers",
    "test_payload_generation_speed": "Payload Generation Speed",
    "test_batch_payloads_speed": "Batch Payloads Speed",
}


def _smart_display_name(name: str) -> str:
    """Generate a human-readable display name from a function name.

    - Uses curated FUNCTION_DISPLAY_NAMES if available.
    - Otherwise strips ``test_``, then strips the code prefix (e.g. ``BNK_C01_``)
      — the badge already shows the code. Falls back to replacing underscores
      and capitalising the first letter.
    """
    if name in FUNCTION_DISPLAY_NAMES:
        return FUNCTION_DISPLAY_NAMES[name]
    raw = name[len("test_"):] if name.startswith("test_") else name
    # Strip code prefix like "BNK_C01_" — the badge already displays this
    m = re.match(r'^([A-Z]+_[A-Z]+\d+)_(.+)$', raw)
    if m:
        desc = m.group(2).replace("_", " ")
        return desc[0].upper() + desc[1:] if desc else desc
    display = raw.replace("_", " ")
    return display[0].upper() + display[1:] if display else display


def get_display_name(folder_name: str) -> str:
    """Convert folder name to display name using lookup or smart formatting."""
    if folder_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[folder_name]
    # Fallback: replace underscores, capitalize
    return folder_name.replace("_", " ").title()


def parse_test_functions(file_path: str, test_type: str = "ui") -> list[TestFunction]:
    """Parse a Python file and extract all test functions with docstrings."""
    tests = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                docstring = ast.get_docstring(node)
                tests.append(TestFunction(
                    name=node.name,
                    display_name=_smart_display_name(node.name),
                    docstring=docstring,
                    type=test_type,
                ))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
    return tests


def discover_sub_modules(base_path: str) -> list[SubModule]:
    """Discover sub-modules inside a module folder (like common_settings/modules/)."""
    sub_modules = []

    # Check if this module has a modules/ subfolder (like common_settings/modules/)
    modules_dir = os.path.join(base_path, "modules")
    if os.path.isdir(modules_dir):
        for sub_name in sorted(os.listdir(modules_dir)):
            sub_path = os.path.join(modules_dir, sub_name)
            if not os.path.isdir(sub_path) or sub_name.startswith("_"):
                continue
            test_files = []
            all_tests = []
            # Look for test/ folder or test_*.py files directly
            test_dir = os.path.join(sub_path, "test")
            if os.path.isdir(test_dir):
                # Scan top-level test files (UI tests)
                for tf in sorted(os.listdir(test_dir)):
                    if tf.startswith("test_") and tf.endswith(".py"):
                        test_files.append(tf)
                        all_tests.extend(parse_test_functions(os.path.join(test_dir, tf), test_type="ui"))
                # Scan test/api/ subdirectory (API tests)
                api_dir = os.path.join(test_dir, "api")
                if os.path.isdir(api_dir):
                    for tf in sorted(os.listdir(api_dir)):
                        if tf.startswith("test_") and tf.endswith(".py"):
                            test_files.append(f"api/{tf}")
                            all_tests.extend(parse_test_functions(os.path.join(api_dir, tf), test_type="api"))
            # Also check for test_*.py directly in sub_path
            for tf in sorted(os.listdir(sub_path)):
                if tf.startswith("test_") and tf.endswith(".py") and tf not in test_files:
                    test_files.append(tf)
                    all_tests.extend(parse_test_functions(os.path.join(sub_path, tf)))

            sub_modules.append(SubModule(
                name=sub_name,
                display=get_display_name(sub_name),
                test_files=test_files,
                tests=all_tests,
            ))
    else:
        # No modules/ folder — look for test files directly
        test_files = []
        all_tests = []
        # Check for test/ folder
        test_dir = os.path.join(base_path, "test")
        if os.path.isdir(test_dir):
            for tf in sorted(os.listdir(test_dir)):
                if tf.startswith("test_") and tf.endswith(".py"):
                    test_files.append(tf)
                    all_tests.extend(parse_test_functions(os.path.join(test_dir, tf)))
        # Also check for Test_cases_* pattern (login_screens uses this)
        for item in sorted(os.listdir(base_path)):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item.startswith("Test_cases"):
                for tf in sorted(os.listdir(item_path)):
                    if tf.startswith("test_") and tf.endswith(".py"):
                        test_files.append(tf)
                        all_tests.extend(parse_test_functions(os.path.join(item_path, tf)))
        # Check for test files directly
        for tf in sorted(os.listdir(base_path)):
            if tf.startswith("test_") and tf.endswith(".py") and tf not in test_files:
                test_files.append(tf)
                all_tests.extend(parse_test_functions(os.path.join(base_path, tf)))

        if test_files:
            # The folder itself is the sub-module
            folder_name = os.path.basename(base_path)
            sub_modules.append(SubModule(
                name=folder_name,
                display=get_display_name(folder_name),
                test_files=test_files,
                tests=all_tests,
            ))

    return sub_modules


def discover_all_modules(project_root: str) -> ModuleListResponse:
    """Main entry point — scan pages/ and return all modules with their tests."""
    pages_dir = os.path.join(project_root, "pages")
    modules = []

    if not os.path.isdir(pages_dir):
        return ModuleListResponse(modules=[])

    for folder_name in sorted(os.listdir(pages_dir)):
        folder_path = os.path.join(pages_dir, folder_name)
        if not os.path.isdir(folder_path) or folder_name.startswith("_"):
            continue

        sub_modules = discover_sub_modules(folder_path)
        if sub_modules:
            modules.append(Module(
                name=folder_name,
                display=get_display_name(folder_name),
                sub_modules=sub_modules,
            ))

    return ModuleListResponse(modules=modules)
