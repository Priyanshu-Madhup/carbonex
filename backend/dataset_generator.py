import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

n = 1000

# Basic org/facility data
org_ids = ['ORG001']
facilities = ['Pune HQ', 'Mumbai Plant', 'Delhi Office',
              'Bengaluru Lab', 'Hyderabad Warehouse']
locations = ['Pune, IN', 'Mumbai, IN',
             'Delhi, IN', 'Bengaluru, IN', 'Hyderabad, IN']

# Fuel types and emission factors (approx. realistic)
fuel_types = ['Diesel', 'LPG', 'Natural Gas', 'Petrol', 'CNG']
fuel_ef_map = {'Diesel': 2.68, 'LPG': 1.51, 'Natural Gas': 2.06,
               'Petrol': 2.31, 'CNG': 2.75}  # kgCO2e per liter or equivalent

# Suppliers and categories
suppliers = ['ABC Plastics', 'GreenSteel Co',
             'LogiTrans', 'PackWise', 'ElectroParts']
purchase_categories = ['Raw material', 'Logistics',
                       'Packaging', 'Electronics', 'Services']
category_ef = {'Raw material': 0.0008, 'Logistics': 0.0012, 'Packaging': 0.0006,
               'Electronics': 0.0015, 'Services': 0.0004}  # kgCO2e per ₹

# Vehicles (some rows will include fleet data)
vehicle_ids = [f'VEH{str(i).zfill(3)}' for i in range(1, 21)]

# Dates: random dates across 2024
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

    # Energy/electricity (kWh) - depends on facility type
    base_elec = {
        'Pune HQ': 2000, 'Mumbai Plant': 8000, 'Delhi Office': 1500, 'Bengaluru Lab': 3500, 'Hyderabad Warehouse': 2500
    }
    elec_kwh = max(0, np.random.normal(
        loc=base_elec[facility], scale=base_elec[facility]*0.25))
    # Renewable portion (0-50%)
    renewable_kwh = round(elec_kwh * np.random.beta(1.5, 6.0), 2)
    # grid emission factor - slight variation per location
    grid_ef = round(np.random.normal(0.82, 0.05), 3)  # kgCO2e/kWh

    # Electricity cost (₹) assuming ~₹8-12 per kWh, add some noise
    elec_cost = round(elec_kwh * np.random.normal(9.5, 1.2), 2)

    # Fuel usage - sometimes zero
    fuel_type = np.random.choice(fuel_types, p=[0.4, 0.1, 0.15, 0.25, 0.1])
    # generator/fuel use more likely for larger facilities
    if np.random.rand() < 0.55:
        fuel_consumed = round(abs(np.random.normal(
            loc=50 if facility == 'Mumbai Plant' else 20, scale=25)), 2)
    else:
        fuel_consumed = 0.0
    fuel_ef = fuel_ef_map[fuel_type]
    generator_hours = round(np.random.exponential(
        scale=2.0), 2) if fuel_consumed > 0 else 0.0

    # Fleet data - sparse
    if np.random.rand() < 0.3:
        vehicle = random.choice(vehicle_ids)
        distance_km = round(abs(np.random.normal(loc=120, scale=80)), 2)
        # km per liter ~10
        vehicle_fuel = round(
            distance_km / np.random.normal(loc=10.0, scale=1.5), 2)
    else:
        vehicle = None
        distance_km = 0.0
        vehicle_fuel = 0.0

    occupancy_rate = round(np.random.uniform(30, 95), 1)

    # Production/activity
    if facility in ['Mumbai Plant', 'Bengaluru Lab']:
        product_output = max(1, int(np.random.normal(
            loc=15000 if facility == 'Mumbai Plant' else 6000, scale=3000)))
    else:
        product_output = int(np.random.normal(loc=800, scale=400))
    product_output = max(0, product_output)

    machine_runtime_hours = round(np.random.uniform(0, 24), 2)
    equipment_power_kw = round(
        np.random.choice([15, 45, 75, 100, 5, 25, 60]), 1)

    # Environment
    temp = round(np.random.normal(28, 6), 1)
    humidity = round(np.random.uniform(25, 85), 1)
    weather = np.random.choice(['Sunny', 'Cloudy', 'Rainy', 'Humid', 'Windy'], p=[
                               0.45, 0.2, 0.15, 0.15, 0.05])
    occupancy_count = int(max(0, round(
        product_output / np.random.uniform(20, 200), 0) + np.random.randint(1, 50)))
    working_hours = round(np.random.choice(
        [8, 9, 10, 12], p=[0.4, 0.3, 0.2, 0.1]), 2)

    # Supply chain / spend
    supplier = random.choice(suppliers)
    category = random.choice(purchase_categories)
    spend = round(abs(np.random.normal(loc=50000 if category ==
                  'Raw material' else 15000, scale=30000)), 2)
    cat_ef = category_ef[category]

    # Derived emissions (kg->tonnes)
    scope2_t = round((elec_kwh - renewable_kwh) * grid_ef / 1000, 4)
    scope1_t = round(fuel_consumed * fuel_ef / 1000, 4)
    scope1_vehicle_t = round(
        vehicle_fuel * fuel_ef_map.get('Diesel', 2.68) / 1000, 4) if vehicle_fuel > 0 else 0.0
    # spend*kgCO2e/₹ -> kg -> t by /1000
    scope3_t = round(spend * cat_ef / 1000, 4)

    # Total emissions (tCO2e)
    total_t = round(scope1_t + scope2_t + scope3_t + scope1_vehicle_t, 4)
    emission_intensity = round(
        total_t / product_output, 6) if product_output > 0 else 0.0

    # Recommendation fields sometimes empty
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

# Save to CSV in the same folder as this script
# use the directory containing this file (backend/)
output_dir = os.path.dirname(__file__)
os.makedirs(output_dir, exist_ok=True)
out_path = os.path.join(output_dir, 'ecosphere_synthetic.csv')

df.to_csv(out_path, index=False)
print("Synthetic dataset generation complete.")
print(f"Saved synthetic dataset to: {out_path}")
print(f"Dataset shape: {df.shape}")
print(f"\nFirst few rows:")
print(df.head())
