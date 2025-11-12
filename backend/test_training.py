from train_xgboost_model import EmissionForecaster

print("Testing model training...")
try:
    forecaster = EmissionForecaster()
    metrics = forecaster.train('ecosphere_synthetic.csv')
    print("✅ Training successful!")
    print(f"R2 Score: {metrics['r2']}")
    print(f"MAE: {metrics['mae']}")
    print(f"RMSE: {metrics['rmse']}")
except Exception as e:
    print(f"❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
