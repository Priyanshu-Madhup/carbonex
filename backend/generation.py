# synthetic_daily_emissions_generator.py
# Generates a 1000-row synthetic daily emissions dataset and saves it to /mnt/data/synthetic_daily_emissions_1000.csv

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# Path to the optional input file (your uploaded monthly/yearly dataset)
input_path = "/mnt/data/universal_emission_dataset_1000.csv"

# Default category lists (used if input file isn't available or doesn't contain useful columns)
default_sectors = [
    "Energy","Finance","Retail","Manufacturing","Healthcare","Tech",
    "Transport","Agriculture","Education","Hospitality"
]
default_countries = [
    "India","USA","UK","Germany","China","Brazil","Canada","Australia","France","Netherlands"
]

# Try to read the provided file to extract sample sectors/countries (case-insensitive column name search)
sample_sectors = default_sectors.copy()
sample_countries = default_countries.copy()
if os.path.exists(input_path):
    try:
        df_orig = pd.read_csv(input_path)
        cols_lower = [c.lower() for c in df_orig.columns]
        # find a probable sector column
        for col, col_l in zip(df_orig.columns, cols_lower):
            if "sector" in col_l or "industry" in col_l:
                vals = df_orig[col].dropna().astype(str).unique().tolist()
                if vals:
                    sample_sectors = vals[:50]
                break
        # find a probable country/location column
        for col, col_l in zip(df_orig.columns, cols_lower):
            if "country" in col_l or "location" in col_l or "region" in col_l:
                vals = df_orig[col].dropna().astype(str).unique().tolist()
                if vals:
                    sample_countries = vals[:50]
                break
    except Exception:
        # If reading fails, continue with defaults
        pass

# Anonymized organization domains (synthetic)
domains = [
    "fin-services.example","green-energy.example","retail-hub.example","manufactory.example",
    "healthcare-co.example","tech-innovate.example","trans-logistics.example","agri-farm.example",
    "edu-institute.example","hotel-chain.example","media-group.example","chemworks.example",
    "auto-mobility.example","pharma-labs.example","food-proc.example","textiles.example",
    "construction.example","telecom.example","consulting.example","biotech.example"
]

n_rows = 1000

# Date range for daily records (last 2 years up to 2025-11-11)
end_date = datetime(2025, 11, 11)
start_date = end_date - timedelta(days=730)
all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

# Sample a date for each row
dates = np.random.choice(all_dates, size=n_rows)

# Generate synthetic numeric metrics
employee_counts = np.random.randint(50, 50000, size=n_rows)                       # employee count per org
energy_kwh = (employee_counts * np.random.uniform(10, 200, size=n_rows)).round(1) # daily energy kWh scaled by employees

# Synthetic emission calculations (coherent but artificial)
scope1 = (energy_kwh * np.random.uniform(0.00005, 0.0005, size=n_rows) * 0.5).round(3)
scope2 = (energy_kwh * np.random.uniform(0.00005, 0.0006, size=n_rows) * 0.8).round(3)
scope3 = (energy_kwh * np.random.uniform(0.0001, 0.001, size=n_rows) * 1.2).round(3)
total_emissions = (scope1 + scope2 + scope3).round(3)

# Other categorical columns
sectors = np.random.choice(sample_sectors, size=n_rows)
countries = np.random.choice(sample_countries, size=n_rows)
domains_sampled = np.random.choice(domains, size=n_rows)
reporting_day = pd.to_datetime(dates).date

# Assemble DataFrame
synthetic_df = pd.DataFrame({
    "org_domain": domains_sampled,
    "date": reporting_day,
    "country": countries,
    "industry_sector": sectors,
    "employee_count": employee_counts,
    "energy_kwh_day": energy_kwh,
    "scope1_tons_CO2e": scope1,
    "scope2_tons_CO2e": scope2,
    "scope3_tons_CO2e": scope3,
    "total_emissions_tons_CO2e": total_emissions
})

# Mark as synthetic and anonymized
synthetic_df["note"] = "synthetic_anonymized_daily_record"

# Shuffle rows for randomness
synthetic_df = synthetic_df.sample(frac=1, random_state=42)._
