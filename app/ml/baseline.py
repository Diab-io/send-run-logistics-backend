"""
Rule-based pricing formula — the benchmark the ML model must beat.
Derived from domain knowledge of the waybill system.
"""

def calculate_baseline_price(
    weight_kg: float,
    distance_km: float,
    vehicle_type: str,
    route_risk: int,
    is_weekend: bool,
    is_festive: bool,
    fuel_price_per_litre: float,
) -> dict:
    # Base rates derived from field survey averages
    BASE_RATE = {"small_car": 500, "big_bus": 300}

    # Per-km rate
    DISTANCE_RATE = {"small_car": 15, "big_bus": 10}

    # Per-kg rate above a 5kg threshold
    WEIGHT_THRESHOLD = 5.0
    WEIGHT_RATE = {"small_car": 100, "big_bus": 50}

    # Fuel multiplier: normalised against a reference price
    REFERENCE_FUEL_PRICE = 700  # Naira per litre baseline
    fuel_multiplier = fuel_price_per_litre / REFERENCE_FUEL_PRICE

    base = BASE_RATE[vehicle_type]
    distance_cost = distance_km * DISTANCE_RATE[vehicle_type]
    weight_cost = max(0, weight_kg - WEIGHT_THRESHOLD) * WEIGHT_RATE[vehicle_type]

    subtotal = (base + distance_cost + weight_cost) * fuel_multiplier

    # Risk surcharge: 0% for level 1, up to 30% for level 5
    risk_surcharge = subtotal * ((route_risk - 1) * 0.075)

    # Demand surcharge
    demand_surcharge = 0
    if is_festive:
        demand_surcharge = subtotal * 0.20
    elif is_weekend:
        demand_surcharge = subtotal * 0.10

    total = subtotal + risk_surcharge + demand_surcharge

    return {
        "total": round(total, 2),
        "breakdown": {
            "base_fare": base,
            "distance_cost": round(distance_cost, 2),
            "weight_cost": round(weight_cost, 2),
            "fuel_multiplier": round(fuel_multiplier, 4),
            "risk_surcharge": round(risk_surcharge, 2),
            "demand_surcharge": round(demand_surcharge, 2),
        },
    }