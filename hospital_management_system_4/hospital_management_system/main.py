import streamlit as st
import pandas as pd
import numpy as np
from data_manager import load_json, save_json
from models import Patient, BloodInventory, Appointment
from logic.ai_engine import MedicalAI
from storage import PATIENT_FILE, STAFF_FILE, APPOINTMENT_FILE
from datetime import datetime
from utils import validate_contact, validate_email
from utils.email_service import send_alert, send_donation_request

# Page Config
st.set_page_config(page_title="Smart Hospital System", layout="wide")

# Sidebar Navigation
st.sidebar.title("🏥 Hospital System")

from auth_manager import login
from models import Staff, Doctor

# Sidebar Navigation Logic (Delayed)
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- LOGIN WALL ---
if st.session_state['user'] is None:
    # Centered Login Layout
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🏥 Hospital System")
        st.subheader("Please Login")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            user = login(email, password)
            if user:
                st.session_state['user'] = user
                st.success(f"Welcome, {user['name']}")
                st.rerun()
            else:
                st.error("Invalid credentials")

    # Stop execution here
    st.stop()

# --- MAIN APP (Only reachable if logged in) ---

# Sidebar

st.sidebar.success(f"👤 {st.session_state['user']['name']} ({st.session_state['user']['role']})")
if st.sidebar.button("Logout"):
    st.session_state['user'] = None
    st.rerun()

# Menu Access Control
role = st.session_state['user'].get('role')

menu_options = []

if role == 'Admin':
    menu_options = ["Admin Dashboard"]
elif role == 'Doctor':
    menu_options = ["Doctor's Cabin"]
elif role in ['Nurse', 'Staff']:
    menu_options = ["Reception Desk", "Blood Bank"]
else:
    # Fallback or unauthorized
    st.error("Access Denied: Unknown Role")
    st.stop()

menu = st.sidebar.radio("Go to:", menu_options)

# Admin Dashboard Implementation
if menu == "Admin Dashboard":
    st.title("Admin Dashboard 📊")
    st.write("Manage Hospital Staff and Users")
    
    tab1, tab2 = st.tabs(["Create User", "Manage Users"])
    
    with tab1:
        st.subheader("Create New User")
        with st.form("create_user"):
            new_name = st.text_input("Name")
            new_age = st.number_input("Age", min_value=18, max_value=80)
            new_contact = st.text_input("Contact")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["Doctor", "Nurse", "Staff", "Admin"])
            
            # Doctor specific
            specialization = st.text_input("Specialization") if new_role == "Doctor" else None
            shift_timing = st.text_input("Shift Timing (e.g. 09:00-17:00)") 
            if new_role == "Doctor":
                 slots_str = st.text_input("Available Slots (comma separated)", value="09:00, 10:00")
            
            submit_user = st.form_submit_button("Create User")
            
            if submit_user:
                # Validation
                staff_data = load_json(STAFF_FILE)
                
                # Validation
                if not validate_email(new_email):
                    st.error("Invalid Email! Must contain '@' and '.'")
                elif not validate_contact(new_contact):
                     st.error("Invalid Contact! Must be 10 digits.")
                elif any(u.get('email') == new_email for u in staff_data):
                    st.error("Email already exists!")
                elif not new_email or not new_password:
                     st.error("Email and Password are required.")
                else:
                    new_pid = max([u['pid'] for u in staff_data] + [200]) + 1
                    
                    if new_role == "Doctor":
                         slots = [s.strip() for s in slots_str.split(',')]
                         new_obj = Doctor(new_pid, new_name, new_age, new_contact, 
                                        specialization, slots, shift_timing, new_email, new_password)
                    else:
                         new_obj = Staff(new_pid, new_name, new_age, new_contact, 
                                       new_role, shift_timing, new_email, new_password)
                    
                    staff_data.append(new_obj.to_dict())
                    save_json(STAFF_FILE, staff_data)
                    st.success(f"User {new_name} created successfully!")

    with tab2:
        st.subheader("Existing Users")
        staff_data = load_json(STAFF_FILE)
        if staff_data:
            df_staff = pd.DataFrame(staff_data)
            # Mask password
            if 'password' in df_staff.columns:
                df_staff['password'] = "****"
            
            st.dataframe(df_staff)
            
            # Delete logic
            u_to_delete = st.selectbox("Select User to Delete", \
                                     [f"{u['name']} ({u['email']})" for u in staff_data])
            if st.button("Delete User"):
                # Logic to remove user by matching unique string
                # Extract email from the selected string: "Name (email)"
                email_to_remove = u_to_delete.split('(')[-1].strip(')')
                
                new_staff_data = [u for u in staff_data if u.get('email') != email_to_remove]
                
                if len(new_staff_data) < len(staff_data):
                    save_json(STAFF_FILE, new_staff_data)
                    st.success(f"User {u_to_delete} removed.")
                    st.rerun()

    # 3. Blood Stock Alerts
    st.divider()
    st.subheader("📢 Blood Stock Alerts")
    
    inventory = BloodInventory()
    low_stock_items = inventory.get_low_stock()
    
    if not low_stock_items:
        st.success("Blood stock levels are adequate.")
    else:
        st.error(f"CRITICAL SHORTAGE DETECTED: {', '.join(low_stock_items)}")
        
        if st.button("🚀 Broadcast Donation Request to All Patients"):
            patients_list = load_json(PATIENT_FILE)
            if not patients_list:
                st.warning("No patients registered to broadcast to.")
            else:
                progress_bar = st.progress(0)
                total_ops = len(patients_list) * len(low_stock_items)
                completed_ops = 0
                
                for p in patients_list:
                    p_email = p.get('email', f"patient_{p['pid']}@hospital.com") # Fallback for POC
                    for blood_type in low_stock_items:
                        send_donation_request(p_email, p['name'], blood_type)
                        completed_ops += 1
                        progress_bar.progress(min(completed_ops / total_ops, 1.0))
                
                st.success("Broadcast sent to all registered patients.")


