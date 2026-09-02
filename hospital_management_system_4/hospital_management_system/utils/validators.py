def validate_contact(contact):
    """
    Validates that the contact number consists only of digits and is exactly 10 characters long.
    """
    if not isinstance(contact, str):
        return False
    return contact.isdigit() and len(contact) == 10

def validate_email(email):
    """
    Validates that the email contains both '@' and '.' characters.
    """
    if not isinstance(email, str):
        return False
    return "@" in email and "." in email
