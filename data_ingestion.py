"""
Bluestock Mutual Fund Capstone Project - Day 1
Data Ingestion Script

This script creates the project directory structure, loads the 10 CSV datasets,
checks them for anomalies, and outputs a detailed ingestion summary report.
"""

import os
import sys
from pathlib import Path
import shutil
import pandas as pd

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def create_directory_structure():
    """
    Creates the project folder structure using pathlib.
    Returns:
        project_root (Path): Path to the project root directory
    """
    print("⏳ [INFO] Setting up project directory structure...")
    
    # Define project root
    project_root = Path("bluestock_mf_capstone")
    
    # Define directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "db",
        project_root / "notebooks",
        project_root / "scripts",
        project_root / "sql",
        project_root / "dashboard",
        project_root / "reports"
    ]
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
        
    return project_root

def copy_raw_datasets(project_root):
    """
    Copies the 10 raw CSV datasets to the project's data/raw directory.
    Args:
        project_root (Path): Path to the project root directory
    """
    source_dir = Path("data") / "raw"
    dest_dir = project_root / "data" / "raw"
    
    # If the source folder doesn't exist, we might have them in data/ (original position)
    if not source_dir.exists():
        source_dir = Path("data")
        
    print(f"⏳ [INFO] Checking for raw datasets in {source_dir}...")
    
    # Find all CSV files that match our datasets
    csv_files = [f for f in os.listdir(source_dir) if f.endswith('.csv') and f[:2].isdigit()]
    
    if not csv_files:
        print("⚠️ [WARNING] No matching CSV datasets found in source directory.")
        return
        
    for file in csv_files:
        src_file = source_dir / file
        dest_file = dest_dir / file
        
        # Avoid copying if file already exists in destination
        if not dest_file.exists():
            shutil.copy2(src_file, dest_file)
            print(f"✅ Copied {file} to {dest_dir}")
        else:
            print(f"ℹ️ File already exists in destination: {file}")

def ingest_and_analyze_datasets(project_root):
    """
    Loads all 10 CSV datasets using pandas, prints stats, and generates
    a summary ingestion report.
    Args:
        project_root (Path): Path to the project root directory
    """
    raw_dir = project_root / "data" / "raw"
    csv_files = sorted([f for f in os.listdir(raw_dir) if f.endswith('.csv') and f[:2].isdigit()])
    
    if not csv_files:
        print("❌ [ERROR] No raw CSV datasets found in data/raw for analysis.")
        return
        
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("        BLUESTOCK MUTUAL FUND CAPSTONE INGESTION SUMMARY       ")
    report_lines.append("=" * 60 + "\n")
    
    print("\n" + "=" * 60)
    print("📊 Ingesting and Analyzing Datasets")
    print("=" * 60)
    
    for file in csv_files:
        path = raw_dir / file
        name = file.split('_', 1)[1].replace('.csv', '')
        
        print(f"\n📂 Ingesting: {file}...")
        report_lines.append(f"📄 Dataset: {file}")
        report_lines.append("-" * 40)
        
        try:
            df = pd.read_csv(path)
            
            # Print Details
            print(f"  Shape: {df.shape}")
            report_lines.append(f"Shape: {df.shape}")
            
            print("\n  Data Types:")
            print(df.dtypes)
            report_lines.append("\nData Types:")
            for col, dtype in df.dtypes.items():
                report_lines.append(f"  - {col}: {dtype}")
                
            print("\n  Head(3):")
            print(df.head(3))
            report_lines.append("\nHead(3):")
            report_lines.append(df.head(3).to_string())
            
            print("\n  Null Value Counts:")
            print(df.isnull().sum())
            report_lines.append("\nNull Value Counts:")
            for col, null_count in df.isnull().sum().items():
                report_lines.append(f"  - {col}: {null_count}")
                
            # Check Anomalies
            anomalies = []
            
            # Check Null values in important columns
            null_cols = df.isnull().sum()
            null_cols = null_cols[null_cols > 0]
            if not null_cols.empty:
                for col, val in null_cols.items():
                    # Check if yoy_growth_pct is the null column in sip inflow
                    if 'sip_inflow' in name and col == 'yoy_growth_pct':
                        anomalies.append(f"⚠️ Note: {val} null values in yoy_growth_pct (expected for the first 12 months).")
                    else:
                        anomalies.append(f"⚠️ Warning: {val} missing values in '{col}'.")
                        
            # Check Duplicates
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                anomalies.append(f"❌ Error: {dup_count} duplicate rows detected.")
                
            # Numeric columns sign check
            if 'nav' in df.columns:
                neg_nav = df[df['nav'] <= 0]
                if not neg_nav.empty:
                    anomalies.append(f"❌ Error: {len(neg_nav)} records have negative or zero NAV.")
            if 'amount' in df.columns:
                neg_amt = df[df['amount'] < 0]
                if not neg_amt.empty:
                    anomalies.append(f"❌ Error: {len(neg_amt)} records have negative amount values.")
            if 'units' in df.columns:
                neg_units = df[df['units'] < 0]
                if not neg_units.empty:
                    anomalies.append(f"❌ Error: {len(neg_units)} records have negative units values.")
            if 'aum_crore' in df.columns:
                neg_aum = df[df['aum_crore'] < 0]
                if not neg_aum.empty:
                    anomalies.append(f"❌ Error: {len(neg_aum)} records have negative AUM.")
                    
            print("\n  Anomalies Found:")
            report_lines.append("\nAnomalies Found:")
            if anomalies:
                for anomaly in anomalies:
                    print(f"  {anomaly}")
                    report_lines.append(f"  {anomaly}")
            else:
                print("  ✅ No anomalies detected.")
                report_lines.append("  ✅ No anomalies detected.")
                
            print("-" * 50)
            report_lines.append("\n" + "=" * 50 + "\n")
            
        except Exception as e:
            err_msg = f"❌ [ERROR] Failed to ingest {file}: {e}"
            print(err_msg)
            report_lines.append(err_msg)
            report_lines.append("\n" + "=" * 50 + "\n")
            
    # Save Report
    summary_path = raw_dir / "ingestion_summary.txt"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"\n✅ Summary report saved to {summary_path}")
    except Exception as e:
        print(f"❌ Failed to save summary report: {e}")

def main():
    """
    Main function to run project setup and data ingestion.
    """
    print("🚀 Running data ingestion pipeline...")
    try:
        project_root = create_directory_structure()
        copy_raw_datasets(project_root)
        ingest_and_analyze_datasets(project_root)
        print("\n✅ Ingestion pipeline run completed successfully.")
    except Exception as e:
        print(f"❌ Critical error in ingestion pipeline: {e}")

if __name__ == "__main__":
    main()