# Skeleton Logic
if menu == "Reception Desk":
    st.title("Reception Desk")
    st.write("Patient Registration and Triage")

    # 1. Registration Form
    with st.expander("➕ Register New Patient"):
        with st.form("add_patient"):
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=0, max_value=120)
            contact = st.text_input("Contact Number")
            blood_group = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            
            submitted = st.form_submit_button("Register Patient")
            
            if submitted:
                if not validate_contact(contact):
                     st.error("Invalid Contact! Must be 10 digits.")
                elif name and contact:
                    # Load existing to generate ID
                    patients_data = load_json(PATIENT_FILE)
                    new_pid = len(patients_data) + 101 # Simple ID generation
                    
                    # Create Object
                    new_patient = Patient(new_pid, name, age, contact, blood_group)
                    
                    # Save
                    patients_data.append(new_patient.to_dict())
                    save_json(PATIENT_FILE, patients_data)
                    
                    st.success(f"Patient {name} registered successfully with ID {new_pid}!")
                else:
                    st.error("Please fill in Name and Contact.")

    # 2. Display Patients
    st.subheader("Current Patients")
    patients_data = load_json(PATIENT_FILE)
    
    if patients_data:
        df = pd.DataFrame(patients_data)
        # Verify columns exist before selecting
        cols_to_show = ["pid", "name", "blood_group", "current_status"]
        # Filter only existing columns to avoid key errors if data is corrupted/partial
        cols_to_show = [c for c in cols_to_show if c in df.columns]
        
        st.dataframe(df[cols_to_show], use_container_width=True)
    else:
        st.info("No patients registered yet.")
    
    # 2.5 Manage Patient Status
    st.divider()
    st.subheader("Manage Patient Status")
    
    if patients_data:
        c1, c2, c3 = st.columns(3)
        with c1:
            p_opts_status = {f"{p['name']} (ID: {p['pid']})": p['pid'] for p in patients_data}
            sel_p_key_status = st.selectbox("Select Patient for Status Update", list(p_opts_status.keys()))
            sel_pid_status = p_opts_status[sel_p_key_status]
        
        with c2:
            current_s = next((p['current_status'] for p in patients_data if p['pid'] == sel_pid_status), "PENDING")
            new_status = st.selectbox("New Status", ["ADMITTED", "DISCHARGED", "PENDING"], index=["ADMITTED", "DISCHARGED", "PENDING"].index(current_s) if current_s in ["ADMITTED", "DISCHARGED", "PENDING"] else 2)

        with c3:
            st.write("") # Spacer
            st.write("")
            if st.button("Update Status"):
                # Logic to find and update
                for p in patients_data:
                    if p['pid'] == sel_pid_status:
                        p['current_status'] = new_status
                        break
                save_json(PATIENT_FILE, patients_data)
                st.success(f"Status updated to {new_status}")
                st.rerun()
    else:
        st.info("No patients to manage.")

    # 3. Schedule Appointment
    st.divider()
    with st.expander("📅 Schedule Appointment"):
        patients_data = load_json(PATIENT_FILE)
        staff_data = load_json(STAFF_FILE)
        
        # Filter Doctors
        doctors = [s for s in staff_data if s['role'] == "Doctor"]
        
        if not patients_data:
            st.warning("No patients available to book.")
        elif not doctors:
            st.warning("No doctors available.")
        else:
            with st.form("book_appointment"):
                # Dropdowns
                p_options = {f"{p['name']} (ID: {p['pid']})": p['pid'] for p in patients_data}
                selected_p_key = st.selectbox("Select Patient", list(p_options.keys()))
                selected_pid = p_options[selected_p_key]
                
                d_options = {f"{d['name']} ({d['specialization']})": d['pid'] for d in doctors}
                selected_d_key = st.selectbox("Select Doctor", list(d_options.keys()))
                selected_did = d_options[selected_d_key]
                
                # Date Time
                appt_date = st.date_input("Date")
                appt_time = st.time_input("Time")
                
                submitted_appt = st.form_submit_button("Book Appointment")
                
                if submitted_appt:
                    # Create Appointment Object
                    # ID Generation
                    existing_appts = load_json(APPOINTMENT_FILE)
                    new_aid = len(existing_appts) + 1001
                    
                    dt_str = f"{appt_date} {appt_time}"
                    
                    # Look up names
                    p_name = next((p['name'] for p in patients_data if p['pid'] == selected_pid), "Unknown")
                    d_name = next((d['name'] for d in doctors if d['pid'] == selected_did), "Unknown")

                    new_appt = Appointment(
                        appointment_id=new_aid,
                        patient_id=selected_pid,
                        doctor_id=selected_did,
                        patient_name=p_name,
                        doctor_name=d_name,
                        time_slot=dt_str
                    )
                    
                    # Save
                    existing_appts.append(new_appt.to_dict())
                    save_json(APPOINTMENT_FILE, existing_appts)
                    
                    st.success(f"Appointment booked for {p_name} with {d_name} on {dt_str}")

