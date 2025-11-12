"""
Synthetic Weekly Emission Dataset Generator

Generates realistic weekly aggregated emission data for carbon footprint analysis.
Includes multi-country, multi-industry facility operations with temporal patterns.
"""
import numpy as np
import pandas as pd
from datetime import timedelta
import random
import os
from typing import Dict, List, Tuple

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)

# ====================
# CONFIGURATION
# ====================

# ====================
# CONFIGURATION
# ====================

# Time range for weekly data
WEEK_START_DATE = '2023-11-06'  # Monday
WEEK_END_DATE = '2025-11-10'
FACILITIES_PER_WEEK_MIN = 90
FACILITIES_PER_WEEK_MAX = 101

# Generate weekly date range
weeks = pd.date_range(start=WEEK_START_DATE, end=WEEK_END_DATE, freq='W-MON')
n_weeks = len(weeks)

# Expand facilities to get ~100 unique combinations
facilities_expanded = [
    'Pune HQ', 'Mumbai Plant', 'Delhi Office', 'Bengaluru Lab', 'Hyderabad Warehouse',
    'Chennai Factory', 'Kolkata Warehouse', 'Ahmedabad Plant', 'Jaipur Office',
    'Lucknow Lab', 'Nagpur Facility', 'Indore Center', 'Bhopal Unit',
    'Patna Office', 'Vadodara Plant', 'Coimbatore Facility', 'Kochi Warehouse',
    'Visakhapatnam Plant', 'Surat Factory', 'Agra Office', 'Nashik Plant',
    'Rajkot Facility', 'Ludhiana Factory', 'Kanpur Warehouse', 'Chandigarh Office',
    'Mysore Lab', 'Guwahati Facility', 'Bhubaneswar Office', 'Thiruvananthapuram Center',
    'Ranchi Plant', 'Jodhpur Facility', 'Amritsar Office', 'Allahabad Warehouse',
    'Varanasi Facility', 'Aurangabad Plant', 'Dhanbad Office', 'Gwalior Center',
    'Jammu Facility', 'Raipur Plant', 'Jabalpur Office', 'Cuttack Warehouse',
    'Bikaner Facility', 'Udaipur Center', 'Ajmer Plant', 'Tirupati Office',
    'Mangalore Facility', 'Shimla Center', 'Dehradun Office', 'Gangtok Lab',
    'Shillong Facility', 'Imphal Center'
]

# Basic org/facility data (keeping for compatibility)
org_ids = ['ORG001']
facilities = facilities_expanded[:50]  # Use 50 facilities for variety

# Industry sectors (from synthetic data example)
industry_sectors = [
    "Energy", "Finance", "Retail", "Manufacturing", "Healthcare", "Tech",
    "Transport", "Agriculture", "Education", "Hospitality", "Media",
    "Chemical", "Automotive", "Pharma", "Food Processing", "Textiles",
    "Construction", "Telecom", "Consulting", "Biotech"
]

# Countries/regions
countries = [
    "India", "USA", "UK", "Germany", "China", "Brazil", "Canada",
    "Australia", "France", "Netherlands", "Japan", "Singapore",
    "UAE", "South Africa", "Mexico", "Italy", "Spain", "South Korea"
]

# Anonymized organization domains
org_domains = [
    "fin-services.example", "green-energy.example", "retail-hub.example",
    "manufactory.example", "healthcare-co.example", "tech-innovate.example",
    "trans-logistics.example", "agri-farm.example", "edu-institute.example",
    "hotel-chain.example", "media-group.example", "chemworks.example",
    "auto-mobility.example", "pharma-labs.example", "food-proc.example",
    "textiles.example", "construction.example", "telecom.example",
    "consulting.example", "biotech.example"
]

# Fuel types with emission factors (kgCO2e per liter)
FUEL_TYPES = ['Diesel', 'LPG', 'Natural Gas', 'Petrol', 'CNG']
FUEL_EF_MAP = {
    'Diesel': 2.68,
    'LPG': 1.51,
    'Natural Gas': 2.06,
    'Petrol': 2.31,
    'CNG': 2.75
}
FUEL_TYPE_PROBS = [0.4, 0.1, 0.15, 0.25, 0.1]

