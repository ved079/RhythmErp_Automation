SCREEN_NAME = "Goods Receipt Note"

GRN_CREATE = "/procure_to_pay/grn/"
GRN_LIST = "/procure_to_pay/grn/"
GRN_GET = "/procure_to_pay/grn/{entry_id}/"
GRN_UPDATE = "/procure_to_pay/grn/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
GRN_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GRN_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GRN_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{GRN_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{GRN_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{GRN_SCHEMA}"