elif menu == "Doctor's Cabin":
    st.title("Doctor's Cabin 🩺")
    
    if 'user' not in st.session_state or st.session_state['user']['role'] != "Doctor":
        st.warning("Please Login as a Doctor (Sidebar) to access this cabin.")
    else:
        current_doc_id = st.session_state['user']['pid']
        st.write(f"Welcome, Dr. {st.session_state['user']['name']}")
        
        # Load Appointments
        appointments = load_json(APPOINTMENT_FILE)
        my_appointments = [a for a in appointments if a['doctor_id'] == current_doc_id and a['status'] == "Scheduled"]
        
        if not my_appointments:
            st.info("No scheduled appointments found.")
        else:
            # 1. Display List/Table as requested
            st.subheader("Upcoming Appointments")
            # Create a clean dataframe for display
            display_data = []
            for a in my_appointments:
                display_data.append({
                    "Time": a.get('time_slot', a.get('date_time', 'N/A')),
                    "Patient": a.get('patient_name', 'Unknown'),
                    "ID": a.get('appointment_id')
                })
            st.dataframe(pd.DataFrame(display_data), use_container_width=True)
            
            # 2. Consultation Interaction
            st.divider()
            st.subheader("Start Consultation")

            # Dropdown for Appointments
            patients_data = load_json(PATIENT_FILE)
            patient_map = {p['pid']: p for p in patients_data}
            
            appt_options = {}
            for appt in my_appointments:
                # Use cached name if available, else lookup
                p_name = appt.get('patient_name')
                if not p_name:
                    p_data = patient_map.get(appt['patient_id'])
                    p_name = p_data['name'] if p_data else "Unknown"
                
                time_val = appt.get('time_slot', appt.get('date_time', 'N/A'))
                label = f"{time_val} - {p_name} (ID: {appt['appointment_id']})"
                
                # We still need the Full Patient Object for the AI context
                pat_obj = patient_map.get(appt['patient_id'])
                if pat_obj:
                    appt_options[label] = (pat_obj, appt['appointment_id'])
            
            selected_appt_label = st.selectbox("Select Patient to Consult", list(appt_options.keys()))
            if selected_appt_label:
                selected_patient_data, selected_appt_id = appt_options[selected_appt_label]
            
            # --- History Logic moved here ---
            
            # History Expander
            with st.expander(f"📂 Patient History: {selected_patient_data['name']}", expanded=False):
                history = selected_patient_data.get("medical_history", [])
                if history:
                    for entry in history:
                        # Fallback for keys
                        diagnosis = entry.get('diagnosis', entry.get('disease', 'Unknown'))
                        treatment = entry.get('treatment', entry.get('details', 'N/A'))
                        doc_id = entry.get('doctor_id', 'Unknown')
                        
                        st.markdown(f"**{entry.get('date', 'N/A')}** - {diagnosis}")
                        st.caption(f"Treatment: {treatment}")
                        if doc_id != 'Unknown':
                            st.caption(f"Dr. ID: {doc_id}")
                        st.divider()
                else:
                    st.info("No medical history found.")

            # --- Existing AI Logic (indentation adjust) ---
            
            # 2. AI Interaction Layout
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"Assessment: {selected_patient_data['name']}")
                


                symptoms = st.text_area("Symptoms", height=150)
            
            if st.button("Consult AI 🤖"):
                with st.spinner("Analyzing..."):
                    ai = MedicalAI()
                    # Reconstruct patient object to ensure we handle history correctly if needed, 
                    # or just pass the raw list. Using raw list from dict is easiest.
                    history = selected_patient_data.get("medical_history", [])
                    result = ai.predict_treatment(symptoms, history)
                    st.session_state['ai_result'] = result

            with col2:
                st.subheader("Treatment Plan")
                if 'ai_result' in st.session_state:
                    result = st.session_state['ai_result']
                    
                    # Display Results
                    if "disclaimer" in result:
                        st.warning(result["disclaimer"])
                    
                    # Parsing the result for better UI
                    try:
                        st.subheader("Diagnosis")
                        st.info(result.get("diagnosis", "N/A"))
                        
                        st.subheader("Risk Level")
                        risk = result.get("risk_level", "Unknown")
                        if risk == "High":
                            st.error(f"🔴 {risk}")
                        elif risk == "Medium":
                            st.warning(f"🟡 {risk}")
                        else:
                            st.success(f"🟢 {risk}")
    
                        st.subheader("Treatment Plan")
                        st.write(result.get("treatment_plan", "N/A"))
                        
                        if result.get("suggested_rx"):
                            st.subheader("Suggested Meds (Rx)")
                            for rx in result["suggested_rx"]:
                                st.write(f"• {rx}")
    
                    except Exception as e:
                        st.error(f"Error parsing response: {e}")
                        st.json(result) # Fallback
    
                    st.divider()
                    st.subheader("Final Decision")
                    final_notes = st.text_area("Final Prescription / Notes", 
                                              value=f"Rx: {', '.join(result.get('suggested_rx', []))}\n\nPlan: {result.get('treatment_plan', '')}")
                    
                    if st.button("Finalize & Save Treatment"):

                        # 1. Update Patient History
                        all_patients = load_json(PATIENT_FILE)
                        for p in all_patients:
                            if p['pid'] == selected_patient_data['pid']:
                                new_record = {
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "diagnosis": result.get("diagnosis", "Consultation"),
                                    "treatment": final_notes,
                                    "doctor_id": current_doc_id
                                }
                                if "medical_history" not in p:
                                    p["medical_history"] = []
                                p["medical_history"].append(new_record)
                                break
                        save_json(PATIENT_FILE, all_patients)
                        
                        # 2. Update Appointment Status
                        all_appts = load_json(APPOINTMENT_FILE)
                        for a in all_appts:
                             if a['appointment_id'] == selected_appt_id:
                                 a['status'] = "Completed"
                                 break
                        save_json(APPOINTMENT_FILE, all_appts)
    
                        st.success("Treatment Saved!")
                        if 'ai_result' in st.session_state:
                            del st.session_state['ai_result']
                        st.rerun()

