import streamlit as st
from devices import device_detail_page
from helpers import load_devices, save_devices, go_home  # ✅ import shared functions



# ---- PAGE CONFIG ----
st.set_page_config(page_title="Smart Plug Dashboard", layout="wide")

# ---- JSON FILE FOR DEVICE STORAGE ----
DEVICE_FILE = "devices.json"



# ---- PAGE STATE ----
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---- NAVIGATION HANDLER ----


def go_device_detail(device_id):
    st.session_state.page = "device_detail"
    st.session_state.current_device = device_id

# ---- HOME PAGE ----
def home_page():
    st.title("💡 Smart Plug Dashboard")
    st.markdown("### Monitor and manage your smart devices easily")

    # Buttons row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📘 User Manual"):
            st.session_state.page = "user_manual"
    with col2:
        st.write("")  # spacing
        st.markdown("### ⚡ My Devices")
    with col3:
        if st.button("➕ Add Device"):
            st.session_state.page = "add_device"
    with col4:
        if st.button("⚙️ Manage Devices"):
            st.session_state.page = "manage_devices"

    st.markdown("---")

    devices = load_devices()
    if not devices:
        st.info("No devices added yet. Click **Add Device** to get started.")
        return

    # Device cards grid
    cols = st.columns(3)
    for i, device in enumerate(devices):
        col = cols[i % 3]
        with col:
            st.container()
            st.markdown(f"#### 🔌 {device['name']}")
            st.markdown(f"**Device ID:** `{device['id']}`")
            if st.button(f"View Details ({device['name']})", key=f"view_{i}"):
                go_device_detail(device["id"])
            st.markdown("---")

# ---- USER MANUAL ----
def user_manual_page():
    st.header("📘 User Manual")
    st.markdown("""
    **Welcome to your Smart Plug Dashboard!**
    
    **Features:**
    - View and monitor multiple smart plugs
    - Add or remove devices
    - Check real-time power, voltage, and energy data
    - Turn devices ON/OFF safely

    **Safety Tips:**
    - Do **not** flash or modify firmware.
    - Use only within rated voltage/current limits.
    - Always disconnect high-load devices before maintenance.
    """)
    st.button("⬅️ Back to Home", on_click=go_home)

# ---- ADD DEVICE ----
def add_device_page():
    st.header("➕ Add New Device")
    name = st.text_input("Device Name")
    dev_id = st.text_input("Device ID")
    if st.button("Save Device"):
        if name and dev_id:
            devices = load_devices()
            devices.append({"name": name, "id": dev_id})
            save_devices(devices)
            st.success(f"✅ {name} added successfully!")
            st.button("⬅️ Back to Home", on_click=go_home)
        else:
            st.warning("Please enter both name and device ID.")
    st.button("⬅️ Back to Home", on_click=go_home)

# ---- MANAGE DEVICES ----
def manage_devices_page():
    st.header("⚙️ Manage Devices")
    devices = load_devices()
    if not devices:
        st.info("No devices to manage.")
        st.button("⬅️ Back to Home", on_click=go_home)
        return

    for i, device in enumerate(devices):
        st.markdown(f"#### {device['name']} (`{device['id']}`)")
        col1, col2 = st.columns([1, 1])
        with col1:
            new_name = st.text_input("Edit name", value=device["name"], key=f"name_{i}")
        with col2:
            new_id = st.text_input("Edit ID", value=device["id"], key=f"id_{i}")

        if st.button("💾 Save Changes", key=f"save_{i}"):
            devices[i] = {"name": new_name, "id": new_id}
            save_devices(devices)
            st.success("Device updated!")

        if st.button("❌ Delete", key=f"delete_{i}"):
            del devices[i]
            save_devices(devices)
            st.warning("Device deleted.")
            st.experimental_rerun()

    st.button("⬅️ Back to Home", on_click=go_home)

# ---- DEVICE DETAIL PLACEHOLDER ----
#

# ---- ROUTER ----
page = st.session_state.page
if page == "home":
    home_page()
elif page == "user_manual":
    user_manual_page()
elif page == "add_device":
    add_device_page()
elif page == "manage_devices":
    manage_devices_page()
elif page == "device_detail":
    device_detail_page()
