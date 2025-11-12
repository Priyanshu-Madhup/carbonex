"""
Generate AI insights for existing organization
Run this once to populate insights for ORG001
"""
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from main import generate_emission_charts, analyze_charts_with_ai
import sqlite3

print("🚀 Generating AI Insights for ORG001...")
print("="*60)

try:
    # Generate charts
    print("\n📊 Step 1: Generating emission charts...")
    chart_data = generate_emission_charts("ORG001")
    print(f"✓ Charts generated (base64 length: {len(chart_data['image_base64'])})")
    
    # Analyze with AI
    print("\n🤖 Step 2: Analyzing charts with Groq Vision AI...")
    insight = analyze_charts_with_ai(
        chart_data['image_base64'],
        chart_data['historical_stats'],
        chart_data['forecast_stats']
    )
    print(f"✓ AI analysis complete!")
    
    # Store in database
    print("\n💾 Step 3: Storing insights in database...")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO emission_insights 
        (organization_id, insight_text, chart_image_base64, 
         historical_mean, historical_std, forecast_mean, forecast_std)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "ORG001",
        insight,
        chart_data['image_base64'],
        chart_data['historical_stats']['mean'],
        chart_data['historical_stats']['std'],
        chart_data['forecast_stats']['mean'],
        chart_data['forecast_stats']['std']
    ))
    conn.commit()
    conn.close()
    
    print(f"✓ Insights stored successfully!")
    
    # Display results
    print("\n" + "="*60)
    print("📊 AI INSIGHT:")
    print("="*60)
    print(f"{insight}")
    print("="*60)
    
    print(f"\n📈 Statistics:")
    print(f"   Historical Mean: {chart_data['historical_stats']['mean']:.2f} tCO₂e")
    print(f"   Forecast Mean:   {chart_data['forecast_stats']['mean']:.2f} tCO₂e")
    
    print(f"\n✅ Success! EcoAI now has access to these insights.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
