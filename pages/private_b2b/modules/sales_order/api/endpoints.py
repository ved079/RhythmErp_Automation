SCREEN_NAME = "Sales Order"

# Sales Order lives in the portal `sales` app (portal.views.sales_order_new).
# Discovered live from the frontend Network tab: list at /sales/sales-order-new/,
# create posts to /sales/sales-order-new/?screen_name=Sales%20Order&viewType=create,
# detail GET at /sales/sales-order-new/{id}/.
SO_CREATE = "/sales/sales-order-new/"
SO_LIST   = "/sales/sales-order-new/"
SO_GET    = "/sales/sales-order-new/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
SO_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{SO_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{SO_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{SO_GET.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{SO_SCHEMA}"
