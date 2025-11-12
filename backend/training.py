# Regenerate synthetic dataset (1000 rows) and train a GradientBoostingRegressor model.
# This script creates the dataset, saves it, performs training with cross-validation, and saves the model.
import random as rnd
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os
import logging
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
import joblib
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=FutureWarning)


# Small helper to show DataFrames in environments without `ace_tools` (CLI friendly).
def display_dataframe_to_user(title, df, max_rows=10):
    """Print a DataFrame to the console with an optional title.

    Tries to use `tabulate` for nicer formatting if available, otherwise falls back to
    pandas' `to_string`. Shows only the first `max_rows` rows for brevity.
    """
    print(f"\n=== {title} ===")
    try:
        from tabulate import tabulate
        print(tabulate(df.head(max_rows), headers="keys",
              tablefmt="psql", showindex=False))
    except Exception:
        # Fallback to pandas repr
        print(df.head(max_rows).to_string(index=False))
    print(f"(shape: {df.shape})\n")


np.random.seed(42)
random.seed(42)

n = 1000
org_ids = ['ORG001']
facilities = ['Pune HQ', 'Mumbai Plant', 'Delhi Office',
              'Bengaluru Lab', 'Hyderabad Warehouse']
locations = ['Pune, IN', 'Mumbai, IN',
             'Delhi, IN', 'Bengaluru, IN', 'Hyderabad, IN']
fuel_types = ['Diesel', 'LPG', 'Natural Gas', 'Petrol', 'CNG']
fuel_ef_map = {'Diesel': 2.68, 'LPG': 1.51,
               'Natural Gas': 2.06, 'Petrol': 2.31, 'CNG': 2.75}
suppliers = ['ABC Plastics', 'GreenSteel Co',
             'LogiTrans', 'PackWise', 'ElectroParts']
purchase_categories = ['Raw material', 'Logistics',
                       'Packaging', 'Electronics', 'Services']
category_ef = {'Raw material': 0.0008, 'Logistics': 0.0012,
               'Packaging': 0.0006, 'Electronics': 0.0015, 'Services': 0.0004}
vehicle_ids = [f'VEH{str(i).zfill(3)}' for i in range(1, 21)]

start = datetime(2024, 1, 1)
end = datetime(2024, 12, 31)
days = (end - start).days + 1
dates = [start + timedelta(days=int(x))
         for x in np.random.randint(0, days, size=n)]

