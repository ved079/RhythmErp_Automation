import streamlit as st
import logging
import queue
import threading
import time
import sys
import os
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import your existing modules (adjust paths as needed)
import config
from common import auth_section, nav_section
from data.test_data import (
    farmer_data, supplier_data, agent_data, customer_data, employee_data,
    gatepass_data, grn_data, qc_data, purchase_booking_data,
    sales_order_data, dispatch_note_data, invoice_data, receipt_data,
    ageing_report_data, stock_transfer_data, st_recon_inventory_data
)
from Registration import farmer_section, supplier_section, agent_section, customer_section, employee_section
from privateb2b.purchase import gatepass_section, grn_section, qc_section, purchase_booking_section
from privateb2b.sales import sales_order_section, lot_creation_section, dispatch_note_section, invoice_section, receipt_section
from reports.all_reports.ageing_report import run as run_ageing_report
from privateb2b import stock_transfer_section
from privateb2b.test_cases import stock_transfer_recon

# -------------------------------------------------------------------
# Custom Logging Handler that writes to a Streamlit container
# -------------------------------------------------------------------
class StreamlitLogHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = self.format(record)
        self.log_queue.put(msg)

# -------------------------------------------------------------------
# Helper: Run Selenium in background with log streaming
# -------------------------------------------------------------------
def run_tests_in_background(selected_modules, creds, log_queue, result_placeholder):
    """
    Execute the selected test suites with the provided credentials.
    Logs are pushed to log_queue and displayed in the UI.
    """
    # Configure logging to use our queue handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = StreamlitLogHandler(log_queue)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)

    driver = None
    try:
        # Start Chrome (headless option can be added if desired)
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")   # Uncomment to run in background
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        wait = WebDriverWait(driver, 60)

        # Perform login with user‑provided credentials
        logging.info("🔐 Logging into ERP...")
        # Override config temporarily
        original_url = config.URL
        original_user = config.USER
        original_pass = config.PASS
        original_tenant = config.TENANT_NAME
        config.URL = creds['url']
        config.USER = creds['username']
        config.PASS = creds['password']
        config.TENANT_NAME = creds['tenant']
        
        auth_section.perform_login(driver, wait, config)
        logging.info("✅ Login successful")

        # Restore original config (optional)
        config.URL = original_url
        config.USER = original_user
        config.PASS = original_pass
        config.TENANT_NAME = original_tenant

        # Execute selected modules
        if "Farmer Registration" in selected_modules:
            logging.info("🚜 Running Farmer Registration...")
            nav_section.go_to_farmer_page(driver, wait)
            farmer_section.fill_registration(driver, wait, farmer_data)

        if "Supplier Registration" in selected_modules:
            logging.info("🏭 Running Supplier Registration...")
            nav_section.go_to_supplier_page(driver, wait)
            supplier_section.fill_supplier_registration(driver, wait, supplier_data)

        if "Agent Registration" in selected_modules:
            logging.info("🤝 Running Agent Registration...")
            nav_section.go_to_agent_page(driver, wait)
            agent_section.fill_agent_registration(driver, wait, agent_data)

        if "Customer Registration" in selected_modules:
            logging.info("🛒 Running Customer Registration...")
            nav_section.go_to_customer_page(driver, wait)
            customer_section.fill_customer_registration(driver, wait, customer_data)

        if "Employee Registration" in selected_modules:
            logging.info("👔 Running Employee Registration...")
            nav_section.go_to_employee_page(driver, wait)
            employee_section.fill_employee_registration(driver, wait, employee_data)

        if "Purchase Flow" in selected_modules:
            logging.info("📦 Running Full Purchase Flow...")
            nav_section.go_to_gatepass_page(driver, wait)
            gatepass_section.fill_gatepass_registration(driver, wait, gatepass_data)
            nav_section.go_to_grn_page(driver, wait)
            grn_section.fill_grn_registration(driver, wait, grn_data)
            grn_section.approve_latest_grn(driver, wait)
            nav_section.go_to_qc_page(driver, wait)
            qc_section.fill_qc_registration(driver, wait, qc_data)
            nav_section.go_to_purchase_booking_page(driver, wait)
            purchase_booking_section.fill_purchase_booking_registration(driver, wait, purchase_booking_data)

        if "Sales Flow" in selected_modules:
            logging.info("💰 Running Full Sales Flow...")
            nav_section.go_to_sales_order_page(driver, wait)
            sales_order_section.fill_sales_order_registration(driver, wait, sales_order_data)
            nav_section.go_to_lot_creation_page(driver, wait)
            lot_creation_section.fill_lot_creation(driver, wait, {
                "customer_name": sales_order_data['customer_name'],
                "items": sales_order_data['items']
            })
            nav_section.go_to_dispatch_note_page(driver, wait)
            dispatch_note_section.fill_dispatch_note_registration(driver, wait, dispatch_note_data)
            nav_section.go_to_invoice_page(driver, wait)
            invoice_section.fill_invoice_registration(driver, wait, invoice_data)
            nav_section.go_to_receipt_page(driver, wait)
            receipt_section.fill_receipt_registration(driver, wait, receipt_data)

        if "Ageing Report" in selected_modules:
            logging.info("📊 Running Ageing Report...")
            run_ageing_report(driver, wait, ageing_report_data)

        if "Stock Transfer Reconciliation" in selected_modules:
            logging.info("🔄 Running Stock Transfer Reconciliation...")
            stock_transfer_recon.run_stock_transfer_reconciliation(driver, wait)

        logging.info("🏁 All selected tests completed!")

    except Exception as e:
        logging.error(f"❌ Test execution failed: {e}")
        raise
    finally:
        if driver:
            driver.quit()
        # Remove the custom handler to avoid duplicate logs on subsequent runs
        logger.removeHandler(handler)


# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------
st.set_page_config(page_title="FPC Automation Dashboard", layout="wide")

# Inject custom CSS for the login card
st.markdown("""
<style>
    /* 1. COMPLETELY KILL THE SCROLL */
    .stApp, [data-testid="stAppViewContainer"], .main {
        overflow: hidden !important;
        height: 100vh !important; /* Changed from 1000vh to 100vh */
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Nuke Streamlit's invisible padding */
    .block-container {
        padding-top: 5rem !important; 
        padding-bottom: 0 !important;
        margin: 0 auto !important;
    }

    /* Hide the Streamlit footer entirely */
    footer {
        display: none !important;
    }

    /* 2. THE LOGIN CARD */
    div[data-testid="stForm"] {
        background: white;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
        max-width: 450px;
        margin: 0 auto; /* Keeps it horizontally centered */
        border: 1px solid #eaeaea;
    }

    /* 3. TOP HEADER TEXT (Transparent background, text painted on) */
    header[data-testid="stHeader"] {
        background-color: white !important;
    }
    header[data-testid="stHeader"]::before {

        content: "🤖 FPC Automation Dashboard";

        display: flex;

        align-items: center;

        padding-left: 2rem;

        font-size: 1.4rem;

        font-weight: 900;

        color: #1e3c72;

        height: 100%;

        position: absolute;

        left: 0;

        top: 0;

    }

    /* 4. FORM TEXT & ALIGNMENTS */
    div[data-testid="stForm"] h2 {
        text-align: center;
        color: #1e3c72;
        font-weight: 600;
        margin: 0 0 0.25rem 0;
        padding: 0;
    }
    div[data-testid="stForm"] .stCaption {
        text-align: center;
        color: #6c757d;
        margin-bottom: 2rem;
    }

    /* 5. INPUT FIELDS */
    div[data-testid="stForm"] input {
        border-radius: 6px !important;
        border: 1px solid #dee2e6 !important;
        padding: 0.6rem !important;
        background-color: #f4f6f9 !important; /* Slight grey tint like the screenshot */
    }

    /* 6. FORGOT PASSWORD LINK */
    .forgot-link {
        text-align: right;
        margin-bottom: 1.5rem;
        margin-top: 0.5rem;
    }
    .forgot-link a {
        color: #6c757d;
        text-decoration: none;
        font-size: 0.85rem;
    }

    /* 7. LOGIN BUTTON (MATCHING THE SCREENSHOT) */
    div[data-testid="stForm"] button {
        background-color: #1e3c72 !important;
        color: white !important;
        width: auto !important; /* Prevents it from stretching full width */
        min-width: 100px;
        border-radius: 6px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600;
        border: none;
    }
    div[data-testid="stForm"] button:hover {
        background-color: #152a51 !important;
    }
            
            /* 1. SHRINK AND STYLE THE LABELS */
    div[data-testid="stForm"] label p {
        font-size: 0.85rem !important;
        color: #4b5563 !important;
        font-weight: 500 !important;
        margin-bottom: -0.2rem !important; /* Pulls the input box closer to the label */
    }

    /* 2. TIGHTEN THE GAPS BETWEEN FIELDS */
    /* Streamlit forces a default 1rem gap between form elements. This kills it. */
    div[data-testid="stForm"] div[data-testid="stVerticalBlock"] > div {
        margin-bottom: -0.5rem !important; 
    }

    /* 3. FIX THE PASSWORD EYE ICON BOX */
    /* Streamlit makes the password toggle a massive blue button. Let's neutralize it. */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: #f8fafc !important; 
        border-radius: 6px !important;
    }
    div[data-testid="stTextInput"] button {
        background-color: transparent !important;
        color: #6c757d !important;
        border: none !important;
    }
    div[data-testid="stTextInput"] button:hover {
        background-color: #e2e8f0 !important;
        color: #1e3c72 !important;
    }
    
    /* 4. CLEAN UP THE INPUT BORDERS */
    div[data-testid="stForm"] input {
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        background-color: transparent !important; /* Let the base web input background show */
    }
    
    /* 5. SEAMLESS INPUT FIELDS & PASSWORD EYE ICON */
    /* Style the outer wrapper to act as the single unified input box */
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: #f4f6f9 !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 6px !important;
        overflow: hidden !important;
        display: flex !important;
    }

    /* Make the typing area stretch, pushing the button away */
    div[data-testid="stTextInput"] input {
        border: none !important;
        background-color: transparent !important;
        padding: 0.6rem !important;
        box-shadow: none !important;
        flex-grow: 1 !important; /* Forces the text area to take up all available space */
    }

    /* THE FIX: Shove the container holding the eye icon to the extreme right */
    div[data-testid="stTextInput"] div[data-baseweb="input"] > div:last-child {
        margin-left: auto !important; /* <--- THIS PUSHES IT TO THE RIGHT EDGE */
        padding-right: 0.8rem !important; /* Keeps it from touching the absolute edge */
        background: transparent !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Strip all remaining backgrounds from the button itself */
    div[data-testid="stTextInput"] button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        width: auto !important;
    }

    /* Style the actual eye graphic */
    div[data-testid="stTextInput"] button svg {
        fill: #6c757d !important;
        width: 1.2rem;
        height: 1.2rem;
        transition: fill 0.2s ease;
    }
    div[data-testid="stTextInput"] button:hover svg {
        fill: #1e3c72 !important; 
    }

    /* 6. FORGOT PASSWORD LINK */
    .forgot-link {
        text-align: right;
        margin-bottom: 1.5rem;
        margin-top: 0.5rem;
    }
    .forgot-link a {
        color: #6c757d;
        text-decoration: none;
        font-size: 0.85rem;
    }
    .forgot-link a:hover {
        color: #1e3c72;
        text-decoration: underline;
    }
</style>
            
""", unsafe_allow_html=True)


