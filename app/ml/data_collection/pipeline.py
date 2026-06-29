import pandas as pd
from pathlib import Path
from app.ml.data_collection.scraper import get_published_prices
from app.ml.data_collection.distance_enrichment import get_route_distance


def load_field_survey_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek

    festive_ranges = [
        ("2025-12-15", "2026-01-05"),
        ("2026-03-28", "2026-04-07"),
        ("2026-06-15", "2026-06-20"),
    ]
    df["is_festive_period"] = False
    if "date" in df.columns:
        for start, end in festive_ranges:
            mask = (df["date"] >= start) & (df["date"] <= end)
            df.loc[mask, "is_festive_period"] = True

    df["source"] = "field_survey"
    return df


def enrich_with_distances(df: pd.DataFrame) -> pd.DataFrame:
    routes = df[["origin_park", "destination"]].drop_duplicates()
    distance_cache = {}

    for _, row in routes.iterrows():
        key = (row["origin_park"], row["destination"])
        if key not in distance_cache:
            result = get_route_distance(row["origin_park"], row["destination"])
            if result:
                distance_cache[key] = result

    def safe_distance(row):
        return (
            distance_cache
            .get((row["origin_park"], row["destination"]), {})
            .get("distance_km", 0)
        )

    def safe_duration(row):
        return (
            distance_cache
            .get((row["origin_park"], row["destination"]), {})
            .get("duration_mins", 0)
        )

    df["distance_km"] = df.apply(safe_distance, axis=1)
    df["estimated_duration_mins"] = df.apply(safe_duration, axis=1)

    print(f"Distance enrichment completed → {len(df)} rows")
    return df


def attach_fuel_prices(df: pd.DataFrame, fuel_csv_path: str | None = None) -> pd.DataFrame:
    if fuel_csv_path and Path(fuel_csv_path).exists():
        fuel = pd.read_csv(fuel_csv_path)
        fuel["date"] = pd.to_datetime(fuel["date"])
        df = pd.merge_asof(
            df.sort_values("date"),
            fuel.sort_values("date"),
            on="date",
            direction="backward",
        )
        df["fuel_price_per_litre"] = df["petrol_price"]
    else:
        # Only fill where not already set
        if "fuel_price_per_litre" not in df.columns:
            df["fuel_price_per_litre"] = 700.0
        else:
            df["fuel_price_per_litre"] = df["fuel_price_per_litre"].fillna(700.0)

    return df


def assign_route_risk(df: pd.DataFrame) -> pd.DataFrame:
    risk_map = {
        ("Akure", "Lagos"): 2,
        ("Akure", "Ibadan"): 2,
        ("Akure", "Ondo"): 2,
        ("Akure", "Owo"): 2,
        ("Akure", "Benin"): 2,
        ("Akure", "Ikare"): 3,
        ("Ondo", "Lagos"): 2,
        ("Ondo", "Ore"): 2,
        ("Owo", "Akure"): 2,
        ("Ikare", "Akure"): 3,
        ("Okitipupa", "Akure"): 3,
        ("Akure", "Abuja"): 3,
    }

    def clean_place(x):
        return str(x).replace(" Park", "").split(",")[0].strip()

    def _get_risk(row):
        origin = clean_place(row.get("origin_park", ""))
        dest = clean_place(row.get("destination", ""))
        return risk_map.get((origin, dest), risk_map.get((dest, origin), 2))

    df["route_risk"] = df.apply(_get_risk, axis=1).astype(int)
    return df


# Columns that MUST exist in the final dataset
REQUIRED_COLUMNS = [
    "origin_park",
    "destination",
    "package_size",
    "package_weight",
    "vehicle_type",
    "day_of_week",
    "is_festive_period",
    "fuel_price_per_litre",
    "price",
]


def build_master_dataset(
    field_survey_csv: str,
    fuel_csv: str | None = None,
    output_path: str = "data/waybill_pricing_clean.csv",
) -> pd.DataFrame:

    print("=== Building Master Dataset ===")

    # 1. Load field survey data
    print("Loading field survey data...")
    field_df = load_field_survey_data(field_survey_csv)
    print(f"  Field records: {len(field_df)}")

    # 2. Load published prices
    print("Loading published price benchmarks...")
    published_df = get_published_prices()
    print(f"  Published records: {len(published_df)}")

    # 3. Combine — only keep columns both share
    #    This is what was breaking before
    combined_cols = list(set(field_df.columns) | set(published_df.columns))
    df = pd.concat([field_df, published_df], ignore_index=True)[combined_cols]
    print(f"  Combined: {len(df)} records")

    # 4. Enrich with distances
    print("Enriching with Google Maps distances...")
    df = enrich_with_distances(df)

    # 5. Fuel prices
    print("Attaching fuel prices...")
    df = attach_fuel_prices(df, fuel_csv)

    # 6. Route risk
    print("Assigning route risk levels...")
    df = assign_route_risk(df)

    # 7. Drop rows missing any required column
    df = df.dropna(subset=REQUIRED_COLUMNS)
    df["price"] = pd.to_numeric(
    df["price"].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
        errors="coerce"
    )
    df = df[df["price"] > 0]
    print(f"  Final clean dataset: {len(df)} records")

    # 8. Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"  Saved to {output_path}")

    return df
