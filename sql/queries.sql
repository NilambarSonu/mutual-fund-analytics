-- Bluestock Mutual Fund Capstone Project
-- Day 2 Analytical Queries (queries.sql)

-- Query 1: Top 5 Mutual Fund Schemes by Assets Under Management (AUM)
-- Rationale: High AUM indicates strong investor trust and fund scale.
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    aum_crore
FROM 
    fact_performance
ORDER BY 
    aum_crore DESC
LIMIT 5;


-- Query 2: Average Daily NAV per Month for SBI Bluechip Direct (AMFI Code: 119551)
-- Rationale: Demonstrates joins with the date dimension to calculate monthly aggregated trends.
SELECT 
    d.year,
    d.month,
    ROUND(AVG(f.nav), 4) AS avg_nav
FROM 
    fact_nav f
JOIN 
    dim_date d ON f.date = d.date
WHERE 
    f.amfi_code = 119551
GROUP BY 
    d.year, d.month
ORDER BY 
    d.year, d.month;


-- Query 3: Monthly SIP YoY Growth (Year-over-Year Inflow Growth)
-- Rationale: Compares the SIP inflows of each month to the corresponding month of the prior year.
-- Demonstrates self-joins and window analytic capabilities.
SELECT 
    t1.month AS current_month,
    t1.sip_inflow_crore AS current_inflow,
    t2.month AS prior_year_month,
    t2.sip_inflow_crore AS prior_inflow,
    ROUND(((t1.sip_inflow_crore - t2.sip_inflow_crore) / CAST(t2.sip_inflow_crore AS REAL)) * 100, 2) AS yoy_growth_percentage
FROM 
    sip_inflows t1
JOIN 
    sip_inflows t2 ON 
        CAST(SUBSTR(t1.month, 1, 4) AS INTEGER) = CAST(SUBSTR(t2.month, 1, 4) AS INTEGER) + 1
        AND SUBSTR(t1.month, 6, 2) = SUBSTR(t2.month, 6, 2)
ORDER BY 
    t1.month;


-- Query 4: Total Transaction Amount and Count by State
-- Rationale: Provides geographic insights on where mutual fund inflows are coming from.
SELECT 
    state,
    COUNT(transaction_id) AS total_transactions,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_amount_in_crores
FROM 
    fact_transactions
GROUP BY 
    state
ORDER BY 
    total_amount_in_crores DESC;


-- Query 5: Direct Mutual Fund Schemes with an Expense Ratio < 1.0%
-- Rationale: Lower expense ratios are highly attractive to retail investors.
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    sub_category,
    expense_ratio_pct
FROM 
    dim_fund
WHERE 
    expense_ratio_pct < 1.0
ORDER BY 
    expense_ratio_pct ASC;


-- Query 6: Total Transaction Volume and Units by Transaction Type
-- Rationale: Analyzes retail transaction behavior across SIP, Lumpsum, and Redemption.
SELECT 
    transaction_type,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_amount_in_crores,
    ROUND(SUM(units), 2) AS total_units_allocated
FROM 
    fact_transactions
GROUP BY 
    transaction_type
ORDER BY 
    total_amount_in_crores DESC;


-- Query 7: Scheme Count and Total AUM per Fund House (AMC)
-- Rationale: Helps analyze the market share and scale of different asset management companies.
SELECT 
    fund_house,
    COUNT(amfi_code) AS scheme_count,
    SUM(aum_crore) AS total_aum_crore,
    ROUND(AVG(aum_crore), 2) AS avg_scheme_aum_crore
FROM 
    fact_performance
GROUP BY 
    fund_house
ORDER BY 
    total_aum_crore DESC;


-- Query 8: Morningstar Ratings Distribution of Schemes
-- Rationale: Shows the distribution of fund quality ratings within the master database.
SELECT 
    morningstar_rating,
    COUNT(amfi_code) AS scheme_count,
    ROUND((COUNT(amfi_code) * 100.0) / (SELECT COUNT(*) FROM fact_performance), 2) AS percentage_share
FROM 
    fact_performance
GROUP BY 
    morningstar_rating
ORDER BY 
    morningstar_rating DESC;


-- Query 9: Stock Holdings Count and Average Current Price by Sector
-- Rationale: Provides industry concentration analysis of equity mutual fund portfolios.
SELECT 
    sector,
    COUNT(DISTINCT stock_symbol) AS unique_stocks_held,
    COUNT(stock_symbol) AS total_holding_records,
    ROUND(AVG(current_price_inr), 2) AS avg_stock_price_inr
FROM 
    portfolio_holdings
GROUP BY 
    sector
ORDER BY 
    unique_stocks_held DESC;


-- Query 10: Average Return Performance and Risk Profile by Risk Grade
-- Rationale: Evaluates risk-adjusted returns (3yr and 5yr) across fund risk categorizations.
SELECT 
    risk_grade,
    COUNT(amfi_code) AS fund_count,
    ROUND(AVG(return_1yr_pct), 2) AS avg_return_1yr,
    ROUND(AVG(return_3yr_pct), 2) AS avg_return_3yr,
    ROUND(AVG(return_5yr_pct), 2) AS avg_return_5yr,
    ROUND(AVG(sharpe_ratio), 2) AS avg_sharpe_ratio
FROM 
    fact_performance
GROUP BY 
    risk_grade
ORDER BY 
    avg_return_3yr DESC;
