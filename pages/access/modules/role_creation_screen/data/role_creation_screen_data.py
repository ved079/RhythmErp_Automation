"""
Role Creation Screen – Test Data Generators
RhythmERP  https://rhythmerp.algorhythms.in/#/master-setup/Rolecreationscreen
"""

import random
import string
import time


# ══════════════════════════════════════════════════════════════════════
#  UNIQUE  SUFFIX  –  avoids collisions across runs
# ══════════════════════════════════════════════════════════════════════
def _ts() -> str:
    """Compact timestamp suffix:  YYMMDDHHmmss"""
    return time.strftime("%y%m%d%H%M%S")


def _rand(n: int = 4) -> str:
    """Random alphanumeric suffix of length *n*."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


# ══════════════════════════════════════════════════════════════════════
#  CREATE  PHASE  DATA
# ══════════════════════════════════════════════════════════════════════
def valid_role_name() -> str:
    """Auto-generated unique role name for happy-path creation."""
    return f"AutoRole_{_ts()}_{_rand()}"


def valid_role_description() -> str:
    return f"Automated test role – {_ts()}"


def valid_role_code() -> str:
    return f"RC{_ts()}"


def create_payload(name: str = "", description: str = "", code: str = "") -> dict:
    """Return a dict with all fields populated if not overridden."""
    return {
        "name": name or valid_role_name(),
        "description": description or valid_role_description(),
        "code": code or valid_role_code(),
    }


# ══════════════════════════════════════════════════════════════════════
#  DUPLICATE  PHASE  DATA
# ══════════════════════════════════════════════════════════════════════
def duplicate_name_exact(base: str) -> str:
    """Return the same name – exact duplicate attempt."""
    return base


def duplicate_name_case_flipped(base: str) -> str:
    """Flip case of every character (case-insensitive dupe check)."""
    return base.swapcase()


def duplicate_name_with_spaces(base: str) -> str:
    """Add leading / trailing spaces and double internal spaces."""
    return f"  {base.replace(' ', '  ')}  "


# ══════════════════════════════════════════════════════════════════════
#  EDIT  PHASE  DATA
# ══════════════════════════════════════════════════════════════════════
def edited_role_name(base: str) -> str:
    return f"{base}_Edited"


def edited_role_description(base: str) -> str:
    return f"{base}_DescEdited"


def edited_role_code(base: str) -> str:
    return f"{base}_CE"


# ══════════════════════════════════════════════════════════════════════
#  SEARCH  PHASE  DATA
# ══════════════════════════════════════════════════════════════════════
def search_exact_name(base: str) -> str:
    return base


def search_partial_name(base: str) -> str:
    """First 5 chars of *base* for partial match."""
    return base[:5] if len(base) >= 5 else base


def search_nonexistent_name() -> str:
    return f"ZZZ_NO_MATCH_{_rand()}"


# ══════════════════════════════════════════════════════════════════════
#  BOUNDARY  /  INVALID  DATA
# ══════════════════════════════════════════════════════════════════════
def empty_string() -> str:
    return ""


def whitespace_only() -> str:
    return "   "


def max_length_name(n: int = 255) -> str:
    return "A" * n


def special_chars_name() -> str:
    return f"Role_{_rand()}@#$%"


def sql_injection_name() -> str:
    return f"Role_{_rand()}' OR 1=1--"


def xss_name() -> str:
    return f"<script>alert('{_rand()}')</script>"


# ══════════════════════════════════════════════════════════════════════
#  PHASE  TAGS  (for report grouping)
# ══════════════════════════════════════════════════════════════════════
PHASE_C = "C"   # Create
PHASE_D = "D"   # Duplicate
PHASE_E = "E"   # Edit
PHASE_S = "S"   # Search
PHASE_P = "P"   # Popup / UI
PHASE_H = "H"   # History