# Suppliers and categories
SUPPLIERS = ['ABC Plastics', 'GreenSteel Co',
             'LogiTrans', 'PackWise', 'ElectroParts']
PURCHASE_CATEGORIES = ['Raw material', 'Logistics',
                       'Packaging', 'Electronics', 'Services']
CATEGORY_EF = {
    'Raw material': 0.0008,
    'Logistics': 0.0012,
    'Packaging': 0.0006,
    'Electronics': 0.0015,
    'Services': 0.0004
}  # kgCO2e per ₹

# Vehicle fleet
VEHICLE_IDS = [f'VEH{str(i).zfill(3)}' for i in range(1, 21)]

# Facility-specific parameters
FACILITY_PARAMS = {
    'Plant': {
        'employee_range': (500, 5000),
        'base_elec_daily': (6000, 10000),
        'base_product_daily': (12000, 18000),
        'operating_days_probs': ([6, 7], [0.3, 0.7])
    },
    'Factory': {
        'employee_range': (500, 5000),
        'base_elec_daily': (6000, 10000),
        'base_product_daily': (12000, 18000),
        'operating_days_probs': ([6, 7], [0.3, 0.7])
    },
    'Lab': {
        'employee_range': (150, 1200),
        'base_elec_daily': (3000, 5000),
        'base_product_daily': (4000, 8000),
        'operating_days_probs': ([5, 6, 7], [0.2, 0.3, 0.5])
    },
    'Center': {
        'employee_range': (150, 1200),
        'base_elec_daily': (3000, 5000),
        'base_product_daily': (4000, 8000),
        'operating_days_probs': ([5, 6, 7], [0.2, 0.3, 0.5])
    },
    'Warehouse': {
        'employee_range': (80, 600),
        'base_elec_daily': (2000, 3500),
        'base_product_daily': (500, 1500),
        'operating_days_probs': ([5, 6, 7], [0.3, 0.4, 0.3])
    },
    'Office': {
        'employee_range': (100, 1000),
        'base_elec_daily': (1500, 2500),
        'base_product_daily': (600, 1200),
        'operating_days_probs': ([5, 6], [0.7, 0.3])
    },
    'HQ': {
        'employee_range': (100, 1000),
        'base_elec_daily': (1500, 2500),
        'base_product_daily': (600, 1200),
        'operating_days_probs': ([5, 6], [0.7, 0.3])
    },
    'default': {
        'employee_range': (100, 800),
        'base_elec_daily': (2000, 4000),
        'base_product_daily': (1000, 3000),
        'operating_days_probs': ([5, 6, 7], [0.3, 0.4, 0.3])
    }
}

# ====================
# HELPER FUNCTIONS
# ====================


def get_facility_type(facility_name: str) -> str:
    """Extract facility type from facility name."""
    for ftype in ['Plant', 'Factory', 'Lab', 'Center', 'Warehouse', 'Office', 'HQ', 'Facility', 'Unit']:
        if ftype in facility_name:
            return ftype
    return 'default'


def get_facility_parameters(facility_name: str) -> Dict:
    """Get operating parameters for a facility type."""
    ftype = get_facility_type(facility_name)
    return FACILITY_PARAMS.get(ftype, FACILITY_PARAMS['default'])


def calculate_emissions(elec_kwh: float, renewable_kwh: float, grid_ef: float,
                        fuel_consumed: float, fuel_ef: float, vehicle_fuel: float,
                        spend: float, cat_ef: float) -> Tuple[float, float, float, float]:
    """Calculate scope 1, 2, 3 emissions and total."""
    scope2_t = round((elec_kwh - renewable_kwh) * grid_ef / 1000, 4)
    scope1_t = round(fuel_consumed * fuel_ef / 1000, 4)
    scope1_vehicle_t = round(
        vehicle_fuel * FUEL_EF_MAP.get('Diesel', 2.68) / 1000, 4) if vehicle_fuel > 0 else 0.0
    scope3_t = round(spend * cat_ef / 1000, 4)
    total_t = round(scope1_t + scope2_t + scope3_t + scope1_vehicle_t, 4)
    return scope1_t + scope1_vehicle_t, scope2_t, scope3_t, total_t


