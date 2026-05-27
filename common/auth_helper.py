"""
auth_helper.py
--------------
Reusable authentication helper for RhythmERP automation.
Call login from any test without repeating code.

Usage in conftest.py (fixture):
    auth = AuthSection(driver)
    auth.login_default()

Usage in tests (manual):
    auth = AuthSection(driver)
    auth.login_as("admin@mail.com", "Admin@123")
"""

from pages.login_screens.Login_Screens_.login_page import LoginPage
from common.logger import log
import config


class AuthSection:
    """
    Reusable authentication helper class for RhythmERP.

    Provides methods to:
    - Login with default credentials from config
    - Login with custom credentials
    - Verify login was successful
    """

    def __init__(self, driver):
        self.driver = driver
        self.login_page = LoginPage(driver)

    def login(self, email=None, password=None):
        """
        Login to RhythmERP application.
        Uses credentials from config.py (loaded from .env) if not provided.

        Args:
            email: User email (defaults to RHYTHMERP_EMAIL from config)
            password: User password (defaults to RHYTHMERP_PASSWORD from config)
        """
        # Load defaults from config
        email = email or config.RHYTHMERP_EMAIL
        password = password or config.RHYTHMERP_PASSWORD

        if not email or not password:
            raise ValueError(
                "Login credentials are missing. "
                "Provide them directly or set RHYTHMERP_EMAIL and RHYTHMERP_PASSWORD in .env file."
            )

        log.info("Attempting login...")
        log.info(f"  Email: {email}")

        # Execute login steps
        self.login_page.load()
        self.login_page.enter_email(email)
        self.login_page.enter_password(password)
        self.login_page.click_login()

        # Verify login succeeded
        self.login_page.wait_for_login_complete()

        log.info("Login successful!")
        return True

    def login_as(self, email, password):
        """
        Login with specific credentials (for role-based testing).

        Args:
            email: Specific user email
            password: Specific user password

        Example:
            auth = AuthSection(driver)
            auth.login_as("admin@mail.com", "Admin@123")
        """
        log.info(f"Logging in as: {email}")
        return self.login(email, password)

    def login_default(self):
        """
        Quick login using default credentials from config/.env.
        Shortcut for the most common case.

        Example:
            auth = AuthSection(driver)
            auth.login_default()
        """
        return self.login()