rows = []
for i in range(n):
    facility_idx = np.random.randint(0, len(facilities))
    facility = facilities[facility_idx]
    loc = locations[facility_idx]
    date = dates[i]
    org = org_ids[0]
    base_elec = {'Pune HQ': 2000, 'Mumbai Plant': 8000, 'Delhi Office': 1500,
                 'Bengaluru Lab': 3500, 'Hyderabad Warehouse': 2500}
    elec_kwh = max(0, np.random.normal(
        loc=base_elec[facility], scale=base_elec[facility]*0.25))
    renewable_kwh = round(elec_kwh * np.random.beta(1.5, 6.0), 2)
    grid_ef = round(np.random.normal(0.82, 0.05), 3)
    elec_cost = round(elec_kwh * np.random.normal(9.5, 1.2), 2)
    fuel_type = np.random.choice(fuel_types, p=[0.4, 0.1, 0.15, 0.25, 0.1])
    if np.random.rand() < 0.55:
        fuel_consumed = round(abs(np.random.normal(
            loc=50 if facility == 'Mumbai Plant' else 20, scale=25)), 2)
    else:
        fuel_consumed = 0.0
    fuel_ef = fuel_ef_map[fuel_type]
    generator_hours = round(np.random.exponential(
        scale=2.0), 2) if fuel_consumed > 0 else 0.0
    if np.random.rand() < 0.3:
        vehicle = random.choice(vehicle_ids)
        distance_km = round(abs(np.random.normal(loc=120, scale=80)), 2)
        vehicle_fuel = round(
            distance_km / np.random.normal(loc=10.0, scale=1.5), 2)
    else:
        vehicle = None
        distance_km = 0.0
        vehicle_fuel = 0.0
    occupancy_rate = round(np.random.uniform(30, 95), 1)
    if facility in ['Mumbai Plant', 'Bengaluru Lab']:
        product_output = max(1, int(np.random.normal(
            loc=15000 if facility == 'Mumbai Plant' else 6000, scale=3000)))
    else:
        product_output = int(np.random.normal(loc=800, scale=400))
    product_output = max(0, product_output)
    machine_runtime_hours = round(np.random.uniform(0, 24), 2)
    equipment_power_kw = round(
        np.random.choice([15, 45, 75, 100, 5, 25, 60]), 1)
    temp = round(np.random.normal(28, 6), 1)
    humidity = round(np.random.uniform(25, 85), 1)
    weather = np.random.choice(['Sunny', 'Cloudy', 'Rainy', 'Humid', 'Windy'], p=[
                               0.45, 0.2, 0.15, 0.15, 0.05])
    occupancy_count = int(max(0, round(
        product_output / np.random.uniform(20, 200), 0) + np.random.randint(1, 50)))
    working_hours = round(np.random.choice(
        [8, 9, 10, 12], p=[0.4, 0.3, 0.2, 0.1]), 2)
    supplier = random.choice(suppliers)
    category = random.choice(purchase_categories)
    spend = round(abs(np.random.normal(loc=50000 if category ==
                  'Raw material' else 15000, scale=30000)), 2)
    cat_ef = category_ef[category]
    scope2_t = round((elec_kwh - renewable_kwh) * grid_ef / 1000, 4)
    scope1_t = round(fuel_consumed * fuel_ef / 1000, 4)
    scope1_vehicle_t = round(
        vehicle_fuel * fuel_ef_map.get('Diesel', 2.68) / 1000, 4) if vehicle_fuel > 0 else 0.0
    scope3_t = round(spend * cat_ef / 1000, 4)
    total_t = round(scope1_t + scope2_t + scope3_t + scope1_vehicle_t, 4)
    emission_intensity = round(
        total_t / product_output, 6) if product_output > 0 else 0.0
    if np.random.rand() < 0.25:
        rec_id = f'REC_{i:04d}'
        action_type = np.random.choice(
            ['Retrofit', 'Policy', 'Supplier change', 'Optimize HVAC', 'Route optimization'])
        expected_reduction = round(total_t * np.random.uniform(0.05, 0.35), 4)
        implementation_cost = round(
            abs(np.random.normal(loc=50000, scale=40000)), 2)
        roi_months = int(np.clip(np.random.normal(12, 8), 1, 60))
        priority = np.random.choice(
            ['High', 'Medium', 'Low'], p=[0.5, 0.35, 0.15])
    else:
        rec_id = None
        action_type = None
        expected_reduction = 0.0
        implementation_cost = 0.0
        roi_months = None
        priority = None
    predicted_next_month = round(total_t * np.random.uniform(0.95, 1.15), 4)
    row = {
        'organization_id': org,
        'facility_name': facility,
        'location': loc,
        'date': date.date().isoformat(),
        'electricity_consumption_kwh': round(elec_kwh, 2),
        'renewable_energy_kwh': renewable_kwh,
        'grid_emission_factor_kgco2_per_kwh': grid_ef,
        'electricity_cost_inr': elec_cost,
        'fuel_type': fuel_type,
        'fuel_consumed_liters': fuel_consumed,
        'fuel_emission_factor_kgco2_per_liter': fuel_ef,
        'generator_runtime_hours': generator_hours,
        'vehicle_id': vehicle,
        'distance_travelled_km': distance_km,
        'vehicle_fuel_consumed_liters': vehicle_fuel,
        'occupancy_rate_percent': occupancy_rate,
        'product_output_units': product_output,
        'machine_runtime_hours': machine_runtime_hours,
        'equipment_power_rating_kw': equipment_power_kw,
        'temperature_celsius': temp,
        'humidity_percent': humidity,
        'weather_condition': weather,
        'occupancy_count': occupancy_count,
        'working_hours_per_day': working_hours,
        'supplier_name': supplier,
        'purchase_category': category,
        'spend_amount_inr': round(spend, 2),
        'category_emission_factor_kgco2_per_inr': cat_ef,
        'scope_1_emissions_tco2e': scope1_t + scope1_vehicle_t,
        'scope_2_emissions_tco2e': scope2_t,
        'scope_3_emissions_tco2e': scope3_t,
        'total_emissions_tco2e': total_t,
        'emission_intensity_tco2e_per_unit': emission_intensity,
        'recommendation_id': rec_id,
        'action_type': action_type,
        'expected_reduction_tco2e': expected_reduction,
        'implementation_cost_inr': implementation_cost,
        'roi_months': roi_months,
        'priority_level': priority,
        'predicted_emission_next_month_tco2e': predicted_next_month
    }
    rows.append(row)

