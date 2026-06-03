import os
import time
import requests
import pandas as pd

def fetch_and_save_nav(scheme_code, raw_dir, max_retries=5, backoff_factor=2):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"[INFO] Fetching NAV for Scheme Code {scheme_code} from {url}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            
            data_json = response.json()
            
            # Check if we got a valid response containing data
            if not data_json or "data" not in data_json or not data_json["data"]:
                print(f"[WARNING] No data found for Scheme Code {scheme_code}")
                return False
                
            meta = data_json.get("meta", {})
            nav_list = data_json["data"]
            
            # Parse into a DataFrame
            df = pd.DataFrame(nav_list)
            # Convert nav to float
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            # Add metadata columns for context
            df["scheme_code"] = scheme_code
            df["scheme_name"] = meta.get("scheme_name", "")
            df["fund_house"] = meta.get("fund_house", "")
            df["scheme_category"] = meta.get("scheme_category", "")
            
            # Reorder columns
            columns = ["scheme_code", "scheme_name", "date", "nav", "fund_house", "scheme_category"]
            df = df[[c for c in columns if c in df.columns]]
            
            # Define output path
            output_filename = f"live_nav_{scheme_code}.csv"
            output_path = os.path.join(raw_dir, output_filename)
            
            df.to_csv(output_path, index=False)
            print(f"[SUCCESS] Saved {len(df)} NAV records for {scheme_code} to {output_path}")
            print(f"Latest NAV: Date={df.iloc[0]['date']}, NAV={df.iloc[0]['nav']}")
            return True
            
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"[WARNING] Attempt {attempt}/{max_retries} failed for {scheme_code}: {e}")
            if attempt < max_retries:
                sleep_time = backoff_factor ** attempt
                print(f"Sleeping for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            else:
                print(f"[ERROR] All {max_retries} attempts failed for Scheme Code {scheme_code}.")
                return False

def main():
    raw_dir = os.path.join("data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    # 1. HDFC Top 100 Direct (125497)
    hdfc_code = 125497
    fetch_and_save_nav(hdfc_code, raw_dir)
    
    # 2. 5 Key Schemes
    key_schemes = {
        119551: "SBI Bluechip",
        120503: "ICICI Bluechip",
        118632: "Nippon Large Cap",
        119092: "Axis Bluechip",
        120841: "Kotak Bluechip"
    }
    
    print("\n[INFO] Fetching 5 key schemes...")
    for code, name in key_schemes.items():
        print(f"\n--- Scheme: {name} ({code}) ---")
        fetch_and_save_nav(code, raw_dir)

if __name__ == "__main__":
    main()
