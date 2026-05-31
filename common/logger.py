"""
logger.py
---------
Custom logging utility for PACS Automation.
Provides colored console output and file logging.
"""

import logging
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


class CustomLogger:
    """
    Custom logger with colored output for test execution.
    Usage:
        log = CustomLogger()
        log.info("Starting test")
        log.passed("Test passed")
        log.failed("Test failed")
        log.error("Something went wrong")
    """

    def __init__(self, log_file=None):
        self.logger = logging.getLogger("PACS_Automation")
        self.logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

            # File handler (optional)
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_format = logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(filename)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
                file_handler.setFormatter(file_format)
                self.logger.addHandler(file_handler)

    def info(self, message):
        """Blue info message."""
        self.logger.info(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

    def passed(self, message):
        """Green pass message."""
        self.logger.info(f"{Fore.GREEN}[PASSED] {message}{Style.RESET_ALL}")

    def failed(self, message):
        """Red fail message."""
        self.logger.error(f"{Fore.RED}[FAILED] {message}{Style.RESET_ALL}")

    def error(self, message):
        """Red error message."""
        self.logger.error(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")

    def warning(self, message):
        """Yellow warning message."""
        self.logger.warning(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")

    def step(self, step_num, message):
        """Yellow step message with step number."""
        self.logger.info(f"{Fore.YELLOW}  Step {step_num}: {message}{Style.RESET_ALL}")

    def separator(self, char="=", length=60):
        """Print a visual separator line."""
        self.logger.info(f"{Fore.WHITE}{char * length}{Style.RESET_ALL}")

    def test_start(self, test_name):
        """Print test start banner."""
        self.separator()
        self.info(f" Running: {test_name}")
        self.separator()

    def test_end(self, test_name, status):
        """Print test end with status."""
        if status.lower() == "passed":
            self.passed(test_name)
        else:
            self.failed(test_name)
        self.separator()


# Create a global logger instance
log = CustomLogger()
