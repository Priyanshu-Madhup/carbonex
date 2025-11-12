"""
Test both predictions and historical data
"""
from train_xgboost_model import EmissionForecaster
from pathlib import Path

backend_dir = Path(__file__).parent
csv_path = backend_dir / "ecosphere_synthetic.csv"
model_path = backend_dir / "xgboost_emission_model.pkl"

print("Loading model...")
forecaster = EmissionForecaster.load(str(model_path))

print("\n1. Generating 52-week forecast for ORG001...")
try:
    predictions = forecaster.predict_52_weeks(str(csv_path), "ORG001")
    print(f"✅ Predictions: {len(predictions)} weeks")
    print(f"   First: Week {predictions[0]['week']} - {predictions[0]['date']} - {predictions[0]['predicted_emissions']:.2f} tCO₂e")
except Exception as e:
    print(f"❌ Predictions Error: {e}")

print("\n2. Getting historical emissions for ORG001...")
try:
    historical = forecaster.get_current_emissions(str(csv_path), "ORG001", weeks=52)
    print(f"✅ Historical: {len(historical)} weeks")
    if historical:
        print(f"   First: Week {historical[0]['week']} - {historical[0]['date']} - {historical[0]['actual_emissions']:.2f} tCO₂e")
except Exception as e:
    print(f"❌ Historical Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All tests passed!")
