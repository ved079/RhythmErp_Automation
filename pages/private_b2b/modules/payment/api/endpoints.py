SCREEN_NAME = "Payment"

PAYMENT_CREATE = "/procure_to_pay/payments/"
PAYMENT_LIST   = "/procure_to_pay/payments/"
PAYMENT_GET    = "/procure_to_pay/payments/{entry_id}/"

# Bank accounts are fetched via the dynamic-screen-wrapper
BANK_LIST  = "/core/dynamic-screen-wrapper/Bank/"
BANK_GET   = "/core/dynamic-screen-wrapper/Bank/{bank_id}/"
BANK_PUT   = "/core/dynamic-screen-wrapper/{bank_id}/"  # edit uses numeric-id endpoint


def build_create_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PAYMENT_CREATE}"


def build_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{PAYMENT_LIST}"


def build_get_url(base_url: str, entry_id) -> str:
    return f"{base_url.rstrip('/')}{PAYMENT_GET.format(entry_id=entry_id)}"


def build_bank_list_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}{BANK_LIST}"


def build_bank_get_url(base_url: str, bank_id) -> str:
    return f"{base_url.rstrip('/')}{BANK_GET.format(bank_id=bank_id)}"


def build_bank_put_url(base_url: str, bank_id) -> str:
    return f"{base_url.rstrip('/')}{BANK_PUT.format(bank_id=bank_id)}"


# Payment types (from ERP filter_dropdown_raw_query)
PAYMENT_TYPE_REGULAR = 151
PAYMENT_TYPE_ADVANCE = 152

# Payment methods
PAYMENT_METHOD_CASH   = 53
PAYMENT_METHOD_CHEQUE = 54
PAYMENT_METHOD_DD     = 55
PAYMENT_METHOD_IMPS   = 141
PAYMENT_METHOD_RTGS   = 143
