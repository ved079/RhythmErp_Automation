SCREEN_NAME = "QC"

QC_CREATE = "/procure_to_pay/quality-control/"
QC_LIST = "/procure_to_pay/quality-control/"
QC_GET = "/procure_to_pay/quality-control/{entry_id}/"
QC_UPDATE = "/procure_to_pay/quality-control/{entry_id}/"

DYNAMIC_SCREEN = "/core/dynamic-screen/{screen_name}/"
QC_SCHEMA = DYNAMIC_SCREEN.format(screen_name=SCREEN_NAME)


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{QC_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{QC_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{QC_GET.format(entry_id=entry_id)}"


def build_update_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{QC_UPDATE.format(entry_id=entry_id)}"


def build_schema_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{QC_SCHEMA}"
