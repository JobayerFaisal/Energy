import requests, time, hashlib, hmac, os, json
from dotenv import load_dotenv

load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
API_ENDPOINT = os.getenv("TUYA_API_ENDPOINT")
DEVICE_ID = "bfec2888eb965010fam3gj"  # your device id

def make_sign(client_id, secret, method, url, access_token="", body=""):
    t = str(int(time.time() * 1000))
    message = client_id + access_token + t
    string_to_sign = "\n".join([method.upper(), hashlib.sha256(body.encode('utf-8')).hexdigest(), "", url])
    sign_str = message + string_to_sign
    sign = hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    return sign, t

def get_token():
    path = "/v1.0/token?grant_type=1"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "sign_method": "HMAC-SHA256"
    }
    url = API_ENDPOINT + path
    res = requests.get(url, headers=headers)
    print("Token response:", res.text)
    data = res.json()
    if not data.get("success"):
        print("❌ Failed to get token:", data)
        return None
    print("✅ Token fetched successfully!")
    return data["result"]["access_token"]

def get_device_status(token):
    path = f"/v1.0/devices/{DEVICE_ID}/status"
    sign, t = make_sign(ACCESS_ID, ACCESS_SECRET, "GET", path, token)
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": t,
        "access_token": token,
        "sign_method": "HMAC-SHA256"
    }
    url = API_ENDPOINT + path
    res = requests.get(url, headers=headers)
    print("Device response:", res.text)
    return res.json()

if __name__ == "__main__":
    token = get_token()
    if token:
        get_device_status(token)
