"""
Bluestock Mutual Fund Capstone Project - Day 6
Advanced Analytics + Risk Metrics (run_advanced_analytics.py)

This script performs:
1. Historical VaR (95%) and CVaR for all 40 schemes
2. Rolling 90-day Sharpe ratio for 5 key funds (plotted over time)
3. Investor cohort analysis (grouped by first transaction year)
4. SIP continuity analysis (flag investors with gap > 35 days as at-risk)
5. Fund recommender (by risk appetite: Low / Moderate / High)
6. Sector HHI concentration (Herfindahl-Hirschman Index) for equity funds
"""

import sys
import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sns.set_theme(style="whitegrid")
plt.rcParams["font.size"] = 11
plt.rcParams["figure.titlesize"] = 14

# ── Path Setup ────────────────────────────────────────────────────────────────
def setup_paths():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "scripts" else Path(".")
    db_path      = project_root / "data" / "db" / "bluestock_mf.db"
    processed    = project_root / "data" / "processed"
    charts       = project_root / "reports" / "charts"
    processed.mkdir(parents=True, exist_ok=True)
    charts.mkdir(parents=True, exist_ok=True)
    return project_root, db_path, processed, charts


# ── 1. VaR & CVaR ────────────────────────────────────────────────────────────
def compute_var_cvar(df_nav_all, df_funds, confidence=0.95):
    """
    Compute historical VaR (95%) and CVaR for all 40 schemes.
    VaR  = 5th percentile of daily return distribution (negative = loss).
    CVaR = mean of returns below VaR threshold.
    """
    print("📊 [INFO] Computing VaR and CVaR for all 40 schemes...")
    records = []
    for _, fund_row in df_funds.iterrows():
        code = fund_row["amfi_code"]
        nav  = df_nav_all[df_nav_all["amfi_code"] == code].sort_values("date").copy()
        nav.set_index("date", inplace=True)
        returns = nav["nav"].pct_change().dropna()
        if len(returns) < 30:
            continue
        var_95  = np.percentile(returns, (1 - confidence) * 100)   # 5th percentile
        cvar_95 = returns[returns <= var_95].mean()
        records.append({
            "amfi_code":         code,
            "scheme_name":       fund_row["scheme_name"],
            "fund_house":        fund_row["fund_house"],
            "category":          fund_row["category"],
            "var_95_pct":        round(var_95 * 100, 4),
            "cvar_95_pct":       round(cvar_95 * 100, 4),
            "total_trading_days": len(returns),
            "mean_daily_return_pct": round(returns.mean() * 100, 4),
            "std_daily_return_pct":  round(returns.std() * 100, 4),
        })
    df_var = pd.DataFrame(records).sort_values("var_95_pct")
    print(f"   Computed VaR/CVaR for {len(df_var)} schemes.")
    return df_var


