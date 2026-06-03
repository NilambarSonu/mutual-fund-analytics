"""
Bluestock Mutual Fund Capstone Project - Day 1
AMFI Code Validation Script

This script validates that all scheme AMFI codes listed in the fund master database
exist with corresponding NAV records in the historical NAV database. It prints a data
quality report and saves the result as a text file in data/raw/.
"""

import sys
from pathlib import Path
import pandas as pd

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def validate_codes(project_root):
    """
    Validates that every amfi_code in the fund master exists in the NAV history.
    Saves a report to data/raw/data_quality_report.txt.
    
    Args:
        project_root (Path): The pathlib Path to the project root.
    """
    raw_dir = project_root / "data" / "raw"
    
    # Locate Fund Master CSV
    fm_path = raw_dir / "01_fund_master.csv"
    if not fm_path.exists():
        fm_path = raw_dir / "fund_master.csv"
        
    # Locate NAV History CSV
    nav_path = raw_dir / "02_nav_history.csv"
    if not nav_path.exists():
        nav_path = raw_dir / "nav_history.csv"
        
    # Handle missing files gracefully
    if not fm_path.exists():
        print(f"❌ [ERROR] Fund master dataset not found at {fm_path}")
        return False
    if not nav_path.exists():
        print(f"❌ [ERROR] NAV history dataset not found at {nav_path}")
        return False
        
    print(f"📂 [INFO] Loading datasets for validation...")
    print(f"   - Fund Master: {fm_path.name}")
    print(f"   - NAV History: {nav_path.name}")
    
    try:
        df_fm = pd.read_csv(fm_path)
        df_nav = pd.read_csv(nav_path)
        
        # Verify columns exist
        fm_code_col = [c for c in df_fm.columns if 'code' in c.lower() or 'amfi' in c.lower()]
        nav_code_col = [c for c in df_nav.columns if 'code' in c.lower() or 'amfi' in c.lower()]
        
        if not fm_code_col:
            print("❌ [ERROR] Could not identify AMFI code column in Fund Master.")
            return False
        if not nav_code_col:
            print("❌ [ERROR] Could not identify AMFI code column in NAV History.")
            return False
            
        fm_col = fm_code_col[0]
        nav_col = nav_code_col[0]
        
        # Extract unique codes
        fm_codes = set(df_fm[fm_col].dropna().unique())
        nav_codes = set(df_nav[nav_col].dropna().unique())
        
        # Check mismatches
        missing_in_nav = fm_codes - nav_codes
        extra_in_nav = nav_codes - fm_codes
        
        # Generate report content
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("             DATA QUALITY & AMFI CODE VALIDATION REPORT         ")
        report_lines.append("=" * 60 + "\n")
        
        report_lines.append(f"Source Files:")
        report_lines.append(f"  - Fund Master: {fm_path}")
        report_lines.append(f"  - NAV History: {nav_path}\n")
        
        report_lines.append(f"Analysis:")
        report_lines.append(f"  - Total unique AMFI codes in Fund Master: {len(fm_codes)}")
        report_lines.append(f"  - Total unique AMFI codes in NAV History: {len(nav_codes)}\n")
        
        # Validation checks
        mismatches_found = False
        
        print("\n" + "=" * 60)
        print("🔍 Running AMFI Validation Checks...")
        print("=" * 60)
        
        if len(missing_in_nav) == 0:
            msg_success = "✅ [SUCCESS] All AMFI codes in Fund Master exist in NAV History."
            print(msg_success)
            report_lines.append(msg_success)
        else:
            mismatches_found = True
            msg_warn = f"⚠️ [WARNING] {len(missing_in_nav)} codes in Fund Master are MISSING from NAV History!"
            print(msg_warn)
            report_lines.append(msg_warn)
            print(f"Missing codes: {list(missing_in_nav)}")
            report_lines.append(f"Missing codes: {list(missing_in_nav)}")
            
        if len(extra_in_nav) > 0:
            msg_extra = f"ℹ️ [INFO] There are {len(extra_in_nav)} codes in NAV History that are NOT in Fund Master."
            print(msg_extra)
            report_lines.append(msg_extra)
            
        # Duplicate checks in fund master
        duplicates = df_fm[df_fm[fm_col].duplicated()]
        if not duplicates.empty:
            msg_dup = f"❌ [ERROR] Duplicate AMFI codes found in Fund Master: {list(duplicates[fm_col].unique())}"
            print(msg_dup)
            report_lines.append(msg_dup)
            mismatches_found = True
        else:
            msg_dup_ok = "✅ [SUCCESS] No duplicate AMFI codes found in Fund Master."
            print(msg_dup_ok)
            report_lines.append(msg_dup_ok)
            
        # Save Report
        report_path = raw_dir / "data_quality_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
            
        print(f"\n💾 Data quality report saved as: {report_path}")
        return not mismatches_found
        
    except Exception as e:
        print(f"❌ [ERROR] Exception occurred during AMFI validation: {e}")
        return False

def main():
    """
    Main function to execute AMFI code validation.
    """
    script_dir = Path(__file__).resolve().parent
    # Setup project root relative to execution location
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path("bluestock_mf_capstone")
        
    validate_codes(project_root)

if __name__ == "__main__":
    main()
