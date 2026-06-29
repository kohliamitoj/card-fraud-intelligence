"""
Generates a realistic synthetic card transaction dataset with ~2% fraud rate.
Run: python -m training.generate_synthetic_data
Output: data/transactions.csv
"""
import uuid
import random
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

N_CARDHOLDERS = 500
N_TRANSACTIONS = 50_000
FRAUD_RATE = 0.02

MCC_CODES = {
    "5411": "Groceries", "5812": "Dining", "5541": "Fuel",
    "4111": "Transport", "7011": "Hotels", "5912": "Pharmacy",
    "7995": "Gambling", "6051": "Crypto/Wire", "4829": "Money Transfer",
    "5999": "Misc Retail", "5045": "Electronics", "5311": "Department Store",
    "5621": "Clothing", "4814": "Telecom", "5734": "Computer Supplies",
}
HIGH_RISK_MCC = {"7995", "6051", "4829", "5912", "5999"}
CHANNELS = ["POS", "ONLINE", "ATM", "CONTACTLESS"]
CARD_TYPES = ["VISA", "MASTERCARD", "AMEX", "RUPAY"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune", "Kolkata", "Ahmedabad"]
CITY_COORDS = {
    "Mumbai": (19.076, 72.877), "Delhi": (28.613, 77.209),
    "Bangalore": (12.971, 77.594), "Hyderabad": (17.385, 78.486),
    "Chennai": (13.083, 80.270), "Pune": (18.520, 73.856),
    "Kolkata": (22.572, 88.363), "Ahmedabad": (23.022, 72.571),
}
MERCHANTS = [f"MERCHANT_{i:04d}" for i in range(300)]
MERCHANT_NAMES = [f"Merchant {random.choice(list(MCC_CODES.values()))} {i}" for i in range(300)]


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def generate_cardholders():
    cardholders = {}
    for i in range(N_CARDHOLDERS):
        city = random.choice(CITIES)
        lat, lon = CITY_COORDS[city]
        cardholders[f"CH_{i:04d}"] = {
            "home_city": city,
            "home_lat": lat + random.gauss(0, 0.05),
            "home_lon": lon + random.gauss(0, 0.05),
            "avg_amount": random.uniform(500, 8000),
            "card_type": random.choice(CARD_TYPES),
        }
    return cardholders


def generate_legitimate_transaction(cardholder_id, ch, timestamp, prev_txn):
    mcc = random.choice(list(MCC_CODES.keys()))
    merchant_idx = random.randint(0, len(MERCHANTS)-1)
    city = ch["home_city"] if random.random() < 0.85 else random.choice(CITIES)
    lat, lon = CITY_COORDS[city]
    lat += random.gauss(0, 0.03)
    lon += random.gauss(0, 0.03)
    amount = abs(random.gauss(ch["avg_amount"], ch["avg_amount"] * 0.4))
    amount = max(10, min(amount, ch["avg_amount"] * 3))

    return {
        "transaction_id": str(uuid.uuid4()),
        "cardholder_id": cardholder_id,
        "card_last4": f"{random.randint(1000, 9999)}",
        "card_type": ch["card_type"],
        "amount": round(amount, 2),
        "currency": "USD",
        "merchant_id": MERCHANTS[merchant_idx],
        "merchant_name": MERCHANT_NAMES[merchant_idx],
        "merchant_category_code": mcc,
        "channel": random.choices(CHANNELS, weights=[40, 35, 15, 10])[0],
        "location_city": city,
        "location_country": "IN",
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "timestamp": timestamp,
        "is_fraud": 0,
    }


def generate_fraud_transaction(cardholder_id, ch, timestamp, prev_txn):
    fraud_type = random.choice(["card_not_present", "card_present", "account_takeover", "velocity"])

    if fraud_type == "card_not_present":
        mcc = random.choice(list(HIGH_RISK_MCC))
        city = random.choice(CITIES)
        amount = random.uniform(ch["avg_amount"] * 2, ch["avg_amount"] * 8)
        channel = "ONLINE"
    elif fraud_type == "card_present":
        mcc = random.choice(["5045", "5311", "7011"])
        city = random.choice([c for c in CITIES if c != ch["home_city"]])
        amount = random.uniform(ch["avg_amount"] * 1.5, ch["avg_amount"] * 5)
        channel = "POS"
    elif fraud_type == "account_takeover":
        mcc = random.choice(["4829", "6051"])
        city = random.choice(CITIES)
        amount = random.uniform(ch["avg_amount"] * 3, ch["avg_amount"] * 10)
        channel = random.choice(["ONLINE", "ATM"])
    else:
        mcc = random.choice(list(MCC_CODES.keys()))
        city = ch["home_city"]
        amount = random.uniform(ch["avg_amount"] * 0.5, ch["avg_amount"] * 2)
        channel = random.choice(CHANNELS)

    lat, lon = CITY_COORDS[city]
    lat += random.gauss(0, 0.05)
    lon += random.gauss(0, 0.05)
    merchant_idx = random.randint(0, len(MERCHANTS)-1)

    return {
        "transaction_id": str(uuid.uuid4()),
        "cardholder_id": cardholder_id,
        "card_last4": f"{random.randint(1000, 9999)}",
        "card_type": ch["card_type"],
        "amount": round(amount, 2),
        "currency": "USD",
        "merchant_id": f"FRAUD_MERCHANT_{random.randint(0, 50):03d}",
        "merchant_name": MERCHANT_NAMES[merchant_idx],
        "merchant_category_code": mcc,
        "channel": channel,
        "location_city": city,
        "location_country": "IN" if random.random() < 0.7 else random.choice(["US", "NG", "RO", "BR"]),
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "timestamp": timestamp,
        "is_fraud": 1,
    }


def generate_dataset():
    cardholders = generate_cardholders()
    cardholder_ids = list(cardholders.keys())

    start_date = datetime.now() - timedelta(days=180)
    records = []
    cardholder_last_txn = {ch_id: None for ch_id in cardholder_ids}

    n_fraud = int(N_TRANSACTIONS * FRAUD_RATE)
    fraud_indices = set(random.sample(range(N_TRANSACTIONS), n_fraud))

    for i in range(N_TRANSACTIONS):
        cardholder_id = random.choice(cardholder_ids)
        ch = cardholders[cardholder_id]
        offset_seconds = random.randint(0, 180 * 24 * 3600)
        timestamp = start_date + timedelta(seconds=offset_seconds)
        prev_txn = cardholder_last_txn[cardholder_id]

        if i in fraud_indices:
            txn = generate_fraud_transaction(cardholder_id, ch, timestamp, prev_txn)
        else:
            txn = generate_legitimate_transaction(cardholder_id, ch, timestamp, prev_txn)

        cardholder_last_txn[cardholder_id] = txn
        records.append(txn)

    df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
    print(f"Generated {len(df)} transactions | Fraud: {df['is_fraud'].sum()} ({df['is_fraud'].mean():.1%})")
    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("data/transactions.csv", index=False)
    print("Saved to data/transactions.csv")
