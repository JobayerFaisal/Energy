import os
import hmac
import hashlib
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- MongoDB ---
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

# -------------------------------------------------------------------
# 📦  CONFIGURATION
# -------------------------------------------------------------------
load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
API_ENDPOINT = os.getenv("TUYA_API_ENDPOINT", "https://openapi.tuyaeu.com")

MONGODB_URI = os.getenv("MONGODB_URI")  # may or may not include a default DB
MONGODB_DB = os.getenv("MONGODB_DB", "tuya_energy")  # fallback database if URI has none

DATA_DIR = Path("data")
DEVICES_JSON_PATH = Path("devices.json")  # optional: [{"name": "...", "id": "..."}]
HTTP_TIMEOUT = 15  # seconds

# -------------------------------------------------------------------
# 🔐 SIGNING & AUTHENTICATION
# -------------------------------------------------------------------
def make_sign(client_id, secret, method, url, access_token: str = "", body: str = ""):
    """Generate Tuya HMAC signature."""
    t = str(int(time.time() * 1000))
    message = client_id + access_token + t
    string_to_sign = "\n".join([
        method.upper(),
        hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "",
        url
    ])
    sign_str = message + string_to_sign
    sign = hmac.new(secret.encode("utf-8"), sign_str.encode("utf-8"),
                    hashlib.sha256).hexdigest().upper()
    return sign, t

def get_token():
    """Fetch Tuya cloud access token."""
    path = "/v1.0/token?grant_type=1"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }
    res = requests.get(API_ENDPOINT + path, headers=headers, timeout=HTTP_TIMEOUT)
    data = res.json()
    if not data.get("success"):
        raise RuntimeError(f"Failed to get token: {data}")
    return data["result"]["access_token"]

# -------------------------------------------------------------------
# ⚡ DEVICE STATUS & CONTROL
# -------------------------------------------------------------------
def get_device_status(device_id: str, token: str):
    """Fetch device's current status values (voltage, power, current, etc.)."""
    path = f"/v1.0/devices/{device_id}/status"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path, token)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256",
    }
    res = requests.get(API_ENDPOINT + path, headers=headers, timeout=HTTP_TIMEOUT)
    return res.json()

def control_device(device_id: str, token: str, command: str, value):
    """Send a command (e.g., switch_1 true/false) to a device."""
    path = f"/v1.0/devices/{device_id}/commands"
    body = f'{{"commands":[{{"code":"{command}","value":{str(value).lower()}}}]}}'
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "POST", path, token, body)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256",
        "Content-Type": "application/json",
    }
    res = requests.post(API_ENDPOINT + path, headers=headers, data=body, timeout=HTTP_TIMEOUT)
    return res.json()

# -------------------------------------------------------------------
# 🗄️  MONGODB HELPERS (SAFE)
# -------------------------------------------------------------------
_mongo_client = None

def _get_mongo():
    """Return a cached Mongo client if URI is configured."""
    global _mongo_client
    if not MONGODB_URI:
        return None
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGODB_URI, tls=True)
    return _mongo_client

def _get_db(client: MongoClient):
    """Return default DB from URI if present; else fallback to MONGODB_DB."""
    db = None
    try:
        db = client.get_default_database()  # only works if URI ends with /<db>
    except Exception:
        db = None
    if db is None:
        db = client[MONGODB_DB]
    return db

def _get_collection(device_id: str):
    """Get (or create) the collection for this device."""
    client = _get_mongo()
    if client is None:
        return None
    db = _get_db(client)
    coll = db[f"readings_{device_id}"]
    try:
        coll.create_index([("timestamp", ASCENDING)])
    except Exception:
        pass
    return coll

