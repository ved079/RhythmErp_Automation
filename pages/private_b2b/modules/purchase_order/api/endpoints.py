SCREEN_NAME = "Purchase Order"

PO_CREATE = "/procure_to_pay/purchase_order/"
PO_LIST = "/procure_to_pay/purchase_order/"
PO_GET = "/procure_to_pay/purchase_order/{entry_id}/"
PO_UPDATE = "/procure_to_pay/purchase_order/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
PO_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PO_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PO_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{PO_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{PO_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PO_SCHEMA}"
