import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, KFold
from xgboost import XGBRegressor

from app.ml.feature_engineering import engineer_features, FEATURE_COLUMNS, TARGET_COLUMN
from app.ml.baseline import calculate_baseline_price
from app.ml.evaluate import evaluate_model_vs_baseline


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,      # L1 — helps with sparse informal data
            reg_lambda=1.0,     # L2
            random_state=42,
        )),
    ])


def train_and_save(data_path: str, output_path: str = "trained_models/pricing_pipeline.joblib"):
    # Load raw data (from cleaned Google Sheets export + scraped data)
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records")

    # Feature engineering
    df = engineer_features(df)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Cross-validation — important since data comes from few motor parks
    pipeline = build_pipeline()
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)

    rmse_scores = cross_val_score(pipeline, X, y, cv=kfold, scoring="neg_root_mean_squared_error")
    mae_scores = cross_val_score(pipeline, X, y, cv=kfold, scoring="neg_mean_absolute_error")

    print(f"CV RMSE: {-rmse_scores.mean():.2f} (+/- {rmse_scores.std():.2f})")
    print(f"CV MAE:  {-mae_scores.mean():.2f} (+/- {mae_scores.std():.2f})")

    # Compare against baseline
    evaluate_model_vs_baseline(df, pipeline, kfold)

    # Final fit on all data
    pipeline.fit(X, y)

    # Save
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output)
    print(f"Pipeline saved to {output}")

    return pipeline


if __name__ == "__main__":
    train_and_save("data/waybill_pricing_clean.csv")