# -------------------------------------------------------------------
# 📊 LOGGING & STORAGE
# -------------------------------------------------------------------
def _parse_metrics(status_json: dict):
    """Extract and normalize metrics from Tuya status response."""
    result = status_json.get("result", [])
    metrics = {item.get("code"): item.get("value") for item in result}

    voltage = (metrics.get("cur_voltage") or 0) / 10.0    # Tuya reports in deciVolts
    power = metrics.get("cur_power") or 0                 # watts
    current = (metrics.get("cur_current") or 0) / 1000.0  # mA -> A
    # Approx energy for 1-minute sample (kWh) if you call once per minute
    energy_kWh = power / 1000.0 / 60.0

    return voltage, current, power, energy_kWh

def log_data(device_id: str, status_data: dict, device_name: str | None = None):
    """Save voltage/current/power to CSV and MongoDB (if configured)."""
    voltage, current, power, energy_kWh = _parse_metrics(status_data)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIR / f"{device_id}.csv"

    # Timestamp: timezone-aware UTC for Mongo; string for CSV
    ts_dt = datetime.now(timezone.utc)
    ts_str = ts_dt.strftime("%Y-%m-%d %H:%M:%S")

    csv_row = {
        "timestamp": ts_str,
        "device_id": device_id,
        "device_name": device_name or "",
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy_kWh": energy_kWh,
    }

    # ---- CSV ----
    df = pd.DataFrame([csv_row])
    write_header = not file_path.exists()
    df.to_csv(file_path, mode="a", header=write_header, index=False)

    # ---- Mongo ----
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
            # Do not break CSV logging if Mongo fails
            print(f"Mongo insert error: {e}")

    return csv_row

def backfill_csv_to_mongo(device_id: str):
    """Import an existing CSV for a device into MongoDB."""
    file_path = DATA_DIR / f"{device_id}.csv"
    coll = _get_collection(device_id)
    if coll is None:
        print("MongoDB not configured; skipping backfill.")
        return 0
    if not file_path.exists():
        print("No CSV found to backfill.")
        return 0

    df = pd.read_csv(file_path)
    docs = []
    for _, row in df.iterrows():
        ts = row.get("timestamp")
        if isinstance(ts, str):
            try:
                ts_dt = datetime.fromisoformat(ts)
            except ValueError:
                try:
                    ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    ts_dt = datetime.now(timezone.utc)
        else:
            ts_dt = datetime.now(timezone.utc)

        docs.append({
            "device_id": device_id,
            "device_name": row.get("device_name") or None,
            "timestamp": ts_dt,
            "voltage": float(row.get("voltage", 0)),
            "current": float(row.get("current", 0)),
            "power": float(row.get("power", 0)),
            "energy_kWh": float(row.get("energy_kWh", 0)),
        })

    if not docs:
        return 0

    try:
        result = coll.insert_many(docs, ordered=False)
        return len(result.inserted_ids)
    except PyMongoError as e:
        print(f"Backfill error: {e}")
        return 0

# -------------------------------------------------------------------
# 🚀 MULTI-DEVICE SUPPORT
# -------------------------------------------------------------------
def load_devices_from_json(path: Path = DEVICES_JSON_PATH):
    """Load device list from devices.json: [{\"name\": ..., \"id\": ...}, ...]."""
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def run_once_all_devices():
    """Fetch and log one reading for each device in devices.json."""
    token = get_token()
    devices = load_devices_from_json()
    results = []
    if not devices:
        print("No devices.json found or empty; nothing to run.")
        return results

    for d in devices:
        name = d.get("name")
        did = d.get("id")
        if not did:
            continue
        status = get_device_status(did, token)
        entry = log_data(did, status, device_name=name)
        results.append(entry)
    return results

# -------------------------------------------------------------------
# 🧪 MAIN (examples)
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Priority: run all devices if devices.json present
    if DEVICES_JSON_PATH.exists():
        out = run_once_all_devices()
        for r in out:
            print(r)
    else:
        # Single-device example (replace with your real device id)
        device_id = os.getenv("TUYA_DEVICE_ID", "YOUR_DEVICE_ID")
        token = get_token()
        status = get_device_status(device_id, token)
        print(log_data(device_id, status))
        # Optional: backfill historical CSV for this device into Mongo
        # backfill_csv_to_mongo(device_id)
