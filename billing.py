from datetime import datetime
import pandas as pd
from tuya_api_mongo import range_docs

# Bangladesh slab rates (example)
RATES = [
    (50, 4.63), (75, 5.26), (200, 7.20), (300, 7.59),
    (400, 8.02), (600, 12.67), (float("inf"), 14.61)
]

def _tier_cost(units_kwh: float) -> float:
    remaining, last_upper, cost = units_kwh, 0, 0.0
    for upper, rate in RATES:
        if remaining <= 0: break
        slab = min(remaining, upper - last_upper)
        cost += slab * rate
        remaining -= slab
        last_upper = upper
    return round(cost, 2)

def daily_monthly_for(device_id: str):
    now = datetime.now()
    # day range
    day_start = datetime(now.year, now.month, now.day)
    day_end   = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
    ddf = range_docs(device_id, day_start, day_end)
    d_units = round(float(ddf["energy_kWh"].sum()) if not ddf.empty else 0.0, 3)
    d_cost  = _tier_cost(d_units)

    # month range
    m_start = datetime(now.year, now.month, 1)
    # naive month-end
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    m_end = next_month.replace(hour=0, minute=0, second=0, microsecond=0)
    mdf = range_docs(device_id, m_start, m_end)
    m_units = round(float(mdf["energy_kWh"].sum()) if not mdf.empty else 0.0, 3)
    m_cost  = _tier_cost(m_units)
    return d_units, d_cost, m_units, m_cost
