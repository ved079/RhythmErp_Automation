# =========================================================================
# 1. IMPORTS & CONSTANTS
# =========================================================================
import random
import string
import datetime
from datetime import timedelta
import datetime

# =========================================================================
# 2. HELPER FUNCTIONS (Alphabetical Order)
# =========================================================================

def gen_balance_type():
    """Returns a random Balance Type."""
    return random.choice(["All", "Closing Balance"])

def gen_company():
    """Generates a random company/agent name."""
    words1 = ["Nexus", "Stellar", "Orbit", "Aegis", "Quantum", "Vertex", "Nova", "Apex", "Cyrus", "Rhythmflows", "Automation"]
    words2 = ["Logistics", "Dynamics", "Trade", "Core", "Innovations", "Solutions", "Networks", "Manufacturing", "Solutions", "Test"]
    suffixes = ["Pvt Ltd", "Industries", "Group"]
    return f"{random.choice(words1)} {random.choice(words2)} {random.choice(suffixes)}"

def gen_customer():
    """Return a random customer name that exists in the system (must match a customer in the dropdown)."""
    customers = [
        "Vedant Enterprises-9999999999|Customer",
        "Ved_Enterprises-9309316566|Customer"
    ]
    return random.choice(customers)

def gen_customer_po_number():
    """Generate a random PO number."""
    return f"PO{random.randint(10000, 99999)}"

def gen_due_status():
    """Returns a random Due Status."""
    return random.choice(["All", "Past Due"])

def gen_email(base_name):
    """Generates a unique email based on the generated name/company."""
    clean_name = base_name.split()[0].lower().replace(".", "").replace(",", "")
    return f"{clean_name}.{random.randint(100,9999)}@example.com"

def gen_empty_bag_weight():
    return round(random.uniform(0, 5), 2)

def gen_gender():
    Gender = [
        "Male",
        "Female"
    ]
    return random.choice(Gender)

def gen_transfer_locations():

    locations = ["Indore", "London"]
    from_loc, to_loc = random.sample(locations, 2)
    return from_loc, to_loc

def gen_group_by(transaction_type):
    """Returns a Group By option depending on the Transaction Type."""
    if transaction_type == "Purchase":
        return random.choice(["Supplier", "Bill Wise"])
    elif transaction_type == "Sales":
        return random.choice(["Customer", "Bill Wise"])
    else:
        return "Bill Wise" # Safe fallback

def gen_item():
    """Returns a random item name from a predefined list."""
    item = ["Soyabean", "Chana", "Tur-Red","Maize-Yellow"]
    return random.choice(item)

def gen_labour_charges():
    return round(random.uniform(0, 100), 2)

def gen_level():
    """Returns a random Level."""
    return random.choice(["Only Chart Of Account"])

def gen_multiple_items():
    """Randomly selects 1 to 4 unique items and generates bags/qty for each."""
    all_items = ["Soyabean", "Chana", "Tur-Red", "Maize-Yellow"]
    
    # Randomly decide how many items to add to this transaction (1 to 4)
    num_items_to_pick = random.randint(1, 1)
    
    # random.sample guarantees we don't pick the same item twice!
    chosen_items = random.sample(all_items, num_items_to_pick)
    
    transaction_items = []
    for item_name in chosen_items:
        transaction_items.append({
            "item": item_name,
            "no_of_bags": random.randint(10, 500),
            "quantity": round(random.uniform(10000, 50000), 1),
            "qc_parameters": get_qc_parameters(item_name) # Assuming you still have this function!
        })
    return transaction_items

def gen_name():
    """Generates a random person name using ONLY A-Z, a-z, and a space."""
    firsts = ["Aarav", "Vikram", "Priya", "Neha", "Rohan", "Kavya", "Elias", "Zara", "Mira", "Tariq", "Rahul", "Lila"]
    lasts = ["Sharma", "Thakur", "Iyer", "Desai", "Brooks", "Sterling", "Mercer", "Vance", "Collins", "Patil", "Singh"]
    return f"{random.choice(firsts)} {random.choice(lasts)}"

def gen_no_of_bags():
    """Returns a random integer between 10 and 500."""
    return random.randint(10, 500)

def gen_office():
    """Generates a random Pune office number."""
    return "020-" + ''.join(random.choices(string.digits, k=8))

