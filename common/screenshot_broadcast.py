"""
screenshot_broadcast.py
-----------------------
Background thread that captures browser screenshots and writes them
to a file for the API to serve. Used for live screenshot streaming.
"""

import threading
import time
import os
import base64
import logging

logger = logging.getLogger(__name__)

_driver = None
_thread = None
_stop_event = threading.Event()
_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'api', 'screenshots', 'live.b64'
)


def start(driver):
    """Start the screenshot broadcast thread."""
    global _driver, _thread, _stop_event

    if _thread is not None and _thread.is_alive():
        logger.warning("Screenshot broadcast already running — stopping previous instance")
        stop()

    _driver = driver
    _stop_event.clear()
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()
    logger.info("Screenshot broadcast started")


def _loop():
    """Main broadcast loop — captures screenshots every 2 seconds."""
    while not _stop_event.is_set():
        try:
            if _driver:
                b64 = _driver.get_screenshot_as_base64()
                with open(_FILE, 'w') as f:
                    f.write(b64)
        except Exception as e:
            logger.debug(f"Screenshot capture failed: {e}")
        _stop_event.wait(2)


def stop():
    """Stop the screenshot broadcast thread and clean up."""
    global _driver
    _stop_event.set()
    _driver = None
    try:
        if os.path.exists(_FILE):
            os.remove(_FILE)
    except OSError:
        pass
    if _thread is not None:
        _thread.join(timeout=5)
    logger.info("Screenshot broadcast stopped")
