# ml/run_pipeline.py
"""
THE ONE SCRIPT YOUR FRIEND RUNS.

Usage:
    python -m app.ml.run_pipeline --survey data/field_survey.csv

This is run ONCE on a laptop after data collection is complete.
It is NOT part of the web server.
"""
import argparse
from app.ml.data_collection.pipeline import build_master_dataset
from app.ml.train import train_and_save


def main():
    parser = argparse.ArgumentParser(description="Build dataset and train pricing model")
    parser.add_argument("--survey", required=True, help="Path to field survey CSV from Google Sheets", default="dummy_waybill_data.csv")
    parser.add_argument("--fuel", default=None, help="Path to fuel prices CSV (optional)")
    parser.add_argument("--output-data", default="app/data/waybill_pricing_clean.csv")
    parser.add_argument("--output-model", default="app/trained_models/pricing_pipeline.joblib")
    args = parser.parse_args()

    # Step 1: Build the master dataset
    # Takes raw survey CSV → enriches with distances, fuel, risk → saves clean CSV
    print("\n========== STEP 1: BUILD DATASET ==========\n")
    df = build_master_dataset(
        field_survey_csv=args.survey,
        fuel_csv=args.fuel,
        output_path=args.output_data,
    )

    print(f"\nDataset ready: {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print(f"Vehicle types: {df['vehicle_type'].value_counts().to_dict()}")
    print(f"Price range: ₦{df['price'].min():.0f} — ₦{df['price'].max():.0f}")

    # Step 2: Train the model
    # Takes clean CSV → feature engineering → XGBoost → compare vs baseline → save .joblib
    print("\n========== STEP 2: TRAIN MODEL ==========\n")
    pipeline = train_and_save(
        data_path=args.output_data,
        output_path=args.output_model,
    )

    print("\n========== DONE ==========")
    print(f"Model saved to: {args.output_model}")
    print("Copy this file to your server's trained_models/ directory before deploying.")


if __name__ == "__main__":
    main()