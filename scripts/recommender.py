"""
Bluestock Mutual Fund Capstone - Fund Recommender (recommender.py)
==================================================================
Usage:
    python scripts/recommender.py --risk Low
    python scripts/recommender.py --risk Moderate
    python scripts/recommender.py --risk High

Input : risk appetite — Low | Moderate | High
Output: Top 3 funds by Sharpe ratio within the matching risk grade.
"""

import sys
import argparse
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np


# ── Risk grade mapping ────────────────────────────────────────────────────────
RISK_GRADE_MAP = {
    "Low":      ["Conservative", "Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High":     ["High", "Very High"],
}


def setup_paths():
    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "scripts" else Path(".")
    return project_root / "data" / "db" / "bluestock_mf.db"


def get_top_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """Return top N funds by Sharpe ratio for the given risk appetite."""
    db_path = setup_paths()
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    df_funds   = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    df_nav_all = pd.read_sql_query("SELECT * FROM fact_nav",  conn)
    conn.close()

    df_nav_all["date"] = pd.to_datetime(df_nav_all["date"])

    allowed_grades = RISK_GRADE_MAP.get(risk_appetite)
    if allowed_grades is None:
        print(f"❌ Unknown risk appetite '{risk_appetite}'. Choose: Low, Moderate, High")
        sys.exit(1)

    # Filter funds whose risk_grade matches the appetite
    # Fall back to expense_ratio bucketing if risk_grade column absent
    if "risk_grade" in df_funds.columns:
        filtered = df_funds[df_funds["risk_grade"].isin(allowed_grades)].copy()
    else:
        # Proxy: Low → expense < 0.8%, Moderate → 0.8-1.5%, High → > 1.5%
        if risk_appetite == "Low":
            filtered = df_funds[df_funds["expense_ratio_pct"] < 0.8].copy()
        elif risk_appetite == "Moderate":
            filtered = df_funds[
                (df_funds["expense_ratio_pct"] >= 0.8) &
                (df_funds["expense_ratio_pct"] <= 1.5)
            ].copy()
        else:
            filtered = df_funds[df_funds["expense_ratio_pct"] > 1.5].copy()

    if filtered.empty:
        # No match by grade — fall back to all funds
        filtered = df_funds.copy()

    rf_daily = 0.065 / 252.0
    results  = []

    for _, row in filtered.iterrows():
        code    = row["amfi_code"]
        nav     = df_nav_all[df_nav_all["amfi_code"] == code].sort_values("date")
        returns = nav["nav"].pct_change().dropna()
        if len(returns) < 30:
            continue
        std = returns.std()
        sharpe = ((returns.mean() - rf_daily) / std * np.sqrt(252)) if std > 0 else 0.0
        results.append({
            "amfi_code":        code,
            "scheme_name":      row["scheme_name"],
            "fund_house":       row["fund_house"],
            "category":         row["category"],
            "expense_ratio_pct": row["expense_ratio_pct"],
            "sharpe_ratio":     round(sharpe, 4),
        })

    df_res = pd.DataFrame(results).sort_values("sharpe_ratio", ascending=False)
    return df_res.head(top_n).reset_index(drop=True)


def print_recommendation(risk_appetite: str, df_top: pd.DataFrame):
    """Pretty-print the recommendation table."""
    print()
    print("=" * 70)
    print(f"  FUND RECOMMENDER — Risk Appetite: {risk_appetite.upper()}")
    print("=" * 70)
    print(f"  {'Rank':<5} {'Scheme Name':<42} {'Sharpe':>7} {'Expense%':>9}")
    print("-" * 70)
    for rank, (_, r) in enumerate(df_top.iterrows(), 1):
        name = r["scheme_name"][:40]
        print(f"  {rank:<5} {name:<42} {r['sharpe_ratio']:>7.3f} {r['expense_ratio_pct']:>9.2f}%")
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Bluestock Mutual Fund Recommender — Top 3 funds by risk appetite"
    )
    parser.add_argument(
        "--risk", choices=["Low", "Moderate", "High"], default="Moderate",
        help="Investor risk appetite: Low | Moderate | High"
    )
    parser.add_argument(
        "--top", type=int, default=3,
        help="Number of funds to recommend (default: 3)"
    )
    args = parser.parse_args()

    df_top = get_top_funds(args.risk, args.top)
    print_recommendation(args.risk, df_top)

    if df_top.empty:
        print("❌ No matching funds found.")
    else:
        print("✅ Recommendation complete.\n")


if __name__ == "__main__":
    main()
