import re, os

FILE = os.path.join("pages", "common_settings", "modules", "uom_conversion", "test", "test_uom_conversion_validation.py")
with open(FILE, "r", encoding="utf-8") as f:
    c = f.read()

replacements = 0

# 1) Tests 16-20, 22: common pattern
pattern = re.compile(
    r'            log\.step\(1, "Get fresh pair[^"]*"\)\n'
    r'            page\.navigate_to_page\(\)\n'
    r'            available = page\.get_available_uoms\(\)\n'
    r'            existing = page\.get_existing_pairs\(\)\n'
    r'            data = generate_fresh_pair\(available, existing\)\n'
    r'            page\.navigate_to_page\(\)\n'
    r'            time\.sleep\(1\)\n'
    r'\n'
    r'            page\.open_add_form\(\)\n'
    r'            page\.select_source_uom\(data\["source_uom"\]\)\n'
    r'            page\.select_target_uom\(data\["target_uom"\]\)\n'
    r'            page\.enter_conversion_factor\(data\["conversion_factor"\]\)\n'
    r'            page\.submit\(\)\n'
    r'            assert page\.is_success_alert_present\(timeout=5\), \\\n'
    r'                "Create should succeed for pair: " \+ data\["source_uom"\] \+ " -> " \+ data\["target_uom"\]\n'
    r'            page\.handle_success_alert\(\)\n'
    r'            log\.info\("  Created: " \+ data\["source_uom"\] \+ " -> " \+ data\["target_uom"\](?:\+ " = " \+ data\["conversion_factor"\])?\)'
)
new = (
    '            log.step(1, "Create fresh record via one-flow")\n'
    '            page.navigate_to_page()\n'
    '            data = page.create_fresh_record()\n'
    '            assert page.is_success_alert_present(timeout=5), \\\n'
    '                "Create should succeed for pair: " + data["source_uom"] + " -> " + data["target_uom"]\n'
    '            page.handle_success_alert()\n'
    '            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])'
)
m = pattern.subn(new, c)
c = m[0]
replacements += m[1]
print(f"  Common pattern (Tests 16-20,22): {m[1]} replacements")

# 2) Test 15: unique with is_record_present
old15 = (
    '            log.step(1, "Get fresh pair and create record (or use existing)")\n'
    '            page.navigate_to_page()\n'
    '            available = page.get_available_uoms()\n'
    '            existing = page.get_existing_pairs()\n'
    '            data = generate_fresh_pair(available, existing)\n'
    '            page.navigate_to_page()\n'
    '            time.sleep(1)\n'
    '\n'
    '            if page.is_record_present(data["source_uom"], data["target_uom"]):\n'
    '                log.info("  Pair already exists: " + data["source_uom"] + " -> " + data["target_uom"] + " \u2014 using it directly")\n'
    '            else:\n'
    '                page.open_add_form()\n'
    '                page.select_source_uom(data["source_uom"])\n'
    '                page.select_target_uom(data["target_uom"])\n'
    '                page.enter_conversion_factor(data["conversion_factor"])\n'
    '                page.submit()\n'
    '\n'
    '                if page.is_validation_alert_present(timeout=5):\n'
    '                    page.handle_validation_warning()\n'
    '                    raise AssertionError(\n'
    '                        "Create failed for new pair: " + data["source_uom"] + " -> " + data["target_uom"])\n'
    '\n'
    '                assert page.is_success_alert_present(timeout=5), \\\n'
    '                    "Success alert expected after creating " + data["source_uom"] + " -> " + data["target_uom"]\n'
    '                page.handle_success_alert()\n'
    '                log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"])\n'
    '\n'
    '            log.step(2, "Open Edit form for the record")\n'
    '            page.navigate_to_page()\n'
    '            time.sleep(1)'
)
new15 = (
    '            log.step(1, "Create fresh record via one-flow")\n'
    '            page.navigate_to_page()\n'
    '            data = page.create_fresh_record()\n'
    '\n'
    '            if page.is_validation_alert_present(timeout=5):\n'
    '                page.handle_validation_warning()\n'
    '                raise AssertionError(\n'
    '                    "Create should succeed: " + data["source_uom"] + " -> " + data["target_uom"])\n'
    '\n'
    '            assert page.is_success_alert_present(timeout=5), \\\n'
    '                "Success alert expected after creating " + data["source_uom"] + " -> " + data["target_uom"]\n'
    '            page.handle_success_alert()\n'
    '            log.info("  Created: " + data["source_uom"] + " -> " + data["target_uom"] + " = " + data["conversion_factor"])\n'
    '\n'
    '            log.step(2, "Open Edit form for the record")\n'
    '            page.navigate_to_page()\n'
    '            time.sleep(1)'
)
if old15 in c:
    c = c.replace(old15, new15, 1)
    replacements += 1
    print("  Test 15: 1 replacement")
else:
    print("  Test 15: NOT FOUND (already updated or pattern mismatch)")

# 3) Test 1: unique pattern
old1 = (
    '            log.step(1, "Get fresh pair from live page data")\n'
    '            page.navigate_to_page()\n'
    '            available = page.get_available_uoms()\n'
    '            existing = page.get_existing_pairs()\n'
    '            data = generate_fresh_pair(available, existing)\n'
    '\n'
    '            log.step(2, "Open Add form and fill all fields")\n'
    '            page.open_add_form()\n'
    '\n'
    '            log.step(3, "Fill Source UOM: " + data["source_uom"] + ", Target UOM: " + data["target_uom"] + ", Factor: " + data["conversion_factor"])\n'
    '            page.select_source_uom(data["source_uom"])\n'
    '            page.select_target_uom(data["target_uom"])\n'
    '            page.enter_conversion_factor(data["conversion_factor"])\n'
    '\n'
    '            log.step(4, "Click Submit")\n'
    '            page.submit()'
)
new1 = (
    '            log.step(1, "Create fresh record via one-flow")\n'
    '            page.navigate_to_page()\n'
    '            data = page.create_fresh_record()'
)
if old1 in c:
    c = c.replace(old1, new1, 1)
    replacements += 1
    print("  Test 1 create block: 1 replacement")
else:
    print("  Test 1 create block: NOT FOUND")

# 4) Renumber Test 1 step 5 -> step 2
if '            log.step(5, "Verify success alert")' in c:
    c = c.replace('            log.step(5, "Verify success alert")', '            log.step(2, "Verify success alert")', 1)
    replacements += 1
    print("  Test 1 step renumber: 1 replacement")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(c)

print(f"\nTotal: {replacements} replacements done!")
print(f"Remaining get_available_uoms calls: {c.count('get_available_uoms')}")
print(f"Remaining generate_fresh_pair calls: {c.count('generate_fresh_pair')}")
print(f"create_fresh_record calls: {c.count('create_fresh_record')}")
