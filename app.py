# app.py — fixed navigation & working buttons

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import altair as alt
import plotly.express as px
import os
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go



# Local modules
from devices import load_devices, save_devices                     # :contentReference[oaicite:0]{index=0}
from get_power_data import fetch_and_log_once                      # :contentReference[oaicite:1]{index=1}
from tuya_api import control_device, get_token                     # :contentReference[oaicite:2]{index=2}
from tuya_api_mongo import latest_docs, range_docs                 # :contentReference[oaicite:3]{index=3}
from billing import daily_monthly_for, _latest_power_voltage       # :contentReference[oaicite:4]{index=4}
from helpers import go_home as _go_home                            # :contentReference[oaicite:5]{index=5}
from billing import aggregate_timeseries_24h, aggregate_totals_all_devices
from billing import daily_monthly_for, _latest_power_voltage, _tier_cost



# ------------------------------------------------------------------------------------
# Page setup

st.set_page_config(page_title="Smart Plug Dashboard", layout="wide")
DATA_DIR = Path("data")

# ------------------------------------------------------------------------------------
# Global Theming (Light Green UI)
# background: linear-gradient(180deg, #C4EAC4 0%, #E0F4E0 100%) !important;
# background: linear-gradient(180deg, #D3F2D3 0%, #E8F8E8 100%) !important;


st.markdown("""
<style>
/* Overall app background */
.stApp {
    background: linear-gradient(180deg, #B5E3B5 0%, #D6F0D6 100%) !important;
}

/* Main content padding */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* Sidebar style */
[data-testid="stSidebar"] {
    background-color: #DDF5DD !important;
    border-right: 1px solid #c0e0c0;
}
[data-testid="stSidebar"] * {
    color: #123524 !important;
    font-size: 0.95rem;
}

/* Titles & captions */
h1, h2, h3, h4, h5 {
    color: #123524 !important;
}
.stCaption, .stMarkdown p {
    color: #215236 !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #ffffff;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #d1e8d1;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

/* Buttons */
.stButton>button {
    background-color: #4CAF50 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.9rem !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton>button:hover {
    background-color: #45A049 !important;
}

/* Quick action row subtle shadow */
.quick-actions-row {
    background-color: #F5FFF5;
    border-radius: 14px;
    padding: 0.8rem 1rem;
    border: 1px solid #d1e8d1;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

/* Section headings */
.section-title {
    font-weight: 700;
    font-size: 1.15rem;
    margin-top: 0.3rem;
}

/* Plotly container tweaks */
.stPlotlyChart {
    background-color: #ffffff;
    padding: 0.6rem;
    border-radius: 12px;
    border: 1px solid #d6ead6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    border: 1px solid #d6ead6;
}

/* Expanders (for manual page) */
.streamlit-expanderHeader {
    font-weight: 600;
    color: #123524 !important;
}
</style>
""", unsafe_allow_html=True)


#--------------------------------------Session defaults------------------------------------------
# Session defaults
if "route" not in st.session_state:
    st.session_state.route = "home"   # "home" | "mydevices" | "add" | "manage" | "device"
if "current_device_id" not in st.session_state:
    st.session_state.current_device_id = None
if "current_device_name" not in st.session_state:
    st.session_state.current_device_name = None



# -----------------------------------------Small helpers-------------------------------------------

# Small helpers
def set_route(new_route: str):
    st.session_state.route = new_route

def go_home():
    set_route("home")

def go_mydevices():
    set_route("mydevices")

def go_add():
    set_route("add")

def go_manage():
    set_route("manage")

def go_reports():
    set_route("reports")

def go_device_detail(device_id: str, device_name: str):
    st.session_state.current_device_id = device_id
    st.session_state.current_device_name = device_name
    set_route("device")

def get_device_by_id(device_id: str):
    for d in load_devices():
        if d.get("id") == device_id:
            return d
    return None




# -------------------------PAGE HOME-----------------------------------------------------------
# Pages

