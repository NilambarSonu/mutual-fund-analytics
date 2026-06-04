"""
Bluestock Mutual Fund Capstone Project - Day 4
Fund Performance Analytics Execution Script (run_performance.py)

This script performs advanced fund performance calculations on the 40 mutual fund schemes:
1. Daily Returns.
2. CAGR (1yr, 3yr, 5yr/max available history).
3. Sharpe Ratio (Rf = 6.5% annually).
4. Sortino Ratio (downside deviation based on negative daily returns).
5. Alpha and Beta via OLS regression on Nifty 100 returns.
6. Maximum Drawdowns (worst peak-to-trough date ranges).
7. Fund Scorecard (0-100) based on weighted percentile ranks of performance metrics.
8. Visual comparison plot of cumulative returns for the Top 5 funds vs Nifty 50 and Nifty 100 over 3 years.
9. Annualized Tracking Errors for the Top 5 funds.
"""

import sys
import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Set plotting style
sns.set_theme(style="whitegrid")
plt.rcParams["font.size"] = 11
plt.rcParams["figure.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12

def setup_paths():
    """
    Sets up and verifies the project directories.
    Returns:
        project_root (Path): Path to the project root directory
    """
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path(".")
        
    db_path = project_root / "data" / "db" / "bluestock_mf.db"
    processed_dir = project_root / "data" / "processed"
    charts_dir = project_root / "reports" / "charts"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    return project_root, db_path, processed_dir, charts_dir

def get_closest_nav(df, target_date):
    """
    Finds the NAV value and the closest date in the DataFrame matching the target date.
    df must have datetime index and 'nav' column.
    """
    target_date = pd.to_datetime(target_date)
    if target_date in df.index:
        return df.loc[target_date, 'nav'], target_date
        
    # Get index of the closest date
    idx = df.index.get_indexer([target_date], method='nearest')[0]
    closest_date = df.index[idx]
    return df.loc[closest_date, 'nav'], closest_date

def calculate_cagr(nav_end, nav_start, years):
    """
    Computes Compound Annual Growth Rate.
    """
    if nav_start <= 0 or nav_end <= 0 or years <= 0:
        return 0.0
    return (nav_end / nav_start) ** (1.0 / years) - 1.0

def main():
    print("🚀 Starting Fund Performance Analytics Pipeline...")
    project_root, db_path, processed_dir, charts_dir = setup_paths()
    
    if not db_path.exists():
        print(f"❌ [ERROR] Database not found at {db_path}. Please run etl_pipeline.py first.")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    
    # 1. Load Dimension and Fact Data
    print("📂 [INFO] Loading tables from SQLite...")
    df_funds = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    df_nav_all = pd.read_sql_query("SELECT * FROM fact_nav", conn)
    df_bench_all = pd.read_sql_query("SELECT * FROM benchmark_indices", conn)
    
    # Convert date columns to datetime
    df_nav_all["date"] = pd.to_datetime(df_nav_all["date"])
    df_bench_all["date"] = pd.to_datetime(df_bench_all["date"])
    
    print(f"   - Funds count: {len(df_funds)}")
    print(f"   - NAV records count: {len(df_nav_all)}")
    print(f"   - Benchmark prices count: {len(df_bench_all)}")
    
    # Extract benchmark daily returns for regression
    print("📈 [INFO] Calculating benchmark daily returns...")
    nifty100_prices = df_bench_all[df_bench_all["index_name"] == "NIFTY100"].sort_values("date").copy()
    nifty100_prices.set_index("date", inplace=True)
    nifty100_prices["daily_return"] = nifty100_prices["close_value"].pct_change()
    
    nifty50_prices = df_bench_all[df_bench_all["index_name"] == "NIFTY50"].sort_values("date").copy()
    nifty50_prices.set_index("date", inplace=True)
    nifty50_prices["daily_return"] = nifty50_prices["close_value"].pct_change()
    
    # Risk-free rate setup
    rf_annual = 0.065 # 6.5% annual rate
    rf_daily = rf_annual / 252.0
    
    # Results dictionary list
    results = []
    
    # Create empty dict to store aligned returns for joint statistical analysis
    daily_returns_dict = {}
    
    print("\n📊 [INFO] Computing performance metrics for all 40 schemes...")
    for idx, fund_row in df_funds.iterrows():
        code = fund_row["amfi_code"]
        name = fund_row["scheme_name"]
        expense_ratio = fund_row["expense_ratio_pct"]
        
        # Filter NAV data for this fund
        df_nav = df_nav_all[df_nav_all["amfi_code"] == code].sort_values("date").copy()
        df_nav.set_index("date", inplace=True)
        
        if df_nav.empty or len(df_nav) < 2:
            print(f"⚠️ [WARNING] Insufficient data for fund {name} ({code})")
            continue
            
        # Calculate daily returns
        df_nav["daily_return"] = df_nav["nav"].pct_change()
        
        # Save daily return series to dict
        daily_returns_dict[code] = df_nav["daily_return"]
        
        # Dates bounding
        latest_date = df_nav.index.max()
        earliest_date = df_nav.index.min()
        
        # Fetch NAV details for CAGR calculations
        nav_latest = df_nav.loc[latest_date, "nav"]
        
        # CAGR 1 Year
        date_1yr_ago = latest_date - pd.DateOffset(years=1)
        nav_1yr_ago, actual_date_1yr = get_closest_nav(df_nav, date_1yr_ago)
        years_1yr = (latest_date - actual_date_1yr).days / 365.25
        cagr_1yr = calculate_cagr(nav_latest, nav_1yr_ago, years_1yr)
        
        # CAGR 3 Year
        date_3yr_ago = latest_date - pd.DateOffset(years=3)
        nav_3yr_ago, actual_date_3yr = get_closest_nav(df_nav, date_3yr_ago)
        years_3yr = (latest_date - actual_date_3yr).days / 365.25
        cagr_3yr = calculate_cagr(nav_latest, nav_3yr_ago, years_3yr)
        
        # CAGR 5 Year (Max available history since Jan 2022)
        nav_earliest = df_nav.loc[earliest_date, "nav"]
        years_max = (latest_date - earliest_date).days / 365.25
        cagr_5yr = calculate_cagr(nav_latest, nav_earliest, years_max)
        
        # Sharpe and Sortino Ratios (based on daily return series)
        returns_clean = df_nav["daily_return"].dropna()
        mean_return = returns_clean.mean()
        std_return = returns_clean.std()
        
        # Sharpe Ratio
        if std_return > 0:
            sharpe_ratio = ((mean_return - rf_daily) / std_return) * np.sqrt(252.0)
        else:
            sharpe_ratio = 0.0
            
        # Sortino Ratio
        downside_returns = returns_clean[returns_clean < 0.0]
        if len(downside_returns) > 1:
            downside_std = downside_returns.std()
            sortino_ratio = ((mean_return - rf_daily) / downside_std) * np.sqrt(252.0)
        else:
            sortino_ratio = 0.0
            
        # Alpha and Beta via OLS Regression on NIFTY100
        # Align series on date
        aligned_df = pd.DataFrame({
            "fund": returns_clean,
            "nifty100": nifty100_prices["daily_return"]
        }).dropna()
        
        if len(aligned_df) > 10:
            slope, intercept, r_value, p_value, std_err = stats.linregress(aligned_df["nifty100"], aligned_df["fund"])
            beta = slope
            alpha = intercept * 252.0 # Annualized
        else:
            beta = 0.0
            alpha = 0.0
            
        # Maximum Drawdown and Worst Drawdown Date Range
        df_nav["running_max"] = df_nav["nav"].cummax()
        df_nav["drawdown"] = df_nav["nav"] / df_nav["running_max"] - 1.0
        max_dd = df_nav["drawdown"].min()
        
        # worst trough date
        trough_date = df_nav["drawdown"].idxmin()
        # peak date leading to the trough
        peak_date = df_nav.loc[:trough_date, "nav"].idxmax()
        
        # Save metrics
        results.append({
            "amfi_code": code,
            "scheme_name": name,
            "fund_house": fund_row["fund_house"],
            "category": fund_row["category"],
            "sub_category": fund_row["sub_category"],
            "expense_ratio_pct": expense_ratio,
            "cagr_1yr_pct": cagr_1yr * 100.0,
            "cagr_3yr_pct": cagr_3yr * 100.0,
            "cagr_5yr_pct": cagr_5yr * 100.0, # max available history (~4.4 years)
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "alpha_pct": alpha * 100.0,
            "beta": beta,
            "max_drawdown_pct": max_dd * 100.0,
            "worst_dd_start": peak_date.strftime("%Y-%m-%d"),
            "worst_dd_end": trough_date.strftime("%Y-%m-%d")
        })

    # Convert results list to DataFrame
    df_metrics = pd.DataFrame(results)
    
    # 2. Scorecard Ranking Calculation
    print("📈 [INFO] Calculating percentile ranks and composite scorecard...")
    # Higher is better: cagr_3yr, sharpe_ratio, alpha_pct, max_drawdown_pct (since it's negative, -10% > -30%)
    # Lower is better: expense_ratio_pct
    df_metrics["rank_3yr"] = df_metrics["cagr_3yr_pct"].rank(pct=True) * 100.0
    df_metrics["rank_sharpe"] = df_metrics["sharpe_ratio"].rank(pct=True) * 100.0
    df_metrics["rank_alpha"] = df_metrics["alpha_pct"].rank(pct=True) * 100.0
    df_metrics["rank_expense"] = (-df_metrics["expense_ratio_pct"]).rank(pct=True) * 100.0
    df_metrics["rank_max_dd"] = df_metrics["max_drawdown_pct"].rank(pct=True) * 100.0
    
    # Composite Scorecard (0-100)
    df_metrics["scorecard"] = (
        0.30 * df_metrics["rank_3yr"] +
        0.25 * df_metrics["rank_sharpe"] +
        0.20 * df_metrics["rank_alpha"] +
        0.15 * df_metrics["rank_expense"] +
        0.10 * df_metrics["rank_max_dd"]
    )
    
    # Round metrics for presentation
    df_metrics["scorecard"] = df_metrics["scorecard"].round(2)
    
    # Sort by scorecard descending
    df_metrics = df_metrics.sort_values("scorecard", ascending=False)
    
    # 3. Export CSV files
    # Deliverable 1: fund_scorecard.csv
    scorecard_cols = [
        "amfi_code", "scheme_name", "fund_house", "category", "sub_category",
        "expense_ratio_pct", "cagr_1yr_pct", "cagr_3yr_pct", "cagr_5yr_pct",
        "sharpe_ratio", "sortino_ratio", "max_drawdown_pct", "worst_dd_start", "worst_dd_end", "scorecard"
    ]
    df_scorecard_export = df_metrics[scorecard_cols].copy()
    
    # Save scorecard to root and processed
    df_scorecard_export.to_csv(project_root / "fund_scorecard.csv", index=False)
    df_scorecard_export.to_csv(processed_dir / "fund_scorecard.csv", index=False)
    print(f"💾 Exported fund_scorecard.csv to root and processed/ ({len(df_scorecard_export)} schemes)")
    
    # Deliverable 2: alpha_beta.csv
    alpha_beta_cols = ["amfi_code", "scheme_name", "fund_house", "alpha_pct", "beta"]
    df_ab_export = df_metrics[alpha_beta_cols].copy()
    df_ab_export.to_csv(project_root / "alpha_beta.csv", index=False)
    df_ab_export.to_csv(processed_dir / "alpha_beta.csv", index=False)
    print(f"💾 Exported alpha_beta.csv to root and processed/ ({len(df_ab_export)} schemes)")
    
    # 4. Identify Top 5 Schemes
    top_5_schemes = df_metrics.head(5).copy()
    print("\n🏆 Top 5 Schemes by Scorecard Score:")
    for rank_idx, (idx, row) in enumerate(top_5_schemes.iterrows(), 1):
        print(f"   {rank_idx}. {row['scheme_name']} ({row['amfi_code']}) - Score: {row['scorecard']}")
        
    # 5. Benchmark Comparison Chart over 3 years
    print("\n📈 [INFO] Plotting 3-year cumulative returns comparison chart...")
    
    # Define 3-year date range for plotting (from 2023-05-29 to 2026-05-29)
    # Get the global max date across fact_nav
    max_nav_date = df_nav_all["date"].max()
    start_3yr_date = max_nav_date - pd.DateOffset(years=3)
    
    # Create matplotlib plot
    plt.figure(figsize=(14, 7))
    
    # Align Nifty 50 and Nifty 100 for cumulative return plotting
    df_n50_3yr = nifty50_prices.loc[start_3yr_date:max_nav_date].sort_index().copy()
    n50_start_val = df_n50_3yr.iloc[0]["close_value"]
    df_n50_3yr["cum_return"] = (df_n50_3yr["close_value"] / n50_start_val - 1.0) * 100.0
    
    df_n100_3yr = nifty100_prices.loc[start_3yr_date:max_nav_date].sort_index().copy()
    n100_start_val = df_n100_3yr.iloc[0]["close_value"]
    df_n100_3yr["cum_return"] = (df_n100_3yr["close_value"] / n100_start_val - 1.0) * 100.0
    
    # Plot benchmarks
    plt.plot(df_n50_3yr.index, df_n50_3yr["cum_return"], label="NIFTY 50", color="black", linestyle="--", linewidth=2.5)
    plt.plot(df_n100_3yr.index, df_n100_3yr["cum_return"], label="NIFTY 100 (Benchmark)", color="dimgray", linestyle=":", linewidth=2.5)
    
    tracking_errors_n50 = []
    tracking_errors_n100 = []
    
    # Plot top 5 funds
    for rank_idx, (idx, row) in enumerate(top_5_schemes.iterrows(), 1):
        code = row["amfi_code"]
        name_short = row["scheme_name"].split(" - ")[0]
        
        df_fund_nav = df_nav_all[(df_nav_all["amfi_code"] == code) & (df_nav_all["date"] >= start_3yr_date)].sort_values("date").copy()
        df_fund_nav.set_index("date", inplace=True)
        
        fund_start_val = df_fund_nav.iloc[0]["nav"]
        df_fund_nav["cum_return"] = (df_fund_nav["nav"] / fund_start_val - 1.0) * 100.0
        
        # Plot
        plt.plot(df_fund_nav.index, df_fund_nav["cum_return"], label=f"{rank_idx}. {name_short}", linewidth=2.0)
        
        # Calculate daily returns for tracking error over the 3-year period
        df_fund_nav["daily_return"] = df_fund_nav["nav"].pct_change()
        
        # Merge returns with benchmarks to compute tracking error
        df_te_align = pd.DataFrame({
            "fund": df_fund_nav["daily_return"],
            "nifty50": nifty50_prices["daily_return"],
            "nifty100": nifty100_prices["daily_return"]
        }).loc[start_3yr_date:max_nav_date].dropna()
        
        te_n50 = (df_te_align["fund"] - df_te_align["nifty50"]).std() * np.sqrt(252.0) * 100.0
        te_n100 = (df_te_align["fund"] - df_te_align["nifty100"]).std() * np.sqrt(252.0) * 100.0
        
        tracking_errors_n50.append({"amfi_code": code, "scheme_name": row["scheme_name"], "tracking_error_nifty50_pct": te_n50})
        tracking_errors_n100.append({"amfi_code": code, "scheme_name": row["scheme_name"], "tracking_error_nifty100_pct": te_n100})
        
    plt.title("3-Year Cumulative Returns Comparison: Top 5 Funds vs Benchmarks (2023-2026)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Date", fontsize=11, labelpad=10)
    plt.ylabel("Cumulative Returns (%)", fontsize=11, labelpad=10)
    plt.legend(loc="upper left", frameon=True, fontsize=10)
    plt.tight_layout()
    
    # Save chart
    plt.savefig(project_root / "benchmark_comparison_chart.PNG", dpi=150)
    plt.savefig(charts_dir / "benchmark_comparison_chart.PNG", dpi=150)
    plt.close()
    print("💾 Saved benchmark_comparison_chart.PNG to root and reports/charts/")
    
    # Print Tracking Errors
    print("\n📉 Annualized Tracking Errors for Top 5 Schemes (Last 3 Years):")
    df_te_n50 = pd.DataFrame(tracking_errors_n50)
    df_te_n100 = pd.DataFrame(tracking_errors_n100)
    
    for idx, row in df_te_n100.iterrows():
        print(f"   - {row['scheme_name']}:")
        print(f"     Tracking Error (vs NIFTY 100): {row['tracking_error_nifty100_pct']:.2f}%")
        print(f"     Tracking Error (vs NIFTY 50) : {df_te_n50.iloc[idx]['tracking_error_nifty50_pct']:.2f}%")
        
    # Close connection
    conn.close()
    print("\n🎉 [COMPLETE] Fund Performance Analytics pipeline executed successfully.")

if __name__ == "__main__":
    main()
