"""
Bluestock Mutual Fund Capstone Project - Day 7
Final Report + Presentation Generator (generate_report.py)

Generates:
  1. reports/Final_Report.pdf  (15-20 pages via reportlab)
  2. reports/Bluestock_MF_Presentation.pptx  (12 slides via python-pptx)
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Colours ───────────────────────────────────────────────────────────────────
BLUE   = (27,  58, 107)   # Bluestock navy  #1B3A6B
ORANGE = (245, 129, 31)   # Bluestock orange #F5811F
WHITE  = (255, 255, 255)
LIGHT  = (238, 242, 247)
DARK   = (40,  40,  40)
GREY   = (120, 120, 120)


def setup_paths():
    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "scripts" else Path(".")
    db_path      = project_root / "data" / "db" / "bluestock_mf.db"
    reports      = project_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return project_root, db_path, reports


def load_data(db_path: Path):
    """Load all relevant tables from SQLite."""
    conn = sqlite3.connect(db_path)
    data = {}
    for table in ["dim_fund", "fact_nav", "benchmark_indices",
                  "fact_transactions", "portfolio_holdings",
                  "sip_inflows", "category_inflows", "industry_folio_count", "fact_aum"]:
        try:
            data[table] = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        except Exception:
            data[table] = pd.DataFrame()
    conn.close()

    # Normalise
    if not data["fact_transactions"].empty and "transaction_date" in data["fact_transactions"].columns:
        data["fact_transactions"].rename(
            columns={"transaction_date": "date", "amount_inr": "amount"}, inplace=True)

    # Load existing derived CSVs
    scorecard_path  = db_path.parent.parent / "processed" / "fund_scorecard.csv"
    alpha_beta_path = db_path.parent.parent / "processed" / "alpha_beta.csv"
    var_path        = db_path.parent.parent / "processed" / "var_cvar_report.csv"
    data["fund_scorecard"] = pd.read_csv(scorecard_path)  if scorecard_path.exists()  else pd.DataFrame()
    data["alpha_beta"]     = pd.read_csv(alpha_beta_path) if alpha_beta_path.exists() else pd.DataFrame()
    data["var_cvar"]       = pd.read_csv(var_path)        if var_path.exists()        else pd.DataFrame()
    return data


# ══════════════════════════════════════════════════════════════════════════════
#  PDF REPORT GENERATION  (reportlab)
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(data: dict, reports_dir: Path, project_root: Path):
    """Generate Final_Report.pdf using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable,
                                    PageBreak, Image as RLImage, KeepTogether)
    from reportlab.platypus import ListItem, ListFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    pdf_path = reports_dir / "Final_Report.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=2.0*cm, rightMargin=2.0*cm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
        title="Bluestock MF Analytics - Final Report",
        author="Nilambar Sonu Behera",
    )

    # ── Styles ────────────────────────────────────────────────────────────────
    rl_blue   = colors.Color(BLUE[0]/255,   BLUE[1]/255,   BLUE[2]/255)
    rl_orange = colors.Color(ORANGE[0]/255, ORANGE[1]/255, ORANGE[2]/255)
    rl_light  = colors.Color(LIGHT[0]/255,  LIGHT[1]/255,  LIGHT[2]/255)

    styles = getSampleStyleSheet()
    H1  = ParagraphStyle("H1",  parent=styles["Heading1"],  fontSize=20, spaceAfter=10,
                         textColor=rl_blue, fontName="Helvetica-Bold")
    H2  = ParagraphStyle("H2",  parent=styles["Heading2"],  fontSize=14, spaceBefore=12,
                         spaceAfter=6,  textColor=rl_blue, fontName="Helvetica-Bold")
    H3  = ParagraphStyle("H3",  parent=styles["Heading3"],  fontSize=12, spaceBefore=8,
                         spaceAfter=4,  textColor=rl_orange, fontName="Helvetica-Bold")
    BODY = ParagraphStyle("BODY", parent=styles["Normal"],  fontSize=10, leading=15,
                          spaceAfter=6, alignment=TA_JUSTIFY)
    BULLET = ParagraphStyle("BULLET", parent=BODY, leftIndent=20, bulletIndent=10,
                             spaceAfter=3)
    CENTER = ParagraphStyle("CENTER", parent=BODY, alignment=TA_CENTER)
    SMALL  = ParagraphStyle("SMALL",  parent=BODY, fontSize=8, textColor=colors.grey)

    def hr(): return HRFlowable(width="100%", thickness=1, color=rl_blue, spaceAfter=8)
    def sp(n=1): return Spacer(1, n*0.4*cm)
    def bullet(text): return Paragraph(f"• {text}", BULLET)
    def h2(text): return Paragraph(text, H2)
    def h3(text): return Paragraph(text, H3)
    def body(text): return Paragraph(text, BODY)
    def ctr(text): return Paragraph(text, CENTER)

    # ── Derived stats ─────────────────────────────────────────────────────────
    df_funds   = data["dim_fund"]
    df_sc      = data["fund_scorecard"]
    df_ab      = data["alpha_beta"]
    df_var     = data["var_cvar"]
    df_txn     = data["fact_transactions"]
    num_funds  = len(df_funds)
    num_txns   = len(df_txn) if not df_txn.empty else 0
    top5_names = (df_sc.head(5)["scheme_name"].tolist()
                  if not df_sc.empty and "scheme_name" in df_sc.columns else [])

    # ── Story ─────────────────────────────────────────────────────────────────
    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story += [sp(4), ctr("<b>BLUESTOCK FINTECH</b>"), sp(0.5)]
    story += [ctr("<font size='26' color='#1B3A6B'><b>Mutual Fund Analytics</b></font>"), sp(0.5)]
    story += [ctr("<font size='18'>Capstone Project I — Final Report</font>"), sp(2)]
    story += [hr()]
    story += [ctr("<font size='12'>Submitted by: <b>Nilambar Sonu Behera</b></font>"), sp(0.3)]
    story += [ctr(f"<font size='10'>Report Date: {datetime.today().strftime('%B %d, %Y')}</font>"), sp(0.3)]
    story += [ctr("<font size='10'>Bluestock Fintech Internship Program</font>"), sp(4)]
    story += [hr(), PageBreak()]

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    story += [h2("1. Executive Summary"), hr()]
    story += [body(
        "This report presents the complete analysis of the Bluestock Mutual Fund Analytics Capstone Project. "
        f"The project analysed <b>{num_funds} mutual fund schemes</b> across 7 categories using historical NAV data "
        "from January 2022 to May 2026. An ETL pipeline was constructed to ingest 10 raw CSV datasets, "
        "clean and normalise the data, and load it into a SQLite relational database. "
        "Advanced performance metrics including CAGR (1yr, 3yr, 5yr), Sharpe Ratio, Sortino Ratio, "
        "Alpha, Beta, VaR (95%), CVaR, Rolling Sharpe, and Sector HHI were computed for all schemes. "
        "A composite Fund Scorecard (0–100) was developed based on weighted percentile ranks, and "
        "a visual dashboard was produced across 4 analytical pages."
    )]
    story += [sp()]
    for i, nm in enumerate(top5_names, 1):
        story += [bullet(f"<b>Rank {i}:</b> {nm}")]
    story += [sp(), PageBreak()]

    # ── 2. Data Sources ───────────────────────────────────────────────────────
    story += [h2("2. Data Sources"), hr()]
    story += [body(
        "The project uses 10 structured CSV datasets provided by Bluestock Fintech, "
        "supplemented by live NAV data fetched from the MFAPI (mfapi.in) for 6 key schemes."
    )]
    tbl_data = [
        ["#", "Dataset", "Rows (approx.)", "Description"],
        ["1", "Fund Master",          "40",          "Scheme metadata, expense ratios, categories"],
        ["2", "NAV History",          "64,320",      "Daily NAV for all 40 schemes (Jan 2022–May 2026)"],
        ["3", "AUM by Fund House",    "Variable",    "Monthly AUM per AMC"],
        ["4", "Monthly SIP Inflows",  "~60",         "Industry-level monthly SIP inflow data"],
        ["5", "Category Inflows",     "~500",        "Net inflows per category per month"],
        ["6", "Industry Folio Count", "~60",         "Total active folios across categories"],
        ["7", "Scheme Performance",   "40",          "Benchmark-reported return and rating data"],
        ["8", "Investor Transactions", f"{num_txns:,}", "Synthetic investor SIP/Lumpsum/Redemption records"],
        ["9", "Portfolio Holdings",   "322",         "Top stock holdings per equity fund"],
        ["10","Benchmark Indices",    "8,050",       "NIFTY 50 and NIFTY 100 daily closing values"],
    ]
    tbl = Table(tbl_data, colWidths=[1*cm, 4.5*cm, 3*cm, 7*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), rl_blue),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1,  -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, rl_light]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story += [tbl, sp(), PageBreak()]

    # ── 3. ETL Design ─────────────────────────────────────────────────────────
    story += [h2("3. ETL Design & Database Architecture"), hr()]
    story += [body("The ETL pipeline was implemented in Python using pandas and SQLite, structured as follows:")]
    story += [h3("3.1 Data Ingestion (Day 1)")]
    story += [
        bullet("<b>scripts/data_ingestion.py</b>: Reads 10 raw CSVs, verifies schemas, creates directory structure."),
        bullet("<b>scripts/live_nav_fetch.py</b>: Fetches live historical NAV via MFAPI REST endpoint."),
        bullet("<b>scripts/validate_amfi.py</b>: Validates AMFI code integrity between fund master and NAV tables."),
    ]
    story += [h3("3.2 Data Cleaning & Transformation (Day 2)")]
    story += [
        bullet("Deduplication and type coercion on all 10 datasets."),
        bullet("Date standardisation to ISO 8601 format across all tables."),
        bullet("Outlier detection in NAV series using IQR-based flagging."),
        bullet("Categorical normalisation for transaction types and risk categories."),
    ]
    story += [h3("3.3 Database Schema")]
    story += [body(
        "All cleaned datasets are loaded into a SQLite database (data/db/bluestock_mf.db) with "
        "12 tables following a star-schema pattern. Core fact tables: fact_nav, fact_transactions, "
        "fact_aum, fact_performance. Dimension tables: dim_fund, dim_date. "
        "Relationship keys: amfi_code (fund identifier), date (time dimension)."
    )]
    story += [sp(), PageBreak()]

    # ── 4. EDA Findings ───────────────────────────────────────────────────────
    story += [h2("4. Exploratory Data Analysis (EDA) Findings"), hr()]
    story += [body("Key observations from the 16 EDA charts generated in Day 3:")]
    eda_findings = [
        "NAV Trends: All equity fund NAVs show a positive trajectory from Jan 2022 to May 2026, "
        "with a significant correction in 2022 followed by a sustained bull run.",
        "Fund Category Distribution: Large-cap and mid-cap funds dominate the tracked universe (50%+), "
        "followed by small-cap and debt funds.",
        "Expense Ratio: Direct plans consistently have ~0.5–0.8% lower expense ratios than regular plans.",
        "SIP Inflows: Sustained month-on-month SIP inflow growth, reaching ₹25,000+ Cr by 2025.",
        "AUM Concentration: Top 5 AMCs (HDFC, ICICI Prudential, SBI, Mirae Asset, Kotak) account for "
        "over 65% of total AUM.",
        "Investor Demographics: Majority of investors are in the 25–45 age bracket; Tier-1 cities "
        "contribute the highest SIP volumes.",
        "Folio Growth: Industry folio count grew by ~40% over the analysis period, signalling "
        "increasing retail participation.",
        "Correlation Matrix: Large-cap funds show high positive correlation (>0.85) with each other "
        "and with Nifty 50; debt funds show near-zero correlation with equity.",
    ]
    for f in eda_findings:
        story += [bullet(f)]
    story += [sp(), PageBreak()]

    # ── 5. Performance Analysis ───────────────────────────────────────────────
    story += [h2("5. Fund Performance Analysis"), hr()]

    story += [h3("5.1 Fund Scorecard (Top 10)")]
    if not df_sc.empty:
        cols_show = ["scheme_name", "cagr_3yr_pct", "sharpe_ratio", "sortino_ratio",
                     "max_drawdown_pct", "scorecard"]
        cols_show = [c for c in cols_show if c in df_sc.columns]
        top10 = df_sc.head(10)[cols_show].copy()
        top10.columns = [c.replace("_pct", " (%)").replace("_", " ").title() for c in top10.columns]
        header = [list(top10.columns)]
        rows   = []
        for _, r in top10.iterrows():
            rows.append([str(round(v, 2)) if isinstance(v, (float, int)) else str(v)
                         for v in r.values])
        sc_tbl = Table(header + rows, repeatRows=1,
                       colWidths=[6*cm, 2*cm, 2*cm, 2.2*cm, 2.5*cm, 2*cm])
        sc_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), rl_blue),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 7),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, rl_light]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story += [sc_tbl, sp()]

    story += [h3("5.2 Alpha & Beta — OLS Regression vs NIFTY 100")]
    story += [body(
        "Alpha and Beta were computed via OLS linear regression (scipy.stats.linregress) of each fund's "
        "daily returns against NIFTY 100 daily returns. Alpha is annualised (intercept × 252). "
        "Funds with Alpha > 0 generate excess returns above what market exposure predicts."
    )]
    if not df_ab.empty:
        top_alpha = df_ab.nlargest(5, "alpha_pct")[["scheme_name", "alpha_pct", "beta"]]
        for _, r in top_alpha.iterrows():
            story += [bullet(f"<b>{r['scheme_name']}</b>: Alpha={r['alpha_pct']:.2f}%, Beta={r['beta']:.3f}")]
    story += [sp()]

    story += [h3("5.3 VaR & CVaR (95% Historical)")]
    story += [body(
        "Historical VaR (95%) represents the 5th percentile of daily return distribution — the worst "
        "expected daily loss 95% of the time. CVaR (Conditional VaR) is the mean loss on days worse than VaR."
    )]
    if not df_var.empty:
        risk_funds = df_var.sort_values("var_95_pct").tail(5)
        for _, r in risk_funds.iterrows():
            story += [bullet(f"{r['scheme_name']}: VaR={r['var_95_pct']:.2f}%, CVaR={r['cvar_95_pct']:.2f}%")]
    story += [sp(), PageBreak()]

    # ── 6. Dashboard Screenshots ───────────────────────────────────────────────
    story += [h2("6. Dashboard Screenshots"), hr()]
    story += [body(
        "Four dashboard pages were generated providing a visual analytical summary "
        "of the mutual fund universe."
    )]
    charts_dir = project_root / "dashboard"
    for pg_name, pg_title in [
        ("page_1_industry_overview.png",  "Page 1: Industry Overview"),
        ("page_2_fund_performance.png",   "Page 2: Fund Performance"),
        ("page_3_investor_analytics.png", "Page 3: Investor Analytics"),
        ("page_4_sip_market_trends.png",  "Page 4: SIP & Market Trends"),
    ]:
        pg_path = charts_dir / pg_name
        story += [h3(pg_title)]
        if pg_path.exists():
            story += [RLImage(str(pg_path), width=16*cm, height=9*cm), sp()]
        else:
            story += [body(f"[{pg_name} — not found]"), sp()]
    story += [PageBreak()]

    # ── 7. Limitations ────────────────────────────────────────────────────────
    story += [h2("7. Limitations"), hr()]
    limitations = [
        "Dataset coverage is limited to Jan 2022 – May 2026 (~4.4 years), so 5-year CAGR uses maximum "
        "available history instead of a full 5-year window.",
        "Investor transaction data is synthetic (generated for demonstration), not real investor records.",
        "Portfolio holdings data covers only a subset of equity funds and represents a single snapshot date.",
        "Benchmark data (NIFTY 50, NIFTY 100) is used as proxy; sector-specific benchmarks for "
        "debt/hybrid funds are not included.",
        "The fund recommender uses Sharpe ratio as the sole ranking criterion within each risk bucket; "
        "a production system would incorporate multi-factor scoring.",
        "Power BI dashboard is represented by Python-generated matplotlib exports due to environment constraints; "
        "a real .pbix file would be required for full interactivity.",
    ]
    for lim in limitations:
        story += [bullet(lim)]
    story += [sp()]

    # ── 8. Recommendations ────────────────────────────────────────────────────
    story += [h2("8. Recommendations"), hr()]
    recs = [
        "Expand NAV history to 10+ years for statistically robust 5-year and 10-year performance comparisons.",
        "Integrate real-time AMFI data feed to keep NAVs current and enable live dashboard updates.",
        "Develop a multi-factor fund recommender incorporating Alpha, Max Drawdown, and Tracking Error "
        "in addition to Sharpe ratio.",
        "Implement a Streamlit or Dash web dashboard for interactive exploration by non-technical stakeholders.",
        "Apply machine learning (Random Forest or XGBoost) to predict future fund performance "
        "based on historical patterns and macroeconomic indicators.",
        "Conduct deeper SIP continuity analysis with investor segmentation to target at-risk investors "
        "with personalised nudges.",
        "Include international fund and Index ETF comparison to benchmark active vs passive strategies.",
    ]
    for rec in recs:
        story += [bullet(rec)]
    story += [sp()]

    # ── Footer ────────────────────────────────────────────────────────────────
    story += [PageBreak()]
    story += [sp(8)]
    story += [hr()]
    story += [ctr("<b>Bluestock Fintech Internship — Mutual Fund Analytics Capstone Project I</b>")]
    story += [ctr(f"Generated: {datetime.today().strftime('%B %d, %Y')}")]
    story += [ctr("Author: Nilambar Sonu Behera | GitHub: NilambarSonu/mutual-fund-analytics")]

    doc.build(story)
    print(f"   Saved Final_Report.pdf ({pdf_path})")
    return pdf_path