def page_home():
    st.title("ENERGY MONITOR DASHBOARD")
    st.caption("At-a-glance overview of your smart energy setup.")
    st_autorefresh(interval=30000, key="home_refresh")     # 30 SECOND INTERVAL

    devices = load_devices()
    total = len(devices)

    total_power_now, present_voltage, today_kwh, today_bill_bdt, month_kwh, month_bill_bdt = \
        aggregate_totals_all_devices(devices)

    # ---- Top metrics ----
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Devices", total)
    with c2:
        st.metric("Total Power (now)", f"{total_power_now:.1f} W")
    with c3:
        st.metric("Present Voltage (max)", f"{present_voltage:.1f} V")
    with c4:
        st.metric("Today’s Bill (BDT)", f"{today_bill_bdt:.2f}")
    with c5:
        st.metric("Monthly Bill (BDT)", f"{month_bill_bdt:.2f}")


    st.markdown("---")

    st.subheader("Quick Actions")
    # Quick Actions styled row
    # st.markdown('<div class="quick-actions-row">', unsafe_allow_html=True)
    # st.markdown('<div class="section-title">Quick Actions</div>', unsafe_allow_html=True)

    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        if st.button("📂 My Devices     -"):
            go_mydevices(); st.rerun()
    with a2:
        if st.button("➕ Add Device     -"):
            go_add(); st.rerun()
    with a3:
        if st.button("⚙️ Manage Devices"):
            go_manage(); st.rerun()
    with a4:
        st.button("📘 User Manual", disabled=True)
    with a5:
        if st.button("📈 Range Reports"):
            go_reports(); st.rerun()


    st.markdown("---")
    st.subheader("Last 24h — Power & Voltage (All Devices)")



    # ---- Aggregated Plotly chart (sum power, avg voltage)
    ts = aggregate_timeseries_24h(devices, resample_rule="5T")
    if ts.empty:
        st.info("No data available for the last 24 hours.")
        return

    fig = go.Figure()

    # --- POWER (Filled Area) ---
    fig.add_trace(
        go.Scatter(
            x=ts["timestamp"],
            y=ts["power_sum_W"],
            mode="lines",
            name="Power (W)",
            line=dict(color="rgba(0, 102, 255, 1)"),
            fill="tozeroy",
            fillcolor="rgba(0, 102, 255, 0.25)"
        )
    )

    # --- VOLTAGE (Filled Area) ---
    fig.add_trace(
        go.Scatter(
            x=ts["timestamp"],
            y=ts["voltage_avg_V"],
            mode="lines",
            name="Voltage (V)",
            line=dict(color="rgba(255, 0, 0, 1)"),
            fill="tozeroy",
            fillcolor="rgba(255, 0, 0, 0.20)"
        )
    )

    fig.update_layout(
        title="Total Power & Voltage — last 24h",
        hovermode="x unified",
        template="plotly_white",

        # Light green chart background
        plot_bgcolor="#C8F9F1",
        paper_bgcolor="#D4F7F2",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
    )



    st.plotly_chart(fig, use_container_width=True)

# ------------------------------Device Status Helper --------------------------------------------------------------------
# def device_status(device_id):
#     df = latest_docs(device_id, n=1)
#     if df.empty:
#         return False   # assume OFF when no data
#     p = float(df.iloc[0].get("power", 0))
#     return p > 1.0     # ON if power > 1 watt

from datetime import datetime, timezone

def _extract_switch(row):
    # Try a dedicated column first (if you later add it)
    if "switch_1" in row and row["switch_1"] is not None:
        return bool(row["switch_1"])

    # Fallback: parse from raw->result
    raw = row.get("raw") or {}
    for dp in raw.get("result", []):
        if dp.get("code") == "switch_1":
            return bool(dp.get("value"))
    return None  # unknown
        

