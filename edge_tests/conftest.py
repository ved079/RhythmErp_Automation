import sys
import os

# Add the project root to the Python path so that we can import config, common, etc.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

@pytest.fixture
def driver():
    """Set up and tear down the WebDriver."""
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@pytest.fixture
def wait(driver):
    """Return a WebDriverWait instance with a 30-second timeout."""
    return WebDriverWait(driver, 30)