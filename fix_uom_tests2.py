import re

FILE = "pages/common_settings/modules/uom_conversion/test/test_uom_conversion_validation.py"
with open(FILE, "r", encoding="utf-8") as f:
    c = f.read()

replacements = 0

# === Fix Test 1 (lines 53-70) ===
old1 = '''            log.step(1, "Get fresh pair from live page data")
            page.navigate_to_page()
            available = page.get_available_uoms()
            existing = page.get_existing_pairs()
            data = generate_fresh_pair(available, existing)
            page.navigate_to_page()
            time.sleep(1)

            log.step(2, "Open Add form and fill all fields")
            page.open_add_form()

            log.step(3, "Fill Source UOM: " + data["source_uom"] + ", Target UOM: " + data["target_uom"] + ", Factor: " + data["conversion_factor"])
            page.select_source_uom(data["source_uom"])
            page.select_target_uom(data["target_uom"])
            page.enter_conversion_factor(data["conversion_factor"])

            log.step(4, "Click Submit")
            page.submit()'''

new1 = '''            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()'''

if old1 in c:
    c = c.replace(old1, new1, 1)
    replacements += 1
    print("Test 1: replaced")
else:
    print("Test 1: NOT FOUND")

# === Fix Test 18 (lines 767-783) ===
old18 = '''            log.step(1, "Get fresh pair and create record to edit-cancel")
            page.navigate_to_page()
            available = page.get_available_uoms()
            existing = page.get_existing_pairs()
            data = generate_fresh_pair(available, existing)
            page.navigate_to_page()
            time.sleep(1)

            page.open_add_form()
            page.select_source_uom(data["source_uom"])
            page.select_target_uom(data["target_uom"])
            page.enter_conversion_factor(data["conversion_factor"])
            page.submit()
            assert page.is_success_alert_present(timeout=5), \\
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")'''

new18 = '''            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \\
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")'''

if old18 in c:
    c = c.replace(old18, new18, 1)
    replacements += 1
    print("Test 18: replaced")
else:
    print("Test 18: NOT FOUND")

# === Fix Test 22 (lines 948-964) ===
old22 = '''            log.step(1, "Get fresh pair and create record to edit-cancel")
            page.navigate_to_page()
            available = page.get_available_uoms()
            existing = page.get_existing_pairs()
            data = generate_fresh_pair(available, existing)
            page.navigate_to_page()
            time.sleep(1)

            page.open_add_form()
            page.select_source_uom(data["source_uom"])
            page.select_target_uom(data["target_uom"])
            page.enter_conversion_factor(data["conversion_factor"])
            page.submit()
            assert page.is_success_alert_present(timeout=5), \\
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")'''

new22 = '''            log.step(1, "Create fresh record via one-flow")
            page.navigate_to_page()
            data = page.create_fresh_record()
            assert page.is_success_alert_present(timeout=5), \\
                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]
            page.handle_success_alert()
            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])

            log.step(2, "Read original factor from table")'''

if old22 in c:
    c = c.replace(old22, new22, 1)
    replacements += 1
    print("Test 22: replaced")
else:
    print("Test 22: NOT FOUND")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(c)

print(f"\nTotal: {replacements} replacements")
print(f"Remaining get_available_uoms: {c.count('get_available_uoms') - 1}")  # -1 for page object import
print(f"Remaining generate_fresh_pair in tests: {c.count('generate_fresh_pair') - 1}")  # -1 for import line
print(f"create_fresh_record calls: {c.count('create_fresh_record')}")
