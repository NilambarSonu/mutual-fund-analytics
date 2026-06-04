-- Bluestock Mutual Fund Capstone Project
-- SQLite Database Schema Definition (schema.sql)
-- Star Schema Design for Mutual Fund Analytics

-- 1. DIMENSION TABLES

-- Dimension Table: Fund Details
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    plan TEXT NOT NULL,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount REAL,
    min_lumpsum_amount REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- Dimension Table: Calendar Dates
CREATE TABLE IF NOT EXISTS dim_date (
    date TEXT PRIMARY KEY, -- format: YYYY-MM-DD
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL, -- 0 (Monday) to 6 (Sunday)
    is_weekend INTEGER NOT NULL -- 0 for weekday, 1 for weekend
);

-- 2. FACT TABLES

-- Fact Table: Daily NAV History
CREATE TABLE IF NOT EXISTS fact_nav (
    date TEXT,
    amfi_code INTEGER,
    nav REAL NOT NULL,
    PRIMARY KEY (date, amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Fact Table: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL,
    units REAL,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT CHECK(kyc_status IN ('Verified', 'Pending', 'Failed')),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Fact Table: Scheme Performance
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    plan TEXT NOT NULL,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Fact Table: Quarterly Asset Under Management (AUM)
CREATE TABLE IF NOT EXISTS fact_aum (
    date TEXT,
    fund_house TEXT,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (date, fund_house),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 3. OTHER ANALYTICAL TABLES

-- Table: Monthly SIP Inflows
CREATE TABLE IF NOT EXISTS sip_inflows (
    month TEXT PRIMARY KEY, -- format: YYYY-MM
    sip_inflow_crore REAL NOT NULL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

-- Table: Category-wise Monthly Inflows
CREATE TABLE IF NOT EXISTS category_inflows (
    month TEXT, -- format: YYYY-MM
    category TEXT,
    net_inflow_crore REAL NOT NULL,
    PRIMARY KEY (month, category)
);

-- Table: Monthly Folio Counts
CREATE TABLE IF NOT EXISTS industry_folio_count (
    month TEXT PRIMARY KEY, -- format: YYYY-MM
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

-- Table: Portfolio holdings
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    amfi_code INTEGER,
    stock_symbol TEXT,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Table: Benchmark Indices Prices
CREATE TABLE IF NOT EXISTS benchmark_indices (
    date TEXT,
    index_name TEXT,
    close_value REAL,
    PRIMARY KEY (date, index_name),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);
