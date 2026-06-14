SCREEN_NAME = "Gate Pass"

GP_CREATE = "/procure_to_pay/gate-pass/"
GP_LIST = "/procure_to_pay/gate-pass/"
GP_GET = "/procure_to_pay/gate-pass/{entry_id}/"
GP_UPDATE = "/procure_to_pay/gate-pass/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
GP_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GP_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GP_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{GP_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{GP_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GP_SCHEMA}"
