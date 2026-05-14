FILE = 'pages/common_settings/modules/uom_conversion/uom_conversion_page.py'
with open(FILE, 'r', encoding='utf-8') as f:
    c = f.read()

old = '''        # Fill factor and submit
        self.enter_conversion_factor(factor)
        self.submit()
        return {"source_uom": source, "target_uom": target, "conversion_factor": factor}'''

new = '''        # Fill factor and submit
        self.enter_conversion_factor(factor)
        self.submit()

        # Handle SweetAlert that appears after submit
        time.sleep(1)
        title = self.get_swal_title()
        if title and 'success' in title.lower():
            self.handle_success_alert()
            log.info("Record created successfully: " + source + " -> " + target)
        elif title:
            self.close_popup()
            raise RuntimeError("Submit failed: " + title)

        return {"source_uom": source, "target_uom": target, "conversion_factor": factor}'''

if old in c:
    c = c.replace(old, new, 1)
    print('create_fresh_record: now handles success alert internally')
else:
    print('NOT FOUND')

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(c)