def gen_pan():
    """Generates a valid format random PAN number (5 letters, 4 digits, 1 letter)."""
    letters1 = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    letter2 = random.choice(string.ascii_uppercase)
    return f"{letters1}{digits}{letter2}"

def gen_phone():
    """Generates a random 10-digit Indian mobile number."""
    return str(random.choice([7, 8, 9])) + ''.join(random.choices(string.digits, k=9))

def gen_quantity():
    """Returns a random float between 100.0 and 5000.0, rounded to 1 decimal."""
    return round(random.uniform(100.0, 500.0), 1)

def gen_ST_quantity():
    return round(random.uniform(1, 10), 1)


def gen_quantity_sales():
    return round(random.uniform(1, 5), 2)

def gen_random_financial_date():
    """Generates a random date between April 1, 2024, and March 31, 2026."""
    
    # Define the boundaries
    start_date = datetime.datetime(2026, 4, 10)
    end_date = datetime.datetime(2026, 4, 14)
    
    # Calculate the total number of days between the two dates
    days_between = (end_date - start_date).days
    
    # Pick a random number of days to add to the start date
    random_days = random.randint(0, days_between)
    
    # Generate the final random date
    random_date = start_date + datetime.timedelta(days=random_days)
    
    return random_date.strftime("%d/%m/%Y")

def gen_rate():
    return round(random.uniform(50000, 80000), 2)

def gen_sales_order_items():
    """Generate 1-3 items with random names, quantities, and rates."""
    all_items = ["Soyabean", "Chana", "Tur-Red", "Maize-Yellow"]
    num_items = random.randint(1, 3)
    chosen = random.sample(all_items, num_items)
    items = []
    for item in chosen:
        items.append({
            'item_name': item,
            'quantity': gen_quantity_sales(),
            'rate': gen_rate(),
            'tax_rate': '5' if item in ["Soyabean", "Chana"] else '0',
            'expected_delivery_date': gen_random_financial_date()
        })
    return items

def gen_supplier():
    suppliers = [
        "Ved_Supplies-9309316566|Supplier",
        "Kavya Singh-9933768617|Farmer",
        "Nexus Logistics Industries-9147295884|Supplier",
        "Mira Thakur-900|Farmer"
    ]
    return random.choice(suppliers)

def gen_tax_rate():
    # Common tax rates: 0, 5, 12, 18
    return str(random.choice([0, 5, 12, 18]))

def gen_transaction_type():
    """Returns a random Transaction Type."""
    return random.choice(["Purchase"])

def gen_transportation_charges():
    return round(random.uniform(0, 1000), 2)

def gen_view_type():
    """Returns a random View Type."""
    return random.choice(["Vertical", "Horizontal"])

def get_qc_parameters(item):
    if item == "Chana":
        return {"Size": 0}               # adjust name if needed (e.g., "Moisture")
    elif item == "Soyabean":
        return {
            "Moisture": 1,
            "Foreign Material": 1,
            "Damaged Seed": 1
        }
    elif item == "Tur-Red":
        return {
            "Size": 70.001
        }
    elif item == "Turmeric":
        return {
            "Moisture": 0,
            "Size": 0
        }
    elif item == "Maize-Yellow":
        return {
            "Foreign Material": 0,
            "Damaged Seed": 0,
            "Moisture": 0
        }
    else:
        return {"Moisture": 1}

# =========================================================================
# 3. SHARED PURCHASE FLOW VARIABLES (Source of Truth)
# =========================================================================
# These guarantee synchronization across Gate Pass, GRN, QC, and Booking
SHARED_SUPPLIER = gen_supplier() # (From your earlier code)
SHARED_ITEM_TYPE = "Farm"
SHARED_TRANSACTION_DATE = gen_random_financial_date()
SHARED_ITEMS_LIST = gen_multiple_items()

# =========================================================================
# 4. DYNAMIC VARIABLE GENERATION (Run once per script execution)
# =========================================================================
f_name = gen_name()

s_company = gen_company()
s_pan = gen_pan()
s_gstin = f"27{s_pan}1Z5" # GSTIN auto-syncs with PAN

a_name = f"{random.choice(['Apex', 'Nova', 'Cyrus', 'Vertex'])} Trade Networks"

c_company = gen_company()
c_pan = gen_pan()

e_name = gen_name()

