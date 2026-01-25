
````md
# ⚡ Energy Monitoring System (Tuya)

A Python-based energy monitoring project that connects to **Tuya-compatible smart energy/power devices**, collects power/energy readings, and helps you analyze usage and estimate billing/cost.

> Repo includes modules like `tuya_api.py`, `get_power_data.py`, `data_collector.py`, and `billing.py` plus configuration via `devices.json` and optional Mongo integration via `tuya_api_mongo.py`. :contentReference[oaicite:1]{index=1}

---

## ✨ What this project does

- Connects to Tuya devices and fetches power/energy data (see `tuya_api.py`, `get_power_data.py`). :contentReference[oaicite:2]{index=2}
- Collects and stores readings over time (see `data_collector.py`, `data/`). :contentReference[oaicite:3]{index=3}
- Calculates electricity billing/cost estimates (see `billing.py`). :contentReference[oaicite:4]{index=4}
- Supports multiple devices via `devices.json` (see `devices.json`, `devices.py`). :contentReference[oaicite:5]{index=5}
- Optional MongoDB-based storage (see `tuya_api_mongo.py`). :contentReference[oaicite:6]{index=6}

---

## 🧱 Project structure

| File/Folder | Purpose |
|------------|---------|
| `app.py` | Main application entry (dashboard/UI/controller) :contentReference[oaicite:7]{index=7} |
| `app_merged.py` | Alternative merged version of the app :contentReference[oaicite:8]{index=8} |
| `tuya_api.py` | Tuya integration helpers :contentReference[oaicite:9]{index=9} |
| `tuya_api_mongo.py` | Tuya + MongoDB integration :contentReference[oaicite:10]{index=10} |
| `get_power_data.py` | Fetch readings from device(s) :contentReference[oaicite:11]{index=11} |
| `data_collector.py` | Periodic collection / logging :contentReference[oaicite:12]{index=12} |
| `billing.py` | Billing/cost calculation utilities :contentReference[oaicite:13]{index=13} |
| `devices.json` | Your device list/config :contentReference[oaicite:14]{index=14} |
| `devices.py` | Device model/helpers :contentReference[oaicite:15]{index=15} |
| `helpers.py` | Shared utilities :contentReference[oaicite:16]{index=16} |
| `data/` | Stored readings/logs (local) :contentReference[oaicite:17]{index=17} |
| `config.toml` | App configuration :contentReference[oaicite:18]{index=18} |
| `requirements.txt` | Python dependencies :contentReference[oaicite:19]{index=19} |

---

## ✅ Prerequisites

- Python 3.9+ recommended
- A Tuya IoT project and credentials (from Tuya Developer Platform)
- At least one Tuya-compatible smart plug/energy meter added to your Tuya account

---

## 🚀 Quick start

### 1) Clone and install dependencies
```bash
git clone https://github.com/JobayerFaisal/Energy_Monitoring_System.git
cd Energy_Monitoring_System

python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
````

### 2) Configure environment variables

This repo currently contains a `.env` file in the root. **Do not commit real secrets**—it’s safer to keep `.env` local and commit only `.env.example`. ([GitHub][1])

Create a `.env` file (or update yours) with your Tuya credentials. Typical variables look like:

```env
# Example (rename to match your code)
TUYA_ACCESS_ID=your_access_id
TUYA_ACCESS_KEY=your_access_key
TUYA_REGION=your_region   # e.g., "us", "eu", "in", etc.
TUYA_USERNAME=your_tuya_account_email_or_phone
TUYA_PASSWORD=your_tuya_account_password
TUYA_COUNTRY_CODE=880
```

> The exact variable names depend on how your `tuya_api.py` loads them. If your code uses different keys, keep the same names used in your `.env`. ([GitHub][1])

### 3) Add your devices (`devices.json`)

Update `devices.json` with your Tuya devices (IDs/names/labels). ([GitHub][1])

Example shape (adjust to your format):

```json
[
  {
    "name": "Main Room Plug",
    "device_id": "xxxxxxxxxxxxxxxxxxxx",
    "location": "Room-101"
  }
]
```

---

## ▶️ Running the project

### Option A — Run the main app

Try:

```bash
python app.py
```

If `app.py` is a Streamlit dashboard in your setup, run:

```bash
streamlit run app.py
```

> Your repo includes `app.py` and `config.toml`, so this project is set up like a typical Python dashboard/app entry point. ([GitHub][1])

### Option B — Collect data periodically

If you want continuous collection, run:

```bash
python data_collector.py
```

This will typically append/store readings into `data/`. ([GitHub][1])

---

## 💰 Billing / cost calculation

Billing logic lives in:

* `billing.py` ([GitHub][1])

You can usually:

* compute cost per day/week/month
* apply a unit price (kWh rate)
* generate summaries based on stored readings

If your billing rate is configurable, keep it in `config.toml` (or inside the app UI). ([GitHub][1])

---

## 🗄️ Storage options

* **Local storage**: data stored under `data/` (simple and easy for development). ([GitHub][1])
* **MongoDB**: use `tuya_api_mongo.py` if you want centralized/production storage. ([GitHub][1])

---

## 🔗 Related repos (your full system)

If you’re running this as a full product with frontend/backend:

* Web frontend repo: `Energy_monitoring_System_web` (has a deployed site listed in About). ([GitHub][2])
* Backend repo: `Energy_Monitoring_System_backend`. ([GitHub][3])

---

## 🔐 Security note (important)

This repo contains a `.env` in the root. Avoid committing secrets.

Recommended:

* Add `.env` to `.gitignore`
* Commit a `.env.example` template instead
* Remove `__pycache__/` from git and ignore it

Both `.env` and `__pycache__/` currently exist in the repo tree. ([GitHub][1])

---

## 🛣️ Roadmap ideas

* Add charts (daily/monthly trends)
* Add CSV export
* Add device grouping (building/floor/room)
* Dockerize (Docker + docker-compose for Mongo + app)
* GitHub Actions for linting/tests

---

## 📄 License

Add a license file (MIT/Apache-2.0/GPL-3.0) depending on how you want others to use it.

```

---

If you want, I can also generate:
- a **`.env.example`** based on the variables your code actually reads, and  
- a **`.gitignore`** that properly ignores `.env`, `__pycache__/`, and `data/` outputs,

…but for that I’d need you to paste the relevant part of `tuya_api.py` where it loads env vars (or tell me what the keys are).
::contentReference[oaicite:32]{index=32}
```

[1]: https://github.com/JobayerFaisal/Energy_Monitoring_System "GitHub - JobayerFaisal/Energy_Monitoring_System"
[2]: https://github.com/JobayerFaisal/Energy_monitoring_System_web?utm_source=chatgpt.com "GitHub - JobayerFaisal/Energy_monitoring_System_web"
[3]: https://github.com/JobayerFaisal/Energy_Monitoring_System_backend?utm_source=chatgpt.com "GitHub - JobayerFaisal/Energy_Monitoring_System_backend"
