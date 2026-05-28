"""
screenshot_store.py
-------------------
Reads the live screenshot file (written by screenshot_broadcast)
for the API to serve. Includes caching to avoid repeated file reads.
"""

import os
import logging

logger = logging.getLogger(__name__)

_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots', 'live.b64')
_last_mtime = 0
_last_data = None
_driver_ref = None


def set_driver(driver):
    """Set the driver reference for direct screenshot capture fallback."""
    global _driver_ref
    _driver_ref = driver


def take_screenshot():
    """Returns base64 screenshot string, or None if no screenshot available."""
    global _last_mtime, _last_data
    try:
        if not os.path.exists(_FILE):
            return None
        mtime = os.path.getmtime(_FILE)
        if mtime == _last_mtime and _last_data:
            return _last_data
        with open(_FILE, 'r') as f:
            data = f.read().strip()
        if data:
            _last_mtime = mtime
            _last_data = data
            return data
    except OSError as e:
        logger.debug(f"Could not read screenshot file: {e}")
    except Exception as e:
        logger.debug(f"Unexpected error reading screenshot: {e}")
    return None