current_transaction_type = gen_transaction_type()

# =========================================================================
# 5. REGISTRATION DATA DICTIONARIES (Farmer, Supplier, Agent, Customer, Employee)
# =========================================================================

farmer_data = {
    "name": f_name,
    "email": gen_email(f_name),
    "phone": gen_phone(),
    "dob": "07/09/2004",
    "gender": gen_gender(),
    "caste": "Open",
    "password": "xyz",
    "farmer_category": 'Walk-in Farmer',
    "state": "Maharashtra",
    "district": "Pune",
    "taluka": "Haveli",
    "village": "Wagholi",
    "pincode": "412105",
    "bank_name": "selb",
    "ifsc": "BARB0DIGIHI",
    "account_no": "29929292",
    "address1": "123 Main Street",        
    "address2": "Near Post Office",       
    "branch_name": "Main Branch",         
    "account_type": "Saving",            
    "bank_proof": "Passbook"              
}

farmer_update_data = {
    "name": farmer_data['name'] + " Updated"
}

supplier_data = {
    "supplier_status": "Active",
    "company_name": s_company,
    "po_type_ref_id": "Import",
    "email_id": gen_email(s_company),
    "mobile_no": gen_phone(),
    "pan_no": s_pan,
    "ownership_status_ref_id": "PLC",
    "contact_person_name": gen_name(),
    "office_number": gen_office(),
    "payment_terms": "Immediate",
    "delivery_terms": "Spot",
    "mode_of_delivery": "Truck",
    "gstin": s_gstin,

    "billing_address": {
        "address_type": "Billing",
        "address": "123 Main Street, Area Name",
        "state": "Maharashtra",
        "district": "Pune",
        "taluka": "Haveli",
        "village": "Wagholi",
        "pin_code": "412105"
    },
    "shipping_address": {
        "address_type": "Shipping",
        "address": "456 Industrial Estate, Area Name",
        "state": "Maharashtra",
        "district": "Pune",
        "taluka": "Haveli",
        "village": "Kharadi",
        "pin_code": "411014"
    },
    "bank": {
        "bank_name": "State Bank of India",
        "branch_name": "Main Branch",
        "ifsc": "SBIN0001234",
        "account_type": "Saving",
        "account_holder_name": s_company, # Auto-synced
        "account_number": "123456789012",
        "bank_proof": "Passbook",
        "bank_proof_file": r"C:\Users\vedantd\Desktop\selenium files\data\blank.pdf"
    }
}

updated_supplier_data = {
    "company_name": supplier_data['company_name'] + " UPDATED" 
}

agent_data = {
    "agent_name": a_name,
    "phone": gen_phone(),
    "email": gen_email(a_name),
    "basis_type": "KG",           
    "commission": 5.5,                  
    "state": "Maharashtra",
    "district": "Pune",
    "taluka": "Haveli",
    "village": "Wagholi",
    "address": "123 Main Street, Wagholi",
    "pincode": "412105",
    "payment_terms": "Immediate",            
    "preferred_payment_method": "Cash",  
    "bank": {
        "bank_name": "State Bank of India",
        "branch_name": "Main Branch",
        "ifsc": "SBIN0001234",
        "account_type": "Saving",
        "account_holder_name": a_name, # Auto-synced
        "account_number": "123456789012",
        "bank_proof": "Passbook",
        "bank_proof_file": r"C:\Users\vedantd\Desktop\selenium files\data\blank.pdf"   
    }
}

updated_agent_data = {
    "agent_name": agent_data['agent_name'] + " UPDATED"
}

