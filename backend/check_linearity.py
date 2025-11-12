"""
Linearity Check Script

Evaluates whether the emission data and predictions show linear or non-linear patterns.
"""
from pandas.plotting import autocorrelation_plot
from scipy.fft import fft
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import os

print("="*60)
print("LINEARITY EVALUATION TOOL")
print("="*60)

# Load dataset
csv_path = os.path.join(os.path.dirname(__file__), 'ecosphere_synthetic.csv')

if not os.path.exists(csv_path):
    print(f"\n❌ Dataset not found at {csv_path}")
    print("Please run dataset_generator.py first!")
    exit(1)

df = pd.read_csv(csv_path)
print(f"\n✓ Loaded dataset: {df.shape[0]:,} records")

# Convert date
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
else:
    print("❌ No 'date' column found in dataset!")
    exit(1)

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Group by week and get average emissions (aggregate daily data to weekly for analysis)
df['week'] = df['date'].dt.to_period('W')
weekly_data = df.groupby('week')['total_emissions_tco2e'].mean().reset_index()
weekly_data['date'] = weekly_data['week'].dt.to_timestamp()
weekly_data['week_index'] = range(len(weekly_data))

print(
    f"✓ Aggregated {len(df)} daily records to {len(weekly_data)} weekly data points for analysis\n")

# ====================
# LINEARITY TESTS
# ====================

print("="*60)
print("LINEARITY ANALYSIS")
print("="*60)

X = weekly_data['week_index'].values.reshape(-1, 1)
y = weekly_data['total_emissions_tco2e'].values

# 1. Linear fit
lr = LinearRegression()
lr.fit(X, y)
y_linear = lr.predict(X)
linear_r2 = r2_score(y, y_linear)

# 2. Calculate variation metrics
residuals = y - y_linear
residual_std = np.std(residuals)
coefficient_of_variation = (residual_std / np.mean(y)) * 100

# 3. Runs test for randomness (pattern detection)
median_y = np.median(y)
runs = np.sum(np.diff(y > median_y) != 0) + 1
n_above = np.sum(y > median_y)
n_below = len(y) - n_above
expected_runs = ((2 * n_above * n_below) / len(y)) + 1
runs_deviation = abs(runs - expected_runs)

