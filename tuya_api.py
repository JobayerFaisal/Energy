import os
import hmac
import hashlib
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
API_ENDPOINT = os.getenv("TUYA_API_ENDPOINT")


# -------------------------------------------------------------------
# 🔐 SIGNING & AUTHENTICATION
# -------------------------------------------------------------------

def make_sign(client_id, secret, method, url, access_token="", body=""):
    """Generate valid Tuya HMAC signature"""
    t = str(int(time.time() * 1000))
    # Tuya's signature string structure
    message = client_id + access_token + t
    string_to_sign = "\n".join([
        method.upper(),
        hashlib.sha256(body.encode('utf-8')).hexdigest(),
        "",
        url
    ])
    sign_str = message + string_to_sign
    sign = hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'),
                    hashlib.sha256).hexdigest().upper()
    return sign, t


def get_token():
    """Fetch Tuya cloud access token"""
    path = "/v1.0/token?grant_type=1"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }
    res = requests.get(API_ENDPOINT + path, headers=headers)
    data = res.json()
    if not data.get("success"):
        raise Exception(f"Failed to get token: {data}")
    return data["result"]["access_token"]


# -------------------------------------------------------------------
# ⚡ DEVICE STATUS & CONTROL
# -------------------------------------------------------------------

def get_device_status(device_id, token):
    """Fetch device's current status values (voltage, power, current, etc.)"""
    path = f"/v1.0/devices/{device_id}/status"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path, token)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256"
    }
    res = requests.get(API_ENDPOINT + path, headers=headers)
    return res.json()


def control_device(device_id, token, command, value):
    """Turn device ON/OFF"""
    path = f"/v1.0/devices/{device_id}/commands"
    body = f'{{"commands":[{{"code":"{command}","value":{str(value).lower()}}}]}}'
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "POST", path, token, body)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256",
        "Content-Type": "application/json"
    }
    res = requests.post(API_ENDPOINT + path, headers=headers, data=body)
    return res.json()


# -------------------------------------------------------------------
# 📊 LOGGING & STORAGE
# -------------------------------------------------------------------

def log_data(device_id, status_data):
    """Save voltage, current, and power readings to CSV for history"""
    result = status_data.get("result", [])
    metrics = {item["code"]: item["value"] for item in result}

    voltage = metrics.get("cur_voltage", 0) / 10.0
    power = metrics.get("cur_power", 0)
    current = metrics.get("cur_current", 0) / 1000.0
    energy_kWh = power / 1000 / 60  # approximate energy for 1-minute sample

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", f"{device_id}.csv")

    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy_kWh": energy_kWh
    }

    df = pd.DataFrame([new_entry])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

    return new_entry