# ══════════════════════════════════════════════════════════════════════════════
#  PPTX PRESENTATION  (python-pptx)
# ══════════════════════════════════════════════════════════════════════════════
def generate_pptx(data: dict, reports_dir: Path, project_root: Path):
    """Generate Bluestock_MF_Presentation.pptx — 12 slides."""
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    SLIDE_W  = prs.slide_width
    SLIDE_H  = prs.slide_height
    BS_BLUE_RGB   = RGBColor(*BLUE)
    BS_ORANGE_RGB = RGBColor(*ORANGE)
    BS_WHITE_RGB  = RGBColor(*WHITE)
    BS_DARK_RGB   = RGBColor(*DARK)
    BS_GREY_RGB   = RGBColor(*GREY)

    BLANK = prs.slide_layouts[6]   # completely blank layout

    # ── Helper functions ──────────────────────────────────────────────────────
    def add_rect(slide, left, top, width, height, fill_rgb, alpha=None):
        shape = slide.shapes.add_shape(1, Inches(left), Inches(top),
                                        Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_rgb
        shape.line.color.rgb = fill_rgb
        return shape

    def add_text(slide, text, left, top, width, height,
                 font_size=14, bold=False, color=None, align=PP_ALIGN.LEFT, italic=False):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = True
        p  = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        if color:
            run.font.color.rgb = color
        return tb

    def add_header_band(slide, title):
        add_rect(slide, 0, 0, 13.33, 1.0, BS_BLUE_RGB)
        add_text(slide, "Bluestock MF Analytics", 0.3, 0.05, 5, 0.5,
                 font_size=13, bold=True, color=BS_WHITE_RGB)
        add_text(slide, title, 0, 0.05, 13.33, 0.9,
                 font_size=20, bold=True, color=RGBColor(*ORANGE), align=PP_ALIGN.CENTER)
        add_text(slide, "Capstone Project I", 8, 0.05, 5, 0.5,
                 font_size=11, color=RGBColor(176, 196, 222), align=PP_ALIGN.RIGHT)

    def add_image_safe(slide, img_path, left, top, width, height):
        img = Path(img_path)
        if img.exists():
            slide.shapes.add_picture(str(img), Inches(left), Inches(top),
                                     Inches(width), Inches(height))
        else:
            add_rect(slide, left, top, width, height, RGBColor(220, 220, 220))
            add_text(slide, f"[Image: {img.name}]", left, top + height/2 - 0.2,
                     width, 0.4, font_size=9, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)

    dash_dir   = project_root / "dashboard"
    charts_dir = project_root / "reports" / "charts"
    df_sc      = data["fund_scorecard"]
    df_funds   = data["dim_fund"]

    # ── Slide 1: Title ────────────────────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, 13.33, 7.5, BS_BLUE_RGB)
    add_text(s, "BLUESTOCK FINTECH", 0, 1.5, 13.33, 1.0,
             font_size=22, bold=True, color=BS_WHITE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Mutual Fund Analytics", 0, 2.6, 13.33, 1.2,
             font_size=40, bold=True, color=BS_ORANGE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Capstone Project I — Final Presentation", 0, 3.9, 13.33, 0.8,
             font_size=18, color=BS_WHITE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Nilambar Sonu Behera  |  June 2026", 0, 4.8, 13.33, 0.6,
             font_size=13, color=RGBColor(176, 196, 222), align=PP_ALIGN.CENTER)

    # ── Slide 2: Problem & Objective ─────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Problem Statement & Objectives")
    add_text(s, "Problem Statement", 0.5, 1.2, 12, 0.5, font_size=14, bold=True, color=BS_BLUE_RGB)
    add_text(s, (
        "Retail mutual fund investors lack accessible, data-driven tools to compare fund performance, "
        "assess risk-adjusted returns, and receive personalised fund recommendations based on "
        "their risk appetite. Raw NAV data from AMFI exists but is unstructured and hard to analyse."
    ), 0.5, 1.8, 12, 1.5, font_size=11, color=BS_DARK_RGB)
    add_text(s, "Objectives", 0.5, 3.4, 12, 0.5, font_size=14, bold=True, color=BS_BLUE_RGB)
    objectives = [
        "Build a robust ETL pipeline to ingest, clean, and load 10+ datasets into SQLite.",
        "Compute performance metrics: CAGR, Sharpe, Sortino, Alpha, Beta, VaR, CVaR.",
        "Develop a composite Fund Scorecard (0-100) based on weighted percentile ranks.",
        "Generate a 4-page analytical dashboard + interactive Power BI template.",
        "Implement a fund recommender system by risk appetite (Low / Moderate / High).",
    ]
    for i, obj in enumerate(objectives):
        add_text(s, f"✓  {obj}", 0.8, 3.9 + i*0.55, 12, 0.5,
                 font_size=10, color=BS_DARK_RGB)

    # ── Slide 3: Data Sources ─────────────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Data Sources & Architecture")
    add_text(s, "10 Datasets | SQLite Database | 12 Tables | 80,000+ Records",
             0, 1.1, 13.33, 0.5, font_size=11, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)
    sources = [
        ("Fund Master (40 funds)",       "Scheme metadata, expense ratios, categories, risk grades"),
        ("NAV History (64,320 rows)",    "Daily NAV per scheme: Jan 2022 – May 2026 (~4.4 years)"),
        ("Investor Transactions (32K+)", "SIP, Lumpsum, Redemption records with investor demographics"),
        ("Benchmark Indices (8,050)",    "NIFTY 50 & NIFTY 100 daily closing values"),
        ("Portfolio Holdings (322)",     "Top stock holdings and sector weights per equity fund"),
        ("SIP Inflows / Category",       "Industry-level monthly inflow and category-wise trends"),
    ]
    for i, (title, desc) in enumerate(sources):
        col = 0.4 if i % 2 == 0 else 6.8
        row = 1.9 + (i // 2) * 1.8
        add_rect(s, col, row, 5.8, 1.5, RGBColor(*LIGHT))
        add_text(s, title, col+0.15, row+0.1, 5.5, 0.45, font_size=11, bold=True, color=BS_BLUE_RGB)
        add_text(s, desc, col+0.15, row+0.55, 5.5, 0.8, font_size=9, color=BS_DARK_RGB)

    # ── Slide 4: System Architecture ─────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "System Architecture & Pipeline")
    arch_steps = [
        ("📥 Ingest", "Raw CSV + MFAPI\nlive NAV fetch"),
        ("🧹 Clean", "Type coercion,\ndedup, validation"),
        ("🗄 Load", "SQLite star schema\n12 tables"),
        ("📊 Analyse", "EDA + Performance\nMetrics + Scoring"),
        ("📈 Visualise", "Dashboard PNGs\nPDF Export"),
        ("🤖 Recommend", "Risk-based fund\nrecommender"),
    ]
    box_w = 1.8
    for i, (icon_title, desc) in enumerate(arch_steps):
        x = 0.3 + i * 2.15
        add_rect(s, x, 1.5, box_w, 1.5, BS_BLUE_RGB)
        add_text(s, icon_title, x, 1.55, box_w, 0.6, font_size=12, bold=True,
                 color=BS_WHITE_RGB, align=PP_ALIGN.CENTER)
        add_text(s, desc, x, 2.15, box_w, 0.8, font_size=9,
                 color=RGBColor(200, 220, 240), align=PP_ALIGN.CENTER)
        if i < len(arch_steps) - 1:
            add_text(s, "→", x + box_w, 1.8, 0.35, 0.7, font_size=20,
                     bold=True, color=BS_ORANGE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Python Stack: pandas | numpy | scipy | matplotlib | seaborn | sqlite3 | reportlab | python-pptx",
             0, 3.4, 13.33, 0.5, font_size=10, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Execution: python scripts/run_pipeline.py  (master pipeline runner)",
             0, 3.9, 13.33, 0.5, font_size=10, color=BS_BLUE_RGB, align=PP_ALIGN.CENTER)

    # ── Slide 5: EDA Highlights (1) ───────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "EDA Highlights — NAV Trends & Category Distribution")
    add_image_safe(s, charts_dir / "nav_trends.png",    0.3, 1.1, 6.0, 3.8)
    add_image_safe(s, charts_dir / "fund_risk_category_dist.png", 6.8, 1.1, 6.0, 3.8)
    add_text(s, "• Sustained NAV growth for equity funds post-2022 correction", 0.3, 5.1, 12.5, 0.4,
             font_size=10, color=BS_DARK_RGB)
    add_text(s, "• Large-cap and mid-cap dominate; debt/liquid funds show stable NAVs", 0.3, 5.5, 12.5, 0.4,
             font_size=10, color=BS_DARK_RGB)

    # ── Slide 6: EDA Highlights (2) ───────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "EDA Highlights — Investor Analytics & SIP Trends")
    add_image_safe(s, charts_dir / "sip_inflows.png",         0.3, 1.1, 6.0, 3.8)
    add_image_safe(s, charts_dir / "category_inflows_heatmap.png", 6.8, 1.1, 6.0, 3.8)
    add_text(s, "• SIP inflows show consistent YoY growth — strong retail participation", 0.3, 5.1, 12.5, 0.4,
             font_size=10, color=BS_DARK_RGB)
    add_text(s, "• Equity-oriented categories receive highest net inflows in FY2025", 0.3, 5.5, 12.5, 0.4,
             font_size=10, color=BS_DARK_RGB)

    # ── Slide 7: Performance Metrics (1) ──────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Fund Performance — Scorecard & Benchmark Comparison")
    add_image_safe(s, project_root / "benchmark_comparison_chart.PNG", 0.3, 1.1, 12.5, 5.8)

    # ── Slide 8: Performance Metrics (2) ──────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Fund Performance — Rolling Sharpe & VaR/CVaR")
    add_image_safe(s, charts_dir / "rolling_sharpe_chart.png", 0.3, 1.1, 8.5, 5.5)
    add_text(s, "Top 5 Scorecard Funds", 9.1, 1.2, 4.0, 0.5, font_size=11, bold=True, color=BS_BLUE_RGB)
    if not df_sc.empty and "scheme_name" in df_sc.columns:
        for rank, (_, r) in enumerate(df_sc.head(5).iterrows(), 1):
            nm  = r["scheme_name"].split(" - ")[0][:28]
            sc  = r.get("scorecard", "")
            add_text(s, f"{rank}. {nm}", 9.1, 1.7 + rank*0.65, 4.0, 0.5,
                     font_size=9, color=BS_DARK_RGB)
            add_text(s, f"Score: {sc}", 9.1, 2.0 + rank*0.65, 4.0, 0.3,
                     font_size=8, color=BS_BLUE_RGB, italic=True)

    # ── Slide 9: Dashboard Screenshots (1) ───────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Dashboard — Industry Overview & Fund Performance")
    add_image_safe(s, dash_dir / "page_1_industry_overview.png",  0.2, 1.1, 6.4, 3.6)
    add_image_safe(s, dash_dir / "page_2_fund_performance.png",   6.8, 1.1, 6.4, 3.6)
    add_text(s, "Page 1: KPI Cards + NAV Trend + AUM Distribution",
             0.2, 4.8, 6.4, 0.4, font_size=9, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Page 2: Return vs Risk Scatter + Normalised NAV Comparison",
             6.8, 4.8, 6.4, 0.4, font_size=9, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)

    # ── Slide 10: Dashboard Screenshots (2) ──────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Dashboard — Investor Analytics & Market Trends")
    add_image_safe(s, dash_dir / "page_3_investor_analytics.png",  0.2, 1.1, 6.4, 3.6)
    add_image_safe(s, dash_dir / "page_4_sip_market_trends.png",   6.8, 1.1, 6.4, 3.6)
    add_text(s, "Page 3: Transaction Type Split + Monthly Volume Trends",
             0.2, 4.8, 6.4, 0.4, font_size=9, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Page 4: SIP Inflow vs Nifty 50 + Category Inflow Heatmap",
             6.8, 4.8, 6.4, 0.4, font_size=9, color=BS_GREY_RGB, align=PP_ALIGN.CENTER)

    # ── Slide 11: Key Findings ────────────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_header_band(s, "Key Findings & Insights")
    findings = [
        ("🏆 Top Performer", "Mirae Asset Large Cap Fund (Score: 86.25) — best 3yr CAGR + Sharpe combination"),
        ("📉 Risk Leaders",  "Liquid funds show lowest VaR (<0.1% daily) — ideal for capital preservation"),
        ("📈 Alpha Generators", "Mid-cap active funds generate positive Alpha (>2% annually) vs NIFTY 100"),
        ("💡 SIP Trends",   "97.8% of investors with 6+ SIPs have avg gaps >35 days — continuity opportunity"),
        ("🏭 HHI Insights", "Sectoral funds have high portfolio concentration (HHI >500) vs diversified funds"),
        ("👥 Cohort Insight", "2024 cohort has the most investors (4,456) with avg SIP of ₹10,987"),
    ]
    for i, (title, detail) in enumerate(findings):
        col = 0.4 if i % 2 == 0 else 6.8
        row = 1.2 + (i // 2) * 2.0
        add_rect(s, col, row, 5.8, 1.7, RGBColor(*LIGHT))
        add_text(s, title, col+0.15, row+0.1, 5.5, 0.5, font_size=12, bold=True, color=BS_BLUE_RGB)
        add_text(s, detail, col+0.15, row+0.6, 5.5, 0.95, font_size=9, color=BS_DARK_RGB)

    # ── Slide 12: Thank You ───────────────────────────────────────────────────
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, 13.33, 7.5, BS_BLUE_RGB)
    add_text(s, "Thank You", 0, 1.5, 13.33, 1.5,
             font_size=48, bold=True, color=BS_ORANGE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Bluestock Fintech — Mutual Fund Analytics Capstone Project I",
             0, 3.2, 13.33, 0.7, font_size=16, color=BS_WHITE_RGB, align=PP_ALIGN.CENTER)
    add_text(s, "Nilambar Sonu Behera  |  GitHub: NilambarSonu/mutual-fund-analytics",
             0, 4.0, 13.33, 0.6, font_size=12, color=RGBColor(176, 196, 222), align=PP_ALIGN.CENTER)
    add_text(s, "June 2026", 0, 4.7, 13.33, 0.5,
             font_size=12, color=BS_WHITE_RGB, align=PP_ALIGN.CENTER)

    pptx_path = reports_dir / "Bluestock_MF_Presentation.pptx"
    prs.save(str(pptx_path))
    print(f"   Saved Bluestock_MF_Presentation.pptx ({pptx_path})")
    return pptx_path


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("🚀 Starting Day 7 — Final Report & Presentation Generator...")
    project_root, db_path, reports_dir = setup_paths()

    if not db_path.exists():
        print(f"❌ Database not found at {db_path}. Run etl_pipeline.py first.")
        sys.exit(1)

    print("📂 [INFO] Loading data...")
    data = load_data(db_path)
    print(f"   Funds: {len(data['dim_fund'])} | NAV rows: {len(data['fact_nav'])} | "
          f"Scorecard: {len(data['fund_scorecard'])} rows | VaR: {len(data['var_cvar'])} rows\n")

    print("📄 [INFO] Generating Final_Report.pdf...")
    generate_pdf(data, reports_dir, project_root)

    print("\n📊 [INFO] Generating Bluestock_MF_Presentation.pptx...")
    generate_pptx(data, reports_dir, project_root)

    print("\n🎉 [COMPLETE] Final report and presentation generated successfully.")


if __name__ == "__main__":
    main()
