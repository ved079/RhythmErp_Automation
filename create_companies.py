from pages.company_onboarding.data.company_onboarding_data import generate_batch_payloads
from common.erp_api_client import RhythmERPAPIClient

print("\nSelect environment:")
print("  1. Deployed  (https://rhythmerp.algorhythms.in)")
print("  2. Local dev (http://localhost:4000)")
print("  3. Custom URL")
env_choice = input("Enter 1 / 2 / 3: ").strip()

if env_choice == '2':
    base_url = 'http://localhost:4000'
elif env_choice == '3':
    base_url = input("Enter base URL: ").strip().rstrip('/')
else:
    base_url = 'https://rhythmerp.algorhythms.in'

print(f"Using: {base_url}\n")

token = input("Paste your ERP token: ").strip()
tenant_id = input("Paste your tenant ID: ").strip()
count = int(input("How many companies to create? ").strip())

client = RhythmERPAPIClient(username='', password='', tenant_id=tenant_id)
client.BASE_URL = base_url
client.login_from_browser(token=token, tenant_id=tenant_id)

existing = client.list_entries('Company Onboarding', page_size=5)
rows = existing.get('screenmatlistingdata_set', [])
enriched = []
for row in rows[:2]:
    detail = client.get_entry('Company Onboarding', row['id'])
    if detail:
        enriched.append(detail)

payloads = generate_batch_payloads(count=count, existing_entries=enriched)
for p in payloads:
    result = client.create_entry(p)
    if result:
        print(f"CREATED #{result.get('id')} - {p['name']}")
    else:
        print(f"FAILED - {p['name']}")
