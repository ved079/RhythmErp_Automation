import threading, time, os, base64

_driver = None
_thread = None
_stop_event = threading.Event()
_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api', 'screenshots', 'live.b64')

def start(driver):
    global _driver, _thread, _stop_event
    _driver = driver
    _stop_event.clear()
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()

def _loop():
    while not _stop_event.is_set():
        try:
            if _driver:
                b64 = _driver.get_screenshot_as_base64()
                with open(_FILE, 'w') as f:
                    f.write(b64)
        except:
            pass
        _stop_event.wait(2)

def stop():
    global _driver
    _stop_event.set()
    _driver = None
    try:
        if os.path.exists(_FILE):
            os.remove(_FILE)
    except:
        pass