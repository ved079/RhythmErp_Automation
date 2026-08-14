from pages.company_onboarding.data.company_onboarding_data import generate_batch_payloads
from common.erp_api_client import RhythmERPAPIClient

print("\nSelect environment:")
print("  1. Deployed  (https://rhythmerp.algorhythms.in)")
print("  2. Local dev (http://localhost:8000)")
print("  3. Custom URL")
env_choice = input("Enter 1 / 2 / 3: ").strip()

if env_choice == '2':
    base_url = 'http://localhost:8001'
    api_endpoint = '/core/dynamic-screen-wrapper/'
elif env_choice == '3':
    base_url = input("Enter base URL: ").strip().rstrip('/')
    api_endpoint = '/core/dynamic-screen-wrapper/'
else:
    base_url = 'https://rhythmerp.algorhythms.in'
    api_endpoint = '/core/dynamic-screen-wrapper/'

print(f"\nUsing: {base_url}{api_endpoint}\n")

token = input("Paste your ERP token: ").strip()
tenant_id = input("Paste your tenant ID: ").strip()
count = int(input("How many companies to create? ").strip())

client = RhythmERPAPIClient(username='', password='', tenant_id=tenant_id)
client.BASE_URL = base_url
client.API_ENDPOINT = api_endpoint
client.login_from_browser(token=token, tenant_id=tenant_id)

print("\nDiscovering Company Onboarding structure from your environment...")
structure = client.discover_structure('Company Onboarding')
if not structure:
    print("ERROR: Could not find any existing Company Onboarding records.")
    print("Please create at least one company manually in your ERP first, then re-run.")
    exit(1)

print(f"  Found: {structure.get('name')} (id={structure.get('id')}, parent_id={structure.get('parent_id')})")

enriched = [structure]
payloads = generate_batch_payloads(count=count, existing_entries=enriched)

print(f"\nCreating {count} companies...\n")
for p in payloads:
    result = client.create_entry(p)
    if result:
        print(f"  CREATED #{result.get('id')} - {p['name']}")
    else:
        resp = getattr(client, '_last_raw_response', None)
        err = resp.text[:200] if resp else 'no response'
        print(f"  FAILED - {p['name']}: {err}")
