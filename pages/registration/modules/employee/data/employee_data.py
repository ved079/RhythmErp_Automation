import random
from datetime import datetime


def generate_employee_name():
    first = ["Rahul", "Priya", "Amit", "Sneha", "Vijay", "Pooja", "Raj", "Anita",
             "Kiran", "Deepa", "Suresh", "Kavita", "Nitin", "Shruti", "Arun", "Neha",
             "Manoj", "Sunita", "Ravi", "Geeta"]
    last  = ["Sharma", "Patil", "Desai", "Kulkarni", "Joshi", "Mehta", "Nair", "Reddy",
             "Iyer", "Pillai", "Bose", "Das", "Rao", "Singh", "Kumar", "Verma",
             "Gupta", "Shah", "Kapoor", "Mishra"]
    middle = ["", "B", "R", "K", "S", "M", "D", "P", "V", "N"]
    m = random.choice(middle)
    return f"{random.choice(first)} {m + ' ' if m else ''}{random.choice(last)}"


def generate_email(prefix="autoemp"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = random.randint(100, 999)
    return f"{prefix}_{timestamp}_{rand}@testmail.com"


def generate_phone_number():
    first = random.choice(["9", "8", "7", "6"])
    rest = "".join(str(random.randint(0, 9)) for _ in range(9))
    return f"{first}{rest}"
