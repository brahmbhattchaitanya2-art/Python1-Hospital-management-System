from models import Doctor
from data_manager import save_json
from storage import STAFF_FILE

def setup_dummy_staff():
    # Create a Doctor
    doc = Doctor(
        pid=201, 
        name="Dr. Smith", 
        age=45, 
        contact="555-0199", 
        specialization="General Physician", 
        available_slots=["09:00", "10:00"],
        shift_timing="09:00-17:00",
        email="dr.smith@hospital.com",
        password="password123"
    )
    # Role is auto-set to "Doctor"
    
    save_json(STAFF_FILE, [doc.to_dict()])
    print("Dummy doctor added to staff.json with credentials")

if __name__ == "__main__":
    setup_dummy_staff()
