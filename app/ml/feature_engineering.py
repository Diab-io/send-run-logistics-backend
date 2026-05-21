import pandas as pd
import numpy as np


# Mapping human-readable categories to numeric estimates
SIZE_MAP = {
    "envelope":    {"length": 35, "width": 25, "height": 3,  "volume_cm3": 2_625},
    "small":       {"length": 40, "width": 30, "height": 25, "volume_cm3": 30_000},
    "medium":      {"length": 50, "width": 40, "height": 35, "volume_cm3": 70_000},
    "large":       {"length": 70, "width": 50, "height": 50, "volume_cm3": 175_000},
    "extra_large": {"length": 100, "width": 60, "height": 60, "volume_cm3": 360_000},
}

WEIGHT_MAP = {
    "very_light": 1.0,
    "light":      3.5,
    "medium":     10.0,
    "heavy":      22.0,
    "very_heavy": 40.0,
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Map categories to numbers
    df["weight_kg"] = df["package_weight"].map(WEIGHT_MAP)
    df["volume_cm3"] = df["package_size"].map({k: v["volume_cm3"] for k, v in SIZE_MAP.items()})

    # Density
    df["density"] = df["weight_kg"] / (df["volume_cm3"] / 1_000_000)

    # Temporal
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Vehicle encoding
    df["vehicle_type_encoded"] = df["vehicle_type"].map({"small_car": 0, "big_bus": 1})

    # Interaction features
    df["weight_distance"] = df["weight_kg"] * df["distance_km"]
    df["fuel_distance"] = df["fuel_price_per_litre"] * df["distance_km"]

    return df


FEATURE_COLUMNS = [
    "weight_kg",
    "volume_cm3",
    "density",
    "distance_km",
    "day_of_week",
    "is_weekend",
    "is_festive_period",
    "fuel_price_per_litre",
    "vehicle_type_encoded",
    "route_risk",
    "weight_distance",
    "fuel_distance",
]

TARGET_COLUMN = "price"