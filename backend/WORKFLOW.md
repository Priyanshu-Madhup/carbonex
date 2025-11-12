# Carbon Emission Prediction Workflow

## 📋 Complete Workflow

### Step 1: Generate Dataset with Variation
```bash
python3 dataset_generator.py
```
This creates `ecosphere_synthetic.csv` with:
- Seasonal patterns (summer/winter peaks)
- Non-linear trends with improvement initiatives
- Multi-frequency cyclical patterns
- Industry-specific emission profiles
- Special event spikes and drops
- Random weekly variation

### Step 2: Check Data Linearity (Optional)
```bash
python3 check_linearity.py
```
This analyzes the generated data and:
- ✅ Checks if patterns are non-linear
- 📊 Shows statistics and visualizations
- 💡 Provides recommendations
- 🖼️ Creates `linearity_check.png`

**What to look for:**
- **Non-linear patterns**: Range ratio > 3.0, Volatility > 15%, Cyclical patterns
- **Linear patterns**: High linear R² (> 0.85), Low variation

### Step 3: Train the Model
```bash
python3 training.py
```
This trains ML models and:
- Compares GradientBoosting, RandomForest, and Ridge
- Selects best model via cross-validation
- Saves trained model to `emission_forecast_model.pkl`
- Generates 4 visualization plots

**Generated Files:**
- `actual_vs_predicted.png` - Test set performance
- `feature_importance.png` - Feature rankings
- `residuals_distribution.png` - Error distribution
- `prediction_timeseries.png` - **Full timeline with predictions**

### Step 4: Use Prediction Functions
```bash
python3 prediction_graph.py
```
This demonstrates:
- Making predictions on new data
- Generating custom visualizations
- Future emission forecasting

## 🎯 Expected Results

### Non-Linear Prediction Graph Should Show:
- ✅ **Seasonal waves** - Clear summer/winter peaks
- ✅ **Cyclical patterns** - Monthly, quarterly oscillations
- ✅ **Growth trend** - Non-linear increase over time
- ✅ **Spikes & drops** - Event-based variations
- ✅ **Industry clustering** - Different emission levels

### If Graph is Too Linear:
1. Check `check_linearity.py` output
2. Verify variation functions in `dataset_generator.py`
3. Regenerate dataset with stronger patterns
4. Retrain model

## 📊 Key Metrics

**Good Non-Linear Data:**
- Range ratio (max/min): > 3.0
- Volatility: > 15%
- Linear R²: < 0.85
- Visible cyclical patterns

**Good Model Performance:**
- R² score: > 0.70
- MAPE: < 30%
- Predictions follow actual trends

## 🔧 Troubleshooting

**Problem:** Graph is too linear
- **Solution:** Regenerate dataset, check variation multipliers

**Problem:** Poor prediction accuracy
- **Solution:** Add more features, tune model hyperparameters

**Problem:** No seasonal patterns visible
- **Solution:** Check seasonal_multiplier function, increase amplitude

## 📁 File Structure

```
backend/
├── dataset_generator.py       # Generate synthetic data
├── check_linearity.py          # Evaluate data patterns
├── training.py                 # Train ML models
├── prediction_graph.py         # Prediction utilities
├── ecosphere_synthetic.csv     # Generated dataset
├── emission_forecast_model.pkl # Trained model
└── *.png                       # Visualization outputs
```

## 💡 Tips

1. **Always check linearity** before training
2. **Regenerate data** if patterns are too simple
3. **Compare multiple models** in training
4. **Visualize predictions** to verify quality
5. **Use prediction_graph.py** for custom forecasts
