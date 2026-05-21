import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from app.ml.baseline import calculate_baseline_price


def evaluate_model_vs_baseline(df: pd.DataFrame, pipeline, kfold: KFold):
    """Head-to-head comparison: XGBoost vs deterministic baseline."""
    from app.ml.feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN

    X = df[FEATURE_COLUMNS].values
    y = df[TARGET_COLUMN].values

    ml_predictions = np.zeros(len(y))
    baseline_predictions = np.zeros(len(y))

    for train_idx, test_idx in kfold.split(X):
        # ML predictions
        pipeline.fit(X[train_idx], y[train_idx])
        ml_predictions[test_idx] = pipeline.predict(X[test_idx])

        # Baseline predictions for the same test fold
        for idx in test_idx:
            row = df.iloc[idx]
            result = calculate_baseline_price(
                weight_kg=row["weight_kg"],
                distance_km=row["distance_km"],
                vehicle_type=row["vehicle_type"],
                route_risk=int(row["route_risk"]),
                is_weekend=bool(row["is_weekend"]),
                is_festive=bool(row["is_festive_period"]),
                fuel_price_per_litre=row["fuel_price_per_litre"],
            )
            baseline_predictions[idx] = result["total"]

    # Comparison
    ml_rmse = np.sqrt(mean_squared_error(y, ml_predictions))
    ml_mae = mean_absolute_error(y, ml_predictions)
    bl_rmse = np.sqrt(mean_squared_error(y, baseline_predictions))
    bl_mae = mean_absolute_error(y, baseline_predictions)

    print("\n===== MODEL COMPARISON =====")
    print(f"{'Metric':<10} {'XGBoost':<15} {'Baseline':<15} {'ML Wins?'}")
    print(f"{'RMSE':<10} {ml_rmse:<15.2f} {bl_rmse:<15.2f} {'YES' if ml_rmse < bl_rmse else 'NO'}")
    print(f"{'MAE':<10} {ml_mae:<15.2f} {bl_mae:<15.2f} {'YES' if ml_mae < bl_mae else 'NO'}")

    improvement = ((bl_mae - ml_mae) / bl_mae) * 100
    print(f"\nML improves MAE by {improvement:.1f}% over baseline")

    return {
        "ml": {"rmse": ml_rmse, "mae": ml_mae},
        "baseline": {"rmse": bl_rmse, "mae": bl_mae},
    }