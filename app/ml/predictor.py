import joblib
import numpy as np
from pathlib import Path
from app.ml.baseline import calculate_baseline_price
from app.config import get_settings

# Category → number mappings
SIZE_MAP = {
    "envelope":    2_625,
    "small":       30_000,
    "medium":      70_000,
    "large":       175_000,
    "extra_large": 360_000,
}

WEIGHT_MAP = {
    "very_light": 1.0,
    "light":      3.5,
    "medium":     10.0,
    "heavy":      22.0,
    "very_heavy": 40.0,
}


class PricingPredictor:
    def __init__(self):
        settings = get_settings()
        model_path = Path(settings.ML_MODEL_PATH)

        if model_path.exists():
            self.pipeline = joblib.load(model_path)
            self.model_available = True
        else:
            self.pipeline = None
            self.model_available = False

    def predict(
        self,
        package_size: str,
        package_weight: str,
        distance_km: float,
        vehicle_type: str,
        route_risk: int,
        day_of_week: int,
        is_festive_period: bool,
        fuel_price_per_litre: float,
    ) -> dict:
        # Convert categories to numbers
        weight_kg = WEIGHT_MAP[package_weight]
        volume_cm3 = SIZE_MAP[package_size]
        density = weight_kg / (volume_cm3 / 1_000_000)
        is_weekend = day_of_week in (5, 6)
        vehicle_type_encoded = 0 if vehicle_type == "small_car" else 1

        # Baseline always runs — fallback + comparison
        baseline = calculate_baseline_price(
            weight_kg=weight_kg,
            distance_km=distance_km,
            vehicle_type=vehicle_type,
            route_risk=route_risk,
            is_weekend=is_weekend,
            is_festive=is_festive_period,
            fuel_price_per_litre=fuel_price_per_litre,
        )

        if not self.model_available:
            return {
                "predicted_price": baseline["total"],
                "price_breakdown": baseline["breakdown"],
                "confidence_band": {
                    "low": round(baseline["total"] * 0.85, 2),
                    "high": round(baseline["total"] * 1.15, 2),
                },
                "model_used": "baseline",
            }

        features = np.array([[
            weight_kg,
            volume_cm3,
            density,
            distance_km,
            day_of_week,
            int(is_weekend),
            int(is_festive_period),
            fuel_price_per_litre,
            vehicle_type_encoded,
            route_risk,
            weight_kg * distance_km,
            fuel_price_per_litre * distance_km,
        ]])

        predicted = max(float(self.pipeline.predict(features)[0]), 200)

        return {
            "predicted_price": round(predicted, 2),
            "price_breakdown": {
                **baseline["breakdown"],
                "ml_adjustment": round(predicted - baseline["total"], 2),
            },
            "confidence_band": {
                "low": round(predicted * 0.90, 2),
                "high": round(predicted * 1.10, 2),
            },
            "model_used": "xgboost",
        }


pricing_predictor = PricingPredictor()