def device_status(device_id, v_thresh=30.0, i_thresh=0.01, stale_secs=120):
    """
    Status rules:
      - 'offline' : no recent data
      - 'on'      : V > v_thresh and I > i_thresh
      - 'idle'    : V > v_thresh and I <= i_thresh
      - 'off'     : V <= v_thresh (ignore current)
    """
    df = latest_docs(device_id, n=1)
    if df.empty:
        return "offline"

    row = df.iloc[0]

    # --- freshness check ---
    ts = row["timestamp"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    age = (now_utc - ts).total_seconds()
    if age > stale_secs:
        return "offline"

    # --- voltage & current logic ---
    v = float(row.get("voltage", 0.0) or 0.0)
    i = float(row.get("current", 0.0) or 0.0)

    if v > v_thresh and i > i_thresh:
        return "on"
    if v > v_thresh and i <= i_thresh:
        return "idle"
    # low voltage = truly off
    return "off"


def status_to_button_type(status: str) -> str:
    if status == "on":
        return "primary"     # green
    if status == "idle":
        return "primary"     # still ON, maybe different label if you want
    if status == "off":
        return "secondary"   # red
    if status == "offline":
        return "secondary"   # maybe grey later
    return "secondary"



# ------------------------------My Devices Page --------------------------------------------------------------------



def page_mydevices():
    st.title("⚡ My Devices")
    st.caption("Browse and open a device to view live data.")

    button_css = """
    <style>
    /* ON / IDLE -> primary */
    .stButton > button[kind="primary"] {
        background-color: #2ecc71 !important;  /* green */
        color: white !important;
        border-radius: 8px;
    }

    /* OFF / OFFLINE -> secondary */
    .stButton > button[kind="secondary"] {
        background-color: #e74c3c !important;  /* red */
        color: white !important;
        border-radius: 8px;
    }

    /* small status pill under device name */
    .status-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .stButton .
    .status-pill.on      { background: #2ecc71; color: #fff; }
    .status-pill.idle    { background: #f1c40f; color: #000; }
    .status-pill.off     { background: #e74c3c; color: #fff; }
    .status-pill.offline { background: #7f8c8d; color: #fff; }
    </style>
    """
    st.markdown(button_css, unsafe_allow_html=True)



    devices = load_devices()
    if not devices:
        st.info("No devices added yet. Click **Add Device** to get started.")
        if st.button("➕ Add Device"):
            go_add(); st.rerun()
        return

    # cols = st.columns(3)
    # for i, d in enumerate(devices):
    #     with cols[i % 3]:
    #         is_on = device_status(d["id"])
    #         btn_type = "primary" if is_on else "secondary"   # primary=green, secondary=red

    #         st.markdown(f"####  {d['name']}")
    #         st.markdown(f"**Device ID:** `{d['id']}`")

    #         if st.button(
    #             f"View Details ({d['name']})",
    #             key=f"view_{i}",
    #             type=btn_type
    #         ):
    #             go_device_detail(d["id"], d["name"])
    #             st.rerun()

    cols = st.columns(3)
    for i, d in enumerate(devices):
        with cols[i % 3]:
            status = device_status(d["id"])  # 'on' / 'idle' / 'off' / 'offline'
            status_label = status.upper()

            if status in ("on", "idle"):
                btn_type = "primary"
            else:
                btn_type = "secondary"

            st.markdown(f"#### {d['name']}")
            st.markdown(f"**Device ID:** `{d['id']}`")
            st.markdown(
                f'<span class="status-pill {status}">{status_label}</span>',
                unsafe_allow_html=True
            )

            if st.button(
                f"View Details ({d['name']})",
                key=f"view_{i}",
                type=btn_type,
            ):
                go_device_detail(d["id"], d["name"])
                st.rerun()

            st.markdown("---")


#------------------------------Add Device Page --------------------------------------------------------------------


def page_add():
    st.header("➕ Add Device")
    st.caption("Register a new Tuya smart plug into the dashboard.")


    name = st.text_input("Device Name")
    dev_id = st.text_input("Device ID")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Save"):
            if name and dev_id:
                devs = load_devices()
                devs.append({"name": name, "id": dev_id})
                save_devices(devs)
                st.success("Device added.")
                go_home()
                st.rerun()
            else:
                st.warning("Enter both name and ID.")
    with c2:
        if st.button("Cancel"):
            go_home()
            st.rerun()


#------------------------------Manage Devices Page --------------------------------------------------------------------

def page_manage():
    st.header("⚙️ Manage Devices")
    st.caption("Edit device names, IDs, or open a device quickly.")


    devs = load_devices()
    if not devs:
        st.info("No devices to manage.")
        return

    for i, d in enumerate(devs):

        # ---------- FIRST ROW ----------
        c1, c2 = st.columns([3, 3])
        with c1:
            new_name = st.text_input("Name", value=d["name"], key=f"nm_{i}")
        with c2:
            new_id = st.text_input("ID", value=d["id"], key=f"id_{i}")

        # ---------- SECOND ROW ----------
        b1, b2, b3 = st.columns([1, 1, 1])
        with b1:
            save_clicked = st.button("Save", key=f"sv_{i}")
        with b2:
            del_clicked = st.button("Delete", key=f"dl_{i}")
        with b3:
            open_clicked = st.button("Open", key=f"open_{i}")

        # ---------- ACTIONS ----------
        if save_clicked:
            devs[i] = {"name": new_name, "id": new_id}
            save_devices(devs)
            st.success("Saved.")
            st.rerun()

        if del_clicked:
            del devs[i]
            save_devices(devs)
            st.warning("Deleted.")
            st.rerun()

        if open_clicked:
            go_device_detail(d["id"], d["name"])
            st.rerun()

        st.markdown("---")   # optional separator between device cards


#------------------------------Device Detail Page ----------------------------------------------
def page_device():
    dev_id = st.session_state.get("current_device_id")
    dev_name = st.session_state.get("current_device_name")

    if not dev_id:
        st.error("No device selected.")
        if st.button("Back to Home"):
            go_home()
            st.rerun()

        return

    # Safety: if name missing, look it up
    if not dev_name:
        d = get_device_by_id(dev_id)
        dev_name = d["name"] if d else dev_id

    # Live refresh every 5s
    st_autorefresh(interval=30000, key=f"data_refresh_{dev_id}")     # 30 SECOND INTERVAL

    st.title(f" {dev_name} — Live")
    st.caption("Live Tuya readings, quick control and billing estimate.")


    # Fetch + log once (writes Mongo)
    result = fetch_and_log_once(dev_id, dev_name)
    if "error" in result:
        st.error(f"Tuya API error: {result['error']}")
        if st.button("⬅️ Back to Home"):
            go_home()
            st.rerun()   # was st.experimental_rerun()
        st.caption("You can also retry after checking connectivity.")
        st.markdown("---")
        return  # don't st.stop(); allow the button above to render


    row = result.get("row", {})
    v = float(row.get("voltage", 0.0))
    c = float(row.get("current", 0.0))
    p = float(row.get("power", 0.0))
    # Simple status logic: if power > 1 W, assume ON
    is_on = p > 1.0
    status_text = "🟢 Device is ON" if is_on else "🔴 Device is OFF"


    m1, m2, m3 = st.columns(3)
    m1.metric("🔋 Voltage (V)", f"{v:.1f}")
    m2.metric("⚡ Power (W)", f"{p:.1f}")
    m3.metric("🔌 Current (A)", f"{c:.3f}")

    # Controls
    # colA, colB, colC = st.columns([1,1,2])
    # with colA:
    #     if st.button("Turn ON"):
    #         try:
    #             token = get_token()
    #             st.info(control_device(dev_id, token, "switch_1", True))
    #         except Exception as e:
    #             st.error(e)
    # with colB:
    #     if st.button("Turn OFF"):
    #         try:
    #             token = get_token()
    #             st.info(control_device(dev_id, token, "switch_1", False))
    #         except Exception as e:
    #             st.error(e)
    # with colC:
    #     if st.button("⬅️ Back to My Devises"):
    #         go_home()
    #         st.rerun()
        # Controls
    colA, colB, colC, colD = st.columns([1,1,1,2])

    with colA:
        if st.button("Turn ON"):
            try:
                token = get_token()
                st.info(control_device(dev_id, token, "switch_1", True))
            except Exception as e:
                st.error(e)

    with colB:
        if st.button("Turn OFF"):
            try:
                token = get_token()
                st.info(control_device(dev_id, token, "switch_1", False))
            except Exception as e:
                st.error(e)

    with colC:
        if st.button("Show Status"):
            st.info(status_text)

    with colD:
        if st.button("⬅️ Back to My Devises"):
            go_home()
            st.rerun()





    st.markdown("### ⚡ Recent Power (last 30 samples)")
    df_recent = latest_docs(dev_id, n=30)
    if not df_recent.empty:
        fig = px.line(
            df_recent,
            x="timestamp",
            y="power",
            title="Power (W)",
            markers=True
        )
        fig.update_layout(
            yaxis_title="Power (W)",
            xaxis_title="Time",
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")




    # Billing
    st.markdown("### 💰 Bill Estimate")
    d_units, d_cost, m_units, m_cost = daily_monthly_for(dev_id)
    b1, b2 = st.columns(2)
    with b1:
        st.metric("📅 Today kWh", f"{d_units:.3f}")
        st.metric("💸 Today BDT", f"{d_cost:.2f}")
    with b2:
        st.metric("🗓 Month kWh", f"{m_units:.3f}")
        st.metric("💰 Month BDT", f"{m_cost:.2f}")



    # Historical
    st.markdown("### 🕰️ Historical Data")
    c1, c2, c3 = st.columns(3)
    with c1:
        start_date = st.date_input("Start", value=datetime.now().date() - timedelta(days=1))
    with c2:
        end_date = st.date_input("End", value=datetime.now().date())
    with c3:
        agg = st.selectbox("Aggregation", ["raw", "1-min", "5-min", "15-min"], index=1)

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt   = datetime.combine(end_date, datetime.max.time())
    df = range_docs(dev_id, start_dt, end_dt)



    if not df.empty:
        df = df.sort_values("timestamp").set_index("timestamp")

        if agg != "raw":
            rule = {"1-min": "1T", "5-min": "5T", "15-min": "15T"}[agg]
            df = df.resample(rule).mean(numeric_only=True).dropna()

        # Plotly line (autoscale). Keep Y ≥ 0 and show unified hover.
        plot_df = df.reset_index()  # Plotly wants columns
        fig = px.line(
            plot_df,
            x="timestamp",
            y="power",
            title=f"Power over time ({agg})",
            markers=(agg == "raw")
        )
        fig.update_layout(
            hovermode="x unified",
            xaxis_title="Time",
            yaxis_title="Power (W)",
            template="plotly_white"
        )
        # Keep Y from going negative but let upper bound autoscale
        fig.update_yaxes(rangemode="tozero")

        # Time controls
        fig.update_xaxes(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    # dict(count=6, step="hour", stepmode="backward", label="6h"),
                    # dict(count=12, step="hour", stepmode="backward", label="12h"),
                    # dict(count=1, step="day", stepmode="backward", label="1d"),
                    dict(step="all", label="All")
                ])
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(plot_df.tail(200))
    else:
        st.info("No data in selected range.")



# ------------------------------Range Reports Page ----------------------------------------------

def _device_label(d):
    return f"{d['name']} ({d['id']})"


def _run_single_device_range_report(dev_id: str, dev_name: str,
                                    start_dt: datetime, end_dt: datetime,
                                    agg: str):
    st.subheader(f"🔌 Single Device: {dev_name}")

    df = range_docs(dev_id, start_dt, end_dt)
    if df.empty:
        st.info("No data for this device in the selected range.")
        return

    df = df.sort_values("timestamp").set_index("timestamp")

    if agg != "raw":
        rule = {"1-min": "1T", "5-min": "5T", "15-min": "15T"}[agg]
        df = df.resample(rule).mean(numeric_only=True).dropna()

    has_v = "voltage" in df.columns
    has_c = "current" in df.columns
    has_e = "energy_kWh" in df.columns

    avg_v = df["voltage"].mean() if has_v else None
    min_v = df["voltage"].min() if has_v else None
    max_v = df["voltage"].max() if has_v else None

    avg_c = df["current"].mean() if has_c else None
    max_c = df["current"].max() if has_c else None

    total_kwh = float(df["energy_kWh"].sum()) if has_e else 0.0
    bill_bdt = _tier_cost(total_kwh)

    c1, c2, c3 = st.columns(3)
    with c1:
        if has_v:
            st.metric("Avg Voltage (V)", f"{avg_v:.2f}")
            st.metric("Min Voltage (V)", f"{min_v:.2f}")
            st.metric("Max Voltage (V)", f"{max_v:.2f}")
        else:
            st.write("No voltage data.")
    with c2:
        if has_c:
            st.metric("Avg Current (A)", f"{avg_c:.3f}")
            st.metric("Max Current (A)", f"{max_c:.3f}")
        else:
            st.write("No current data.")
    with c3:
        st.metric("Total Energy (kWh)", f"{total_kwh:.3f}")
        st.metric("Estimated Bill (BDT)", f"{bill_bdt:.2f}")

    st.markdown("#### Voltage & Current over time")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.6, 0.4],
        subplot_titles=("Voltage (V)", "Current (A)"),
    )

    if has_v:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["voltage"],
                mode="lines",
                name="Voltage (V)",
            ),
            row=1,
            col=1,
        )

    if has_c:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["current"],
                mode="lines",
                name="Current (A)",
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        showlegend=False,
        height=400,
    )
    # fig.update_xaxes(
    #     title_text="Time",
    #     rangeslider=dict(visible=True),
    #     rangeselector=dict(
    #         buttons=[
    #             dict(count=6, step="hour", stepmode="backward", label="6h"),
    #             dict(count=12, step="hour", stepmode="backward", label="12h"),
    #             dict(count=1, step="day", stepmode="backward", label="1d"),
    #             dict(step="all", label="All"),
    #         ]
    #     ),
    #     row=2,
    #     col=1,
    # )
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=1)
    fig.update_yaxes(title_text="Current (A)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------Range Reports Page ----------------------------------------------

def _run_all_devices_range_report(devices, start_dt: datetime, end_dt: datetime,
                                  agg: str):
    st.subheader("🌐 All Devices — Combined Power & Bill")

    dev_ids = [d["id"] for d in devices]

    # Time-series for total power
    frames = []
    for d in devices:
        df = range_docs(d["id"], start_dt, end_dt)
        if df.empty or "timestamp" not in df.columns or "power" not in df.columns:
            continue
        df = df[["timestamp", "power"]].sort_values("timestamp").set_index("timestamp")
        if agg != "raw":
            rule = {"1-min": "1T", "5-min": "5T", "15-min": "15T"}[agg]
            df = df.resample(rule).mean(numeric_only=True)
        frames.append(df)

    if not frames:
        st.info("No power data for any device in this range.")
        return

    aligned = pd.concat(frames, axis=1)
    total_power = aligned.sum(axis=1, min_count=1)

    # Total kWh across all devices (use original energy_kWh)
    total_kwh = 0.0
    for did in dev_ids:
        df_e = range_docs(did, start_dt, end_dt)
        if not df_e.empty and "energy_kWh" in df_e.columns:
            total_kwh += float(df_e["energy_kWh"].sum())
    total_kwh = round(total_kwh, 3)
    bill_bdt = _tier_cost(total_kwh)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Energy (kWh)", f"{total_kwh:.3f}")
    with c2:
        st.metric("Estimated Total Bill (BDT)", f"{bill_bdt:.2f}")

    st.markdown("#### Total Power over time (all devices)")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=total_power.index,
            y=total_power.values,
            mode="lines",
            name="Total Power (W)",
        )
    )
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        yaxis_title="Power (W)",
        xaxis_title="Time",
    )
    # fig.update_yaxes(rangemode="tozero")
    # fig.update_xaxes(
    #     rangeslider=dict(visible=True),
    #     rangeselector=dict(
    #         buttons=[
    #             dict(count=6, step="hour", stepmode="backward", label="6h"),
    #             dict(count=12, step="hour", stepmode="backward", label="12h"),
    #             dict(count=1, step="day", stepmode="backward", label="1d"),
    #             dict(step="all", label="All"),
    #         ]
    #     ),
    # )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------Range Reports Page ----------------------------------------------

