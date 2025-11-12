"""
XGBoost Carbon Emission Forecasting Model
Predicts 52 weeks of future emissions for organizations
Uses the ecosphere_synthetic.csv format with weekly data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmissionForecaster:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy='median')
        self.feature_columns = []
        self.org_stats = {}  # Store organization statistics
        
    def prepare_features(self, df, is_training=True):
        """Prepare features for training/prediction"""
        df = df.copy()
        
        # Use existing date column or convert week_start_date
        if 'date' not in df.columns and 'week_start_date' in df.columns:
            df['date'] = pd.to_datetime(df['week_start_date'], format='%d-%m-%Y', dayfirst=True)
        else:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', dayfirst=True)
        
        # Sort by organization and date
        df = df.sort_values(['organization_id', 'date'])
        
        # Temporal features (already present but recalculate to ensure consistency)
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['quarter'] = df['date'].dt.quarter
        df['day_of_year'] = df['date'].dt.dayofyear
        
        # Cyclical encoding for temporal features
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['week_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
        df['week_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
        
        # One-hot encode categorical features
        categorical_cols = ['season', 'facility_type', 'country', 'industry_sector', 'fuel_type', 'weather_condition']
        for col in categorical_cols:
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                df = pd.concat([df, dummies], axis=1)
        
        # Lag features for time series
        if 'total_emissions_tco2e' in df.columns and is_training:
            for org_id in df['organization_id'].unique():
                org_mask = df['organization_id'] == org_id
                # Previous weeks emissions
                df.loc[org_mask, 'emissions_lag_1'] = df.loc[org_mask, 'total_emissions_tco2e'].shift(1)
                df.loc[org_mask, 'emissions_lag_2'] = df.loc[org_mask, 'total_emissions_tco2e'].shift(2)
                df.loc[org_mask, 'emissions_lag_4'] = df.loc[org_mask, 'total_emissions_tco2e'].shift(4)
                # Rolling averages
                df.loc[org_mask, 'emissions_rolling_4'] = df.loc[org_mask, 'total_emissions_tco2e'].rolling(4, min_periods=1).mean()
                df.loc[org_mask, 'emissions_rolling_12'] = df.loc[org_mask, 'total_emissions_tco2e'].rolling(12, min_periods=1).mean()
        
        return df
    
    def train(self, csv_path, target_col='total_emissions_tco2e'):
        """Train XGBoost model on the dataset"""
        logger.info(f"Loading dataset from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        logger.info("Preparing features...")
        df = self.prepare_features(df, is_training=True)
        
        # Define feature columns
        base_features = [
            'year', 'month', 'week_of_year', 'quarter', 'day_of_year',
            'month_sin', 'month_cos', 'week_sin', 'week_cos',
            'electricity_consumption_kwh', 'renewable_energy_kwh',
            'fuel_consumed_liters', 'distance_travelled_km',
            'occupancy_rate_percent', 'product_output_units',
            'machine_runtime_hours', 'equipment_power_rating_kw',
            'temperature_celsius', 'humidity_percent',
            'employee_count', 'spend_amount_inr',
            'grid_emission_factor_kgco2_per_kwh',
            'fuel_emission_factor_kgco2_per_liter',
            'category_emission_factor_kgco2_per_inr',
            'emissions_lag_1', 'emissions_lag_2', 'emissions_lag_4',
            'emissions_rolling_4', 'emissions_rolling_12'
        ]
        
        # Add one-hot encoded features
        categorical_dummies = [col for col in df.columns if any(
            col.startswith(prefix) for prefix in [
                'season_', 'facility_type_', 'country_', 
                'industry_sector_', 'fuel_type_', 'weather_condition_'
            ]
        )]
        
        self.feature_columns = [col for col in base_features + categorical_dummies if col in df.columns]
        
        logger.info(f"Using {len(self.feature_columns)} features")
        
        # Remove rows with NaN target
        df_clean = df.dropna(subset=[target_col])
        
        # Store organization statistics for prediction
        for org_id in df_clean['organization_id'].unique():
            org_data = df_clean[df_clean['organization_id'] == org_id]
            self.org_stats[org_id] = {
                'mean_emissions': org_data[target_col].mean(),
                'std_emissions': org_data[target_col].std(),
                'last_date': org_data['date'].max(),
                'feature_means': org_data[self.feature_columns].mean().to_dict()
            }
        
        logger.info(f"Training with {len(df_clean)} samples")
        
        X = df_clean[self.feature_columns]
        y = df_clean[target_col]
        
        # Handle missing values
        X_imputed = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imputed)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # XGBoost with optimal parameters
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            tree_method='hist',
            objective='reg:squarederror'
        )
        
        # Cross-validation
        logger.info("Performing cross-validation...")
        cv_scores = cross_val_score(
            self.model, X_scaled, y,
            cv=tscv, scoring='r2', n_jobs=-1
        )
        logger.info(f"CV R² scores: {cv_scores}")
        logger.info(f"Mean CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        # Train on full dataset
        logger.info("Training on full dataset...")
        self.model.fit(X_scaled, y)
        
        # Evaluate
        y_pred = self.model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        r2 = r2_score(y, y_pred)
        
        metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'cv_r2_mean': float(cv_scores.mean()),
            'cv_r2_std': float(cv_scores.std())
        }
        
        logger.info(f"Training Metrics - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
        
        return metrics
    
    def predict_52_weeks(self, csv_path, organization_id):
        """Predict next 52 weeks of emissions for an organization"""
        logger.info(f"Loading dataset for prediction...")
        df = pd.read_csv(csv_path)
        
        # Filter for specific organization
        org_data = df[df['organization_id'] == organization_id].copy()
        
        if len(org_data) == 0:
            raise ValueError(f"No data found for organization_id: {organization_id}")
        
        # Prepare features (need training=True to get lag features from historical data)
        org_data = self.prepare_features(org_data, is_training=True)
        org_data = org_data.sort_values('date')
        
        # Get last known date and data
        last_date = org_data['date'].max()
        last_row = org_data.iloc[-1:].copy()
        
        # Get recent emissions for lag feature updates
        if 'total_emissions_tco2e' in org_data.columns:
            recent_emissions = org_data['total_emissions_tco2e'].tail(12).values
        else:
            recent_emissions = np.zeros(12)
        
        predictions = []
        
        # Get last known values for lag features
        last_emission_lag_1 = last_row['emissions_lag_1'].values[0] if 'emissions_lag_1' in last_row.columns else 0
        last_emission_lag_2 = last_row['emissions_lag_2'].values[0] if 'emissions_lag_2' in last_row.columns else 0
        last_emission_lag_4 = last_row['emissions_lag_4'].values[0] if 'emissions_lag_4' in last_row.columns else 0
        last_rolling_4 = last_row['emissions_rolling_4'].values[0] if 'emissions_rolling_4' in last_row.columns else 0
        last_rolling_12 = last_row['emissions_rolling_12'].values[0] if 'emissions_rolling_12' in last_row.columns else 0
        
        # Predict 52 weeks ahead
        for week_num in range(1, 53):
            future_date = last_date + timedelta(weeks=week_num)
            
            # Create future row based on last row
            future_row = last_row.copy()
            future_row['date'] = future_date
            future_row['year'] = future_date.year
            future_row['month'] = future_date.month
            future_row['week_of_year'] = future_date.isocalendar()[1]
            future_row['quarter'] = (future_date.month - 1) // 3 + 1
            future_row['day_of_year'] = future_date.timetuple().tm_yday
            
            # Update cyclical features
            future_row['month_sin'] = np.sin(2 * np.pi * future_row['month'] / 12)
            future_row['month_cos'] = np.cos(2 * np.pi * future_row['month'] / 12)
            future_row['week_sin'] = np.sin(2 * np.pi * future_row['week_of_year'] / 52)
            future_row['week_cos'] = np.cos(2 * np.pi * future_row['week_of_year'] / 52)
            
            # Update lag features with recent predictions
            if len(predictions) >= 1:
                future_row['emissions_lag_1'] = predictions[-1]['predicted_emissions']
            else:
                future_row['emissions_lag_1'] = last_emission_lag_1
                
            if len(predictions) >= 2:
                future_row['emissions_lag_2'] = predictions[-2]['predicted_emissions']
            else:
                future_row['emissions_lag_2'] = last_emission_lag_2
                
            if len(predictions) >= 4:
                future_row['emissions_lag_4'] = predictions[-4]['predicted_emissions']
            else:
                future_row['emissions_lag_4'] = last_emission_lag_4
            
            # Update rolling averages
            recent_with_pred = list(recent_emissions) + [p['predicted_emissions'] for p in predictions]
            future_row['emissions_rolling_4'] = np.mean(recent_with_pred[-4:]) if len(recent_with_pred) >= 4 else last_rolling_4
            future_row['emissions_rolling_12'] = np.mean(recent_with_pred[-12:]) if len(recent_with_pred) >= 12 else last_rolling_12
            
            # Ensure all feature columns exist
            for col in self.feature_columns:
                if col not in future_row.columns:
                    future_row[col] = 0.0
            
            # Prepare features for prediction
            X_future = future_row[self.feature_columns]
            X_future_imputed = self.imputer.transform(X_future)
            X_future_scaled = self.scaler.transform(X_future_imputed)
            
            # Predict
            prediction = self.model.predict(X_future_scaled)[0]
            
            predictions.append({
                'week': week_num,
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted_emissions': float(max(0, prediction))  # Ensure non-negative
            })
        
        return predictions
    
    def get_current_emissions(self, csv_path, organization_id, weeks=52):
        """Get historical emissions for comparison"""
        df = pd.read_csv(csv_path)
        org_data = df[df['organization_id'] == organization_id].copy()
        
        if len(org_data) == 0:
            return []
        
        # Use week_start_date if available, otherwise use date
        if 'date' in org_data.columns:
            org_data['date'] = pd.to_datetime(org_data['date'], format='%d-%m-%Y', dayfirst=True)
        elif 'week_start_date' in org_data.columns:
            org_data['date'] = pd.to_datetime(org_data['week_start_date'], format='%d-%m-%Y', dayfirst=True)
        else:
            raise ValueError("Dataset must have either 'date' or 'week_start_date' column")
        
        org_data = org_data.sort_values('date').tail(weeks)
        
        return [
            {
                'week': idx + 1,
                'date': row['date'].strftime('%Y-%m-%d'),
                'actual_emissions': float(row['total_emissions_tco2e'])
            }
            for idx, row in org_data.iterrows()
        ]
    
    def save(self, filepath):
        """Save model and artifacts"""
        artifact = {
            'model': self.model,
            'scaler': self.scaler,
            'imputer': self.imputer,
            'feature_columns': self.feature_columns,
            'org_stats': self.org_stats,
            'training_date': datetime.now().isoformat()
        }
        joblib.dump(artifact, filepath)
        logger.info(f"Model saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath):
        """Load model and artifacts"""
        artifact = joblib.load(filepath)
        forecaster = cls()
        forecaster.model = artifact['model']
        forecaster.scaler = artifact['scaler']
        forecaster.imputer = artifact['imputer']
        forecaster.feature_columns = artifact['feature_columns']
        forecaster.org_stats = artifact.get('org_stats', {})
        logger.info(f"Model loaded from: {filepath}")
        return forecaster


if __name__ == "__main__":
    # Training script
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(backend_dir, 'ecosphere_synthetic.csv')
    model_path = os.path.join(backend_dir, 'xgboost_emission_model.pkl')
    
    if os.path.exists(csv_path):
        logger.info("Starting training...")
        forecaster = EmissionForecaster()
        metrics = forecaster.train(csv_path)
        
        logger.info("\n=== Training Metrics ===")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")
        
        forecaster.save(model_path)
        logger.info("\nTraining complete!")
    else:
        logger.error(f"Dataset not found at: {csv_path}")
        logger.info("Please upload the dataset first")

