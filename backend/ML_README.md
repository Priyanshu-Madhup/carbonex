# CarbonEx ML Emission Forecasting

## Overview
This module implements a 52-week carbon emission forecasting system using XGBoost machine learning. It predicts future weekly emissions based on historical data, temporal patterns, operational metrics, and categorical features (country, industry sector).

## Features
- **XGBoost Model**: High-performance gradient boosting with 300 estimators
- **Time Series Cross-Validation**: 5-fold TimeSeriesSplit for robust evaluation
- **Feature Engineering**:
  - Cyclical temporal encoding (month_sin/cos, week_sin/cos)
  - Lag features (1, 2, 4 weeks back)
  - Rolling averages (4, 12 weeks)
  - One-hot encoding for categorical features
- **52-Week Predictions**: Forecasts entire year ahead with iterative prediction

## Architecture

### Backend Files
- `train_xgboost_model.py`: Training script and EmissionForecaster class
- `main.py`: FastAPI endpoints for upload, train, and forecast
- `ecosphere_synthetic.csv`: Training dataset (uploaded by user)
- `xgboost_emission_model.pkl`: Trained model artifact

### Frontend Components
- `Dashboard.js`: Main UI for model setup and visualization
- `Dashboard.css`: Styling with gradient cards and charts

## API Endpoints

### 1. Upload Dataset
```http
POST /api/ml/upload-dataset?session_token=<token>
Content-Type: multipart/form-data

Body: file (CSV file)
```
**Response:**
```json
{
  "message": "Dataset uploaded successfully",
  "filepath": "x:/carbon/carbonex/backend/ecosphere_synthetic.csv",
  "filename": "ecosphere_synthetic.csv",
  "size_bytes": 1234567
}
```

### 2. Train Model
```http
POST /api/ml/train-model?session_token=<token>
```
**Response:**
```json
{
  "message": "Model trained successfully",
  "metrics": {
    "mae": 0.1234,
    "rmse": 0.2345,
    "r2": 0.9567,
    "cv_r2_mean": 0.9450,
    "cv_r2_std": 0.0123
  },
  "model_path": "x:/carbon/carbonex/backend/xgboost_emission_model.pkl",
  "training_date": "2025-01-15T10:30:00"
}
```

### 3. Get Forecast
```http
GET /api/ml/forecast/{organization_id}?session_token=<token>
```
**Response:**
```json
{
  "organization_id": "ORG001",
  "forecast_weeks": 52,
  "predictions": [
    {
      "week": 1,
      "date": "2025-01-20",
      "predicted_emissions": 12.3456
    },
    ...
  ],
  "historical": [
    {
      "week": 1,
      "date": "2024-01-15",
      "actual_emissions": 11.9876
    },
    ...
  ],
  "generated_at": "2025-01-15T10:35:00"
}
```

### 4. Get Model Info
```http
GET /api/ml/model-info?session_token=<token>
```
**Response:**
```json
{
  "model_exists": true,
  "dataset_exists": true,
  "training_date": "2025-01-15T10:30:00",
  "num_features": 87,
  "model_type": "XGBoost Regressor",
  "model_path": "x:/carbon/carbonex/backend/xgboost_emission_model.pkl"
}
```

## Usage Instructions

### Step 1: Upload Dataset
1. Go to Dashboard in CarbonEx app
2. Click "Choose CSV Dataset"
3. Select your `ecosphere_synthetic.csv` file
4. Click "Upload Dataset"

**Dataset Requirements:**
- **Format**: CSV with weekly aggregated data
- **Required Columns**:
  - `organization_id`: Unique org identifier
  - `week_start_date` or `date`: Date column
  - `total_emissions_tco2e`: Target variable (emissions in tons CO2e)
  - Operational features: electricity_consumption_kwh, fuel_consumed_liters, etc.
  - Categorical features: country, industry_sector, fuel_type, weather_condition
  - Temporal features: month, week_of_year, quarter, year, season

### Step 2: Train Model
1. Click "Train XGBoost Model"
2. Wait 1-2 minutes for training to complete
3. View training metrics (MAE, RMSE, R²)

**Training Process:**
- Loads dataset and prepares features
- Performs 5-fold time series cross-validation
- Trains XGBoost with 300 estimators
- Saves model to `xgboost_emission_model.pkl`

