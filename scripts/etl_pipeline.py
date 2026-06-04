"""
Bluestock Mutual Fund Capstone Project - Day 2
ETL Ingestion & Cleaning Pipeline (etl_pipeline.py)

This script performs the following tasks:
1. Initialises project directories.
2. Cleans the 10 raw CSV datasets based on strict data quality rules.
3. Saves the cleaned files as CSVs in data/processed/.
4. Connects to SQLite (bluestock_mf.db) using SQLAlchemy.
5. Deletes existing database records to avoid primary key duplicates on rerun.
6. Executes the DDL statements in sql/schema.sql.
7. Populates the dim_date dimension table.
8. Loads all data into SQLite and verifies that row counts match the processed datasets.
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def setup_paths():
    """
    Sets up and verifies the project directories.
    Returns:
        project_root (Path): The pathlib Path to the project root.
    """
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path(".")
        
    # Ensure processed and db directories exist
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "db").mkdir(parents=True, exist_ok=True)
    
    return project_root

def clean_nav_history(df):
    """
    Cleans the NAV history dataset:
    - Parses date to datetime.
    - Removes duplicates based on amfi_code + date.
    - Sorts by amfi_code + date ascending.
    - Reindexes to full calendar date ranges to forward-fill missing weekend/holiday NAVs.
    - Filters out NAV <= 0.
    """
    print("⏳ [INFO] Cleaning nav_history.csv...")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    
    # Sort
    df = df.sort_values(by=["amfi_code", "date"])
    
    # Forward-fill weekends/holidays per scheme group
    cleaned_groups = []
    for code, group in df.groupby("amfi_code"):
        group = group.set_index("date").sort_index()
        # Create continuous date range from first available date to last available date
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq="D")
        group = group.reindex(full_range)
        group["amfi_code"] = code
        group["nav"] = group["nav"].ffill()
        group = group.reset_index().rename(columns={"index": "date"})
        cleaned_groups.append(group)
        
    cleaned_df = pd.concat(cleaned_groups, ignore_index=True)
    
    # Validate NAV > 0
    cleaned_df = cleaned_df[cleaned_df["nav"] > 0]
    
    # Format date back to string for SQLite consistency
    cleaned_df["date"] = cleaned_df["date"].dt.strftime("%Y-%m-%d")
    print(f"✅ Cleaned nav_history: Shape went from {df.shape} to {cleaned_df.shape}")
    return cleaned_df

def clean_investor_transactions(df):
    """
    Cleans the investor transactions dataset:
    - Normalises transaction type to 'SIP', 'Lumpsum', or 'Redemption'.
    - Validates amount_inr > 0.
    - Normalises dates.
    - Validates KYC status format.
    """
    print("⏳ [INFO] Cleaning investor_transactions.csv...")
    df = df.copy()
    
    # Normalise transaction dates
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date"])
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    
    # Normalise transaction type
    type_map = {
        "sip": "SIP",
        "lumpsum": "Lumpsum",
        "redemption": "Redemption"
    }
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.lower().map(type_map)
    # Default missing/unknown transaction types to Lumpsum
    df["transaction_type"] = df["transaction_type"].fillna("Lumpsum")
    
    # Validate amount > 0
    df = df[df["amount_inr"] > 0]
    
    # Generate units column (amount / 100 as placeholder if missing, or mock units)
    # Looking at original data, it has columns: investor_id, transaction_date, amfi_code, transaction_type, amount_inr, etc.
    # Let's add a calculated units column using amount / mock NAV or simply default it to amount / 100 if units not in columns
    if "units" not in df.columns:
        df["units"] = (df["amount_inr"] / 100.0).round(4)
        
    # Standardise KYC status
    kyc_map = {
        "verified": "Verified",
        "pending": "Pending",
        "failed": "Failed"
    }
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.lower().map(kyc_map).fillna("Pending")
    
    print("✅ Cleaned investor_transactions successfully.")
    return df

def clean_scheme_performance(df):
    """
    Cleans the scheme performance dataset:
    - Normalises numerical variables.
    - Checks for expense ratio boundaries (0.1% - 2.5%) and flags anomalies.
    """
    print("⏳ [INFO] Cleaning scheme_performance.csv...")
    df = df.copy()
    
    # Convert numerical columns
    cols_to_numeric = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", 
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", 
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct", 
        "aum_crore", "expense_ratio_pct", "morningstar_rating"
    ]
    
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    # Default missing ratings to 3
    if "morningstar_rating" in df.columns:
        df["morningstar_rating"] = df["morningstar_rating"].fillna(3).astype(int)
        
    # Flag expense ratio anomalies
    if "expense_ratio_pct" in df.columns:
        anomalies = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
        if not anomalies.empty:
            print(f"⚠️ [WARNING] Detected {len(anomalies)} expense ratio anomalies (outside 0.1% - 2.5% range):")
            for _, row in anomalies.iterrows():
                print(f"   - Scheme {row['amfi_code']}: expense_ratio = {row['expense_ratio_pct']}%")
                
    print("✅ Cleaned scheme_performance successfully.")
    return df

def clean_generic_dataset(df, name):
    """
    Standard clean logic for the other datasets.
    """
    print(f"⏳ [INFO] Cleaning {name}...")
    df = df.copy()
    
    # Standardise date/month formats
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    if "month" in df.columns:
        # Standardise YYYY-MM
        df["month"] = df["month"].astype(str).str.strip().str.slice(0, 7)
        
    # Remove duplicates
    df = df.drop_duplicates()
    
    return df

def build_date_dimension(dates_series):
    """
    Builds a dim_date calendar dimension dataframe from a series of dates.
    """
    dates = pd.to_datetime(dates_series.dropna().unique())
    df_date = pd.DataFrame({"date": dates})
    df_date = df_date.sort_values(by="date")
    
    df_date["year"] = df_date["date"].dt.year
    df_date["month"] = df_date["date"].dt.month
    df_date["day"] = df_date["date"].dt.day
    df_date["quarter"] = df_date["date"].dt.quarter
    df_date["day_of_week"] = df_date["date"].dt.dayofweek # 0 is Monday
    df_date["is_weekend"] = df_date["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)
    
    df_date["date"] = df_date["date"].dt.strftime("%Y-%m-%d")
    return df_date

def execute_sql_schema(db_path, schema_path):
    """
    Deletes the existing database and executes schema.sql.
    """
    if db_path.exists():
        db_path.unlink()
        print(f"🔥 [INFO] Deleted existing SQLite database at {db_path.name} to avoid duplicates.")
        
    print(f"⚙️ [INFO] Creating SQLite tables using {schema_path.name}...")
    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print("✅ Database tables created successfully.")
    except Exception as e:
        print(f"❌ [ERROR] Failed to run schema.sql: {e}")
        sys.exit(1)
    finally:
        conn.close()

def main():
    """
    Main ETL workflow execution.
    """
    print("🚀 Starting ETL Ingestion & Database Load...")
    project_root = setup_paths()
    
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    db_path = project_root / "data" / "db" / "bluestock_mf.db"
    schema_path = project_root / "sql" / "schema.sql"
    
    # 1. Recreate DB structure
    execute_sql_schema(db_path, schema_path)
    
    # Mapping CSV files to cleaning actions and table names
    csv_mappings = {
        "01_fund_master.csv": ("dim_fund", None),
        "02_nav_history.csv": ("fact_nav", clean_nav_history),
        "03_aum_by_fund_house.csv": ("fact_aum", None),
        "04_monthly_sip_inflows.csv": ("sip_inflows", None),
        "05_category_inflows.csv": ("category_inflows", None),
        "06_industry_folio_count.csv": ("industry_folio_count", None),
        "07_scheme_performance.csv": ("fact_performance", clean_scheme_performance),
        "08_investor_transactions.csv": ("fact_transactions", clean_investor_transactions),
        "09_portfolio_holdings.csv": ("portfolio_holdings", None),
        "10_benchmark_indices.csv": ("benchmark_indices", None)
    }
    
    cleaned_datasets = {}
    all_dates = []
    
    # 2. Extract and Clean
    for file, (table_name, clean_func) in csv_mappings.items():
        src_path = raw_dir / file
        if not src_path.exists():
            print(f"❌ [ERROR] Missing raw file: {file}")
            continue
            
        df = pd.read_csv(src_path)
        
        # Apply custom cleaning function if defined, otherwise generic cleaning
        if clean_func:
            df_cleaned = clean_func(df)
        else:
            df_cleaned = clean_generic_dataset(df, file)
            
        # Collect date values to construct unified dim_date
        if "date" in df_cleaned.columns:
            all_dates.extend(df_cleaned["date"].tolist())
            
        cleaned_datasets[table_name] = df_cleaned
        
        # Save to data/processed
        dest_path = processed_dir / file
        df_cleaned.to_csv(dest_path, index=False)
        print(f"💾 Saved cleaned {file} to {dest_path.parent.name}/{dest_path.name}")
        
    # 3. Build & Load Date Dimension
    if all_dates:
        print("\n⏳ [INFO] Building unified calendar date dimension table...")
        df_date = build_date_dimension(pd.Series(all_dates))
        cleaned_datasets["dim_date"] = df_date
        df_date.to_csv(processed_dir / "dim_date.csv", index=False)
        print(f"✅ Generated dim_date: {len(df_date)} calendar dates. Saved to processed/dim_date.csv")
        
    # 4. Load into SQLite
    print("\n⏳ [INFO] Loading cleaned datasets into SQLite database...")
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Establish load order to satisfy foreign key relationships
    load_order = [
        "dim_fund", "dim_date", "fact_nav", "fact_aum", 
        "fact_transactions", "fact_performance", "sip_inflows", 
        "category_inflows", "industry_folio_count", "portfolio_holdings", 
        "benchmark_indices"
    ]
    
    verification_results = []
    
    for table in load_order:
        if table in cleaned_datasets:
            df_to_load = cleaned_datasets[table]
            try:
                # Load
                df_to_load.to_sql(table, con=engine, if_exists="append", index=False)
                # Verify row count
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                db_count = cursor.fetchone()[0]
                conn.close()
                
                df_count = len(df_to_load)
                status = "✅ MATCH" if db_count == df_count else "❌ MISMATCH"
                print(f"  - Table '{table}': CSV Rows = {df_count}, DB Rows = {db_count} [{status}]")
                verification_results.append((table, df_count, db_count, status))
            except Exception as e:
                print(f"  - ❌ [ERROR] Failed to load table '{table}': {e}")
                verification_results.append((table, len(df_to_load), 0, "❌ FAILED"))
                
    # Print Loading Verification Summary
    print("\n" + "=" * 60)
    print("📋 DATABASE LOAD VERIFICATION SUMMARY")
    print("=" * 60)
    all_matched = True
    for table, csv_r, db_r, stat in verification_results:
        print(f"  {table.ljust(22)}: CSV = {str(csv_r).rjust(6)} | DB = {str(db_r).rjust(6)} | {stat}")
        if "MISMATCH" in stat or "FAILED" in stat:
            all_matched = False
            
    if all_matched:
        print("\n🎉 [COMPLETE] ETL Pipeline executed successfully. Database loaded and verified.")
    else:
        print("\n⚠️ [WARNING] ETL Ingestion completed with errors or mismatches. See details above.")

if __name__ == "__main__":
    main()
