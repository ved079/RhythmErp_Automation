#!/usr/bin/env python3
"""
FK Resolver — Auto-discover foreign key IDs from live RhythmERP.

Each batch_create script imports this to resolve dropdown/FK field values
at runtime instead of hardcoding them. This makes scripts portable and
resilient to database changes.

Usage:
    from common.fk_resolver import FkResolver

    resolver = FkResolver(api_client)
    tax_type_ids = resolver.resolve("Tax Type")   # returns {name: id, ...}
    uom_ids      = resolver.resolve("UOM")         # returns {name: id, ...}
    country_ids  = resolver.resolve("Country")     # returns {name: id, ...}
"""

import sys
from pathlib import Path


class FkResolver:
    """Resolves FK dropdown IDs from the live RhythmERP instance."""

    # Known screens and the field to use as the display name
    SCREEN_NAME_FIELDS = {
        "UOM":              "uom_code",
        "UOM Code":         "uom_code",
        "Tax Type":         "name",
        "Country":          "name",
        "State":            "name",
        "District":         "name",
        "Vehicle Type":     "name",
        "Fuel Type":        "name",
        "Account Type":     "name",
        "Account":          "name",
        "Tax Authority":    "tax_name",
        "Error Code Type":  "name",
        "HSN SAC Type":     "name",
        "Ownership Status": "name",
        "Bank":             "bank_name",
        "Item Category":    "item_code",
        "Item Group":       "code",
        "HSN SAC Code":     "code",
        "HSN SAC":          "hsn_sac_no",
        # Item Master FK screens
        "Item Type":          "name",
        "Item Attribute1":    "name",
        "Item Attribute2":    "name",
        "Item Attribute3":    "name",
        "Item Attribute4":    "name",
        "Item Attribute5":    "name",
        "Item Sourcing":      "name",
        # Commodity screens
        "Location":           "name",
        "Item Master":        "name",
        "Quality Parameter":  "name",
        # Customer registration screens
        "Sale Type":          "name",
        "Supply Type":        "name",
        # Farmer registration screens
        "Farmer Category":    "name",
    }

    def __init__(self, api_client):
        """
        Args:
            api_client: ErpApiClient instance with an active session.
        """
        self.api = api_client

    def resolve(self, screen_name, parent_screen=None, field_key=None):
        """
        Resolve all entries for a given screen from the live API, returning {display_name: id}.

        Args:
            screen_name: The ERP screen/attribute_name (e.g. "UOM", "Tax Type")
            parent_screen: The module's own screen name, for fallback via get_dropdown_options
            field_key: The FK field key on the parent screen, for fallback

        Returns:
            dict: {display_name_str: integer_id, ...}
                  e.g. {"Kilogram": 501, "Metric Ton": 502, ...}
        """
        live = self._fetch_from_api(screen_name)
        if live is not None:
            return live
        # Fallback: some screens don't expose list_entries but embed FK
        # options in the parent screen's schema (filter_dropdown_raw_query).
        if parent_screen and field_key:
            options = self.api.get_dropdown_options(parent_screen, field_key)
            if options:
                return {str(opt.get("key", "")): int(opt["id"]) for opt in options if opt.get("id") is not None}
        return {}

    def resolve_one(self, screen_name, display_name):
        """
        Resolve a single FK ID by display name.

        Args:
            screen_name: The ERP screen name (e.g. "UOM")
            display_name: The display name to look up (e.g. "Kilogram")

        Returns:
            int or None: The ID if found, else None
        """
        ids = self.resolve(screen_name)
        return ids.get(display_name)

    def resolve_any_id(self, screen_name):
        """
        Get ANY valid ID from the given screen (useful for picking random FK values).

        Returns:
            int or None: A valid ID, or None if screen is empty
        """
        ids = self.resolve(screen_name)
        if ids:
            return list(ids.values())[0]
        return None

    def resolve_random_ids(self, screen_name, count=3):
        """
        Get multiple random valid IDs from a screen (for variety in batch creation).

        Returns:
            list[int]: List of valid IDs (may be fewer than count if screen has fewer entries)
        """
        import random
        ids = self.resolve(screen_name)
        values = list(ids.values())
        if len(values) <= count:
            return values
        return random.sample(values, count)

    # ── Internal ────────────────────────────────────────────────────────

    def _fetch_from_api(self, screen_name):
        """Query the live ERP to get all entries for a screen."""
        try:
            data = self.api.list_entries(screen_name, page_size=200)
            items = data.get("screenmatlistingdata_set", [])
            if not items:
                return None

            name_field = self.SCREEN_NAME_FIELDS.get(screen_name, "name")
            result = {}

            for item in items:
                item_id = item.get("id")
                # Try the configured name field first, then fall back to common fields
                display = (item.get(name_field)
                           or item.get("name")
                           or item.get("uom_description")
                           or item.get("uom_code")
                           or item.get("tax_name")
                           or item.get("bank_name")
                           or item.get("code")
                           or str(item_id))
                if item_id is not None:
                    result[str(display)] = int(item_id)

            return result if result else None

        except Exception as e:
            print(f"  [FK] Warning: Could not resolve '{screen_name}': {e}")
            return None


# ── Standalone discovery utility ─────────────────────────────────────

def discover_all_fk_ids(api_client, screens=None):
    """
    Discover FK IDs for a list of screens and return the full map.

    Args:
        api_client: ErpApiClient with active session
        screens: list of screen names to resolve. If None, resolves all common ones.

    Returns:
        dict: {screen_name: {display_name: id, ...}, ...}
    """
    if screens is None:
        screens = [
            "UOM", "Tax Type", "Country", "State", "District",
            "Vehicle Type", "Fuel Type", "Account Type", "Account",
            "Tax Authority", "Error Code Type", "HSN SAC Type",
            "Ownership Status",
        ]

    resolver = FkResolver(api_client)
    results = {}
    for screen in screens:
        print(f"  [FK] Resolving '{screen}'...", end=" ", flush=True)
        ids = resolver.resolve(screen)
        count = len(ids)
        print(f"{count} entries found")
        if ids:
            # Show first 5
            for i, (name, fid) in enumerate(ids.items()):
                if i >= 5:
                    print(f"    ... and {count - 5} more")
                    break
                print(f"    {name}: {fid}")
        results[screen] = ids

    return results


if __name__ == "__main__":
    # Standalone FK discovery tool
    print("=" * 70)
    print("  FK ID DISCOVERY TOOL")
    print("=" * 70)
    print()
    print("  Paste your ERP token (from DevTools Authorization header):")
    token = input("  Token: ").strip()

    if not token:
        print("  No token provided. Exiting.")
        sys.exit(1)

    # We need to import the API client
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))

    from common.erp_api_client import ErpApiClient

    api = ErpApiClient()
    api.set_session_from_token(token)

    print()
    results = discover_all_fk_ids(api)

    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for screen, ids in results.items():
        print(f"  {screen}: {len(ids)} IDs resolved")
    print()
    print(f"  All FK IDs resolved from live API (no cache used).")
