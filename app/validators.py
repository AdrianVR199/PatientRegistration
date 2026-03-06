import re
from datetime import datetime

VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

VALID_SEX = {"Male", "Female", "Other", "Decline to Answer"}


def validate_name(value, field="name"):
    if not value or not isinstance(value, str):
        return f"{field} is required."
    value = value.strip()
    if not (1 <= len(value) <= 50):
        return f"{field} must be 1–50 characters."
    if not re.match(r"^[A-Za-z\-']+$", value):
        return f"{field} may only contain letters, hyphens, or apostrophes."
    return None


def validate_dob(value):
    if not value:
        return "date_of_birth is required."
    try:
        dob = datetime.strptime(value, "%m/%d/%Y")
    except ValueError:
        return "date_of_birth must be MM/DD/YYYY format."
    if dob.date() >= datetime.today().date():
        return "date_of_birth cannot be today or in the future."
    return None


def validate_phone(value, field="phone_number"):
    if not value:
        return f"{field} is required."
    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        return f"{field} must be a valid 10-digit U.S. phone number."
    return None


def validate_email(value):
    if not value:
        return None  
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        return "email format is invalid."
    return None


def validate_state(value):
    if not value:
        return "state is required."
    if value.upper() not in VALID_STATES:
        return "state must be a valid 2-letter U.S. state abbreviation."
    return None


def validate_zip(value):
    if not value:
        return "zip_code is required."
    if not re.match(r"^\d{5}(-\d{4})?$", value):
        return "zip_code must be 5-digit or ZIP+4 format."
    return None


def validate_sex(value):
    if not value:
        return "sex is required."
    if value not in VALID_SEX:
        return f"sex must be one of: {', '.join(VALID_SEX)}."
    return None


def validate_patient_data(data, partial=False):
    """
    Validate patient fields.
    partial=True: only validate fields that are present (for PUT updates).
    Returns a list of error strings. Empty list = valid.
    """
    errors = []

    def check(field, fn, *args):
        if partial and field not in data:
            return
        err = fn(data.get(field), *args)
        if err:
            errors.append(err)

    check("first_name",    validate_name, "first_name")
    check("last_name",     validate_name, "last_name")
    check("date_of_birth", validate_dob)
    check("sex",           validate_sex)
    check("phone_number",  validate_phone, "phone_number")
    check("state",         validate_state)
    check("zip_code",      validate_zip)

    if not partial or "email" in data:
        err = validate_email(data.get("email"))
        if err:
            errors.append(err)

    if not partial or "emergency_contact_phone" in data:
        ecp = data.get("emergency_contact_phone")
        if ecp:
            err = validate_phone(ecp, "emergency_contact_phone")
            if err:
                errors.append(err)

    required_strings = {
        "address_line_1": (1, 200),
        "city": (1, 100),
    }
    for field, (mn, mx) in required_strings.items():
        if partial and field not in data:
            continue
        val = data.get(field, "")
        if not val or not (mn <= len(str(val).strip()) <= mx):
            errors.append(f"{field} is required and must be {mn}–{mx} characters.")

    return errors
