import random
import string
from datetime import datetime


def generate_agent_name():
    prefixes = ["Shree", "Sai", "Nav", "Prime", "Royal", "Global", "Star", "Sri"]
    cores = ["Trading", "Services", "Agencies", "Solutions", "Associates", "Enterprises"]
    return f"{random.choice(prefixes)} {random.choice(cores)}"


def generate_email(prefix="autoagent"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}@testmail.com"


def generate_phone_number():
    first = random.choice(["9", "8", "7", "6"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(9))
    return f"{first}{rest}"


def generate_address():
    numbers = ["101", "202", "303", "404"]
    streets = ["MG Road", "Station Road", "Main Street", "Shivaji Path"]
    areas = ["Pune", "Mumbai", "Nagpur", "Nashik"]
    return f"{random.choice(numbers)} {random.choice(streets)}, {random.choice(areas)}"


def generate_ifsc_code():
    bank = "".join(random.choice(string.ascii_uppercase) for _ in range(4))
    branch = f"0{random.randint(100000, 999999)}"
    return f"{bank}{branch}"


def generate_account_number():
    length = random.randint(10, 16)
    return "".join(str(random.randint(0, 9)) for _ in range(length))
