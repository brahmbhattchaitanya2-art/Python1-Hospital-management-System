from data_manager import load_json, save_json
from storage import STAFF_FILE, ensure_data_dir

def initialize_admin():
    """
    Checks if admin exists in staff.json. If not, adds default admin.
    """
    # Ensure directory exists first
    ensure_data_dir()
    
    staff_data = load_json(STAFF_FILE)
    
    # Check if admin exists
    admin_email = "admin@hospital.com"
    if any(u.get('email') == admin_email for u in staff_data):
        print("Admin user already exists.")
        return

    # Create Admin User
    admin_user = {
        "pid": 100, # Fixed ID for Admin
        "name": "System Admin",
        "age": 30,
        "contact": "N/A",
        "role": "Admin",
        "email": admin_email,
        "password": "admin123", # Default
        "shift_timing": "N/A"
    }
    
    staff_data.append(admin_user)
    save_json(STAFF_FILE, staff_data)
    print("Admin user migrated successfully.")

if __name__ == "__main__":
    initialize_admin()
