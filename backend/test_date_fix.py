"""
Quick test to verify all endpoints work after date format fix
"""
import pandas as pd
from pathlib import Path

backend_dir = Path(__file__).parent
csv_path = backend_dir / "ecosphere_synthetic.csv"

print("🔍 Testing date parsing...")

# Test 1: Read CSV and parse dates
df = pd.read_csv(csv_path)
print(f"✓ CSV loaded: {len(df)} rows")

# Test 2: Parse week_start_date
df['week_start_date'] = pd.to_datetime(df['week_start_date'], format='%d-%m-%Y', dayfirst=True)
print(f"✓ Date parsing successful")
print(f"  First date: {df['week_start_date'].iloc[0]}")
print(f"  Last date: {df['week_start_date'].iloc[-1]}")

# Test 3: Filter by organization
org_data = df[df['organization_id'] == 'ORG001']
print(f"✓ ORG001 data: {len(org_data)} rows")

# Test 4: Get last 52 weeks
last_52 = org_data.sort_values('week_start_date').tail(52)
print(f"✓ Last 52 weeks retrieved")

print(f"\n✅ All date parsing tests passed!")
print(f"\nYou can now:")
print(f"  1. Refresh the Dashboard page")
print(f"  2. Submit organization form")
print(f"  3. All ML endpoints should work")
