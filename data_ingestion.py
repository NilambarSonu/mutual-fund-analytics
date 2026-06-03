import os
import pandas as pd
import numpy as np

def explore_csv_files(raw_dir):
    print("=" * 60)
    print("       STEP 1: LOADING AND EXPLORING 10 CSV DATASETS       ")
    print("=" * 60)
    
    csv_files = sorted([f for f in os.listdir(raw_dir) if f.endswith('.csv') and f[:2].isdigit()])
    
    datasets = {}
    for file in csv_files:
        name = file.split('_', 1)[1].replace('.csv', '')
        path = os.path.join(raw_dir, file)
        print(f"\n[INFO] Loading {file} (dataset: {name})...")
        try:
            df = pd.read_csv(path)
            datasets[name] = df
            print(f"Shape: {df.shape}")
            print("\nDtypes:")
            print(df.dtypes)
            print("\nFirst 3 rows:")
            print(df.head(3))
            print("-" * 50)
        except Exception as e:
            print(f"[ERROR] Failed to load {file}: {e}")
            
    return datasets

def check_anomalies(datasets):
    print("\n" + "=" * 60)
    print("                 STEP 2: ANOMALY DETECTION                 ")
    print("=" * 60)
    
    for name, df in datasets.items():
        print(f"\n--- Anomalies in {name} ---")
        
        # Check for Null Values
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if not null_cols.empty:
            print("Missing values detected:")
            for col, val in null_cols.items():
                print(f"  - {col}: {val} missing ({val/len(df)*100:.2f}%)")
        else:
            print("No missing values.")
            
        # Check for Duplicates
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            print(f"Duplicate rows detected: {duplicate_count}")
        else:
            print("No duplicate rows.")
            
        # Check specific anomalies per dataset if applicable
        if 'nav_history' in name:
            if 'nav' in df.columns:
                neg_nav = df[df['nav'] <= 0]
                if not neg_nav.empty:
                    print(f"Non-positive NAV values detected: {len(neg_nav)}")
                    print(neg_nav.head(3))
        if 'investor_transactions' in name:
            if 'amount' in df.columns:
                neg_amt = df[df['amount'] < 0]
                if not neg_amt.empty:
                    print(f"Negative transaction amounts detected: {len(neg_amt)}")
            if 'units' in df.columns:
                neg_units = df[df['units'] < 0]
                if not neg_units.empty:
                    print(f"Negative transaction units detected: {len(neg_units)}")

def explore_fund_master(datasets):
    print("\n" + "=" * 60)
    print("               STEP 3: FUND MASTER EXPLORATION             ")
    print("=" * 60)
    
    # Locate fund_master
    df_fm = None
    for name, df in datasets.items():
        if 'fund_master' in name:
            df_fm = df
            break
            
    if df_fm is None:
        print("[ERROR] Fund master dataset not found among loaded datasets.")
        return
        
    cols = df_fm.columns
    print(f"Fund Master Columns: {list(cols)}")
    
    # Print uniques for fund houses, categories, sub-categories, risk grades
    # Let's inspect column names dynamically or assume standard ones
    house_col = [c for c in cols if 'house' in c.lower() or 'amc' in c.lower() or 'fund_house' in c.lower()][0]
    cat_col = [c for c in cols if 'category' in c.lower() and 'sub' not in c.lower()][0]
    subcat_col = [c for c in cols if 'sub_category' in c.lower() or 'subcategory' in c.lower()][0]
    risk_col = [c for c in cols if 'risk' in c.lower()][0]
    
    print(f"\nUnique Fund Houses ({df_fm[house_col].nunique()}):")
    print(df_fm[house_col].unique())
    
    print(f"\nUnique Categories ({df_fm[cat_col].nunique()}):")
    print(df_fm[cat_col].unique())
    
    print(f"\nUnique Sub-Categories ({df_fm[subcat_col].nunique()}):")
    print(df_fm[subcat_col].unique())
    
    print(f"\nUnique Risk Grades ({df_fm[risk_col].nunique()}):")
    print(df_fm[risk_col].unique())

def validate_amfi_codes(datasets):
    print("\n" + "=" * 60)
    print("                STEP 4: AMFI CODE VALIDATION               ")
    print("=" * 60)
    
    df_fm = None
    df_nav = None
    
    for name, df in datasets.items():
        if 'fund_master' in name:
            df_fm = df
        elif 'nav_history' in name:
            df_nav = df
            
    if df_fm is None or df_nav is None:
        print("[ERROR] Could not find both fund_master and nav_history datasets.")
        return
        
    # Find AMFI code columns (scheme_code or amfi_code or code)
    fm_code_col = [c for c in df_fm.columns if 'code' in c.lower() or 'amfi' in c.lower()][0]
    nav_code_col = [c for c in df_nav.columns if 'code' in c.lower() or 'amfi' in c.lower()][0]
    
    print(f"Fund Master AMFI column: '{fm_code_col}'")
    print(f"NAV History AMFI column: '{nav_code_col}'")
    
    fm_codes = set(df_fm[fm_code_col].dropna().unique())
    nav_codes = set(df_nav[nav_code_col].dropna().unique())
    
    print(f"Total unique AMFI codes in Fund Master: {len(fm_codes)}")
    print(f"Total unique AMFI codes in NAV History: {len(nav_codes)}")
    
    # Confirm every code in fund_master exists in nav_history
    missing_in_nav = fm_codes - nav_codes
    if len(missing_in_nav) == 0:
        print("\n[SUCCESS] Verification complete: Every AMFI code in fund_master exists in nav_history.")
    else:
        print(f"\n[WARNING] Data Quality Issue: {len(missing_in_nav)} codes in fund_master are MISSING from nav_history!")
        print(f"Missing codes: {list(missing_in_nav)[:10]}...")
        
    extra_in_nav = nav_codes - fm_codes
    if len(extra_in_nav) > 0:
        print(f"[INFO] There are {len(extra_in_nav)} codes in nav_history that are NOT in fund_master.")
        print(f"Sample extra codes: {list(extra_in_nav)[:10]}...")
        
    # Data quality summary
    print("\n--- Data Quality Summary ---")
    total_mismatch = len(missing_in_nav) + len(extra_in_nav)
    print(f"Fund Master codes matched in NAV history: {len(fm_codes - missing_in_nav)} / {len(fm_codes)} ({len(fm_codes - missing_in_nav)/len(fm_codes)*100:.2f}%)")
    print(f"Any duplicate scheme_codes in Fund Master: {df_fm[fm_code_col].duplicated().any()}")

if __name__ == "__main__":
    raw_dir = os.path.join("data", "raw")
    datasets = explore_csv_files(raw_dir)
    check_anomalies(datasets)
    explore_fund_master(datasets)
    validate_amfi_codes(datasets)
