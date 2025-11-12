import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emission_insights'")
table_exists = cursor.fetchone()

if table_exists:
    print("✓ emission_insights table exists")
    
    cursor.execute('SELECT * FROM emission_insights')
    result = cursor.fetchall()
    
    print(f"\n📊 Total insights in DB: {len(result)}")
    
    if result:
        latest = result[-1]
        print(f"\n🔍 Latest insight:")
        print(f"   Organization ID: {latest[1]}")
        print(f"   Insight: {latest[2]}")
        print(f"   Historical Mean: {latest[4]:.2f} tCO₂e")
        print(f"   Forecast Mean: {latest[6]:.2f} tCO₂e")
        print(f"   Created at: {latest[8]}")
    else:
        print("\n⚠️  No insights found in database!")
        print("   You need to call /api/ml/generate-insights/ORG001 endpoint first.")
else:
    print("❌ emission_insights table does not exist!")
    print("   Database needs to be reinitialized.")

conn.close()
