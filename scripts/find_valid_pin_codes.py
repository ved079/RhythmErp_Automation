r"""
find_valid_pin_codes.py
-----------------------
Try common pin codes for our verified address chains to find ones
the server accepts. Run once, then hardcode the results.

Run:
    python -m scripts.find_valid_pin_codes
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from common.erp_api_client import RhythmERPAPIClient
from pages.registration.modules.agent.utils.api_agent_utils import AgentAPIUtils
from common.logger import log


# Pin codes to try per address chain (district-specific common codes)
_PIN_CODE_ATTEMPTS = {
    # Maharashtra / Akola (district 208)
    "maharashtra_akola": [
        444001, 444002, 444003, 444004, 444005,
        444100, 444101, 444102, 444103,
        444200, 444201, 444202, 444203,
        444601, 444602, 444603,
        444701, 444702,
    ],
    # Punjab (district 764)
    "punjab": [
        141001, 141002, 141003, 141004, 141005,
        141100, 141101, 141102,
        141200, 141201,
        141300, 141400,
    ],
    # State 101 / district 233
    "state101_dist233": [
        380001, 380002, 380003, 380004, 380005,
        380006, 380007, 380008, 380009,
        380010, 380011, 380012,
        382001, 382002, 382003,
        382110, 382115, 382120,
        382140, 382150,
        382330, 382340, 382350,
        383001, 383002,
        384001, 384002,
    ],
}


def main():
    log.info("Logging in...")
    client = RhythmERPAPIClient()
    client.login()
    api = AgentAPIUtils(api_client=client)
    log.info("Login OK\n")

    valid_pins = {}

    chains = [
        ("maharashtra_akola", {
            "state_ref_id_id": 12,
            "district_ref_id_id": 208,
            "sub_district_ref_id_id": 13041,
            "village_ref_id_id": 422660,
        }),
        ("punjab", {
            "state_ref_id_id": 82,
            "district_ref_id_id": 764,
            "sub_district_ref_id_id": 13939,
            "village_ref_id_id": 775472,
        }),
        ("state101_dist233", {
            "state_ref_id_id": 101,
            "district_ref_id_id": 233,
            "sub_district_ref_id_id": 12979,
            "village_ref_id_id": None,
        }),
    ]

    for chain_name, chain_data in chains:
        print(f"\n{'='*50}")
        print(f"  Testing: {chain_name}")
        print(f"{'='*50}")

        found = False
        for pin in _PIN_CODE_ATTEMPTS[chain_name]:
            # Build minimal payload with this pin code
            payload = api.generate_unique_payload(name_prefix="PinTest")
            # Override ALL address rows with this chain + pin
            for child in payload.get("children", []):
                if child.get("stepper_name") == "Address Details":
                    for detail in child.get("details", []):
                        detail["state_ref_id_id"] = chain_data["state_ref_id_id"]
                        detail["district_ref_id_id"] = chain_data["district_ref_id_id"]
                        detail["sub_district_ref_id_id"] = chain_data["sub_district_ref_id_id"]
                        detail["village_ref_id_id"] = chain_data.get("village_ref_id_id")
                        detail["pin_code"] = pin

            result = client.create_entry(payload)
            raw = client._last_raw_response

            if result is not None:
                print(f"  PIN {pin}: ACCEPTED (id={result.get('id')})")
                valid_pins[chain_name] = pin
                found = True
                break
            else:
                # Check if it was pin_code error or something else
                error_msg = ""
                if raw and raw.text:
                    try:
                        error_data = raw.json()
                        if "errors" in error_data:
                            error_msg = "; ".join(
                                e.get("error_message", str(e))
                                for e in error_data["errors"]
                            )
                        elif "message" in error_data:
                            error_msg = error_data["message"]
                    except Exception:
                        error_msg = raw.text[:100]
                print(f"  PIN {pin}: REJECTED — {error_msg}")

        if not found:
            print(f"  No valid pin code found for {chain_name}!")

    # Summary
    print(f"\n\n{'#'*50}")
    print(f"  VALID PIN CODES")
    print(f"{'#'*50}")
    for chain_name, pin in valid_pins.items():
        print(f"  {chain_name}: {pin}")

    print(f"\n  Copy these into _ADDRESS_CHAINS in api_agent_utils.py")

    client.close()


if __name__ == "__main__":
    main()
