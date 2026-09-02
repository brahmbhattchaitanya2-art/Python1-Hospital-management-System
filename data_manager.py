import json
import os
from storage import ensure_data_dir

def load_json(filepath):
    ensure_data_dir()
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(filepath, data):
    ensure_data_dir()
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")
        return False