### Step 3: Generate Forecast
1. Enter your Organization ID (e.g., "ORG001")
2. Click "Generate 52-Week Forecast"
3. View results:
   - Statistics cards (total, average, min, max)
   - 52-week bar chart visualization
   - Detailed predictions table
   - Historical vs predicted comparison

## Model Details

### XGBoost Parameters
```python
{
  'n_estimators': 300,
  'learning_rate': 0.05,
  'max_depth': 6,
  'min_child_weight': 3,
  'subsample': 0.8,
  'colsample_bytree': 0.8,
  'gamma': 0.1,
  'reg_alpha': 0.1,
  'reg_lambda': 1.0,
  'random_state': 42,
  'tree_method': 'hist'
}
```

### Feature Groups
1. **Temporal Features** (9):
   - year, month, week_of_year, quarter, day_of_year
   - month_sin, month_cos, week_sin, week_cos

2. **Operational Features** (13):
   - electricity_consumption_kwh, renewable_energy_kwh
   - fuel_consumed_liters, distance_travelled_km
   - occupancy_rate_percent, product_output_units
   - machine_runtime_hours, equipment_power_rating_kw
   - temperature_celsius, humidity_percent
   - employee_count, spend_amount_inr
   - emission factors (grid, fuel, category)

3. **Lag Features** (5):
   - emissions_lag_1, emissions_lag_2, emissions_lag_4
   - emissions_rolling_4, emissions_rolling_12

4. **Categorical Features** (60+):
   - One-hot encoded: season, facility_type, country, industry_sector, fuel_type, weather_condition

**Total Features**: ~87 features

### Prediction Method
The model uses **iterative forecasting**:
1. Start with last known week's data
2. Predict next week's emissions
3. Update lag features with new prediction
4. Update rolling averages
5. Advance temporal features (week, month, etc.)
6. Repeat for 52 weeks

This approach allows the model to use its own predictions as inputs for future predictions, creating a realistic forecast sequence.

## Performance Metrics

Expected performance on synthetic data:
- **MAE** (Mean Absolute Error): 0.10-0.20 tCO₂e
- **RMSE** (Root Mean Squared Error): 0.15-0.30 tCO₂e
- **R²** (Coefficient of Determination): 0.92-0.98
- **CV R²** (Cross-Validation R²): 0.90-0.96

## Troubleshooting

### Issue: "Dataset not found"
**Solution**: Upload CSV dataset first before training

### Issue: "Model not found"
**Solution**: Train model before generating forecast

### Issue: "No data found for organization_id"
**Solution**: Ensure organization ID exists in uploaded dataset

### Issue: Training takes too long
**Solution**: Reduce `n_estimators` to 100 in `train_xgboost_model.py`

### Issue: Predictions are negative
**Solution**: Model automatically clips negative predictions to 0

## Files Modified

### Backend
- ✅ `train_xgboost_model.py` - Complete rewrite aligned with CSV structure
- ✅ `main.py` - Added 4 ML endpoints
- ✅ `requirements.txt` - Added xgboost, scikit-learn, pandas, numpy, joblib

### Frontend
- ✅ `src/components/Dashboard.js` - New component (400+ lines)
- ✅ `src/components/Dashboard.css` - Full styling (700+ lines)
- ✅ `src/App.js` - Integrated Dashboard route

## Next Steps

1. **Enhanced Visualization**: Integrate Chart.js or Recharts for interactive charts
2. **Model Comparison**: Add multiple models (RandomForest, LSTM, Prophet)
3. **Confidence Intervals**: Display prediction uncertainty ranges
4. **Feature Importance**: Show which factors drive emissions most
5. **Scenario Testing**: Allow users to modify inputs and see impact
6. **Export Results**: Download predictions as CSV/PDF report
7. **Real-time Predictions**: Auto-retrain model on new data

## Dependencies

```txt
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
```

## Technical Notes

- **Model Size**: ~2-5 MB (depends on num_estimators and max_depth)
- **Training Time**: 30-120 seconds (depends on dataset size and CPU)
- **Prediction Time**: <1 second for 52 weeks
- **Memory Usage**: ~100-500 MB during training
- **Dataset Size**: Supports 1K-1M rows efficiently

## Credits

Implementation based on `training.py` reference with enhancements:
- Time series forecasting with iterative predictions
- Enhanced feature engineering with cyclical encoding
- Robust error handling and validation
- RESTful API integration
- Interactive dashboard UI

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Author**: CarbonEx Team
