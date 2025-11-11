# billing.py
import pandas as pd
from datetime import datetime

# --- Bangladesh Tiered Rates (as of Feb 29, 2024) ---
RATES = [
    (50, 4.63),   # 0–50  (Palli Bidyut)
    (75, 5.26),   # 51–75
    (200, 7.20),  # 76–200
    (300, 7.59),  # 201–300
    (400, 8.02),  # 301–400
    (600, 12.67), # 401–600
    (float("inf"), 14.61)  # Above 600
]


def calculate_tiered_cost(units_kwh: float) -> float:
    """Return cost in Taka for given kWh based on Bangladesh’s tiered rates."""
    remaining = units_kwh
    last_upper = 0
    cost = 0.0
    for upper, rate in RATES:
        if remaining <= 0:
            break
        slab_units = min(remaining, upper - last_upper)
        cost += slab_units * rate
        remaining -= slab_units
        last_upper = upper
    return round(cost, 2)


def daily_and_monthly_bill(device_id: str):
    """Return (daily_units, daily_cost, monthly_units, monthly_cost)"""
    file_path = f"data/{device_id}.csv"
    try:
        df = pd.read_csv(file_path, parse_dates=["timestamp"])
    except FileNotFoundError:
        return 0, 0, 0, 0

    df["date"] = df["timestamp"].dt.date
    today = datetime.now().date()

    # --- Daily totals ---
    daily_df = df[df["date"] == today]
    daily_units = round(daily_df["energy_kWh"].sum(), 3)
    daily_cost = calculate_tiered_cost(daily_units)

    # --- Monthly totals ---
    month_df = df[df["timestamp"].dt.month == datetime.now().month]
    monthly_units = round(month_df["energy_kWh"].sum(), 3)
    monthly_cost = calculate_tiered_cost(monthly_units)

    return daily_units, daily_cost, monthly_units, monthly_cost
