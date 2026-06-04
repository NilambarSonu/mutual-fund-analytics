"""
Bluestock Mutual Fund Capstone Project - Day 3
EDA Visualisations Export Script (run_eda.py)

This script performs the EDA analysis programmatically, generating and saving
16 distinct analytical charts as PNG images in reports/charts/.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

# Reconfigure stdout to use UTF-8 to prevent emoji print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Set plotting style
sns.set_theme(style="whitegrid")
plt.rcParams["font.size"] = 11
plt.rcParams["figure.titlesize"] = 15
plt.rcParams["axes.labelsize"] = 12

def setup_directories():
    """
    Initialises and returns project directory paths.
    """
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "scripts":
        project_root = script_dir.parent
    else:
        project_root = Path(".")
        
    charts_dir = project_root / "reports" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    return project_root, charts_dir

def main():
    print("🚀 Starting programmatically rendering and exporting 16 EDA charts...")
    project_root, charts_dir = setup_directories()
    
    processed_dir = project_root / "data" / "processed"
    db_path = project_root / "data" / "db" / "bluestock_mf.db"
    
    # Check if processed datasets exist
    if not processed_dir.exists():
        print(f"❌ [ERROR] Processed datasets directory not found at {processed_dir}")
        sys.exit(1)
        
    # Connect to SQLite for querying
    conn = sqlite3.connect(db_path)
    
    print("\n📈 [INFO] Loading processed datasets...")
    
    # Load dataframes
    df_fund = pd.read_csv(processed_dir / "01_fund_master.csv")
    df_nav = pd.read_csv(processed_dir / "02_nav_history.csv")
    df_aum = pd.read_csv(processed_dir / "03_aum_by_fund_house.csv")
    df_sip = pd.read_csv(processed_dir / "04_monthly_sip_inflows.csv")
    df_cat_inflow = pd.read_csv(processed_dir / "05_category_inflows.csv")
    df_folios = pd.read_csv(processed_dir / "06_industry_folio_count.csv")
    df_perf = pd.read_csv(processed_dir / "07_scheme_performance.csv")
    df_tx = pd.read_csv(processed_dir / "08_investor_transactions.csv")
    df_holdings = pd.read_csv(processed_dir / "09_portfolio_holdings.csv")
    df_bench = pd.read_csv(processed_dir / "10_benchmark_indices.csv")
    df_date = pd.read_csv(processed_dir / "dim_date.csv")
    
    print("✅ All datasets loaded successfully.")
    
    # -------------------------------------------------------------
    # CHART 1: NAV Trend Analysis (2022-2026)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 1: nav_trends.png...")
    plt.figure(figsize=(14, 7))
    df_nav["date"] = pd.to_datetime(df_nav["date"])
    
    # Plot top 5 funds by AUM to keep static chart readable
    top_5_codes = df_perf.sort_values(by="aum_crore", ascending=False).head(5)["amfi_code"].tolist()
    
    for code in top_5_codes:
        scheme_name = df_fund[df_fund["amfi_code"] == code]["scheme_name"].values[0]
        fund_data = df_nav[df_nav["amfi_code"] == code].sort_values(by="date")
        plt.plot(fund_data["date"], fund_data["nav"], label=scheme_name, linewidth=2)
        
    # Shading 2023 Bull Run: April 2023 to Dec 2023
    plt.axvspan(pd.Timestamp("2023-04-01"), pd.Timestamp("2023-12-31"), color="green", alpha=0.1, label="2023 Bull Run")
    # Shading 2024 Market Corrections: Jan 2024 to June 2024
    plt.axvspan(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-30"), color="red", alpha=0.1, label="2024 Correction")
    
    plt.title("Daily NAV Trends for Top 5 Mutual Fund Schemes (2022-2026)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Date", fontsize=11, labelpad=10)
    plt.ylabel("Net Asset Value (NAV) in INR", fontsize=11, labelpad=10)
    plt.legend(loc="upper left", frameon=True, fontsize=9)
    plt.tight_layout()
    plt.savefig(charts_dir / "nav_trends.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 2: AUM Growth Grouped Bar (2022-2025)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 2: aum_growth.png...")
    plt.figure(figsize=(14, 7))
    df_aum["date"] = pd.to_datetime(df_aum["date"])
    df_aum["year"] = df_aum["date"].dt.year
    
    # Group by year and fund house, sum aum_crore
    df_aum_year = df_aum.groupby(["year", "fund_house"])["aum_crore"].mean().reset_index()
    # Convert AUM to Lakh Crores (AUM Crore / 100000)
    df_aum_year["aum_lakh_crores"] = df_aum_year["aum_crore"] / 100000.0
    
    ax = sns.barplot(data=df_aum_year, x="year", y="aum_lakh_crores", hue="fund_house", palette="tab20")
    
    # Highlight SBI at 12.5L Cr dominance
    # Draw arrow pointing to SBI in 2025
    # Let's find SBI's AUM in 2025:
    sbi_2025_row = df_aum_year[(df_aum_year["year"] == 2025) & (df_aum_year["fund_house"] == "SBI Mutual Fund")]
    if not sbi_2025_row.empty:
        sbi_aum = sbi_2025_row["aum_lakh_crores"].values[0]
        ax.annotate(f"SBI Dominance: {sbi_aum:.2f}L Cr", 
                    xy=(3.05, sbi_aum), # index of 2025 on x-axis is 3
                    xytext=(1.8, 11),
                    arrowprops=dict(facecolor="navy", shrink=0.05, width=1.5, headwidth=6))
                    
    plt.title("Mutual Fund House (AMC) Average Quarterly AUM Growth (2022-2025)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Year", fontsize=11, labelpad=10)
    plt.ylabel("Asset Under Management (AUM) in Lakh Crores INR", fontsize=11, labelpad=10)
    plt.legend(title="Fund House", bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(charts_dir / "aum_growth.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 3: SIP Inflow Time-Series
    # -------------------------------------------------------------
    print("🎨 Generating Chart 3: sip_inflows.png...")
    plt.figure(figsize=(14, 6))
    
    # Sort by month
    df_sip = df_sip.sort_values(by="month")
    
    plt.plot(df_sip["month"], df_sip["sip_inflow_crore"], marker="o", color="blue", linewidth=2, label="SIP Inflow")
    
    # Find all-time high in Dec 2025
    dec_2025 = df_sip[df_sip["month"] == "2025-12"]
    if not dec_2025.empty:
        ath_val = dec_2025["sip_inflow_crore"].values[0]
        # x index is len(df_sip) - 1 since we sorted
        x_idx = list(df_sip["month"]).index("2025-12")
        plt.annotate(f"ATH Dec 2025: ₹{ath_val:,.0f} Cr",
                     xy=(x_idx, ath_val),
                     xytext=(x_idx - 10, ath_val - 4000),
                     arrowprops=dict(facecolor="darkgreen", shrink=0.08, width=1.5, headwidth=6),
                     fontweight="bold")
                     
    # Rotate x labels
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.title("Monthly Mutual Fund Industry SIP Inflows (Jan 2022 - Dec 2025)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Month", fontsize=11, labelpad=10)
    plt.ylabel("SIP Inflow (in Crores INR)", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(charts_dir / "sip_inflows.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 4: Category Inflow Heatmap
    # -------------------------------------------------------------
    print("🎨 Generating Chart 4: category_inflows_heatmap.png...")
    plt.figure(figsize=(14, 7))
    
    # Pivot category inflows
    df_cat_pivot = df_cat_inflow.pivot(index="category", columns="month", values="net_inflow_crore")
    
    sns.heatmap(df_cat_pivot, cmap="RdYlGn", center=0, annot=False, cbar_kws={"label": "Net Inflow (Crores INR)"})
    plt.title("Category-wise Monthly Net Fund Inflows (Heatmap)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Month", fontsize=11, labelpad=10)
    plt.ylabel("Fund Category", fontsize=11, labelpad=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    plt.savefig(charts_dir / "category_inflows_heatmap.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 5: Investor Age Group Pie Chart
    # -------------------------------------------------------------
    print("🎨 Generating Chart 5: investor_age_pie.png...")
    plt.figure(figsize=(8, 8))
    age_counts = df_tx["age_group"].value_counts()
    
    plt.pie(age_counts.values, labels=age_counts.index, autopct="%1.1f%%", startangle=140, 
            colors=sns.color_palette("pastel"))
    plt.title("Investor Age Group Distribution (Total Transactions)", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(charts_dir / "investor_age_pie.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 6: Box Plot of SIP Amount by Age Group
    # -------------------------------------------------------------
    print("🎨 Generating Chart 6: investor_sip_box.png...")
    plt.figure(figsize=(12, 6))
    
    # Filter for SIP transactions
    df_sip_tx = df_tx[df_tx["transaction_type"] == "SIP"]
    
    # If not enough records, plot overall transactions
    if len(df_sip_tx) < 10:
        df_sip_tx = df_tx
        
    sns.boxplot(data=df_sip_tx, x="age_group", y="amount_inr", hue="age_group", palette="Set2", legend=False)
    plt.title("SIP Transaction Amount Distribution by Investor Age Group", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Age Group", fontsize=11, labelpad=10)
    plt.ylabel("SIP Transaction Amount (INR)", fontsize=11, labelpad=10)
    plt.yscale("log") # Use log scale as transaction amount can vary heavily
    plt.tight_layout()
    plt.savefig(charts_dir / "investor_sip_box.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 7: Gender Transaction Split
    # -------------------------------------------------------------
    print("🎨 Generating Chart 7: investor_gender_bar.png...")
    plt.figure(figsize=(10, 6))
    
    # Count gender transactions
    gender_counts = df_tx.groupby(["gender", "transaction_type"])["amount_inr"].count().reset_index()
    gender_counts = gender_counts.rename(columns={"amount_inr": "transaction_count"})
    
    sns.barplot(data=gender_counts, x="transaction_type", y="transaction_count", hue="gender", palette="Set1")
    plt.title("Transaction Volume Split by Gender & Transaction Type", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Transaction Type", fontsize=11, labelpad=10)
    plt.ylabel("Number of Transactions", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(charts_dir / "investor_gender_bar.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 8: State Geographic Distribution
    # -------------------------------------------------------------
    print("🎨 Generating Chart 8: state_geographic.png...")
    plt.figure(figsize=(12, 7))
    
    # Calculate average and sum transaction amount by state
    df_state = df_tx.groupby("state")["amount_inr"].sum().reset_index()
    # Convert to Crores
    df_state["amount_crores"] = df_state["amount_inr"] / 10000000.0
    df_state = df_state.sort_values(by="amount_crores", ascending=False)
    
    sns.barplot(data=df_state, x="amount_crores", y="state", hue="state", palette="viridis", legend=False)
    plt.title("Total Transaction Investment Volume by Indian State (in Crores)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Total Investment (Crores INR)", fontsize=11, labelpad=10)
    plt.ylabel("State", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(charts_dir / "state_geographic.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 9: T30 vs B30 City Tier Pie Chart
    # -------------------------------------------------------------
    print("🎨 Generating Chart 9: city_tier_pie.png...")
    plt.figure(figsize=(8, 8))
    
    tier_counts = df_tx["city_tier"].value_counts()
    
    plt.pie(tier_counts.values, labels=tier_counts.index, autopct="%1.1f%%", startangle=140, 
            colors=["skyblue", "lightcoral"])
    plt.title("Distribution of Transactions: T30 vs B30 Cities (City Tier)", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(charts_dir / "city_tier_pie.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 10: Folio Count Growth
    # -------------------------------------------------------------
    print("🎨 Generating Chart 10: folio_count_growth.png...")
    plt.figure(figsize=(12, 6))
    
    df_folios = df_folios.sort_values(by="month")
    
    plt.plot(df_folios["month"], df_folios["total_folios_crore"], marker="s", color="orange", linewidth=2.5, label="Total Folios")
    plt.plot(df_folios["month"], df_folios["equity_folios_crore"], marker="^", color="red", linestyle="--", label="Equity Folios")
    
    # Highlight milestones:
    # 13.26 Cr (Jan 2022) to 26.12 Cr (Dec 2025)
    plt.annotate("Start: 13.26 Cr", xy=(0, 13.26), xytext=(2, 14.5),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=4))
    
    last_idx = len(df_folios) - 1
    plt.annotate("End: 26.12 Cr", xy=(last_idx, 26.12), xytext=(last_idx - 6, 24.5),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=4),
                 fontweight="bold")
                 
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.title("Growth of Industry Mutual Fund Folios (Jan 2022 - Dec 2025)", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Month", fontsize=11, labelpad=10)
    plt.ylabel("Number of Folios (in Crores)", fontsize=11, labelpad=10)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(charts_dir / "folio_count_growth.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 11: NAV Return Correlation Matrix Heatmap
    # -------------------------------------------------------------
    print("🎨 Generating Chart 11: nav_correlation_matrix.png...")
    plt.figure(figsize=(12, 10))
    
    # Select 10 funds: 5 key schemes we fetched + 5 other schemes
    select_codes = [125497, 119551, 120503, 118632, 119092, 120841, 119552, 120504, 118633, 119599]
    df_nav_10 = df_nav[df_nav["amfi_code"].isin(select_codes)].copy()
    
    # Pivot
    df_nav_pivot = df_nav_10.pivot(index="date", columns="amfi_code", values="nav")
    # Replace columns with scheme names
    code_name_map = {code: df_fund[df_fund["amfi_code"] == code]["scheme_name"].values[0].split(" - ")[0] for code in select_codes}
    df_nav_pivot = df_nav_pivot.rename(columns=code_name_map)
    
    # Daily returns
    df_returns = df_nav_pivot.pct_change()
    corr_matrix = df_returns.corr()
    
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", square=True)
    plt.title("Daily NAV Return Correlation Matrix (Selected 10 Funds)", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(charts_dir / "nav_correlation_matrix.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 12: Sector Allocation Donut Chart
    # -------------------------------------------------------------
    print("🎨 Generating Chart 12: sector_allocation_donut.png...")
    plt.figure(figsize=(9, 9))
    
    # Group sector weight_pct
    df_sector = df_holdings.groupby("sector")["weight_pct"].sum().reset_index()
    df_sector = df_sector.sort_values(by="weight_pct", ascending=False)
    
    # Plot donut
    plt.pie(df_sector["weight_pct"], labels=df_sector["sector"], autopct="%1.1f%%", startangle=90, 
            colors=sns.color_palette("muted"), pctdistance=0.85)
            
    # Draw circle
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    
    plt.title("Aggregated Equity Portfolio Weight by Sector", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(charts_dir / "sector_allocation_donut.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 13: Fund Risk Category Pie Chart (Extra Chart 1)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 13: fund_risk_category_dist.png...")
    plt.figure(figsize=(8, 8))
    
    risk_counts = df_fund["risk_category"].value_counts()
    
    plt.pie(risk_counts.values, labels=risk_counts.index, autopct="%1.1f%%", startangle=140, 
            colors=sns.color_palette("Set2"))
    plt.title("Distribution of Mutual Fund Schemes by Risk Category", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(charts_dir / "fund_risk_category_dist.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 14: Expense Ratio vs Morningstar Rating Scatter (Extra Chart 2)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 14: expense_vs_rating.png...")
    plt.figure(figsize=(10, 6))
    
    sns.boxplot(data=df_perf, x="morningstar_rating", y="expense_ratio_pct", hue="morningstar_rating", palette="YlGnBu", legend=False)
    plt.title("Fund Expense Ratio Distribution by Morningstar Rating", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Morningstar Rating", fontsize=11, labelpad=10)
    plt.ylabel("Expense Ratio (%)", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(charts_dir / "expense_vs_rating.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 15: Payment Mode Volume Bar (Extra Chart 3)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 15: payment_mode_bar.png...")
    plt.figure(figsize=(10, 6))
    
    pay_counts = df_tx.groupby("payment_mode")["amount_inr"].count().reset_index()
    pay_counts = pay_counts.sort_values(by="amount_inr", ascending=False)
    
    sns.barplot(data=pay_counts, x="payment_mode", y="amount_inr", hue="payment_mode", palette="pastel", legend=False)
    plt.title("Number of Transactions by Payment Mode", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Payment Mode", fontsize=11, labelpad=10)
    plt.ylabel("Transaction Count", fontsize=11, labelpad=10)
    plt.tight_layout()
    plt.savefig(charts_dir / "payment_mode_bar.png", dpi=150)
    plt.close()
    
    # -------------------------------------------------------------
    # CHART 16: Top 10 Stocks Held by Weights (Extra Chart 4)
    # -------------------------------------------------------------
    print("🎨 Generating Chart 16: top_stocks_weight.png...")
    plt.figure(figsize=(12, 6))
    
    # Group by stock symbol
    df_stocks = df_holdings.groupby(["stock_symbol", "stock_name", "sector"])["weight_pct"].mean().reset_index()
    df_stocks = df_stocks.sort_values(by="weight_pct", ascending=False).head(10)
    
    sns.barplot(data=df_stocks, x="weight_pct", y="stock_name", hue="sector", dodge=False, palette="Set2")
    plt.title("Top 10 Stocks Held in Equity Portfolios by Average Weight", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Average Holding Weight (%)", fontsize=11, labelpad=10)
    plt.ylabel("Stock Name", fontsize=11, labelpad=10)
    plt.legend(title="Sector", loc="lower right")
    plt.tight_layout()
    plt.savefig(charts_dir / "top_stocks_weight.png", dpi=150)
    plt.close()
    
    print("\n🎉 [COMPLETE] Successfully generated and exported all 16 PNG charts.")
    conn.close()

if __name__ == "__main__":
    main()
