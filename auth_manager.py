from data_manager import load_json
from storage import STAFF_FILE

ADMIN_USER = {
    "email": "admin@hospital.com",
    "password": "admin123",
    "role": "Admin",
    "name": "System Admin"
}

def login(email, password):
    """
    Authenticates a user against ADMIN_USER or staff.json.
    Returns the user dictionary if successful, else None.
    """
    # Load Staff Data
    staff_data = load_json(STAFF_FILE)
    if not staff_data:
        # Fallback if file is empty/missing but let's check hardcoded just in case?
        # User requested to load from JSON.
        if email == ADMIN_USER["email"] and password == ADMIN_USER["password"]:
             return ADMIN_USER
        return None
        
    for user in staff_data:
        # Safely get email/password in case legacy data exists without it
        u_email = user.get("email")
        u_pass = user.get("password")
        
        if u_email == email and u_pass == password:
            return user
    
    # Final fallback for hardcoded admin if NOT in JSON (e.g. before migration)
    if email == ADMIN_USER["email"] and password == ADMIN_USER["password"]:
        return ADMIN_USER
            
    return None