# ── 2. Rolling 90-day Sharpe ──────────────────────────────────────────────────
def compute_rolling_sharpe(df_nav_all, df_funds, charts_dir, rf_annual=0.065):
    """
    Rolling 90-day Sharpe for 5 representative funds.
    Sharpe_t = (mean_90d - rf_daily) / std_90d * sqrt(252)
    """
    print("📈 [INFO] Computing and plotting rolling 90-day Sharpe ratios...")
    rf_daily = rf_annual / 252.0

    # Pick 5 diverse key funds: top scorecard + variety
    key_codes = [148567, 120505, 120843, 100033, 120504]   # same top-5 from Day 4
    key_names = {}
    for _, row in df_funds.iterrows():
        if row["amfi_code"] in key_codes:
            key_names[row["amfi_code"]] = row["scheme_name"].split(" - ")[0]

    fig, ax = plt.subplots(figsize=(14, 6))
    palette = plt.cm.tab10.colors

    for idx, code in enumerate(key_codes):
        nav = df_nav_all[df_nav_all["amfi_code"] == code].sort_values("date").copy()
        nav.set_index("date", inplace=True)
        returns = nav["nav"].pct_change().dropna()
        rolling_sharpe = (
            (returns.rolling(90).mean() - rf_daily) /
            returns.rolling(90).std()
        ) * np.sqrt(252)
        label = key_names.get(code, str(code))
        ax.plot(rolling_sharpe.index, rolling_sharpe, label=label,
                color=palette[idx], linewidth=1.8, alpha=0.85)

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_title("Rolling 90-Day Sharpe Ratio — Top 5 Funds (2022–2026)",
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Sharpe Ratio (Annualised)", fontsize=11)
    ax.legend(loc="lower right", fontsize=9, frameon=True)
    plt.tight_layout()
    chart_path = charts_dir / "rolling_sharpe_chart.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    print(f"   Saved rolling_sharpe_chart.png")
    return chart_path


# ── 3. Investor Cohort Analysis ───────────────────────────────────────────────
def investor_cohort_analysis(df_txn, df_funds):
    """
    Group investors by first transaction year.
    Compute avg SIP amount, total invested, and top fund preference per cohort.
    """
    print("👥 [INFO] Running investor cohort analysis...")
    sip = df_txn[df_txn["transaction_type"] == "SIP"].copy()
    first_year = sip.groupby("investor_id")["date"].min().dt.year.rename("cohort_year")
    sip = sip.join(first_year, on="investor_id")

    cohort = (
        sip.groupby("cohort_year")
        .agg(
            num_investors=("investor_id", "nunique"),
            avg_sip_amount=("amount", "mean"),
            total_invested=("amount", "sum"),
        )
        .reset_index()
    )

    # Top fund preference per cohort (most frequently invested fund)
    top_fund = (
        sip.groupby(["cohort_year", "amfi_code"])
        .size()
        .reset_index(name="txn_count")
        .sort_values(["cohort_year", "txn_count"], ascending=[True, False])
        .groupby("cohort_year")
        .first()
        .reset_index()[["cohort_year", "amfi_code"]]
    )
    code_to_name = df_funds.set_index("amfi_code")["scheme_name"].to_dict()
    top_fund["top_fund_name"] = top_fund["amfi_code"].map(code_to_name)

    cohort = cohort.merge(top_fund[["cohort_year", "top_fund_name"]], on="cohort_year", how="left")
    cohort["avg_sip_amount"] = cohort["avg_sip_amount"].round(2)
    cohort["total_invested"]  = cohort["total_invested"].round(2)
    print(cohort.to_string(index=False))
    return cohort


# ── 4. SIP Continuity Analysis ────────────────────────────────────────────────
def sip_continuity_analysis(df_txn):
    """
    For investors with 6+ SIP transactions:
    - Compute avg gap between SIP dates.
    - Flag investors with avg gap > 35 days as 'at-risk'.
    """
    print("🔄 [INFO] Running SIP continuity analysis...")
    sip = df_txn[df_txn["transaction_type"] == "SIP"].copy()
    sip = sip.sort_values(["investor_id", "date"])

    # Investors with 6+ SIP transactions
    counts = sip.groupby("investor_id").size()
    eligible = counts[counts >= 6].index
    sip_eligible = sip[sip["investor_id"].isin(eligible)].copy()

    def avg_gap(grp):
        dates = grp["date"].sort_values()
        if len(dates) < 2:
            return np.nan
        return dates.diff().dt.days.dropna().mean()

    gaps = sip_eligible.groupby("investor_id").apply(avg_gap).reset_index()
    gaps.columns = ["investor_id", "avg_gap_days"]
    gaps["sip_status"] = np.where(gaps["avg_gap_days"] > 35, "at-risk", "regular")

    total     = len(gaps)
    at_risk   = (gaps["sip_status"] == "at-risk").sum()
    regular   = total - at_risk
    rate      = at_risk / total * 100 if total > 0 else 0
    print(f"   Investors with 6+ SIPs: {total}")
    print(f"   At-risk (gap > 35 days): {at_risk} ({rate:.1f}%)")
    print(f"   Regular (gap <= 35 days): {regular}")
    return gaps, {"total": total, "at_risk": at_risk, "regular": regular, "at_risk_rate_pct": round(rate, 2)}


# ── 5. Sector HHI Concentration ───────────────────────────────────────────────
def sector_hhi_concentration(df_holdings, df_funds):
    """
    HHI = Σ(weight_i²) per fund. High HHI = concentrated portfolio.
    Compare across all equity funds (categories with 'Equity' or 'Mid' etc.).
    """
    print("🏭 [INFO] Computing Sector HHI Concentration for equity funds...")
    equity_cats = ["Large Cap", "Mid Cap", "Small Cap", "Multi Cap",
                   "Flexi Cap", "ELSS", "Sectoral"]
    equity_funds = df_funds[df_funds["category"].isin(equity_cats)]["amfi_code"].tolist()
    holdings_eq  = df_holdings[df_holdings["amfi_code"].isin(equity_funds)].copy()

    if holdings_eq.empty:
        print("   No equity fund holdings data found.")
        return pd.DataFrame()

    hhi = (
        holdings_eq.groupby("amfi_code")
        .apply(lambda g: (g["weight_pct"] ** 2).sum())
        .reset_index(name="hhi_score")
    )
    code_to_name = df_funds.set_index("amfi_code")["scheme_name"].to_dict()
    hhi["scheme_name"] = hhi["amfi_code"].map(code_to_name)
    hhi = hhi.sort_values("hhi_score", ascending=False)
    hhi["concentration"] = pd.cut(
        hhi["hhi_score"],
        bins=[0, 200, 500, float("inf")],
        labels=["Diversified", "Moderate", "Concentrated"],
    )
    print(hhi[["scheme_name", "hhi_score", "concentration"]].to_string(index=False))
    return hhi


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("🚀 Starting Advanced Analytics & Risk Metrics Pipeline...\n")
    project_root, db_path, processed_dir, charts_dir = setup_paths()

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}. Run etl_pipeline.py first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    print("📂 [INFO] Loading data from SQLite...")
    df_funds    = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    df_nav_all  = pd.read_sql_query("SELECT * FROM fact_nav", conn)
    df_txn      = pd.read_sql_query("SELECT * FROM fact_transactions", conn)
    df_holdings = pd.read_sql_query("SELECT * FROM portfolio_holdings", conn)

    df_nav_all["date"] = pd.to_datetime(df_nav_all["date"])
    # Normalise transaction date column
    if "transaction_date" in df_txn.columns:
        df_txn.rename(columns={"transaction_date": "date", "amount_inr": "amount"}, inplace=True)
    df_txn["date"] = pd.to_datetime(df_txn["date"])

    print(f"   Funds: {len(df_funds)} | NAV rows: {len(df_nav_all)} | "
          f"Txn rows: {len(df_txn)} | Holdings rows: {len(df_holdings)}\n")

    # ── 1. VaR & CVaR ────────────────────────────────────────────────────────
    df_var = compute_var_cvar(df_nav_all, df_funds)
    var_path = processed_dir / "var_cvar_report.csv"
    df_var.to_csv(var_path, index=False)
    print(f"   Saved var_cvar_report.csv ({len(df_var)} rows)\n")

    print("🔍 Top 5 Highest VaR (Riskiest Funds):")
    print(df_var.tail(5)[["scheme_name", "var_95_pct", "cvar_95_pct"]].to_string(index=False))
    print()
    print("🔍 Top 5 Lowest VaR (Safest Funds):")
    print(df_var.head(5)[["scheme_name", "var_95_pct", "cvar_95_pct"]].to_string(index=False))
    print()

    # ── 2. Rolling 90-day Sharpe ──────────────────────────────────────────────
    compute_rolling_sharpe(df_nav_all, df_funds, charts_dir)
    print()

    # ── 3. Investor Cohort Analysis ───────────────────────────────────────────
    cohort_df = investor_cohort_analysis(df_txn, df_funds)
    cohort_path = processed_dir / "investor_cohort_analysis.csv"
    cohort_df.to_csv(cohort_path, index=False)
    print(f"   Saved investor_cohort_analysis.csv\n")

    # ── 4. SIP Continuity Analysis ────────────────────────────────────────────
    sip_gaps, sip_summary = sip_continuity_analysis(df_txn)
    sip_path = processed_dir / "sip_continuity_report.csv"
    sip_gaps.to_csv(sip_path, index=False)
    print(f"   Saved sip_continuity_report.csv\n")

    # ── 5. Sector HHI ─────────────────────────────────────────────────────────
    hhi_df = sector_hhi_concentration(df_holdings, df_funds)
    if not hhi_df.empty:
        hhi_path = processed_dir / "sector_hhi_report.csv"
        hhi_df.to_csv(hhi_path, index=False)
        print(f"   Saved sector_hhi_report.csv\n")

    conn.close()

    # ── 6. Advanced Insights Summary ─────────────────────────────────────────
    print("=" * 65)
    print("📝 ADVANCED INSIGHTS SUMMARY")
    print("=" * 65)
    riskiest = df_var.iloc[-1]
    safest   = df_var.iloc[0]
    print(f"\n1. HIGHEST VaR FUND (Riskiest): {riskiest['scheme_name']}")
    print(f"   VaR(95%)={riskiest['var_95_pct']:.2f}%  |  CVaR={riskiest['cvar_95_pct']:.2f}%")
    print(f"\n2. LOWEST VaR FUND (Safest): {safest['scheme_name']}")
    print(f"   VaR(95%)={safest['var_95_pct']:.2f}%  |  CVaR={safest['cvar_95_pct']:.2f}%")
    if not cohort_df.empty:
        big_cohort = cohort_df.loc[cohort_df["num_investors"].idxmax()]
        print(f"\n3. LARGEST INVESTOR COHORT: Year {big_cohort['cohort_year'].astype(int)}")
        print(f"   Investors: {big_cohort['num_investors']} | Avg SIP: ₹{big_cohort['avg_sip_amount']:,.0f}")
    print(f"\n4. SIP CONTINUITY RATE: {100 - sip_summary['at_risk_rate_pct']:.1f}% regular investors "
          f"({sip_summary['at_risk']} at-risk out of {sip_summary['total']})")
    if not hhi_df.empty:
        conc = hhi_df[hhi_df["concentration"] == "Concentrated"]
        print(f"\n5. CONCENTRATED PORTFOLIOS (HHI): {len(conc)} equity funds have concentrated sector exposure.")
        if len(conc) > 0:
            print(f"   Most concentrated: {conc.iloc[0]['scheme_name']} (HHI={conc.iloc[0]['hhi_score']:.1f})")
    print("\n🎉 [COMPLETE] Advanced Analytics pipeline finished successfully.")


if __name__ == "__main__":
    main()
