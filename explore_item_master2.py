import requests
import json
import re
import sys

BASE = 'https://rhythmerp.algorhythms.in'

# Login
r = requests.post(BASE + '/auth/login1/', json={
    'username': 'user@admin.com', 'password': 'Tenant@123456789', 'tenant': '599'
}, headers={'X-Tenant-ID': '599'})
set_cookie = r.headers.get('Set-Cookie', '')
match = re.search(r'refresh_token=([^;]+)', set_cookie)
token = match.group(1) if match else (r.json().get('access') if r.status_code == 200 else None)
print(f'Login OK')

H = {'Authorization': 'Bearer ' + token, 'X-Tenant-ID': '599', 'Content-Type': 'application/json'}

# 1. Get a few more detailed entries to see FK patterns
print('\n' + '='*60)
print('MORE DETAILED ENTRIES')
print('='*60)
r = requests.get(BASE + '/core/dynamic-screen-wrapper/Item%20Master/', headers=H, params={
    'page_number': 1, 'page_size': 10
})
items = r.json().get('screenmatlistingdata_set', [])

for item in items[:5]:
    eid = item.get('id')
    r2 = requests.get(BASE + f'/core/dynamic-screen-wrapper/Item%20Master/{eid}/', headers=H)
    if r2.status_code == 200:
        d = r2.json()
        print(f'\n--- ID={eid}, name="{d.get("name")}" ---')
        print(f'  code: {d.get("code")}')
        print(f'  item_category: {d.get("item_category")}')
        print(f'  item_group: {d.get("item_group")}')
        print(f'  item_type: {d.get("item_type")}')
        print(f'  item_attribute1: {d.get("item_attribute1")}')
        print(f'  item_attribute2: {d.get("item_attribute2")}')
        print(f'  item_attribute3: {d.get("item_attribute3")}')
        print(f'  item_attribute4: {d.get("item_attribute4")}')
        print(f'  item_attribute5: {d.get("item_attribute5")}')
        print(f'  uom: {d.get("uom")}')
        print(f'  hsn_sac_code: {d.get("hsn_sac_code")}')
        print(f'  base_uom: {d.get("base_uom")}')
        print(f'  base_uom_conversion: {d.get("base_uom_conversion")}')
        print(f'  status: {d.get("status")}')
        children = d.get('children', [])
        for c in children:
            sn = c.get('stepper_name', '?')
            print(f'  child[{sn}]: {json.dumps({k:v for k,v in c.items() if k not in ["stepper_name","is_stepper","details","children"]}, indent=2)}')

# 2. Get FK dropdown options via screen schema
print('\n' + '='*60)
print('FK DROPDOWN OPTIONS')
print('='*60)
r = requests.get(BASE + '/core/dynamic-screen/Item%20Master/', headers=H)
schema = r.json()
fields = schema.get('screendefinition_set', [])

def flatten_fields(field_set):
    result = []
    for f in field_set:
        result.append(f)
        if f.get('children'):
            result.extend(flatten_fields(f['children']))
    return result

all_fields = flatten_fields(fields)
for f in all_fields:
    if f.get('field_type_val') == 'dropdown':
        fkey = f.get('field_key')
        flabel = f.get('field_label')
        filter_dd = f.get('filter_dropdown_raw_query', [])
        dd = f.get('dropdown_raw_query', '')
        if isinstance(filter_dd, list) and filter_dd:
            print(f'\n  {fkey} ({flabel}): {len(filter_dd)} options')
            for opt in filter_dd[:10]:
                print(f'    id={opt.get("id")}, key={opt.get("key")}')
            if len(filter_dd) > 10:
                print(f'    ... and {len(filter_dd)-10} more')
        elif dd:
            print(f'\n  {fkey} ({flabel}): raw_query present (length={len(str(dd))})')

# 3. Try to create a test entry to verify the payload format
print('\n' + '='*60)
print('TEST CREATE')
print('='*60)
payload = {
    "id": "",
    "attribute_name": "Item Master",
    "name": "",
    "code": "",
    "description": "API test item",
    "item_category": 66,
    "item_group": 89,
    "item_type": 114,
    "item_attribute1": 122,
    "item_attribute2": 67,
    "item_attribute3": 10,
    "item_attribute4": None,
    "item_attribute5": None,
    "uom": 506,
    "hsn_sac_code": 108,
    "base_uom": 506,
    "base_uom_conversion": "1",
    "status": True,
    "children": [
        {
            "stepper_name": "Additional Details",
            "is_stepper": True,
            "details": [],
            "children": [],
            "is_critical": False,
            "include_wip_in_stock_cal": False,
            "is_packing_material": False
        },
        {
            "stepper_name": "Define Item Master Details",
            "is_stepper": True,
            "details": [],
            "children": [],
            "attachment_type": None,
            "item_attachment": None
        },
        {
            "stepper_name": "Product Order Packeging Details",
            "is_stepper": True,
            "details": [],
            "children": []
        }
    ]
}

r = requests.post(BASE + '/core/dynamic-screen-wrapper/', json=payload, headers=H)
print(f'Status: {r.status_code}')
print(f'Response: {json.dumps(r.json(), indent=2)[:2000]}')
