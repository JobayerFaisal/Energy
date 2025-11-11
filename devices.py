import streamlit as st
import pandas as pd
from tuya_api import get_token, get_device_status, control_device, log_data
from helpers import load_devices, go_home
import time
import os
from billing import daily_and_monthly_bill



# ---------------------------------------------------------
# 🔹 DEVICE DETAIL PAGE
# ---------------------------------------------------------
def device_detail_page():
    """Show live dashboard for a selected device."""
    devices = load_devices()
    device_id = st.session_state.get("current_device")
    device = next((d for d in devices if d["id"] == device_id), None)

    if not device:
        st.error("Device not found.")
        st.button("⬅️ Back to Home", on_click=go_home)
        return

    st.title(f"🔌 {device['name']} — Live Dashboard")
    st.button("⬅️ Back to Home", on_click=go_home)

    try:
        # -------------------------------------------------
        # 🔐 1. Get Access Token
        # -------------------------------------------------
        token = get_token()

        # -------------------------------------------------
        # 🔁 2. Fetch & Display Data
        # -------------------------------------------------
        response = get_device_status(device_id, token)
        if not response.get("success"):
            st.error(f"❌ Tuya Error: {response}")
            return

        result = response["result"]
        data = {item["code"]: item["value"] for item in result}

        # Try all naming variants
        voltage = data.get("cur_voltage") or data.get("voltage") or 0
        power = data.get("cur_power") or data.get("power") or 0
        current = data.get("cur_current") or data.get("current") or 0

        # Normalize
        if voltage > 1000: voltage /= 10
        if current > 100: current /= 1000

        # Log reading
        new_entry = log_data(device_id, response)

        # -------------------------------------------------
        # 📊 3. Display Metrics
        # -------------------------------------------------
        c1, c2, c3 = st.columns(3)
        c1.metric("🔋 Voltage (V)", f"{voltage:.1f}")
        c2.metric("⚡ Power (W)", f"{power:.1f}")
        c3.metric("🔌 Current (A)", f"{current:.3f}")

        st.success(f"Last logged at: {new_entry['timestamp']}")

        # -------------------------------------------------
        # 🎛️ 4. Control Buttons
        # -------------------------------------------------
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Turn ON"):
                res = control_device(device_id, token, "switch_1", True)
                st.info(res)
        with col2:
            if st.button("Turn OFF"):
                res = control_device(device_id, token, "switch_1", False)
                st.info(res)

        # -------------------------------------------------
        # 🧾 5. Show Recent Log Chart
        # -------------------------------------------------
        st.markdown("### 📈 Recent Power Trend")
        file_path = os.path.join("data", f"{device_id}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path).tail(30)
            st.line_chart(df[["power"]])
        else:
            st.info("No logged data yet. Refresh after 1 minute.")

                # -------------------------------------------------
        # 💰 7. Daily & Monthly Bill Summary
        # -------------------------------------------------
        st.markdown("### 💰 Electricity Bill Estimate")

        daily_units, daily_cost, monthly_units, monthly_cost = daily_and_monthly_bill(device_id)

        c1, c2 = st.columns(2)
        with c1:
            st.metric("📅 Today's Consumption", f"{daily_units:.3f} kWh")
            st.metric("💸 Today's Bill", f"{daily_cost:.2f} ৳")
        with c2:
            st.metric("🗓 This Month's Consumption", f"{monthly_units:.3f} kWh")
            st.metric("💰 Monthly Bill Estimate", f"{monthly_cost:.2f} ৳")


        # -------------------------------------------------
        # 🕓 6. Optional: Raw API Response
        # -------------------------------------------------
        with st.expander("📜 Raw Tuya Response"):
            st.json(response)

    except Exception as e:
        st.error(f"Error fetching device data: {e}")