df = pd.DataFrame(rows)

# Save CSV to backend/ folder (same directory as this script)
output_dir = os.path.dirname(os.path.abspath(__file__))
out_csv = os.path.join(output_dir, 'ecosphere_synthetic.csv')

try:
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved synthetic dataset to: {out_csv}")
except Exception as e:
    logger.error(f"Failed to save CSV: {e}")
    raise

# ====================
# ENHANCED TRAINING PIPELINE
# ====================

logger.info("Starting enhanced training pipeline...")

# Define features and target
features = [
    "electricity_consumption_kwh",
    "renewable_energy_kwh",
    "fuel_consumed_liters",
    "distance_travelled_km",
    "spend_amount_inr",
    "temperature_celsius",
    "humidity_percent",
    "occupancy_rate_percent",
    "product_output_units",
    "machine_runtime_hours",
    "equipment_power_rating_kw"
]
target = "total_emissions_tco2e"

# Data cleaning and validation
df = df[df[target].notna()].copy()
df.sort_values('date', inplace=True)
df.reset_index(drop=True, inplace=True)

# Ensure all features exist
for col in features:
    if col not in df.columns:
        df[col] = 0.0
        logger.warning(f"Feature '{col}' not found, filled with 0.0")

logger.info(f"Dataset shape: {df.shape}, Features: {len(features)}")

# Extract features and target
X = df[features].copy()
y = df[target].copy().values

# Preprocessing pipeline with error handling
try:
    imputer = SimpleImputer(strategy='median')
    X_imputed = imputer.fit_transform(X)
    logger.info("Data imputation completed")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)
    logger.info("Feature scaling completed")
except Exception as e:
    logger.error(f"Preprocessing failed: {e}")
    raise

# Temporal train/test split (respects time ordering)
split_idx = int(len(df) * 0.8)
X_train = X_scaled[:split_idx]
X_test = X_scaled[split_idx:]
y_train = y[:split_idx]
y_test = y[split_idx:]

logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

# ====================
# MODEL COMPARISON
# ====================

logger.info("Training multiple models for comparison...")

models = {
    'GradientBoosting': GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        random_state=42,
        verbose=0
    ),
    'RandomForest': RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        verbose=0
    ),
    'Ridge': Ridge(
        alpha=1.0,
        random_state=42
    )
}

# Cross-validation with TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
cv_results = {}

