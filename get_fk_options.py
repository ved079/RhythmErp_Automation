import requests
import json
import re

BASE = 'https://rhythmerp.algorhythms.in'
r = requests.post(BASE + '/auth/login1/', json={
    'username': 'user@admin.com', 'password': 'Tenant@123456789', 'tenant': '599'
}, headers={'X-Tenant-ID': '599'})
match = re.search(r'refresh_token=([^;]+)', r.headers.get('Set-Cookie', ''))
token = match.group(1) if match else r.json().get('access')
print(f'Login OK')

H = {'Authorization': 'Bearer ' + token, 'X-Tenant-ID': '599'}

# Get full schema with all dropdown options
r = requests.get(BASE + '/core/dynamic-screen/Item%20Master/', headers=H)
schema = r.json()

def flatten_fields(field_set):
    result = []
    for f in field_set:
        result.append(f)
        if f.get('children'):
            result.extend(flatten_fields(f['children']))
    return result

all_fields = flatten_fields(schema.get('screendefinition_set', []))

print('# Full FK Dropdown Options for Item Master')
print('# Generated from live ERP API')
print()

for f in all_fields:
    if f.get('field_type_val') == 'dropdown':
        fkey = f.get('field_key')
        flabel = f.get('field_label', '').strip()
        options = f.get('filter_dropdown_raw_query', [])
        if isinstance(options, list) and options:
            print(f'# {fkey} ({flabel}) — {len(options)} options')
            print(f'{fkey.upper().replace(" ", "_")}_OPTIONS = {{')
            for opt in options:
                key = opt.get('key', '')
                oid = opt.get('id')
                print(f'    "{key}": {oid},')
            print('}')
            print()