# ====================
# MAIN GENERATION LOGIC
# ====================

rows = []
record_counter = 0

for week_date in weeks:
    # Randomly select facilities to have records this week
    n_facilities_this_week = np.random.randint(
        FACILITIES_PER_WEEK_MIN, FACILITIES_PER_WEEK_MAX)
    selected_facilities = np.random.choice(
        facilities, size=n_facilities_this_week, replace=True)

    for facility in selected_facilities:
        org = org_ids[0]

        # Assign categorical features
        industry_sector = random.choice(industry_sectors)
        country = random.choice(countries)
        org_domain = random.choice(org_domains)
        loc = f"{facility.split()[0]}, {country}"

        # Get facility-specific parameters
        params = get_facility_parameters(facility)
        employee_count = np.random.randint(*params['employee_range'])
        base_elec_daily = np.random.randint(*params['base_elec_daily'])
        base_product_daily = np.random.randint(*params['base_product_daily'])
        days_options, days_probs = params['operating_days_probs']
        operating_days = np.random.choice(days_options, p=days_probs)

        # WEEKLY AGGREGATED VALUES

        # Energy/electricity (kWh) - weekly total
        elec_kwh_daily = max(0, np.random.normal(
            loc=base_elec_daily, scale=base_elec_daily*0.25))
        elec_kwh = round(elec_kwh_daily * operating_days, 2)
        renewable_kwh = round(elec_kwh * np.random.beta(1.5, 6.0), 2)
        grid_ef = round(np.random.normal(0.82, 0.05), 3)
        elec_cost = round(elec_kwh * np.random.normal(9.5, 1.2), 2)

        # Fuel usage - weekly total
        fuel_type = np.random.choice(FUEL_TYPES, p=FUEL_TYPE_PROBS)
        if np.random.rand() < 0.55:
            fuel_daily = abs(np.random.normal(
                loc=50 if 'Plant' in facility else 20, scale=25))
            fuel_consumed = round(fuel_daily * operating_days, 2)
        else:
            fuel_consumed = 0.0
        fuel_ef = FUEL_EF_MAP[fuel_type]
        generator_hours = round(np.random.exponential(
            scale=2.0) * operating_days, 2) if fuel_consumed > 0 else 0.0

        # Fleet data - weekly totals
        if np.random.rand() < 0.3:
            vehicle = random.choice(VEHICLE_IDS)
            distance_km = round(abs(np.random.normal(
                loc=120, scale=80)) * operating_days, 2)
            vehicle_fuel = round(
                distance_km / np.random.normal(loc=10.0, scale=1.5), 2)
        else:
            vehicle = None
            distance_km = 0.0
            vehicle_fuel = 0.0

        # Weekly average occupancy rate
        occupancy_rate = round(np.random.uniform(30, 95), 1)

        # Production/activity - weekly total
        product_output_daily = max(1, int(np.random.normal(
            loc=base_product_daily, scale=base_product_daily*0.3)))
        product_output = product_output_daily * operating_days
        product_output = max(0, product_output)

        # Machine runtime - weekly total hours
        machine_runtime_hours = round(
            np.random.uniform(0, 24) * operating_days, 2)
        equipment_power_kw = round(
            np.random.choice([15, 45, 75, 100, 5, 25, 60]), 1)

        # Environment - weekly averages
        temp = round(np.random.normal(28, 6), 1)
        humidity = round(np.random.uniform(25, 85), 1)
        weather = np.random.choice(['Sunny', 'Cloudy', 'Rainy', 'Humid', 'Windy'],
                                   p=[0.45, 0.2, 0.15, 0.15, 0.05])

        occupancy_count = int(max(0, round(product_output / np.random.uniform(20, 200), 0) +
                                  np.random.randint(1, 50)))

        # Total working hours for the week
        daily_hours = np.random.choice([8, 9, 10, 12], p=[0.4, 0.3, 0.2, 0.1])
        working_hours_per_week = round(daily_hours * operating_days, 2)

        # Supply chain / spend - weekly total
        supplier = random.choice(SUPPLIERS)
        category = random.choice(PURCHASE_CATEGORIES)
        spend_daily = abs(np.random.normal(
            loc=50000 if category == 'Raw material' else 15000, scale=30000))
        spend = round(spend_daily * operating_days, 2)
        cat_ef = CATEGORY_EF[category]

        # Calculate emissions using helper function
        scope1_t, scope2_t, scope3_t, total_t = calculate_emissions(
            elec_kwh, renewable_kwh, grid_ef, fuel_consumed, fuel_ef, vehicle_fuel, spend, cat_ef
        )
        emission_intensity = round(
            total_t / product_output, 6) if product_output > 0 else 0.0

        # Recommendation fields sometimes empty
        if np.random.rand() < 0.25:
            rec_id = f'REC_{record_counter:04d}'
            action_type = np.random.choice(
                ['Retrofit', 'Policy', 'Supplier change', 'Optimize HVAC', 'Route optimization'])
            expected_reduction = round(
                total_t * np.random.uniform(0.05, 0.35), 4)
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

        predicted_next_week = round(total_t * np.random.uniform(0.95, 1.15), 4)

        row = {
            'organization_id': org,
            'org_domain': org_domain,
            'facility_name': facility,
            'location': loc,
            'country': country,
            'industry_sector': industry_sector,
            'employee_count': employee_count,
            'week_start_date': week_date.date().isoformat(),
            'week_end_date': (week_date + timedelta(days=6)).date().isoformat(),
            'operating_days_in_week': operating_days,
            'electricity_consumption_kwh': elec_kwh,
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
            'working_hours_per_week': working_hours_per_week,
            'supplier_name': supplier,
            'purchase_category': category,
            'spend_amount_inr': spend,
            'category_emission_factor_kgco2_per_inr': cat_ef,
            'scope_1_emissions_tco2e': scope1_t,  # Already includes vehicle emissions
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
            'predicted_emission_next_week_tco2e': predicted_next_week,
            'record_id': 'synthetic_anonymized_weekly_record'
        }

        rows.append(row)
        record_counter += 1