# Session state to track login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "log_queue" not in st.session_state:
    st.session_state.log_queue = queue.Queue()
if "test_running" not in st.session_state:
    st.session_state.test_running = False

# --- Define the Pop-Up Dialog Function ---
@st.dialog("Authenticating...")
def show_validation_popup(user_input, pass_input, tenant_input):
    st.write("Connecting to ERP to verify credentials. Please wait...")
    with st.spinner("Running headless browser..."):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 30)
            
            # Temporarily override config
            original = (config.URL, config.USER, config.PASS, config.TENANT_NAME)
            config.USER = user_input
            config.PASS = pass_input
            config.TENANT_NAME = tenant_input
            
            auth_section.perform_login(driver, wait, config)
            
            # Restore config
            (config.URL, config.USER, config.PASS, config.TENANT_NAME) = original
            driver.quit()
            
            st.session_state.logged_in = True
            st.session_state.credentials = {
                'url': config.URL,
                'username': user_input,
                'password': pass_input,
                'tenant': tenant_input
            }
            st.success("✅ Login successful! Redirecting...")
            time.sleep(1) # Give them a second to see the success message
            st.rerun() # Closes the popup and loads the dashboard
            
        except Exception as e:
            st.error("❌ Login failed. Please check your credentials.")
            if 'driver' in locals() and driver:
                driver.quit()

