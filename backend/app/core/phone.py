import re
from typing import NamedTuple, Optional

class NormalizedIndianPhone(NamedTuple):
    is_valid: bool
    core_digits: str        # 10 digits, e.g., '9014722400'
    e164: str               # '+919014722400'
    msg91_recipient: str    # '919014722400'
    display: str            # '+91 90147 22400'
    error_message: Optional[str] = None

def parse_and_validate_indian_phone(phone_input: str) -> NormalizedIndianPhone:
    """
    Validates and normalizes Indian mobile phone numbers.
    
    Supported formats:
    - 10 digits: '9014722400'
    - 11 digits starting with 0: '09014722400'
    - 12 digits starting with 91: '919014722400'
    - E.164 with +91: '+919014722400'
    - Numbers with punctuation/spaces: '+91 90147-22400', '(90147) 22400'
    
    Valid Indian mobile numbers must be 10 digits starting with 6, 7, 8, or 9.
    """
    if not phone_input or not isinstance(phone_input, str):
        return NormalizedIndianPhone(
            is_valid=False,
            core_digits="",
            e164="",
            msg91_recipient="",
            display="",
            error_message="Phone number is required."
        )

    # Strip all non-digit characters
    digits = re.sub(r'\D', '', phone_input.strip())

    core = ""
    if len(digits) == 10:
        core = digits
    elif len(digits) == 11 and digits.startswith("0"):
        core = digits[1:]
    elif len(digits) == 12 and digits.startswith("91"):
        core = digits[2:]
    elif len(digits) == 13 and digits.startswith("091"):
        core = digits[3:]
    else:
        return NormalizedIndianPhone(
            is_valid=False,
            core_digits="",
            e164="",
            msg91_recipient="",
            display="",
            error_message="Please enter a valid 10-digit Indian mobile number."
        )

    # Indian mobile numbers must start with 6, 7, 8, or 9 and have 10 digits
    if not re.match(r'^[6-9]\d{9}$', core):
        return NormalizedIndianPhone(
            is_valid=False,
            core_digits="",
            e164="",
            msg91_recipient="",
            display="",
            error_message="Indian mobile numbers must be 10 digits starting with 6, 7, 8, or 9."
        )

    e164_val = f"+91{core}"
    msg91_val = f"91{core}"
    display_val = f"+91 {core[:5]} {core[5:]}"

    return NormalizedIndianPhone(
        is_valid=True,
        core_digits=core,
        e164=e164_val,
        msg91_recipient=msg91_val,
        display=display_val,
        error_message=None
    )
