"""
Offline feature engineering for model training.
Mirrors the logic in app/core/feature_builder.py so train/serve features are identical.
"""
import math
import numpy as np
import pandas as pd

HIGH_RISK_MCC = {"5912", "7995", "6051", "4829", "6050", "5999", "7273"}
HIGH_RISK_COUNTRIES = {"NG", "RO", "BR", "UA", "PK", "ID"}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["cardholder_id", "timestamp"]).reset_index(drop=True)

    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_night"] = ((df["hour_of_day"] < 6) | (df["hour_of_day"] >= 22)).astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_online"] = (df["channel"] == "ONLINE").astype(int)
    df["is_atm"] = (df["channel"] == "ATM").astype(int)
    df["is_international"] = (df["location_country"] != "IN").astype(int)
    df["is_high_risk_mcc"] = df["merchant_category_code"].isin(HIGH_RISK_MCC).astype(int)
    df["is_high_risk_country"] = df["location_country"].isin(HIGH_RISK_COUNTRIES).astype(int)

    df["epoch"] = df["timestamp"].astype(np.int64) // 10**9

    velocity_features = _compute_velocity_features(df)
    df = pd.concat([df, velocity_features], axis=1)

    cardholder_stats = df.groupby("cardholder_id")["amount"].agg(["mean", "std"]).rename(
        columns={"mean": "ch_avg_amount", "std": "ch_std_amount"}
    ).fillna(1)
    df = df.join(cardholder_stats, on="cardholder_id")
    df["ch_std_amount"] = df["ch_std_amount"].replace(0, 1)
    df["amount_zscore"] = (df["amount"] - df["ch_avg_amount"]) / df["ch_std_amount"]

    df["time_since_last_txn_seconds"] = _time_since_last(df)
    df["distance_from_last_txn_km"] = _distance_from_last(df)
    df["is_new_merchant"] = _is_new_entity(df, "merchant_id")
    df["is_new_country"] = _is_new_entity(df, "location_country")

    df["impossible_travel"] = 0
    mask = (df["distance_from_last_txn_km"] > 0) & (df["time_since_last_txn_seconds"] > 0)
    speed = df.loc[mask, "distance_from_last_txn_km"] / (df.loc[mask, "time_since_last_txn_seconds"] / 3600)
    df.loc[mask, "impossible_travel"] = (speed > 900).astype(int)

    return df


def _compute_velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    windows = {"1h": 3600, "24h": 86400, "7d": 604800}
    results = {f"velocity_{k}": [] for k in windows}
    results["amount_velocity_1h"] = []
    results["amount_velocity_24h"] = []

    for ch_id, group in df.groupby("cardholder_id"):
        epochs = group["epoch"].values
        amounts = group["amount"].values
        for i in range(len(group)):
            e = epochs[i]
            for k, secs in windows.items():
                count = int(np.sum((epochs[:i] >= e - secs) & (epochs[:i] < e)))
                results[f"velocity_{k}"].append(count)
            results["amount_velocity_1h"].append(float(np.sum(amounts[:i][epochs[:i] >= e - 3600])))
            results["amount_velocity_24h"].append(float(np.sum(amounts[:i][epochs[:i] >= e - 86400])))

    return pd.DataFrame(results, index=df.index)


def _time_since_last(df: pd.DataFrame) -> pd.Series:
    result = []
    for _, group in df.groupby("cardholder_id"):
        epochs = group["epoch"].values
        diffs = np.concatenate([[999999], np.diff(epochs)])
        result.extend(np.minimum(diffs, 999999).tolist())
    return pd.Series(result, index=df.index)


def _distance_from_last(df: pd.DataFrame) -> pd.Series:
    result = []
    for _, group in df.groupby("cardholder_id"):
        lats = group["latitude"].values
        lons = group["longitude"].values
        dists = [0.0]
        for i in range(1, len(group)):
            if not (np.isnan(lats[i]) or np.isnan(lats[i-1])):
                dists.append(haversine_km(lats[i-1], lons[i-1], lats[i], lons[i]))
            else:
                dists.append(0.0)
        result.extend(dists)
    return pd.Series(result, index=df.index)


def _is_new_entity(df: pd.DataFrame, col: str) -> pd.Series:
    result = []
    for _, group in df.groupby("cardholder_id"):
        vals = group[col].values
        seen = set()
        flags = []
        for v in vals:
            flags.append(int(v not in seen))
            seen.add(v)
        result.extend(flags)
    return pd.Series(result, index=df.index)


FEATURE_COLS = [
    "amount", "hour_of_day", "day_of_week", "is_night", "is_weekend",
    "velocity_1h", "velocity_24h", "velocity_7d",
    "amount_velocity_1h", "amount_velocity_24h",
    "amount_zscore", "time_since_last_txn_seconds", "distance_from_last_txn_km",
    "is_new_merchant", "is_new_country", "is_high_risk_country",
    "is_high_risk_mcc", "is_international", "is_online", "is_atm",
    "impossible_travel",
]
