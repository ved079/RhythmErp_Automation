"""Scan pages/ directory to discover modules, sub-modules, and test functions."""

import ast
import os
from typing import Optional

from api.models import Module, SubModule, TestFunction, ModuleListResponse


# Map folder names → display names
DISPLAY_NAMES = {
    "login_screens": "Login Screens",
    "access_screen": "Access Screen",
    "company_onboarding": "Company Onboarding",
    "common_settings": "Common Settings",
    "commodity_settings": "Commodity Settings",
    "designation": "Designation",
    "bank": "Bank",
    "error_code_mst": "Error Code Master",
    "hsn_sac": "HSN/SAC",
    "season": "Season",
    "tax_authority": "Tax Authority",
    "tax_rate": "Tax Rate",
    "uom": "UOM",
    "uom_conversion": "UOM Conversion",
    "vehicle_master": "Vehicle Master",
    "crop_master": "Crop Master",
    "item_master": "Item Master",
    "quality_parameter_master": "Quality Parameter Master",
}


def get_display_name(folder_name: str) -> str:
    """Convert folder name to display name using lookup or smart formatting."""
    if folder_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[folder_name]
    # Fallback: replace underscores, capitalize
    return folder_name.replace("_", " ").title()


def parse_test_functions(file_path: str) -> list[TestFunction]:
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
                    display_name=node.name.replace("test_", "").replace("_", " ").title(),
                    docstring=docstring,
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
                for tf in sorted(os.listdir(test_dir)):
                    if tf.startswith("test_") and tf.endswith(".py"):
                        test_files.append(tf)
                        all_tests.extend(parse_test_functions(os.path.join(test_dir, tf)))
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