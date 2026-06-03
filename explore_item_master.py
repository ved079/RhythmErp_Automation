import requests
import json
import sys

BASE = 'https://rhythmerp.algorhythms.in'

# Login
r = requests.post(BASE + '/auth/login1/', json={
    'username': 'user@admin.com',
    'password': 'Tenant@123456789',
    'tenant': '599'
}, headers={'X-Tenant-ID': '599'})

# Extract token from Set-Cookie or response body
token = None
set_cookie = r.headers.get('Set-Cookie', '')
import re
match = re.search(r'refresh_token=([^;]+)', set_cookie)
if match:
    token = match.group(1)
else:
    data = r.json() if r.status_code == 200 else {}
    token = data.get('access') or data.get('token')

if not token:
    print(f'Login failed: {r.status_code} {r.text[:300]}')
    sys.exit(1)

print(f'Login OK, token: {token[:30]}...')

H = {'Authorization': 'Bearer ' + token, 'X-Tenant-ID': '599', 'Content-Type': 'application/json'}

# 1. Get screen schema
print('\n' + '='*60)
print('SCREEN SCHEMA')
print('='*60)
r = requests.get(BASE + '/core/dynamic-screen/Item%20Master/', headers=H)
if r.status_code == 200:
    schema = r.json()
    print(f'ID: {schema.get("id")}')
    print(f'Attribute: {schema.get("attribute_name")}')
    print(f'Master table: {schema.get("master_table_name")}')
    print(f'Detail table: {schema.get("detail_table_name")}')
    print(f'Sub-detail table: {schema.get("sub_detail_table_name")}')
    fields = schema.get('screendefinition_set', [])
    print(f'\nTotal fields in schema: {len(fields)}')
    for f in fields:
        children = f.get('children', [])
        child_info = f' + {len(children)} children' if children else ''
        print(f'  {f.get("field_key")} ({f.get("field_type_val")}) - {f.get("field_label")} req={f.get("is_required")} grid={f.get("is_grid")} stepper={f.get("is_stepper_name")}{child_info}')
        if children:
            for c in children:
                grandchildren = c.get('children', [])
                gc_info = f' + {len(grandchildren)} children' if grandchildren else ''
                print(f'    -> {c.get("field_key")} ({c.get("field_type_val")}) - {c.get("field_label")} req={c.get("is_required")} grid={c.get("is_grid")}{gc_info}')
                if grandchildren:
                    for gc in grandchildren:
                        print(f'       -> {gc.get("field_key")} ({gc.get("field_type_val")}) - {gc.get("field_label")} req={gc.get("is_required")}')
else:
    print(f'Schema failed: {r.status_code} {r.text[:300]}')

# 2. List existing entries
print('\n' + '='*60)
print('LIST ENTRIES')
print('='*60)
r = requests.get(BASE + '/core/dynamic-screen-wrapper/Item%20Master/', headers=H, params={
    'page_number': 1, 'page_size': 5
})
if r.status_code == 200:
    data = r.json()
    items = data.get('screenmatlistingdata_set', [])
    total = data.get('page_total_records', 0)
    print(f'Total entries: {total}')
    for item in items:
        print(f'  ID={item.get("id")}, name={item.get("name")}, keys={list(item.keys())}')
else:
    print(f'List failed: {r.status_code} {r.text[:300]}')

# 3. Get detailed entry for first item
print('\n' + '='*60)
print('DETAILED ENTRY')
print('='*60)
if items:
    entry_id = items[0].get('id')
    entry_name = items[0].get('name')
    r = requests.get(BASE + f'/core/dynamic-screen-wrapper/Item%20Master/{entry_id}/', headers=H)
    if r.status_code == 200:
        detail = r.json()
        print(f'Entry: {entry_name} (ID: {entry_id})')
        print(f'Top-level keys: {list(detail.keys())}')
        print(f'\nFull detail:')
        print(json.dumps(detail, indent=2)[:8000])
    else:
        print(f'Detail failed: {r.status_code} {r.text[:300]}')