def page_reports():
    st.title("📈 Range Reports")
    st.caption("Generate custom range reports for one device or all devices combined.")

    devices = load_devices()
    if not devices:
        st.info("No devices configured yet.")
        return

    # Device selector with "All devices" option
    options = ["All devices (combined)"] + [_device_label(d) for d in devices]
    choice = st.selectbox("Device / Scope", options)

    selected_dev = None
    if choice != "All devices (combined)":
        for d in devices:
            if _device_label(d) == choice:
                selected_dev = d
                break

    c1, c2, c3 = st.columns(3)
    with c1:
        start_date = st.date_input("Start date", value=datetime.now().date())
    with c2:
        end_date = st.date_input("End date", value=datetime.now().date())
    with c3:
        agg = st.selectbox("Aggregation", ["raw", "1-min", "5-min", "15-min"], index=2)

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    if start_dt >= end_dt:
        st.warning("Start must be before end.")
        return

    if st.button("Run report"):
        if choice == "All devices (combined)":
            _run_all_devices_range_report(devices, start_dt, end_dt, agg)
        else:
            _run_single_device_range_report(
                selected_dev["id"], selected_dev["name"], start_dt, end_dt, agg
            )


# ------------------------------User Manual Page ----------------------------------------------

def page_manual():
    st.title("📘 User Manual")
    st.caption("How to use the Smart Plug Energy Monitor dashboard effectively.")

    st.markdown("### 1. Overview")
    st.markdown(
        "- **Home**: High-level overview of all devices, today & monthly bill, and 24h chart.\n"
        "- **My Devices**: List of all configured smart plugs.\n"
        "- **Range Reports**: Detailed analytics for a custom date range for single & all combined devices.\n"
        "- **Device page**: Control, Live readings and billing estimate."
    )

    with st.expander("Introducing with a new device"):
        st.markdown(
            "1. Add your device in the socket.\n"
            "2. Connect it to WiFi using the Tuya **SmartLife** app.\n"
            "3. Ensure it is online in the Tuya **SmartLife** app.\n"
            "4. Note down the **Device ID** from the Tuya app (Click to Device > Edit >  Device Info > Device ID/Virtual ID).\n"
            "2. Use **Add Device** in this dashboard to register it."
        )

    with st.expander("Getting started"):
        st.markdown(
            "1. Go to **Add Device** from the sidebar or Home quick actions.\n"
            "2. Enter a **Device Name** (friendly label) and the **Device ID** from Tuya.\n"
            "3. Click **Save**. The device will appear under **My Devices**.\n"
            "4. Open the device to start logging live data."
        )

    with st.expander("Live Device View & Controls"):
        st.markdown(
            "- Open a device from **My Devices**.\n"
            "- The top metrics show **Voltage (V)**, **Power (W)** and **Current (A)** in real-time.\n"
            "- Use **Turn ON / Turn OFF** buttons to control the plug via Tuya.\n"
            "- **Bill Estimate** shows today and this month’s kWh and cost (BDT) based on Bangladeshi tariff."
        )

    with st.expander("Range Reports (Single & All Devices)"):
        st.markdown(
            "- Go to **Range Reports** from the sidebar or Home quick action.\n"
            "- Choose either **All devices (combined)** or a single device.\n"
            "- Select **Start date**, **End date**, and **Aggregation** (raw / 1-min / 5-min / 15-min).\n"
            "- Click **Run report**:\n"
            "  - Single Device: Voltage, Current stats, total energy and bill for that device.\n"
            "  - All Devices: Combined power curve, total kWh and bill for all devices."
        )
    
    with st.expander("Managing Devices"):
        st.markdown(
            "- Go to **Manage Devices** from the sidebar or Home quick action.\n"
            "- Edit device names or IDs directly in the text fields.\n"
            "- Use **Save** to update, **Delete** to remove, or **Open** to view live data."
        )

    with st.expander("Understanding key metrics"):
        st.markdown(
            "- **Power (W)**: Instant power consumption.\n"
            "- **Energy (kWh)**: Accumulated energy over time.\n"
            "- **Voltage (V)** and **Current (A)**: Line quality and load.\n"
            "- **Bill (BDT)**: Calculated using your configured tiered tariff."
        )

    with st.expander("Troubleshooting"):
        st.markdown(
            "- If a device shows **Tuya API error**, check:\n"
            "  - Internet connectivity.\n"
            "  - Tuya credentials / token configuration.\n"
            "  - Device is online in the Tuya app.\n"
            "- If charts are empty:\n"
            "  - Make sure the device has been opened at least once to start logging.\n"
            "  - Adjust the date range and aggregation."
        )


