# Login_screens_runner.py
# --------------------
# Multi-product runner for PACS and RhythmERP login/forgot-password.
# ONLY runs the normal flow. No test framework. No gimmicks.
#
# Usage:
#     python Login_screens_runner.py --product pacs --login
#     python Login_screens_runner.py --product rhythmerp --login
#     python Login_screens_runner.py --product pacs --forgot-password
#     python Login_screens_runner.py --product rhythmerp --forgot-password

import sys
import os
import argparse
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from common.logger import log
from common.browser_utils import get_driver
from pages.login_screens.Login_Screens_.login_page import LoginPage


def run_login(product):
    """Normal login flow â€” enter creds, select facility, login, verify dashboard."""
    if product == "rhythmerp":
        from config import RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_LOGIN_URL
        email, password, login_url = RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_LOGIN_URL
        use_index = True
    else:
        from config import PACS_EMAIL, PACS_PASSWORD, LOGIN_URL, PACS_FACILITY
        email, password, login_url, facility = PACS_EMAIL, PACS_PASSWORD, LOGIN_URL, PACS_FACILITY
        use_index = False

    log.separator()
    log.info(f" {product.upper()} â€” LOGIN SMOKE TEST")
    log.info(f" URL: {login_url}")
    log.separator()

    driver = get_driver()
    page = LoginPage(driver)

    try:
        page.load_url(login_url)
        page.enter_email(email)
        page.enter_password(password)

        if use_index:
            page.select_facility_by_index(index=0)
        else:
            page.select_facility(facility)

        page.click_login()
        page.wait_for_login_complete(login_url=login_url)

        log.info(f"Login successful! URL: {driver.current_url}")

    except Exception as e:
        log.error(f"Login FAILED: {e}")
        driver.save_screenshot(f"{product}_login_failed.png")

    finally:
        input("Press Enter to close browser...")
        try:
            driver.quit()
        except Exception:
            pass


def run_forgot_password(product):
    """Normal forgot password flow â€” email -> OTP -> new password -> reset -> login -> verify dashboard."""
    if product == "rhythmerp":
        from config import RHYTHMERP_FP_EMAIL, RHYTHMERP_LOGIN_URL, RHYTHMERP_EMAIL
        email = RHYTHMERP_FP_EMAIL
        login_url = RHYTHMERP_LOGIN_URL
        login_username = RHYTHMERP_EMAIL
        use_index = True
        timestamp = datetime.now().strftime("%H%M%S")
        new_password = f"Test@{timestamp}x"
    else:
        from config import FP_EMAIL, LOGIN_URL, FP_NEW_PASSWORD, FP_USERNAME, FP_TENANT
        email = FP_EMAIL
        login_url = LOGIN_URL
        login_username = FP_USERNAME
        facility = FP_TENANT
        use_index = False
        new_password = FP_NEW_PASSWORD

    log.separator()
    log.info(f" {product.upper()} â€” FORGOT PASSWORD SMOKE TEST")
    log.info(f" Email: {email}")
    log.info(f" New password: {new_password}")
    log.separator()

    driver = get_driver()
    page = LoginPage(driver)

    try:
        # â”€â”€ Step 1: Load login page and go to forgot password â”€â”€
        page.load_url(login_url)
        log.info("Login page loaded")

        from pages.login_screens.Login_Screens_.forgot_password_page import ForgotPasswordPage
        fp_page = ForgotPasswordPage(driver)
        fp_page.navigate_to_forgot_password()
        log.info("Navigated to forgot password page")

        # â”€â”€ Step 2: Enter email and send OTP â”€â”€
        fp_page.enter_email(email)
        log.info(f"Entered email: {email}")

        fp_page.click_send_otp()
        log.info("Clicked Send OTP")

        time.sleep(3)

        if not fp_page.is_otp_screen_displayed():
            log.error("OTP screen did NOT appear")
            driver.save_screenshot(f"{product}_forgot_password_failed.png")
            return

        log.info("OTP screen appeared")

        # â”€â”€ Step 3: Enter OTP (3 attempts) â”€â”€
        otp_accepted = False
        for attempt in range(3):
            otp = input(f"  Enter OTP received on {email} ({attempt + 1}/3): ")
            fp_page.enter_otp(otp)
            log.info("OTP entered")

            time.sleep(2)
            alert = fp_page.get_alert_danger_text()
            if alert:
                log.warning(f"Wrong OTP: {alert}")
                log.info("Check email for new OTP and try again")
            else:
                log.info("OTP accepted!")
                otp_accepted = True
                break

        if not otp_accepted:
            log.error("Failed 3 times. Aborting.")
            driver.save_screenshot(f"{product}_forgot_password_failed.png")
            return

        # â”€â”€ Step 4: Enter new password and confirm â”€â”€
        fp_page.enter_new_password(new_password)
        fp_page.enter_confirm_password(new_password)
        log.info("Entered new password and confirm password")

        # â”€â”€ Step 5: Click Reset Password â”€â”€
        fp_page.click_reset_password()
        log.info("Clicked Reset Password")

        time.sleep(3)

        # â”€â”€ Step 6: Verify success screen â”€â”€
        if fp_page.is_success_screen_displayed():
            msg = fp_page.get_success_message_text()
            log.info(f"Password reset SUCCESSFUL! Message: {msg}")
        else:
            log.error("Success screen not shown")
            driver.save_screenshot(f"{product}_reset_verify.png")
            return

        # â”€â”€ Step 7: Click login link on success screen -> redirected to login page â”€â”€
        fp_page.click_login_link_after_success()
        time.sleep(2)
        log.info("Redirected to login page")

        # â”€â”€ Step 8: Login with new credentials â”€â”€
        login_page = LoginPage(driver)
        login_page.wait_for_page_load()
        login_page.enter_email(login_username)
        login_page.enter_password(new_password)

        if use_index:
#             login_page.select_facility_by_index(index=0)
        else:
            login_page.select_facility(facility)

        login_page.click_login()
        log.info("Logged in with new credentials")

        # â”€â”€ Step 9: Verify dashboard â”€â”€
        login_page.wait_for_login_complete(login_url=login_url)
        log.info(f"FORGOT PASSWORD FLOW COMPLETE! URL: {driver.current_url}")

    except Exception as e:
        log.error(f"Forgot Password FAILED: {e}")
        driver.save_screenshot(f"{product}_forgot_password_failed.png")

    finally:
        input("Press Enter to close browser...")
        try:
            driver.quit()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Login Screens Runner")
    parser.add_argument("--product", choices=["pacs", "rhythmerp"], default="pacs",
                        help="Product to test (default: pacs)")
    parser.add_argument("--login", action="store_true", help="Run login smoke test")
    parser.add_argument("--forgot-password", action="store_true", help="Run forgot password smoke test")

    args = parser.parse_args()

    if args.login:
        run_login(args.product)
    elif args.forgot_password:
        run_forgot_password(args.product)
    else:
        parser.print_help()
        print("\nError: No action specified. Use --login or --forgot-password")


if __name__ == "__main__":
    main()