customer_data = {
    "company_name": c_company,
    "supply_type": "Goods",
    "customer_type": "New",
    "sale_type": "Contract",
    "email": gen_email(c_company),
    "mobile": gen_phone(),
    "pan": c_pan,
    "ownership_status": "PLC",
    "contact_person": gen_name(),
    "office_number": gen_office(),
    "preferred_payment_method": "Cash",
    "gst_registration_type": "Regular",
    "payment_terms": "Immediate",
    "delivery_terms": "Spot",
    "mode_of_delivery": "Truck",
    "courier_terms": "Paid",
    "deposit": 1000.00,
    "quantity_tolerance": 5,
    "rate_tolerance": 2,       

    "billing_address": {
        "address_type": "Billing",
        "state": "Maharashtra",
        "district": "Pune",
        "taluka": "Haveli",
        "village": "Wagholi",
        "address": "123 Main Street, Wagholi",
        "pin_code": "412105"
    },
    "shipping_address": {
        "address_type": "Shipping",
        "state": "Maharashtra",
        "district": "Pune",
        "taluka": "Haveli",
        "village": "Kharadi",
        "address": "456 Industrial Estate, Kharadi",
        "pin_code": "411014"
    },
    "bank": {
        "bank_name": "State Bank of India",
        "branch_name": "Main Branch",
        "ifsc": "SBIN0001234",
        "account_type": "Saving",
        "account_holder_name": c_company, # Auto-synced
        "account_number": "123456789012",
        "bank_proof": "Passbook",
        "bank_proof_file": r"C:\Users\vedantd\Desktop\selenium files\data\blank.pdf"
    }
}

updated_customer_data = {
    "company_name": customer_data['company_name'] + " UPDATED"
}

employee_data = {
    "employee_name": e_name,
    "email": gen_email(e_name),
    "phone": gen_phone(),
    "designation": "Manager",
    "maker_checker": "Maker"
}

updated_employee_data = {
    "employee_name": employee_data['employee_name'] + " UPDATED"
}

# =========================================================================
# 6. PURCHASE FLOW DICTIONARIES (Gate Pass, GRN, QC, Purchase Booking)
# =========================================================================

gatepass_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "supplier": SHARED_SUPPLIER,
    "item_type": SHARED_ITEM_TYPE,
    "department": "Businesss Division",
    "division": "HR",
    "location": "London",
    "sale_type": "B2B",
    "delivery_terms": "Delivery",
    "vehicle_no": f"MH12AB{random.randint(1000, 9999)}",
    "driver_name": "Ramesh",
    "driver_contact": "9876543210",
    "in_time": "10:30",
    "items": SHARED_ITEMS_LIST
}

grn_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "supplier": SHARED_SUPPLIER
}

qc_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "supplier": SHARED_SUPPLIER,
    "item_type": SHARED_ITEM_TYPE,
    "items": SHARED_ITEMS_LIST 
}

purchase_booking_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "supplier": SHARED_SUPPLIER,
    "items": SHARED_ITEMS_LIST, 
    "payment_terms": "Immediate",
    "attachment_file": r"C:\Users\vedantd\Desktop\selenium files\data\blank.pdf"
}

# =========================================================================
# 7. SALES FLOW DICTIONARIES (Sales Order, Dispatch, Invoice, Receipt)
# =========================================================================

sales_order_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "customer_name": gen_customer(),
    "department": "Businesss Division",
    "division": "HR",
    "location": "London",
    "sale_type": "B2B",
    "customer_po_number": gen_phone(),
    "customer_po_date": gen_random_financial_date(),
    "transportation_charges": 0,
    "items": gen_sales_order_items()
}

dispatch_note_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "customer_name": sales_order_data['customer_name'],
    "sale_type": "Contract", 
    "supply_type": "Goods",
    "department": sales_order_data['department'],
    "division": sales_order_data['division'],
    "location": sales_order_data['location'],
    "type_of_sale": sales_order_data['sale_type'],
    "transportation_charges": 0,
    "items": sales_order_data['items'], 
    "transporter_name": 'Truck',
    "vehicle_no": f"MH12AB{random.randint(1000, 9999)}",
    "distance": 1.0,
    "attachment_file": r"C:\Users\vedantd\Desktop\selenium files\data\blank.pdf"
}

invoice_data = {
    "customer_name": sales_order_data['customer_name'],
    "sales_type": "Contract",
    "supply_type": "Goods",
    "transportation_charges": 0
}

receipt_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "receipt_type": "Regular",
    "department": sales_order_data['department'],
    "division": sales_order_data['division'],
    "location": sales_order_data['location'],
    "type_of_sale": sales_order_data['sale_type'],
    "customer_name": sales_order_data['customer_name'],
    "payment_method": "Cash",
    "company_account_number": "Cash In Hand - Chana Dal Mills (Akola) - 123",
    "customer_bank_name": "DUMMY BANK"
}

# =========================================================================
# 8. REPORT DATA DICTIONARIES (All Reports)
# =========================================================================

