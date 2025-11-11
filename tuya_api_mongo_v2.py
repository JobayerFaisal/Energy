
import os
import hmac
import hashlib
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- MongoDB ---
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
API_ENDPOINT = os.getenv("TUYA_API_ENDPOINT")
MONGODB_URI = os.getenv("MONGODB_URI")

# ---------------------- SIGNING ----------------------
def make_sign(client_id, secret, method, url, access_token="", body=""):
    t = str(int(time.time() * 1000))
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
    path = "/v1.0/token?grant_type=1"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path)
    headers = {"client_id": ACCESS_ID, "sign": sign, "t": t, "sign_method": "HMAC-SHA256"}
    res = requests.get(API_ENDPOINT + path, headers=headers, timeout=15)
    data = res.json()
    if not data.get("success"):
        raise Exception(f"Failed to get token: {data}")
    return data["result"]["access_token"]

# ---------------------- DEVICE API ----------------------
def get_device_status(device_id, token):
    path = f"/v1.0/devices/{device_id}/status"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path, token)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256"
    }
    res = requests.get(API_ENDPOINT + path, headers=headers, timeout=15)
    return res.json()

def control_device(device_id, token, command, value):
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
    res = requests.post(API_ENDPOINT + path, headers=headers, data=body, timeout=15)
    return res.json()

# ---------------------- MONGO ----------------------
_mongo_client = None

def _get_mongo():
    global _mongo_client
    if not MONGODB_URI:
        return None
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI, tls=True)
    return _mongo_client

def _get_collection(device_id: str):
    client = _get_mongo()
    if client is None:
        return None
    db = client.get_default_database() if client.get_default_database() else client["tuya_energy"]
    coll = db[f"readings_{device_id}"]
    try:
        coll.create_index([("timestamp", ASCENDING)])
    except Exception:
        pass
    return coll

# ---------------------- LOGGING ----------------------
def log_data(device_id, status_data, device_name=None):
    """Save reading to CSV and Mongo. Supports optional device_name."""
    result = status_data.get("result", [])
    metrics = {item["code"]: item["value"] for item in result}

    voltage = metrics.get("cur_voltage", 0) / 10.0
    power = metrics.get("cur_power", 0)
    current = metrics.get("cur_current", 0) / 1000.0
    energy_kWh = power / 1000 / 60  # 1-minute sample approximation

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", f"{device_id}.csv")

    ts_dt = datetime.now(timezone.utc)
    ts_str = ts_dt.strftime("%Y-%m-%d %H:%M:%S")

    row = {
        "timestamp": ts_str,
        "device_id": device_id,
        "device_name": device_name or "",
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy_kWh": energy_kWh
    }

    # CSV
    df = pd.DataFrame([row])
    write_header = not os.path.exists(file_path)
    df.to_csv(file_path, mode="a", header=write_header, index=False)

    # Mongo
    coll = _get_collection(device_id)
    if coll is not None:
        try:
            doc = {
                "device_id": device_id,
                "device_name": device_name,
                "timestamp": ts_dt,
                "voltage": float(voltage),
                "current": float(current),
                "power": float(power),
                "energy_kWh": float(energy_kWh),
            }
            coll.insert_one(doc)
        except PyMongoError as e:
            print(f"Mongo insert error: {e}")

    return row
