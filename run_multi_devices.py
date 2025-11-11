
import json
import time
from pathlib import Path
from tuya_api_mongo_v2 import get_token, get_device_status, log_data

DEVICES_JSON_PATH = Path("D:/SmartHome/SmartHome/devices.json")  # adjust if needed

def load_devices():
    if DEVICES_JSON_PATH.exists():
        return json.loads(DEVICES_JSON_PATH.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"{DEVICES_JSON_PATH} not found")

def run_once():
    token = get_token()
    devices = load_devices()
    results = []
    for d in devices:
        name = d.get("name")
        did = d.get("id")
        if not did:
            continue
        status = get_device_status(did, token)
        entry = log_data(did, status, device_name=name)
        results.append(entry)
    return results

if __name__ == "__main__":
    # Run a single cycle; for a daemon/cron, call run_once() on your schedule.
    out = run_once()
    for r in out:
        print(r)
