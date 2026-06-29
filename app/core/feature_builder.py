import math
from datetime import datetime, timezone
from typing import Optional
import numpy as np

HIGH_RISK_MCC = {"5912", "7995", "6051", "4829", "6050", "5999", "7273"}
HIGH_RISK_COUNTRIES = {"NG", "RO", "BR", "UA", "PK", "ID"}

MCC_CATEGORY_MAP = {
    "5411": "Groceries", "5812": "Dining", "5541": "Fuel",
    "4111": "Transport", "7011": "Hotels", "5912": "Pharmacy",
    "7995": "Gambling", "6051": "Crypto/Wire", "4829": "Money Transfer",
    "5999": "Misc Retail", "5045": "Electronics", "5311": "Department Store",
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_features(
    txn: dict,
    history: list[dict],
    cardholder_stats: dict,
) -> dict:
    ts: datetime = txn["timestamp"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    hour = ts.hour
    dow = ts.weekday()
    is_night = int(hour < 6 or hour >= 22)
    is_weekend = int(dow >= 5)

    now_epoch = ts.timestamp()
    recent_1h = [h for h in history if now_epoch - h["timestamp"].timestamp() <= 3600]
    recent_24h = [h for h in history if now_epoch - h["timestamp"].timestamp() <= 86400]
    recent_7d = [h for h in history if now_epoch - h["timestamp"].timestamp() <= 604800]

    velocity_1h = len(recent_1h)
    velocity_24h = len(recent_24h)
    velocity_7d = len(recent_7d)
    amount_velocity_1h = sum(h["amount"] for h in recent_1h)
    amount_velocity_24h = sum(h["amount"] for h in recent_24h)

    avg_amount = cardholder_stats.get("avg_amount", txn["amount"])
    std_amount = cardholder_stats.get("std_amount", 1.0) or 1.0
    amount_zscore = (txn["amount"] - avg_amount) / std_amount

    time_since_last_txn = 999999.0
    distance_from_last_txn = 0.0
    if history:
        last = max(history, key=lambda h: h["timestamp"])
        time_since_last_txn = now_epoch - last["timestamp"].timestamp()
        if txn.get("latitude") and last.get("latitude"):
            distance_from_last_txn = haversine_km(
                txn["latitude"], txn["longitude"],
                last["latitude"], last["longitude"],
            )

    known_merchants = {h["merchant_id"] for h in history}
    is_new_merchant = int(txn["merchant_id"] not in known_merchants)

    known_countries = {h["location_country"] for h in history}
    is_new_country = int(txn["location_country"] not in known_countries)
    is_high_risk_country = int(txn["location_country"] in HIGH_RISK_COUNTRIES)
    is_high_risk_mcc = int(txn["merchant_category_code"] in HIGH_RISK_MCC)

    is_international = int(txn["location_country"] != "US")
    is_online = int(txn["channel"] == "ONLINE")
    is_atm = int(txn["channel"] == "ATM")

    impossible_travel = 0
    if distance_from_last_txn > 0 and time_since_last_txn > 0:
        speed_kmh = (distance_from_last_txn / time_since_last_txn) * 3600
        impossible_travel = int(speed_kmh > 900)

    return {
        "amount": txn["amount"],
        "hour_of_day": hour,
        "day_of_week": dow,
        "is_night": is_night,
        "is_weekend": is_weekend,
        "velocity_1h": velocity_1h,
        "velocity_24h": velocity_24h,
        "velocity_7d": velocity_7d,
        "amount_velocity_1h": amount_velocity_1h,
        "amount_velocity_24h": amount_velocity_24h,
        "amount_zscore": amount_zscore,
        "time_since_last_txn_seconds": min(time_since_last_txn, 999999),
        "distance_from_last_txn_km": distance_from_last_txn,
        "is_new_merchant": is_new_merchant,
        "is_new_country": is_new_country,
        "is_high_risk_country": is_high_risk_country,
        "is_high_risk_mcc": is_high_risk_mcc,
        "is_international": is_international,
        "is_online": is_online,
        "is_atm": is_atm,
        "impossible_travel": impossible_travel,
    }


FEATURE_NAMES = [
    "amount", "hour_of_day", "day_of_week", "is_night", "is_weekend",
    "velocity_1h", "velocity_24h", "velocity_7d",
    "amount_velocity_1h", "amount_velocity_24h",
    "amount_zscore", "time_since_last_txn_seconds", "distance_from_last_txn_km",
    "is_new_merchant", "is_new_country", "is_high_risk_country",
    "is_high_risk_mcc", "is_international", "is_online", "is_atm",
    "impossible_travel",
]


def features_to_array(features: dict) -> np.ndarray:
    return np.array([[features[f] for f in FEATURE_NAMES]], dtype=np.float32)