elif menu == "Blood Bank":
    st.title("Blood Bank 🩸")
    # 1. Initialize Inventory (using Session State for persistence in POC)
    if 'inventory' not in st.session_state:
        st.session_state['inventory'] = BloodInventory()
    
    inventory = st.session_state['inventory']

    # 2. Critical Alert
    low_stock = inventory.get_low_stock() # Uses NumPy boolean indexing
    if low_stock:
        st.error(f"⚠️ Low Stock Alert: {', '.join(low_stock)}")
    else:
        st.success("Stock levels are adequate.")

    # 3. Visualization
    
    # Matplotlib Visualization
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Conditional Colors: Red if < 5, Blue otherwise
    colors = ['red' if x < 5 else 'skyblue' for x in inventory.quantities]
    
    bars = ax.bar(inventory.types, inventory.quantities, color=colors)
    
    # Y-Axis Settings
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Units Available")
    ax.set_title("Blood Inventory Status")
    
    # Critical Threshold Line
    ax.axhline(y=5, color='red', linestyle='--', label='Critical Threshold (5 Units)')
    ax.legend()
    
    # Annotations on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    st.pyplot(fig)

    # 4. Update Logic
    with st.expander("Update Stock"):
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            b_type = st.selectbox("Blood Type", inventory.types)
        with col_up2:
            qty = st.number_input("Units to Add/Remove", min_value=-10, max_value=50, step=1)
        
        if st.button("Update Stock"):
            success, message = inventory.update_stock(b_type, int(qty))
            
            if success:
                st.success(message)
                st.rerun() # Refresh to show new graph
            else:
                st.error(message)
