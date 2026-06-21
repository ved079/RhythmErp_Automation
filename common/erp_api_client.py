"""
erp_api_client.py
-----------------
Direct API client for Rhythm ERP dynamic screens.
Bypasses the UI entirely for fast, reliable data creation.

Uses the same endpoint that the Angular frontend uses:
  POST /core/dynamic-screen-wrapper/

Authentication:
  - Bearer token obtained via /auth/login1/ (pure API, no browser needed)
  - Token extracted from refresh_token cookie in Set-Cookie header
  - X-Tenant-ID header (e.g., "681")

Usage:
    client = RhythmERPAPIClient()
    client.login()
    client.create_entry({"id": "", "attribute_name": "Designation", ...})

    # Or use existing browser token:
    client = RhythmERPAPIClient()
    client.login_from_browser(token="eyJ...", tenant_id="681")

    # Discover a screen's payload structure:
    structure = client.discover_structure("Supplier")

Speed comparison:
  - UI via Selenium: 30-60 seconds per entry (flaky with Angular Material)
  - API via this client: ~0.3 seconds per entry (deterministic)
"""

import re
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
        tenant_id: str = "681",
    ):
        """
        Initialize the API client.

        Args:
            username: Email for login (defaults to RHYTHMERP_EMAIL from .env)
            password: Password for login (defaults to RHYTHMERP_PASSWORD from .env)
            tenant_id: X-Tenant-ID header value (default "681")
        """
        self.username = username or config.RHYTHMERP_EMAIL
        self.password = password or config.RHYTHMERP_PASSWORD
        self.tenant_id = tenant_id
        self.session = requests.Session()
        self.token = None
        self._logged_in = False

        # WARNING: _last_raw_response is NOT thread-safe. Concurrent API calls may
        # overwrite this value. Do not run API validation tests in parallel until
        # the base client is refactored to return (result, response) tuples.
        self._last_raw_response = None

    # ================================================================
    # Authentication
    # ================================================================

    def login(self) -> tuple:
        """
        Authenticate against the ERP and obtain a Bearer token.

        Uses the /auth/login1/ endpoint discovered from the ERP's auth flow.
        The token is extracted from the refresh_token cookie in the
        Set-Cookie response header — this is a valid JWT that works as
        a Bearer token for all subsequent API calls.

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

        # POST to /auth/login1/ with username, password, and tenant
        login_url = f"{self.BASE_URL}/auth/login1/"

        try:
            resp = self.session.post(
                login_url,
                json={
                    "username": self.username,
                    "password": self.password,
                    "tenant": self.tenant_id,
                },
                timeout=30,
            )
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot reach ERP at {self.BASE_URL}. "
                "Check network or VPN connection."
            )

        # Extract JWT from the refresh_token cookie in Set-Cookie header
        set_cookie = resp.headers.get("Set-Cookie", "")
        match = re.search(r'refresh_token=([^;]+)', set_cookie)

        if not match:
            # Fallback: try extracting from response body (some versions)
            if resp.status_code == 200:
                data = resp.json()
                self.token = (
                    data.get("access")
                    or data.get("token")
                    or data.get("key")
                    or data.get("auth_token")
                )
                if self.token:
                    self._set_session_headers()
                    self._logged_in = True
                    log.info(
                        f"[API] Login successful (body token). "
                        f"Tenant: {self.tenant_id}"
                    )
                    return self.token, self.tenant_id

            log.warning(
                f"[API] /auth/login1/ returned {resp.status_code}. "
                "Trying fallback endpoints..."
            )
            self._fallback_login()
            return self.token, self.tenant_id

        self.token = match.group(1)
        self._set_session_headers()
        self._logged_in = True

        log.info(
            f"[API] Login successful. Token: {self.token[:30]}... "
            f"Tenant: {self.tenant_id}"
        )
        return self.token, self.tenant_id

    def _fallback_login(self):
        """
        Fallback: try alternative login endpoints if /auth/login1/ fails.

        Tries older/different API paths and extracts token from
        response body or cookies.
        """
        login_urls = [
            f"{self.BASE_URL}/api/auth/login/",
            f"{self.BASE_URL}/api/token/",
            f"{self.BASE_URL}/api/v1/auth/login/",
        ]

        for url in login_urls:
            try:
                # Try with "username" key first (same as login1)
                for payload_keys in [
                    {"username": self.username, "password": self.password, "tenant": self.tenant_id},
                    {"email": self.username, "password": self.password},
                ]:
                    resp = self.session.post(url, json=payload_keys, timeout=30)

                    if resp.status_code == 200:
                        # Try cookie first
                        set_cookie = resp.headers.get("Set-Cookie", "")
                        match = re.search(r'refresh_token=([^;]+)', set_cookie)
                        if match:
                            self.token = match.group(1)
                        else:
                            data = resp.json()
                            self.token = (
                                data.get("access")
                                or data.get("token")
                                or data.get("key")
                            )

                        if self.token:
                            self._set_session_headers()
                            self._logged_in = True
                            log.info(f"[API] Fallback login successful via {url}")
                            return
            except Exception:
                continue

        raise ValueError(
            "Could not authenticate via any known login endpoint. "
            "Use login_from_browser() with a token captured from DevTools."
        )

    def login_from_browser(self, token: str, tenant_id: str = "681"):
        """
        Set auth using a token captured from the browser's DevTools.

        Use this when the login endpoint is unknown or returns an
        encrypted token. Capture the real Bearer token by:
        1. Open ERP in Chrome DevTools -> Network tab
        2. Look at any XHR request to /core/...
        3. Copy the Authorization header value (after "Bearer ")

        Args:
            token: Bearer token string (WITHOUT "Bearer " prefix)
            tenant_id: X-Tenant-ID value (default "681")
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
            self._last_raw_response = None
            return None

        # WARNING: _last_raw_response is NOT thread-safe. Concurrent API calls may
        # overwrite this value. Do not run API validation tests in parallel until
        # the base client is refactored to return (result, response) tuples.
        self._last_raw_response = resp

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
            self._last_raw_response = resp
            if resp.status_code == 200:
                return resp.json()
            log.warning(
                f"[API] List entries failed for '{screen_name}': "
                f"{resp.status_code} — {resp.text[:200]}"
            )
            return None
        except requests.ConnectionError:
            self._last_raw_response = None
            log.error(f"[API] Connection error listing '{screen_name}'")
            return None
        except Exception as e:
            self._last_raw_response = None
            log.error(f"[API] List error: {e}")
            return None

    def update_entry(self, entry_id, payload: Dict) -> Optional[Dict]:
        """
        Update an existing entry on any dynamic screen.

        The ERP uses POST to the same create endpoint for updates.
        It distinguishes create vs update by the ``id`` field:
          - Create: POST /core/dynamic-screen-wrapper/  with id="" (empty)
          - Update: POST /core/dynamic-screen-wrapper/  with id=<existing_id>

        Neither PUT nor POST work on /{ScreenName}/{id}/ — both return 405.
        The {id}/ sub-path only accepts GET (for reading entries).

        Args:
            entry_id: The entry's ID to update.
            payload: Complete JSON payload with updated fields.
                     Must include "attribute_name" matching the screen name
                     and "id" set to the existing entry ID.

        Returns:
            Response JSON dict on success, None on failure.
        """
        self._ensure_auth()

        entry_name = (
            payload.get("name")
            or payload.get("company_name")
            or f"entry-{entry_id}"
        )

        # Ensure the payload has the correct ID for update
        # This is how the ERP distinguishes create (id="") from update (id=<int>)
        payload["id"] = entry_id

        try:
            resp = self.session.post(
                f"{self.BASE_URL}{self.API_ENDPOINT}",
                json=payload,
                timeout=30,
            )
        except requests.ConnectionError:
            log.error(f"[API] Connection error updating {entry_name}")
            self._last_raw_response = None
            return None

        # WARNING: _last_raw_response is NOT thread-safe. Concurrent API calls may
        # overwrite this value. Do not run API validation tests in parallel until
        # the base client is refactored to return (result, response) tuples.
        self._last_raw_response = resp

        if resp.status_code in (200, 201):
            log.info(f"[API] Updated: {entry_name} (id={entry_id})")
            return resp.json()
        else:
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
                f"[API] Failed to update '{entry_name}' (id={entry_id}): {error_msg}"
            )
            return None

    def get_entry(self, screen_name: str, entry_id) -> Optional[Dict]:
        """
        Get a detailed entry by ID.

        This is the MOST IMPORTANT method for discovering payload structure.
        The response shows the FULL JSON including nested children arrays.

        Args:
            screen_name: Screen name (e.g., "Supplier")
            entry_id: The entry's ID (from list_entries)

        Returns:
            Complete entry dict with all fields and nested structures, or None.
        """
        self._ensure_auth()

        try:
            resp = self.session.get(
                f"{self.BASE_URL}{self.API_ENDPOINT}{screen_name}/{entry_id}/",
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            log.warning(
                f"[API] Get entry failed for {screen_name}/{entry_id}: "
                f"{resp.status_code}"
            )
            return None
        except Exception as e:
            log.error(f"[API] Get entry error: {e}")
            return None

    def discover_structure(self, screen_name: str) -> Optional[Dict]:
        """
        Auto-discover the payload structure for a screen.

        Fetches the list endpoint to find an existing entry, then fetches
        the detailed entry to reveal the full JSON structure including
        nested children arrays and stepper objects.

        Use this when adding API support for a NEW screen:
          1. Call discover_structure("NewScreen")
          2. Study the returned dict
          3. If it has 'children' with 'stepper_name' -> complex screen
          4. If flat with no children -> simple screen
          5. Copy the structure as your payload template

        Args:
            screen_name: Screen name (e.g., "Supplier", "Customer")

        Returns:
            Detailed entry dict (use as template), or None if no entries exist.
        """
        self._ensure_auth()

        log.info(f"[API] Discovering structure for '{screen_name}'...")

        # Step 1: Get list of existing entries
        data = self.list_entries(screen_name, page=1, page_size=5)
        if not data:
            log.warning(f"[API] Could not list entries for '{screen_name}'")
            return None

        items = data.get("screenmatlistingdata_set", [])
        if not items:
            log.warning(
                f"[API] No existing entries for '{screen_name}'. "
                "Create one manually via UI first, then re-run."
            )
            return None

        # Step 2: Get detailed entry for the first item
        entry_id = items[0].get("id")
        if not entry_id:
            log.warning("[API] First entry has no ID")
            return None

        detail = self.get_entry(screen_name, entry_id)
        if detail:
            # Log structure hints
            has_children = "children" in detail and bool(detail["children"])
            if has_children:
                stepper_names = [
                    c.get("stepper_name", "?")
                    for c in detail.get("children", [])
                ]
                log.info(
                    f"[API] Complex screen: {len(detail['children'])} stepper(s) "
                    f"— {stepper_names}"
                )
            else:
                log.info("[API] Simple screen: flat structure (no children/steppers)")

            log.info(
                f"[API] Top-level keys: {list(detail.keys())}"
            )

        return detail

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
    # Workflow actions
    # ================================================================

    def workflow_action(
        self,
        screen_name: str,
        entry_id: int,
        workflow_id: str,
        conditions: list,
        execution_reference: str,
        node_id: int = None,
        label: str = "",
        workflow_data: dict = None,
    ) -> Optional[Dict]:
        """
        Perform a workflow transition on an entry.

        Sends the full workflow_data so the server can validate field-level
        conditions (e.g. land_classification check on Farmer Verify).

        Args:
            screen_name: Screen name (e.g., "Farmer")
            entry_id: Entry ID
            workflow_id: Workflow UUID from the entry GET response
            conditions: List of condition dicts from workflow_action.rawConditions.paths[].conditions
            execution_reference: Base64-encoded execution reference string
            node_id: nodeId from the workflow path
            label: Action label e.g. "Verify", "Approve"
            workflow_data: Full entry record from get_entry() — required for Farmer

        Returns:
            Response JSON dict on success (200/201), None on failure.
        """
        self._ensure_auth()

        body = {
            "attribute_name": screen_name,
            "executionReference": execution_reference,
            "nodeId": node_id,
            "label": label,
            "conditions": conditions,
            "id": entry_id,
            "workflow_id": workflow_id,
            "workflow_remark": "",
            "workflow_error_codes": [],
        }
        if workflow_data is not None:
            body["workflow_data"] = workflow_data

        try:
            resp = self.session.post(
                f"{self.BASE_URL}/core/dynamic-screen-workflow-action/",
                json=body,
                timeout=30,
            )
        except requests.ConnectionError:
            log.error(f"[API] Connection error on workflow action for {screen_name}#{entry_id}")
            self._last_raw_response = None
            return None

        self._last_raw_response = resp

        if resp.status_code in (200, 201):
            log.info(f"[API] Workflow action succeeded for {screen_name}#{entry_id}")
            return resp.json()
        else:
            error_msg = f"Status {resp.status_code}"
            try:
                error_data = resp.json()
                if "error" in error_data:
                    error_msg = error_data["error"]
                elif "message" in error_data:
                    error_msg = error_data["message"]
            except Exception:
                error_msg = resp.text[:200]
            log.error(
                f"[API] Workflow action failed for {screen_name}#{entry_id}: {error_msg}"
            )
            return None

    def workflow_action_from_entry(
        self,
        screen_name: str,
        entry_id: int,
        label: str,
    ) -> Optional[Dict]:
        """
        High-level helper: GET the entry, find the matching workflow path by label,
        and POST the workflow action with the full entry as workflow_data.

        This is the correct way to do Verify/Approve — mirrors exactly what the
        browser does when the Edit form is open and you click Verify/Approve.

        Returns the response dict on success, or None with the error logged.
        """
        entry = self.get_entry(screen_name, entry_id)
        if not entry:
            log.error(f"[API] workflow_action_from_entry: could not GET {screen_name}#{entry_id}")
            return None

        wf = entry.get("workflow_action", {})
        paths = wf.get("rawConditions", {}).get("paths", [])
        path = next((p for p in paths if p.get("label") == label), None)
        if not path:
            available = [p.get("label") for p in paths]
            log.error(
                f"[API] workflow_action_from_entry: label '{label}' not available for "
                f"{screen_name}#{entry_id}. Available: {available}"
            )
            return None

        workflow_id = entry.get("workflow_id", "")
        # Build workflow_data: the entry record without the workflow meta fields
        workflow_data = {k: v for k, v in entry.items()
                         if k not in ("workflow_action", "workflow_id",
                                      "workflow_error_codes", "workflow_remark",
                                      "attribute_name")}
        workflow_data.setdefault("create_version", False)

        return self.workflow_action(
            screen_name=screen_name,
            entry_id=entry_id,
            workflow_id=workflow_id,
            conditions=path.get("conditions", []),
            execution_reference=path.get("executionReference", ""),
            node_id=path.get("nodeId"),
            label=label,
            workflow_data=workflow_data,
        )

    # ================================================================
    # Cleanup
    # ================================================================

    def close(self):
        """Close the requests session."""
        self.session.close()
        log.info("[API] Session closed")


# ═══════════════════════════════════════════════════════════════════════════════
# ErpApiClient — Thin wrapper for batch_create scripts
# ═══════════════════════════════════════════════════════════════════════════════
# The v2 batch_create scripts use this simpler interface:
#   - prompt_for_token() + set_session_from_token(token)  instead of login()
#   - batch_create(screen_name, payloads)                  instead of batch_create(payloads)
#   - print_results(results, screen_name)                  for pretty printing
#   - Results are [{success: bool, ...}, ...]              instead of [Dict|None, ...]
# ═══════════════════════════════════════════════════════════════════════════════

class ErpApiClient(RhythmERPAPIClient):
    """
    Convenience wrapper for API-first batch creation scripts.

    Extends RhythmERPAPIClient with:
      - prompt_for_token(): interactive token input from DevTools
      - set_session_from_token(): quick auth setup
      - batch_create(screen_name, payloads): takes screen_name + payloads,
        returns [{success: bool, data/error: ...}, ...]
      - print_results(): pretty-print batch results
    """

    def prompt_for_token(self) -> str:
        """
        Interactively prompt the user for their Bearer token.

        The token can be captured from Chrome DevTools:
          1. Open ERP in Chrome -> F12 -> Network tab
          2. Click any XHR request to /core/...
          3. Copy the Authorization header value (after "Bearer ")

        Returns:
            The token string entered by the user.
        """
        print()
        print("  Paste your ERP token (from DevTools Authorization header):")
        print("  (Look for 'Bearer xxx...' in any /core/ request)")
        token = input("  Token: ").strip()
        return token

    def set_session_from_token(self, token: str, tenant_id: str = "681"):
        """
        Set the session using a Bearer token from DevTools.

        Args:
            token: Bearer token string (with or without "Bearer " prefix)
            tenant_id: X-Tenant-ID value (default "681")
        """
        # Strip "Bearer " prefix if the user pasted the full header
        if token.startswith("Bearer "):
            token = token[7:]
        self.login_from_browser(token, tenant_id)
        print(f"  Session set. Tenant: {tenant_id}")

    def batch_create(self, screen_name: str, payloads: list, delay: float = 0.3) -> list:
        """
        Create multiple entries on a specific screen.

        Args:
            screen_name: The ERP screen name (e.g., "Bank", "Tax Rate")
            payloads: List of JSON payloads (each must include attribute_name)
            delay: Seconds between requests

        Returns:
            List of result dicts: [{"success": True/False, "data": ..., "error": ...}, ...]
        """
        self._ensure_auth()

        results = []
        total = len(payloads)

        print(f"  Creating {total} entries on '{screen_name}'...")

        for i, payload in enumerate(payloads, 1):
            # Get a display name for logging
            entry_name = (
                payload.get("name")
                or payload.get("tax_name")
                or payload.get("bank_name")
                or payload.get("tax_rate_name")
                or payload.get("company_name")
                or f"entry-{i}"
            )

            print(f"    [{i}/{total}] {entry_name}...", end=" ", flush=True)

            result = self.create_entry(payload)

            if result is not None:
                results.append({"success": True, "data": result})
                print("OK")
            else:
                last_resp = self._last_raw_response
                if last_resp is not None:
                    status = last_resp.status_code
                    body = last_resp.text[:500].replace('\n', ' ').replace('\r', '')
                    error_detail = f"HTTP {status}: {body}"
                else:
                    error_detail = "No response (network error)"
                results.append({"success": False, "error": error_detail})
                print(f"FAILED ({error_detail[:120]})")

            if delay and i < total:
                time.sleep(delay)

        return results

    def print_results(self, results: list, screen_name: str):
        """
        Pretty-print batch creation results.

        Args:
            results: List of result dicts from batch_create()
            screen_name: Screen name for display
        """
        created = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))

        print()
        print(f"  {screen_name}: {created}/{len(results)} created", end="")
        if failed:
            print(f", {failed} failed")
        else:
            print()

        # Show failure details
        for i, r in enumerate(results):
            if not r.get("success"):
                print(f"    Entry {i+1}: {r.get('error', 'Unknown error')}")

    def list_entries(self, screen_name: str, page_size: int = 200, **kwargs) -> dict:
        """
        List entries for a screen. Overrides parent to simplify the interface.

        Args:
            screen_name: Screen name
            page_size: Number of entries per page (default 200 for FK resolution)

        Returns:
            Response dict with screenmatlistingdata_set
        """
        return super().list_entries(
            screen_name,
            page=kwargs.get("page", 1),
            page_size=page_size,
            search=kwargs.get("search", ""),
        )
