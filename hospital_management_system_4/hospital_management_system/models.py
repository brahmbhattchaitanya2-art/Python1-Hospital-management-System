import datetime
import numpy as np
from data_manager import load_json, save_json
from storage import INVENTORY_FILE
from utils import validate_contact, validate_email

class Person:
    def __init__(self, pid, name, age, contact):
        if not validate_contact(contact):
            raise ValueError("Contact must be a 10-digit number")
        
        self.pid = pid
        self.name = name
        self.age = age
        self.contact = contact

    def to_dict(self):
        return self.__dict__

class Patient(Person):
    def __init__(self, pid, name, age, contact, blood_group):
        super().__init__(pid, name, age, contact)
        self.blood_group = blood_group
        self.medical_history = []
        self.current_status = "PENDING"
        self.assigned_doctor_id = None

    def add_history(self, disease, prediction_notes):
        entry = {
            "date": datetime.date.today(),
            "disease": disease,
            "ai_prediction": prediction_notes
        }
        self.medical_history.append(entry)

    def admit(self):
        self.current_status = "ADMITTED"


    def discharge(self):
        self.current_status = "DISCHARGED"

    @classmethod
    def from_dict(cls, data):
        """
        Reconstructs a Patient object from a dictionary.
        """
        # 1. Create the instance using the basic constructor arguments
        patient = cls(
            pid=data["pid"],
            name=data["name"],
            age=data["age"],
            contact=data["contact"],
            blood_group=data.get("blood_group", "Unknown")
        )
        
        # 2. Manually restore the complex/mutable attributes
        # Use .get() with defaults to prevent errors if keys are missing
        patient.medical_history = data.get("medical_history", [])
        patient.current_status = data.get("current_status", "PENDING")
        patient.assigned_doctor_id = data.get("assigned_doctor_id", None)
        
        return patient

class Appointment:
    def __init__(self, appointment_id, patient_id, doctor_id, patient_name, doctor_name, time_slot, status="Scheduled"):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.time_slot = time_slot
        self.status = status

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(
            appointment_id=data["appointment_id"],
            patient_id=data["patient_id"],
            doctor_id=data["doctor_id"],
            patient_name=data.get("patient_name", "Unknown"),
            doctor_name=data.get("doctor_name", "Unknown"),
            time_slot=data.get("time_slot", data.get("date_time", "N/A")), # Fallback for old data
            status=data.get("status", "Scheduled")
        )

class Staff(Person):
    def __init__(self, pid, name, age, contact, role, shift_timing, email, password):
        super().__init__(pid, name, age, contact)
        
        if not validate_email(email):
            raise ValueError("Invalid Email Format")
            
        self.role = role
        self.shift_timing = shift_timing
        self.email = email
        self.password = password

    def verify_password(self, input_password):
        return self.password == input_password

class Doctor(Staff):
    def __init__(self, pid, name, age, contact, specialization, available_slots, shift_timing, email, password):
        super().__init__(pid, name, age, contact, role="Doctor", shift_timing=shift_timing, email=email, password=password)
        self.specialization = specialization
        self.available_slots = available_slots

    def assign_patient(self, patient_id):
        # Linking patient ID to doctor (printing confirmation as requested)
        print(f"Patient {patient_id} assigned to Doctor {self.name} ({self.pid}).")

class BloodInventory:
    def __init__(self, limit=5):
        self.types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        self.limit = limit
        
        # Load Existing Data
        data = load_json(INVENTORY_FILE)
        
        if not data:
            # Case 1: Empty - Use Defaults
            self.quantities = np.array([10, 10, 10, 10, 10, 10, 10, 10]) 
            self._save() # Initialize File
        elif isinstance(data[0], int):
            # Case 2: Old Format (List of Ints)
            self.quantities = np.array(data)
            # We will convert to new format on next save
        else:
            # Case 3: New Format (List of Dicts)
            # Extract units in the correct order of self.types
            q_list = [next((item['units'] for item in data if item['blood_group'] == t), 0) for t in self.types]
            self.quantities = np.array(q_list)

    def get_low_stock(self):
        # Using boolean indexing as requested
        low_stock_indices = self.quantities < self.limit
        return [self.types[i] for i in range(len(self.types)) if low_stock_indices[i]]

    def update_stock(self, blood_type, qty_change):
        if blood_type in self.types:
            index = self.types.index(blood_type)
            current_qty = self.quantities[index]
            
            # Validation: Prevent negative stock
            if current_qty + qty_change < 0:
                return False, f"Error: Cannot remove {abs(qty_change)} units. Only {current_qty} available."
            
            self.quantities[index] += qty_change
            self._save()
            return True, f"Updated {blood_type} by {qty_change} units."
        else:
            return False, f"Error: Unknown blood type {blood_type}"

    def _save(self):
        # Helper to save in the new structured format
        save_data = [{"blood_group": t, "units": int(q)} for t, q in zip(self.types, self.quantities)]
        save_json(INVENTORY_FILE, save_data)

