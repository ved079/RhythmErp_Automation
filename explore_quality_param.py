import requests
import json

BASE = 'https://rhythmerp.algorhythms.in'

# Login
r = requests.post(BASE + '/core/login/', json={'username': 'user@admin.com', 'password': 'Tenant@123456789'}, headers={'X-Tenant-ID': '599'})
token = r.json()['data']['access']
print('Login OK')

H = {'Authorization': 'Bearer ' + token, 'X-Tenant-ID': '599'}

# GET Quality Parameter Master - existing entries
print('\n=== GET Quality Parameter Master ===')
r = requests.get(BASE + '/core/dynamic-screen-wrapper/?screen_name=Quality+Parameter+Master', headers=H)
print(f'Status: {r.status_code}')
data = r.json()
print(f'Top keys: {list(data.keys())}')
inner = data.get('data', {})
print(f'Data type: {type(inner)}')
if isinstance(inner, dict):
    print(f'Data keys: {list(inner.keys())}')
    count = inner.get('count', 'N/A')
    print(f'Count: {count}')
    results = inner.get('results', [])
    if results:
        print(f'Number of results: {len(results)}')
        print(f'First entry keys: {list(results[0].keys())}')
        print(f'First entry: {json.dumps(results[0], indent=2)}')
        if len(results) > 1:
            print(f'Second entry: {json.dumps(results[1], indent=2)}')
    else:
        print('No results found')
else:
    print(f'Raw data: {json.dumps(data, indent=2)[:2000]}')

# Also try to create a test entry to see what fields are accepted
print('\n\n=== POST test entry to Quality Parameter Master ===')
post_headers = {**H, 'Content-Type': 'application/json'}

# Try with minimal fields first
payload = {
    'screen_name': 'Quality Parameter Master',
    'data': {
        'name': 'Test_QP_Discovery'
    }
}
r = requests.post(BASE + '/core/dynamic-screen-wrapper/', json=payload, headers=post_headers)
print(f'Status: {r.status_code}')
print(f'Response: {json.dumps(r.json(), indent=2)[:1500]}')

# If that worked, GET it back to see full structure
if r.status_code in [200, 201]:
    print('\n=== GET back after create ===')
    r2 = requests.get(BASE + '/core/dynamic-screen-wrapper/?screen_name=Quality+Parameter+Master', headers=H)
    data2 = r2.json()
    results2 = data2.get('data', {}).get('results', [])
    if results2:
        # Find our test entry
        for entry in results2:
            if entry.get('name') == 'Test_QP_Discovery':
                print(json.dumps(entry, indent=2))
                break