for name, model in models.items():
    try:
        # Time series cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=tscv,
            scoring='r2',
            n_jobs=-1
        )
        cv_results[name] = {
            'mean_r2': cv_scores.mean(),
            'std_r2': cv_scores.std()
        }
        logger.info(
            f"{name} - CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    except Exception as e:
        logger.error(f"Cross-validation failed for {name}: {e}")

# Select best model based on CV
best_model_name = max(cv_results, key=lambda k: cv_results[k]['mean_r2'])
best_model = models[best_model_name]
logger.info(f"Best model selected: {best_model_name}")

# Train best model on full training set
try:
    best_model.fit(X_train, y_train)
    logger.info(f"{best_model_name} training completed")
except Exception as e:
    logger.error(f"Model training failed: {e}")
    raise

# ====================
# MODEL EVALUATION
# ====================

y_pred = best_model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

# Calculate percentage errors
mape = np.mean(np.abs((y_test - y_pred) / np.clip(y_test, 1e-10, None))) * 100

logger.info(
    f"Test Results - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}, MAPE: {mape:.2f}%")

# Prediction intervals (approximate using residuals)
residuals = y_test - y_pred
residual_std = np.std(residuals)
pred_interval_95 = 1.96 * residual_std

# ====================
# SAVE MODEL & ARTIFACTS
# ====================

try:
    out_model_path = os.path.join(output_dir, 'emission_forecast_model.pkl')
    os.makedirs(os.path.dirname(out_model_path) or '.', exist_ok=True)

    model_artifact = {
        'model': best_model,
        'model_name': best_model_name,
        'scaler': scaler,
        'imputer': imputer,
        'features': features,
        'cv_results': cv_results,
        'test_metrics': {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        },
        'pred_interval_95': pred_interval_95,
        'training_date': datetime.now().isoformat()
    }

    joblib.dump(model_artifact, out_model_path)
    logger.info(f"Model saved to: {out_model_path}")
except Exception as e:
    logger.error(f"Failed to save model: {e}")
    raise

# ====================
# DISPLAY RESULTS
# ====================

# Compare all models
comparison_df = pd.DataFrame([
    {
        'model': name,
        'CV_R2_mean': cv_results[name]['mean_r2'],
        'CV_R2_std': cv_results[name]['std_r2']
    }
    for name in cv_results.keys()
])
display_dataframe_to_user("Model Comparison (Cross-Validation)", comparison_df)

# Best model metrics
metrics_df = pd.DataFrame([{
    'model': best_model_name,
    'MAE': round(mae, 4),
    'RMSE': round(rmse, 4),
    'R2': round(r2, 6),
    'MAPE_%': round(mape, 2),
    'Pred_Interval_95%': f"±{pred_interval_95:.4f}"
}])
display_dataframe_to_user("Test Set Evaluation", metrics_df)

# Sample predictions with confidence intervals
sample_idx = rnd.sample(range(len(y_test)), k=min(10, len(y_test)))
sample_df = df.iloc[split_idx:].iloc[sample_idx][[
    'date', 'facility_name']].copy().reset_index(drop=True)
sample_df['actual_tco2e'] = y_test[sample_idx]
sample_df['predicted_tco2e'] = np.round(y_pred[sample_idx], 4)
sample_df['error'] = np.round(y_test[sample_idx] - y_pred[sample_idx], 4)
sample_df['error_%'] = np.round(
    100 * sample_df['error'] / np.clip(sample_df['actual_tco2e'], 1e-10, None), 2)
display_dataframe_to_user("Sample Predictions with Errors", sample_df)

# ====================
# VISUALIZATION
# ====================

try:
    # Plot 1: Actual vs Predicted with confidence interval
    plt.figure(figsize=(12, 5))
    plt.plot(y_test, label='Actual', alpha=0.7, linewidth=2)
    plt.plot(y_pred, label='Predicted', alpha=0.7, linewidth=2)
    plt.fill_between(
        range(len(y_pred)),
        y_pred - pred_interval_95,
        y_pred + pred_interval_95,
        alpha=0.2,
        label='95% Prediction Interval'
    )
    plt.title(f'Actual vs Predicted - {best_model_name} (R²={r2:.4f})')
    plt.xlabel('Test sample index')
    plt.ylabel('Total emissions (tCO2e)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt_path1 = os.path.join(output_dir, 'actual_vs_predicted.png')
    plt.savefig(plt_path1, dpi=150)
    plt.close()
    logger.info(f"Saved plot: {plt_path1}")

    # Plot 2: Feature importance (if available)
    if hasattr(best_model, 'feature_importances_'):
        imp = best_model.feature_importances_
        imp_norm = imp / imp.sum() if imp.sum() > 0 else imp

        plt.figure(figsize=(10, 6))
        indices = np.argsort(imp_norm)[::-1]
        colors = plt.cm.viridis(np.linspace(0, 1, len(features)))
        plt.bar(range(len(features)), imp_norm[indices], color=colors)
        plt.xticks(range(len(features)), [features[i] for i in indices],
                   rotation=45, ha='right')
        plt.title(f'Feature Importance - {best_model_name}')
        plt.ylabel('Normalized Importance')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt_path2 = os.path.join(output_dir, 'feature_importance.png')
        plt.savefig(plt_path2, dpi=150)
        plt.close()
        logger.info(f"Saved plot: {plt_path2}")
    else:
        logger.warning(f"{best_model_name} does not have feature_importances_")
        plt_path2 = None

    # Plot 3: Residuals distribution
    plt.figure(figsize=(10, 5))
    plt.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(0, color='red', linestyle='--',
                linewidth=2, label='Zero error')
    plt.title('Residuals Distribution')
    plt.xlabel('Residual (Actual - Predicted)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt_path3 = os.path.join(output_dir, 'residuals_distribution.png')
    plt.savefig(plt_path3, dpi=150)
    plt.close()
    logger.info(f"Saved plot: {plt_path3}")

except Exception as e:
    logger.error(f"Visualization failed: {e}")

# ====================
# SUMMARY
# ====================

print(f"\n{'='*60}")
print(f"{'TRAINING COMPLETE':^60}")
print(f"{'='*60}")
print(f"Saved synthetic CSV to: {out_csv}")
print(f"Model saved to: {out_model_path}")
print(f"Actual vs Predicted plot: {plt_path1}")
if plt_path2:
    print(f"Feature importance plot: {plt_path2}")
print(f"Residuals distribution plot: {plt_path3}")
print(f"{'='*60}\n")