df = pd.DataFrame(rows)

# Shuffle rows for randomness
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# ====================
# SAVE DATASET
# ====================

output_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ else '.'
os.makedirs(output_dir, exist_ok=True)
out_path = os.path.join(output_dir, 'ecosphere_synthetic.csv')

df.to_csv(out_path, index=False)

# ====================
# SUMMARY
# ====================

print("\n" + "="*60)
print("  SYNTHETIC WEEKLY EMISSION DATASET GENERATION COMPLETE")
print("="*60)
print(f"✓ Dataset saved to: {out_path}")
print(f"✓ Total records: {len(df):,}")
print(f"✓ Time period: {WEEK_START_DATE} to {WEEK_END_DATE}")
print(f"✓ Weeks covered: {n_weeks}")
print(f"✓ Features: {len(df.columns)}")
print(f"✓ Facilities: {len(facilities)}")
print(f"✓ Countries: {len(countries)}")
print(f"✓ Industries: {len(industry_sectors)}")
print("="*60)
print(f"\nDataset shape: {df.shape}")
print(f"\nSample statistics:")
print(
    f"  Average weekly emissions: {df['total_emissions_tco2e'].mean():.2f} tCO2e")
print(
    f"  Median weekly emissions: {df['total_emissions_tco2e'].median():.2f} tCO2e")
print(f"  Max weekly emissions: {df['total_emissions_tco2e'].max():.2f} tCO2e")
print(f"  Min weekly emissions: {df['total_emissions_tco2e'].min():.2f} tCO2e")
print(f"\nFirst few rows:")
print(df.head(3).to_string(max_cols=10))
print("="*60 + "\n")
