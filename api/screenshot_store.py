"""Global store for the active Selenium driver — used by screenshot API."""

_driver = None

def set_driver(driver):
    global _driver
    _driver = driver

def get_driver():
    return _driver

def take_screenshot() -> str | None:
    """Returns base64 PNG string or None if no driver active."""
    if _driver is None:
        return None
    try:
        return _driver.get_screenshot_as_base64()
    except Exception:
        return None