SCREEN_NAME = "Purchase Booking"

# REST endpoints follow the same procure_to_pay pattern as GP, QC, GRN:
#   GP  → /procure_to_pay/gate-pass/
#   QC  → /procure_to_pay/quality-control/
#   GRN → /procure_to_pay/grn/
# If this URL returns 404, try /procure_to_pay/purchase_booking/ (snake_case)
PB_CREATE = "/procure_to_pay/purchase-booking/"
PB_LIST   = "/procure_to_pay/purchase-booking/"
PB_GET    = "/procure_to_pay/purchase-booking/{entry_id}/"
PB_UPDATE = "/procure_to_pay/purchase-booking/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
PB_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PB_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PB_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{PB_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{PB_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PB_SCHEMA}"


# Query params required by the ERP's async SUBMIT pipeline.
# Without request_method=SUBMIT the server takes a different code path and 500s.
CREATE_PARAMS = {
    "screenName": SCREEN_NAME,
    "request_method": "SUBMIT",
}
