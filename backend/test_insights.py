"""
Test script to verify chart generation and AI insights
"""
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv()

# Import the functions
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
from io import BytesIO
from groq import Groq

print("🔧 Testing Chart Generation and AI Analysis...")
print("=" * 60)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_test_charts():
    """Generate test charts"""
    try:
        csv_path = backend_dir / "ecosphere_synthetic.csv"
        model_path = backend_dir / "xgboost_emission_model.pkl"
        organization_id = "ORG001"
        
        print(f"\n📊 Reading data from: {csv_path}")
        
        # Read historical data
        df = pd.read_csv(csv_path)
        org_data = df[df['organization_id'] == organization_id].copy()
        org_data['week_start_date'] = pd.to_datetime(org_data['week_start_date'])
        org_data = org_data.sort_values('week_start_date')
        last_52_weeks = org_data.tail(52)
        
        print(f"✓ Found {len(last_52_weeks)} historical weeks")
        
        # Get forecast data
        from train_xgboost_model import EmissionForecaster
        forecaster = EmissionForecaster.load(str(model_path))
        forecast_df = forecaster.predict_52_weeks(str(csv_path), organization_id)
        
        print(f"✓ Generated {len(forecast_df)} forecast weeks")
        
        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.patch.set_facecolor('#f8fafc')
        
        # Historical Chart
        weeks_hist = [f"W{i+1}" for i in range(len(last_52_weeks))]
        emissions_hist = last_52_weeks['total_emissions_tco2e'].values
        
        ax1.bar(weeks_hist, emissions_hist, color='#00bfa6', alpha=0.8, edgecolor='#008577', linewidth=1.5)
        ax1.set_title('Historical Emissions Data (Last 52 Weeks)', fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('Week', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Total Emissions (tCO₂e)', fontsize=12, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_facecolor('#ffffff')
        
        # Add statistics text
        stats_text = f"Mean: {emissions_hist.mean():.2f} | Std: {emissions_hist.std():.2f} | Min: {emissions_hist.min():.2f} | Max: {emissions_hist.max():.2f} tCO₂e"
        ax1.text(0.5, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Set x-axis ticks to show every 4th week
        tick_positions = list(range(0, len(weeks_hist), 4))
        ax1.set_xticks(tick_positions)
        ax1.set_xticklabels([weeks_hist[i] for i in tick_positions], rotation=45)
        
        # Forecast Chart
        weeks_forecast = [f"W{i+1}" for i in range(len(forecast_df))]
        emissions_forecast = [p['predicted_emissions'] for p in forecast_df]
        
        ax2.bar(weeks_forecast, emissions_forecast, color='#667eea', alpha=0.8, edgecolor='#4c51bf', linewidth=1.5)
        ax2.set_title('52-Week Emission Forecast (ML Prediction)', fontsize=16, fontweight='bold', pad=20)
        ax2.set_xlabel('Week', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Predicted Emissions (tCO₂e)', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        ax2.set_facecolor('#ffffff')
        
        # Add forecast statistics
        forecast_mean = np.mean(emissions_forecast)
        forecast_std = np.std(emissions_forecast)
        forecast_min = np.min(emissions_forecast)
        forecast_max = np.max(emissions_forecast)
        forecast_stats = f"Mean: {forecast_mean:.2f} | Std: {forecast_std:.2f} | Min: {forecast_min:.2f} | Max: {forecast_max:.2f} tCO₂e"
        ax2.text(0.5, 0.98, forecast_stats, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', horizontalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Set x-axis ticks
        ax2.set_xticks(tick_positions)
        ax2.set_xticklabels([weeks_forecast[i] for i in tick_positions], rotation=45)
        
        plt.tight_layout()
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        print(f"✓ Chart generated successfully (base64 length: {len(image_base64)})")
        
        return {
            "image_base64": image_base64,
            "historical_stats": {
                "mean": float(emissions_hist.mean()),
                "std": float(emissions_hist.std()),
                "min": float(emissions_hist.min()),
                "max": float(emissions_hist.max())
            },
            "forecast_stats": {
                "mean": float(forecast_mean),
                "std": float(forecast_std),
                "min": float(forecast_min),
                "max": float(forecast_max)
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_with_ai(chart_data):
    """Analyze charts with AI"""
    try:
        print(f"\n🤖 Sending to Groq Vision API...")
        
        image_url = f"data:image/png;base64,{chart_data['image_base64']}"
        
        historical_stats = chart_data['historical_stats']
        forecast_stats = chart_data['forecast_stats']
        
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze these carbon emission charts and provide a concise 2-3 line insight.

Historical Stats: Mean={historical_stats['mean']:.2f}, Std={historical_stats['std']:.2f}, Min={historical_stats['min']:.2f}, Max={historical_stats['max']:.2f} tCO₂e
Forecast Stats: Mean={forecast_stats['mean']:.2f}, Std={forecast_stats['std']:.2f}, Min={forecast_stats['min']:.2f}, Max={forecast_stats['max']:.2f} tCO₂e

Focus on:
1. Key trend differences between historical and forecast
2. Any concerning patterns or positive changes
3. Actionable insight for emissions reduction

Keep response to 2-3 sentences maximum."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_completion_tokens=200,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        insight = completion.choices[0].message.content.strip()
        
        print(f"✓ AI Analysis complete!")
        print(f"\n{'='*60}")
        print(f"📊 AI INSIGHT:")
        print(f"{'='*60}")
        print(f"{insight}")
        print(f"{'='*60}")
        
        return insight
        
    except Exception as e:
        print(f"❌ Error analyzing with AI: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run the test
if __name__ == "__main__":
    chart_data = generate_test_charts()
    
    if chart_data:
        print(f"\n📈 Historical Stats:")
        print(f"   Mean: {chart_data['historical_stats']['mean']:.2f} tCO₂e")
        print(f"   Std:  {chart_data['historical_stats']['std']:.2f} tCO₂e")
        print(f"   Range: {chart_data['historical_stats']['min']:.2f} - {chart_data['historical_stats']['max']:.2f} tCO₂e")
        
        print(f"\n📉 Forecast Stats:")
        print(f"   Mean: {chart_data['forecast_stats']['mean']:.2f} tCO₂e")
        print(f"   Std:  {chart_data['forecast_stats']['std']:.2f} tCO₂e")
        print(f"   Range: {chart_data['forecast_stats']['min']:.2f} - {chart_data['forecast_stats']['max']:.2f} tCO₂e")
        
        analyze_with_ai(chart_data)
        
        print(f"\n✅ Test completed successfully!")
    else:
        print(f"\n❌ Test failed!")