# ---------- LOGIN LAYOUT ----------
if not st.session_state.logged_in:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        with st.form("login_form"):
            st.markdown("<h2>Welcome Back</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #6c757d; font-size: 0.9rem;'>Login to continue</p>", unsafe_allow_html=True)

            username = st.text_input("Username", value=config.USER)
            password = st.text_input("Password", type="password")
            tenant = st.text_input("Tenant Name", value=config.TENANT_NAME)

            st.markdown('<div class="forgot-link"><a href="#">Forgot Password?</a></div>', unsafe_allow_html=True)

            submitted = st.form_submit_button("Login")

    st.markdown('</div>', unsafe_allow_html=True)
    
    if submitted:
        show_validation_popup(username, password, tenant)
        
    st.stop()


# -------------------------------------------------------------------
# Main Dashboard (after login)
# -------------------------------------------------------------------
st.header("📋 Select Test Modules to Run")

# Module selection
col1, col2 = st.columns(2)
with col1:
    st.subheader("Registrations")
    run_farmer = st.checkbox("Farmer Registration")
    run_supplier = st.checkbox("Supplier Registration")
    run_agent = st.checkbox("Agent Registration")
    run_customer = st.checkbox("Customer Registration")
    run_employee = st.checkbox("Employee Registration")

with col2:
    st.subheader("Flows & Reports")
    run_purchase = st.checkbox("Purchase Flow (Gate Pass → GRN → QC → PB)")
    run_sales = st.checkbox("Sales Flow (SO → Lot → Dispatch → Invoice → Receipt)")
    run_ageing = st.checkbox("Ageing Report")
    run_stock_transfer = st.checkbox("Stock Transfer Reconciliation")

# Build list of selected module names
selected_modules = []
if run_farmer: selected_modules.append("Farmer Registration")
if run_supplier: selected_modules.append("Supplier Registration")
if run_agent: selected_modules.append("Agent Registration")
if run_customer: selected_modules.append("Customer Registration")
if run_employee: selected_modules.append("Employee Registration")
if run_purchase: selected_modules.append("Purchase Flow")
if run_sales: selected_modules.append("Sales Flow")
if run_ageing: selected_modules.append("Ageing Report")
if run_stock_transfer: selected_modules.append("Stock Transfer Reconciliation")

# Run button
if st.button("▶️ Run Selected Tests", disabled=st.session_state.test_running):
    if not selected_modules:
        st.warning("Please select at least one module.")
    else:
        st.session_state.test_running = True
        st.session_state.log_queue = queue.Queue()
        # Start background thread
        thread = threading.Thread(
            target=run_tests_in_background,
            args=(selected_modules, st.session_state.credentials, st.session_state.log_queue, st.empty())
        )
        thread.start()
        st.session_state.thread = thread

# Live Log Display
st.subheader("📜 Live Execution Log")
log_container = st.empty()
log_text = ""

# Continuously update log display while test is running or until queue is empty
while st.session_state.test_running or not st.session_state.log_queue.empty():
    try:
        new_line = st.session_state.log_queue.get(timeout=0.1)
        log_text += new_line + "\n"
        log_container.text(log_text)
    except queue.Empty:
        # If test is no longer running and queue is empty, break
        if not st.session_state.test_running:
            break

# Check if thread finished
if st.session_state.get("test_running") and not st.session_state.thread.is_alive():
    st.session_state.test_running = False
    st.success("✅ Test execution completed!")

# -------------------------------------------------------------------
# Download Section
# -------------------------------------------------------------------
st.subheader("📁 Generated Reports")

download_dirs = [
    "download_files",
    "reports/test_cases/downloads",
    os.path.join(os.getcwd(), "downloads")
]

all_files = []
for d in download_dirs:
    if os.path.exists(d):
        for ext in ['*.xlsx', '*.xls', '*.pdf']:
            all_files.extend(glob.glob(os.path.join(d, ext)))

# Get latest 10 files, sorted by modification time
all_files = sorted(set(all_files), key=os.path.getmtime, reverse=True)[:20]

if all_files:
    for f in all_files:
        col1, col2 = st.columns([4, 1])
        col1.write(os.path.basename(f))
        with open(f, "rb") as file:
            col2.download_button(
                label="📥 Download",
                data=file,
                file_name=os.path.basename(f),
                key=f
            )
else:
    st.info("No reports generated yet. Run tests to see files here.")