# ------------------------------------------------------------------------------------------------------------------------
# Sidebar navigation (kept in sync with router)

nav_choice = st.sidebar.radio(
    "Navigate",
    ["Home", "My Devices", "Add Device", "Manage Devices", "Range Reports", "User Manual"],
    index={
        "home": 0,
        "mydevices": 1,
        "add": 2,
        "manage": 3,
        "reports": 4,
        "manual": 5
    }.get(st.session_state.route, 0)
)

st.sidebar.markdown("---")
st.sidebar.caption("Auto-logging every 30s while a device page is open.")

sidebar_map = {
    "Home": "home",
    "My Devices": "mydevices",
    "Add Device": "add",
    "Manage Devices": "manage",
    "Range Reports": "reports",
    "User Manual": "manual",
}


if sidebar_map[nav_choice] != st.session_state.route and st.session_state.route != "device":
    set_route(sidebar_map[nav_choice])


# ------------------------------------------------------------------------------------------------------------------------

# Router
if st.session_state.route == "home":
    page_home()
elif st.session_state.route == "mydevices":
    page_mydevices()
elif st.session_state.route == "add":
    page_add()
elif st.session_state.route == "manage":
    page_manage()
elif st.session_state.route == "device":
    page_device()
elif st.session_state.route == "reports":
    page_reports()
elif st.session_state.route == "manual":
    page_manual()
else:
    page_home()

# End of app.py


