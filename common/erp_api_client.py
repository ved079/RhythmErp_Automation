"""
erp_api_client.py
-----------------
Direct API client for Rhythm ERP dynamic screens.
Bypasses the UI entirely for fast, reliable data creation.

Uses the same endpoint that the Angular frontend uses:
  POST /core/dynamic-screen-wrapper/

Authentication:
  - Bearer token obtained via login API
  - X-Tenant-ID header (e.g., "599")

Usage:
    client = RhythmERPAPIClient()
    client.login()
    client.create_entry({"id": "", "attribute_name": "Designation", ...})

    # Or use existing browser token:
    client = RhythmERPAPIClient()
    client.login_from_browser(token="eyJ...", tenant_id="599")

Speed comparison:
  - UI via Selenium: 30-60 seconds per entry (flaky with Angular Material)
  - API via this client: ~0.3 seconds per entry (deterministic)
"""

import requests
import time
from typing import List, Dict, Optional

from common.logger import log
import config


class RhythmERPAPIClient:
    """
    Direct API client for Rhythm ERP dynamic screens.

    Screen-agnostic: works for Supplier, Customer, Farmer, Designation,
    HSN SAC, Error Code Mst — anything on the dynamic-screen-wrapper endpoint.
    """

    BASE_URL = config.RHYTHMERP_BASE_URL.rstrip("/")
    API_ENDPOINT = "/core/dynamic-screen-wrapper/"
    SCREEN_SCHEMA_ENDPOINT = "/core/dynamic-screen/{screen_name}/"

    def __init__(
        self,
        username: str = None,
        password: str = None,
        tenant_id: str = "599",
    ):
        """
        Initialize the API client.

        Args:
            username: Email for login (defaults to RHYTHMERP_EMAIL from .env)
            password: Password for login (defaults to RHYTHMERP_PASSWORD from .env)
            tenant_id: X-Tenant-ID header value (default "599")
        """
        self.username = username or config.RHYTHMERP_EMAIL
        self.password = password or config.RHYTHMERP_PASSWORD
        self.tenant_id = tenant_id
        self.session = requests.Session()
        self.token = None
        self._logged_in = False

    # ================================================================
    # Authentication
    # ================================================================

    def login(self) -> tuple:
        """
        Authenticate against the ERP and obtain a Bearer token.

        The login flow mirrors what the Angular frontend does:
        1. POST email + password to the login endpoint
        2. Extract the access token from the response
        3. Set Authorization + X-Tenant-ID headers on the session

        Returns:
            (token, tenant_id) tuple

        Raises:
            ConnectionError: If the ERP is unreachable
            ValueError: If login fails or token cannot be extracted
        """
        log.info("[API] Logging into Rhythm ERP...")
        log.info(f"[API]   Email: {self.username}")

        if not self.username or not self.password:
            raise ValueError(
                "Login credentials missing. Set RHYTHMERP_EMAIL and "
                "RHYTHMERP_PASSWORD in .env or pass them directly."
            )

        # Step 1: Hit the login page to get a session
        login_url = f"{self.BASE_URL}/api/auth/login/"

        try:
            resp = self.session.post(
                login_url,
                json={
                    "email": self.username,
                    "password": self.password,
                },
                timeout=30,
            )
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot reach ERP at {self.BASE_URL}. "
                "Check network or VPN connection."
            )

        # Step 2: Try to extract token from response
        if resp.status_code == 200:
            data = resp.json()
            self.token = (
                data.get("access")
                or data.get("token")
                or data.get("key")
                or data.get("auth_token")
            )
        else:
            # The login endpoint might be different — try the session approach
            # where we use the same cookie-based auth as the browser
            log.warning(
                f"[API] Standard login returned {resp.status_code}. "
                "Trying session-based auth..."
            )
            self._session_login()
            return self.token, self.tenant_id

        if not self.token:
            raise ValueError(
                f"Could not extract token from login response. "
                f"Status: {resp.status_code}, Body: {resp.text[:200]}"
            )

        # Step 3: Set session headers
        self._set_session_headers()
        self._logged_in = True

        log.info(
            f"[API] Login successful. Token: {self.token[:30]}... "
            f"Tenant: {self.tenant_id}"
        )
        return self.token, self.tenant_id

    def _session_login(self):
        """
        Fallback: obtain a token by doing a browser-like login flow.
        POSTs credentials to the login page and extracts the token
        from the response cookies or localStorage equivalent.
        """
        # Try the login URL that the Angular app uses
        login_urls = [
            f"{self.BASE_URL}/api/token/",
            f"{self.BASE_URL}/api/v1/auth/login/",
            f"{self.BASE_URL}/api/auth/login/",
        ]

        for url in login_urls:
            try:
                resp = self.session.post(
                    url,
                    json={
                        "email": self.username,
                        "password": self.password,
                    },
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.token = (
                        data.get("access")
                        or data.get("token")
                        or data.get("key")
                    )
                    if self.token:
                        self._set_session_headers()
                        self._logged_in = True
                        log.info(
                            f"[API] Session login successful via {url}"
                        )
                        return
            except Exception:
                continue

        raise ValueError(
            "Could not authenticate via any known login endpoint. "
            "Use login_from_browser() with a token captured from DevTools."
        )

    def login_from_browser(self, token: str, tenant_id: str = "599"):
        """
        Set auth using a token captured from the browser's DevTools.

        Use this when the login endpoint is unknown or returns an
        encrypted token. Capture the real Bearer token by:
        1. Open ERP in Chrome DevTools -> Network tab
        2. Look at any XHR request to /core/...
        3. Copy the Authorization header value (after "Bearer ")

        Args:
            token: Bearer token string (WITHOUT "Bearer " prefix)
            tenant_id: X-Tenant-ID value (default "599")
        """
        self.token = token
        self.tenant_id = tenant_id
        self._set_session_headers()
        self._logged_in = True
        log.info(
            f"[API] Session set from browser token. Tenant: {self.tenant_id}"
        )

    def _set_session_headers(self):
        """Set the default headers on the requests session."""
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": str(self.tenant_id),
                "Content-Type": "application/json",
            }
        )

    def is_authenticated(self) -> bool:
        """Check if the client has a valid token."""
        return self._logged_in and self.token is not None

    def _ensure_auth(self):
        """Raise if not authenticated."""
        if not self.is_authenticated():
            raise RuntimeError(
                "API client is not authenticated. Call login() or "
                "login_from_browser() first."
            )

    # ================================================================
    # Entry creation
    # ================================================================

    def create_entry(self, payload: Dict) -> Optional[Dict]:
        """
        Create a single entry on any dynamic screen.

        Args:
            payload: Complete JSON payload matching the screen's format.
                     Must include "attribute_name" matching the screen name.
                     Example for Supplier:
                       {
                           "id": "",
                           "attribute_name": "Supplier",
                           "name": "Test Corp",
                           "ownership_status_ref_id": 3,
                           ...
                       }

        Returns:
            Response JSON dict on success (status 200/201), None on failure.
        """
        self._ensure_auth()

        screen_name = payload.get("attribute_name", "unknown")
        entry_name = (
            payload.get("name")
            or payload.get("company_name")
            or "entry"
        )

        try:
            resp = self.session.post(
                f"{self.BASE_URL}{self.API_ENDPOINT}",
                json=payload,
                timeout=30,
            )
        except requests.ConnectionError:
            log.error(f"[API] Connection error creating {entry_name}")
            return None

        if resp.status_code in (200, 201):
            log.info(f"[API] Created: {entry_name} (screen: {screen_name})")
            return resp.json()
        else:
            # Parse validation errors if available
            error_msg = f"Status {resp.status_code}"
            try:
                error_data = resp.json()
                if "errors" in error_data:
                    errs = error_data["errors"]
                    error_msg = "; ".join(
                        e.get("error_message", str(e)) for e in errs
                    )
                elif "message" in error_data:
                    error_msg = error_data["message"]
            except Exception:
                error_msg = resp.text[:200]

            log.error(
                f"[API] Failed to create '{entry_name}': {error_msg}"
            )
            return None

    def batch_create(
        self, payloads: List[Dict], delay: float = 0.3
    ) -> List[Optional[Dict]]:
        """
        Create multiple entries in sequence.

        Args:
            payloads: List of JSON payloads.
            delay: Seconds between requests to avoid rate limiting.

        Returns:
            List of response JSONs (None for failed entries).
        """
        self._ensure_auth()

        results = []
        total = len(payloads)

        log.info(
            f"[API] Batch creating {total} entries "
            f"(delay={delay}s, est. {total * delay:.1f}s)..."
        )

        for i, payload in enumerate(payloads, 1):
            entry_name = (
                payload.get("name")
                or payload.get("company_name")
                or f"entry-{i}"
            )
            log.info(f"[API] [{i}/{total}] Creating: {entry_name}")

            result = self.create_entry(payload)
            results.append(result)

            if delay and i < total:
                time.sleep(delay)

        success = sum(1 for r in results if r is not None)
        log.info(
            f"[API] Batch complete: {success}/{total} succeeded"
        )
        return results

    # ================================================================
    # Dropdown / FK resolution
    # ================================================================

    def get_screen_schema(self, screen_name: str) -> Optional[Dict]:
        """
        Get the screen schema (field definitions) for a dynamic screen.

        Args:
            screen_name: Screen name, e.g., "Supplier", "Customer"

        Returns:
            Schema dict with screendefinition_set containing all fields,
            or None on failure.
        """
        self._ensure_auth()

        try:
            resp = self.session.get(
                f"{self.BASE_URL}{self.SCREEN_SCHEMA_ENDPOINT.format(screen_name=screen_name)}",
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                log.warning(
                    f"[API] Schema fetch failed for '{screen_name}': "
                    f"{resp.status_code}"
                )
                return None
        except Exception as e:
            log.error(f"[API] Schema fetch error: {e}")
            return None

    def get_dropdown_options(self, screen_name: str, field_key: str) -> List[Dict]:
        """
        Fetch dropdown options for a specific field.

        This uses the screen schema's dropdown_raw_query or filter_dropdown_raw_query
        to find available options. For simple dropdowns (Ownership Status, PO Type),
        the options are returned from the schema's filter_dropdown_raw_query.

        Args:
            screen_name: The screen name (e.g., "Supplier")
            field_key: The field key (e.g., "ownership_status_ref_id")

        Returns:
            List of option dicts with "id" and "key" fields.
        """
        self._ensure_auth()

        schema = self.get_screen_schema(screen_name)
        if not schema:
            return []

        # Search in all field definitions (top-level + children)
        all_fields = self._flatten_fields(schema.get("screendefinition_set", []))

        for field in all_fields:
            if field.get("field_key") == field_key:
                filter_data = field.get("filter_dropdown_raw_query", [])
                if isinstance(filter_data, list) and filter_data:
                    return filter_data
                break

        return []

    def _flatten_fields(self, field_set: List[Dict]) -> List[Dict]:
        """Recursively flatten all fields including children."""
        result = []
        for field in field_set:
            result.append(field)
            if "children" in field and field["children"]:
                result.extend(self._flatten_fields(field["children"]))
        return result

    def find_dropdown_id(
        self, screen_name: str, field_key: str, option_name: str
    ) -> Optional[int]:
        """
        Find a dropdown option's integer ID by its display name.

        Args:
            screen_name: The screen name (e.g., "Supplier")
            field_key: The field key (e.g., "ownership_status_ref_id")
            option_name: The option name to search for (case-insensitive)

        Returns:
            The integer ID, or None if not found.
        """
        options = self.get_dropdown_options(screen_name, field_key)
        for opt in options:
            key = str(opt.get("key", "")).lower()
            if option_name.lower() in key or key in option_name.lower():
                return opt.get("id")
        log.warning(
            f"[API] Dropdown option '{option_name}' not found "
            f"for {screen_name}.{field_key}"
        )
        return None

    # ================================================================
    # List / Read
    # ================================================================

    def list_entries(
        self,
        screen_name: str,
        page: int = 1,
        page_size: int = 10,
        search: str = "",
    ) -> Optional[Dict]:
        """
        List entries for a dynamic screen.

        Args:
            screen_name: Screen name (e.g., "Supplier")
            page: Page number
            page_size: Items per page
            search: Search string

        Returns:
            Response dict with screenmatlistingdata_set, or None.
        """
        self._ensure_auth()

        params = {
            "page_number": page,
            "page_size": page_size,
            "page_data_search_field": "",
            "page_data_search": "",
            "search_string": search,
            "is_excel_download": "false",
        }

        try:
            resp = self.session.get(
                f"{self.BASE_URL}{self.API_ENDPOINT}{screen_name}/",
                params=params,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            log.error(f"[API] List error: {e}")
            return None

    def entry_exists(self, screen_name: str, name: str) -> bool:
        """
        Check if an entry with the given name exists in the screen.

        Args:
            screen_name: Screen name (e.g., "Supplier")
            name: Entry name to search for

        Returns:
            True if found, False otherwise.
        """
        result = self.list_entries(
            screen_name, page=1, page_size=100, search=name
        )
        if result and "screenmatlistingdata_set" in result:
            for entry in result["screenmatlistingdata_set"]:
                if entry.get("name", "").lower() == name.lower():
                    return True
        return False

    # ================================================================
    # Cleanup
    # ================================================================

    def close(self):
        """Close the requests session."""
        self.session.close()
        log.info("[API] Session closed")
