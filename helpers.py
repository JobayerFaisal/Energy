import json
import os
import streamlit as st

DEVICE_FILE = "devices.json"

def load_devices():
    """Load all devices from the JSON file."""
    if not os.path.exists(DEVICE_FILE):
        return []
    with open(DEVICE_FILE, "r") as f:
        return json.load(f)

def save_devices(devices):
    """Save all devices to the JSON file."""
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f, indent=4)

def go_home():
    """Navigate back to home page."""
    st.session_state.page = "home"
