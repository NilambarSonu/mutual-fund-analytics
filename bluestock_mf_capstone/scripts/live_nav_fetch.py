"""
Bluestock Mutual Fund Capstone Project - Day 1
Live NAV Fetching Script

This script fetches live NAV data from mfapi.in for 5 key schemes,
parses the JSON response into a pandas DataFrame with columns [amfi_code, date, nav],
and saves each scheme's data as a CSV file in data/raw/.
"""

import sys
from pathlib import Path
import time
import requests
import pandas as pd

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def fetch_scheme_nav(amfi_code, output_dir, max_retries=5, backoff_factor=2):
    """
    Fetches the historical and live NAV records for a given AMFI scheme code,
    processes it into a pandas DataFrame, and saves it as a CSV.
    
    Args:
        amfi_code (int): The AMFI code of the scheme to fetch.
        output_dir (Path): The pathlib directory to save the output CSV.
        max_retries (int): Maximum number of retries for connection errors.
        backoff_factor (int): Multiplier for exponential backoff sleep.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    url = f"https://api.mfapi.in/mf/{amfi_code}"
    print(f"⏳ [INFO] Fetching NAV for AMFI code {amfi_code}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=20)
            
            # Check for HTTP status errors
            response.raise_for_status()
            
            data_json = response.json()
            
            # Validate response payload structure
            if not data_json or "data" not in data_json or not data_json["data"]:
                print(f"⚠️ [WARNING] No data found for AMFI code {amfi_code} (Attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(backoff_factor ** attempt)
                    continue
                return False
                
            nav_list = data_json["data"]
            
            # Convert list of {date, nav} to DataFrame
            df = pd.DataFrame(nav_list)
            
            # Map columns to: amfi_code, date, nav
            df["amfi_code"] = amfi_code
            
            # Reorder and filter columns to match exact requirements
            df = df[["amfi_code", "date", "nav"]]
            
            # Ensure NAV is numeric
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            
            # Save to CSV
            output_file = output_dir / f"live_nav_{amfi_code}.csv"
            df.to_csv(output_file, index=False)
            
            latest_nav = df.iloc[0]["nav"]
            latest_date = df.iloc[0]["date"]
            print(f"✅ [SUCCESS] Saved {len(df)} NAV records to {output_file.name}")
            print(f"   Latest NAV: Date={latest_date}, NAV={latest_nav}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ [WARNING] Attempt {attempt}/{max_retries} failed for {amfi_code}: {e}")
            if attempt < max_retries:
                sleep_time = backoff_factor ** attempt
                print(f"   Sleeping for {sleep_time}s before retrying...")
                time.sleep(sleep_time)
            else:
                print(f"❌ [ERROR] Failed to fetch NAV for AMFI code {amfi_code} after {max_retries} attempts.")
                return False
        except Exception as e:
            print(f"❌ [ERROR] An unexpected error occurred for AMFI code {amfi_code}: {e}")
            return False
            
    return False

def main():
    """
    Main execution loop to fetch NAV for all 5 key schemes.
    """
    print("🚀 Starting Live NAV Fetcher...")
    
    # Path setup
    script_dir = Path(__file__).resolve().parent
    # Check if we are running in the scripts subfolder or workspace root
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path("bluestock_mf_capstone")
        
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 5 Key Schemes as per requirements
    schemes = {
        125497: "HDFC Top 100 Direct",
        119551: "SBI Bluechip Direct",
        120503: "ICICI Bluechip Direct",
        118632: "Nippon Large Cap Direct",
        119092: "Axis Bluechip Direct"
    }
    
    success_count = 0
    
    for amfi_code, name in schemes.items():
        print(f"\n--- Scheme: {name} ({amfi_code}) ---")
        if fetch_scheme_nav(amfi_code, raw_dir):
            success_count += 1
            
    print(f"\n📊 Run Summary: Successfully fetched {success_count}/{len(schemes)} schemes.")
    if success_count == len(schemes):
        print("✅ [COMPLETE] Live NAV fetching complete without errors.")
    else:
        print("⚠️ [WARNING] Some schemes failed to fetch.")

if __name__ == "__main__":
    main()