# 4. Check for seasonality
fft_values = np.abs(fft(y - np.mean(y)))
frequencies = np.fft.fftfreq(len(y))
# Find dominant frequency (excluding DC component)
dominant_freq_idx = np.argmax(fft_values[1:len(y)//2]) + 1
dominant_period = 1 / \
    abs(frequencies[dominant_freq_idx]
        ) if frequencies[dominant_freq_idx] != 0 else 0

# 5. Range and volatility
min_emission = np.min(y)
max_emission = np.max(y)
range_ratio = max_emission / min_emission if min_emission > 0 else 0
volatility = np.std(y) / np.mean(y) * 100

# ====================
# PRINT RESULTS
# ====================

print(f"\n📊 DESCRIPTIVE STATISTICS:")
print(f"  Mean emissions: {np.mean(y):.2f} tCO2e")
print(f"  Std deviation: {np.std(y):.2f} tCO2e")
print(f"  Min emissions: {min_emission:.2f} tCO2e")
print(f"  Max emissions: {max_emission:.2f} tCO2e")
print(f"  Range ratio (max/min): {range_ratio:.2f}x")
print(f"  Volatility (CV): {volatility:.2f}%")

print(f"\n📈 LINEAR FIT METRICS:")
print(f"  Linear R² score: {linear_r2:.4f}")
print(f"  Linear slope: {lr.coef_[0]:.4f} tCO2e/week")
print(f"  Residual std: {residual_std:.2f} tCO2e")
print(f"  Coefficient of variation: {coefficient_of_variation:.2f}%")

print(f"\n🔄 PATTERN ANALYSIS:")
print(f"  Number of runs: {runs}")
print(f"  Expected runs (random): {expected_runs:.1f}")
print(f"  Runs deviation: {runs_deviation:.1f}")
print(f"  Dominant cycle period: {dominant_period:.1f} weeks")

print(f"\n" + "="*60)
print("LINEARITY ASSESSMENT")
print("="*60)

# Determine linearity
is_linear = True
reasons = []

if linear_r2 < 0.85:
    is_linear = False
    reasons.append(f"Low linear R² ({linear_r2:.4f} < 0.85)")

if coefficient_of_variation > 30:
    is_linear = False
    reasons.append(f"High variation ({coefficient_of_variation:.1f}% > 30%)")

if range_ratio > 3.0:
    is_linear = False
    reasons.append(f"Large range ratio ({range_ratio:.1f}x > 3.0)")

if abs(runs_deviation) > 10:
    is_linear = False
    reasons.append(
        f"Non-random pattern (runs deviation: {runs_deviation:.1f})")

if dominant_period > 0 and 4 <= dominant_period <= 52:
    is_linear = False
    reasons.append(
        f"Cyclical pattern detected (period: {dominant_period:.1f} weeks)")

if volatility < 15:
    reasons.append(
        f"Low volatility ({volatility:.1f}% < 15%) - data may be too smooth")

if is_linear:
    print("\n❌ DATA APPEARS LINEAR!")
    print("\nThe data shows predominantly linear characteristics.")
    if reasons:
        print("\nWarnings:")
        for reason in reasons:
            print(f"  • {reason}")
else:
    print("\n✅ DATA SHOWS NON-LINEAR PATTERNS!")
    print("\nReasons:")
    for reason in reasons:
        print(f"  • {reason}")

# ====================
# VISUALIZATION
# ====================

print(f"\n" + "="*60)
print("GENERATING VISUALIZATION...")
print("="*60)

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# Plot 1: Time series with linear trend
ax1 = axes[0, 0]
ax1.plot(weekly_data['date'], y, label='Actual Emissions',
         linewidth=2, color='#1e88e5', alpha=0.8)
ax1.plot(weekly_data['date'], y_linear, label='Linear Trend',
         linewidth=2, color='red', linestyle='--', alpha=0.7)
ax1.set_title('Emissions Over Time with Linear Trend',
              fontsize=12, fontweight='bold')
ax1.set_xlabel('Date')
ax1.set_ylabel('Emissions (tCO2e)')
ax1.legend()
ax1.grid(alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# Plot 2: Residuals
ax2 = axes[0, 1]
ax2.scatter(range(len(residuals)), residuals, alpha=0.6, s=30, color='purple')
ax2.axhline(y=0, color='red', linestyle='--', linewidth=2)
ax2.axhline(y=residual_std, color='orange', linestyle=':', linewidth=1.5,
            label=f'±1 Std ({residual_std:.1f})')
ax2.axhline(y=-residual_std, color='orange', linestyle=':', linewidth=1.5)
ax2.set_title('Residuals from Linear Fit', fontsize=12, fontweight='bold')
ax2.set_xlabel('Week Index')
ax2.set_ylabel('Residual (tCO2e)')
ax2.legend()
ax2.grid(alpha=0.3)

# Plot 3: Distribution
ax3 = axes[1, 0]
ax3.hist(y, bins=30, edgecolor='black', alpha=0.7, color='green')
ax3.axvline(np.mean(y), color='red', linestyle='--', linewidth=2, label='Mean')
ax3.axvline(np.median(y), color='orange',
            linestyle='--', linewidth=2, label='Median')
ax3.set_title('Emission Distribution', fontsize=12, fontweight='bold')
ax3.set_xlabel('Emissions (tCO2e)')
ax3.set_ylabel('Frequency')
ax3.legend()
ax3.grid(alpha=0.3)

# Plot 4: Autocorrelation (showing cycles)
ax4 = axes[1, 1]
autocorrelation_plot(pd.Series(y), ax=ax4, color='#e53935')
ax4.set_title('Autocorrelation (Cyclic Pattern Detection)',
              fontsize=12, fontweight='bold')
ax4.set_xlabel('Lag (weeks)')
ax4.set_ylabel('Autocorrelation')
ax4.grid(alpha=0.3)

plt.tight_layout()
output_path = os.path.join(os.path.dirname(__file__), 'linearity_check.png')
plt.savefig(output_path, dpi=150, facecolor='white', edgecolor='none')
print(f"\n✓ Visualization saved to: {output_path}")

plt.close()

# ====================
# RECOMMENDATIONS
# ====================

print(f"\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

if is_linear:
    print("\n⚠️  The data is too linear. To create non-linear patterns:")
    print("  1. Run dataset_generator.py to generate new data with enhanced variation")
    print("  2. Ensure variation functions are creating diverse patterns")
    print("  3. Check that seasonal, cyclical, and event multipliers are active")
    print("  4. Increase volatility and range in industry profiles")
    print("\nSuggested command:")
    print("  python3 dataset_generator.py")
else:
    print("\n✅ The data has good non-linear characteristics!")
    print("  Next steps:")
    print("  1. Run training.py to train the model")
    print("  2. Check prediction_timeseries.png for prediction quality")
    print("\nSuggested command:")
    print("  python3 training.py")

print(f"\n" + "="*60 + "\n")