trial_balance_data = {
    "frequency": "As On Date",           
    "view_type": "Vertical",
    "balance_type": "All",
    "level": gen_level(),
    "file_format": "EXCEL",        
    "transaction_date": SHARED_TRANSACTION_DATE  
}

balance_sheet_data = {
    "level": gen_level(),
    "view_type": gen_view_type(),
    "file_format": "EXCEL",
    "amount_unit_conversion": "Lakh",
    "transaction_date": "07/04/2026"
}

profit_loss_data = {
    "transaction_date": "07/04/2026",
    "level": gen_level(),
    "view_type": gen_view_type(),
    "division": "HR",
    "department": "Businesss Division",
    "type_of_sale": "B2B",
    "location": "London",
    "file_format": "EXCEL",
    "amount_unit_conversion": "Lakh"
}

payable_data = {
    "file_format": "EXCEL"
}

receivable_data = {
    "file_format": "EXCEL"
}

inventory_report_data = {
    "item": gen_item(),
    "from_date": "01/04/2025",
    "to_date": "07/04/2026",
    "division": "HR",
    "department": "Businesss Division",
    "type_of_sale": "B2B",
    "location": "London",
    "file_format": "EXCEL"
}

inventory_summary_data = {
    "item": "Soyabean",
    "from_date": "01/04/2025",
    "to_date": "07/04/2026",
    "file_format": "EXCEL"
}

ageing_report_data = {
    "transaction_type": current_transaction_type,
    "due_status": gen_due_status(),
    "from_date": "01/04/2025",
    "to_date": "07/04/2026",
    "division": "HR",
    "department": "Businesss Division",
    "type_of_sale": "B2B",
    "location": "London",
    "file_format": "EXCEL",
    "group_by": gen_group_by(current_transaction_type) 
}

ledger_enquiry_data = {
    "account": "Cash In Hand Shivani 1",
    "frequency": "Date Range",
    "file_format": "EXCEL",
    "from_date": "01/01/2026",
    "to_date": "07/04/2026"
}

day_book_data = {
    "for_type": "All Transaction",
    "frequency": "Date Range",
    "voucher_type": "Sale",
    "file_format": "EXCEL",
    "from_date": "01/01/2026",
    "to_date": "07/04/2026"
}

sales_order_status_data = {
    "customer_name": "Ved_Enterprises-9309316566|Customer",
    "from_date": "01/01/2026",
    "to_date": "07/04/2026",
    "division": "HR",
    "department": "Businesss Division",
    "type_of_sale": "B2B",
    "location": "London",
    "lot_status": "Created",
    "dispatch_status": "Created",
    "invoice_status": "Created",
    "receipt_status": "Created",
    "file_format": "EXCEL"
}

supplier_balance_data = {
    "supplier_name": "Ved_Supplies-9309316566|Supplier",
    "file_format": "EXCEL"
}

customer_balance_data = {
    "customer_name": "Ved_Enterprises-9309316566|Customer",
    "file_format": "EXCEL"
}

statistics_data = {
    "from_date": "01/01/2026",
    "to_date": "07/04/2026",
    "file_format": "EXCEL"
}

weighted_average_rate_data = {
    "for_day": "04/04/2026",
    "file_format": "EXCEL"
}

# STOCK TRANSFER DATA

ST_FROM_LOCATION, ST_TO_LOCATION = gen_transfer_locations()

# --- Your dictionary stays exactly the same ---
stock_transfer_data = {
    "transaction_date": SHARED_TRANSACTION_DATE,
    "item_type": SHARED_ITEM_TYPE,
    "from_department": "Businesss Division",
    "from_division": "HR",
    "from_sale_type": "B2B",
    "from_location": ST_FROM_LOCATION,
    "item_name": gen_item(),  
    "to_department": "Businesss Division",
    "to_division": "HR",
    "to_sale_type": "B2B",
    "to_location": ST_TO_LOCATION,
    "transfer_quantity": gen_ST_quantity()
}

# =========================================================================
# 9. RECONCILIATION SPECIFIC DATA
# =========================================================================

st_recon_inventory_data = {
    "item": "",  
    "from_date": "",
    "to_date": SHARED_TRANSACTION_DATE,  
    "division": "HR",
    "department": "Businesss Division",
    "type_of_sale": "B2B",
    "location": "",  
    "file_format": "EXCEL"
}