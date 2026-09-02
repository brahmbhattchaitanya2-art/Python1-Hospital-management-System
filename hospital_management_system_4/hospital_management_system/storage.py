import os
import json

DATA_DIR = "data"
PATIENT_FILE = os.path.join(DATA_DIR, "patients.json")
STAFF_FILE = os.path.join(DATA_DIR, "staff.json")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
APPOINTMENT_FILE = os.path.join(DATA_DIR, "appointments.json")

def ensure_data_dir():
    # Check if DATA_DIR exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Loop through the files and create them if they don't exist
    for file_path in [PATIENT_FILE, STAFF_FILE, INVENTORY_FILE, APPOINTMENT_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
            print(f"Created {file_path}")
        else:
            print(f"Found existing {file_path}")

if __name__ == "__main__":
    ensure_data_dir()
