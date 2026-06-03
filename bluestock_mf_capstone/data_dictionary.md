# Bluestock Mutual Fund Database - Data Dictionary

This document details the database schema design, table structures, column definitions, data types, and references for the SQLite database `bluestock_mf.db`.

## Database Schema Overview

The database uses a **Star Schema** design optimized for analytical query execution:

- **Dimension Tables**: `dim_fund`, `dim_date`
- **Fact Tables**: `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`
- **Supporting Tables**: `sip_inflows`, `category_inflows`, `industry_folio_count`, `portfolio_holdings`, `benchmark_indices`

---

## 1. Dimension Tables

### Table: `dim_fund`
Stores metadata and details for each mutual fund scheme.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | **Primary Key**. Association of Mutual Funds in India (AMFI) scheme identifier code. | `01_fund_master.csv` |
| `fund_house` | `TEXT` | Name of the Asset Management Company (AMC). | `01_fund_master.csv` |
| `scheme_name` | `TEXT` | Full name of the mutual fund scheme. | `01_fund_master.csv` |
| `category` | `TEXT` | Broad asset class category (e.g., Equity, Debt). | `01_fund_master.csv` |
| `sub_category` | `TEXT` | Sub-classification category (e.g., Large Cap, Small Cap, Liquid, Gilt). | `01_fund_master.csv` |
| `plan` | `TEXT` | Plan option type (e.g., Direct Plan, Regular Plan). | `01_fund_master.csv` |
| `launch_date` | `TEXT` | Date the scheme was launched (format: `YYYY-MM-DD`). | `01_fund_master.csv` |
| `benchmark` | `TEXT` | Benchmark index used to evaluate the fund's relative performance. | `01_fund_master.csv` |
| `expense_ratio_pct` | `REAL` | Percentage of fund assets used for administrative and operating expenses. | `01_fund_master.csv` |
| `exit_load_pct` | `REAL` | Exit load percentage charged to the investor if redeemed before a period. | `01_fund_master.csv` |
| `min_sip_amount` | `REAL` | Minimum transaction amount allowed for Systematic Investment Plans (SIP). | `01_fund_master.csv` |
| `min_lumpsum_amount` | `REAL` | Minimum amount allowed for one-time lumpsum investment. | `01_fund_master.csv` |
| `fund_manager` | `TEXT` | Name of the lead fund manager. | `01_fund_master.csv` |
| `risk_category` | `TEXT` | Risk grade classification of the scheme (e.g., High, Very High, Moderate). | `01_fund_master.csv` |
| `sebi_category_code` | `TEXT` | SEBI classification standard code. | `01_fund_master.csv` |

---

### Table: `dim_date`
Unified calendar date table for time-series analysis and analytical joins.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `date` | `TEXT` | **Primary Key**. Date in `YYYY-MM-DD` format. | Derived |
| `year` | `INTEGER` | Calendar year (e.g., `2024`). | Derived |
| `month` | `INTEGER` | Calendar month index (`1` to `12`). | Derived |
| `day` | `INTEGER` | Calendar day of month (`1` to `31`). | Derived |
| `quarter` | `INTEGER` | Quarter index (`1` to `4`). | Derived |
| `day_of_week` | `INTEGER` | Day of week index (`0` for Monday to `6` for Sunday). | Derived |
| `is_weekend` | `INTEGER` | Weekend indicator (`1` if Saturday or Sunday, `0` otherwise). | Derived |

---

## 2. Fact Tables

### Table: `fact_nav`
Daily NAV historical records. Missing weekend/holiday records have been forward-filled (`ffill`).

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `date` | `TEXT` | **Composite Primary Key**. Reference to `dim_date(date)`. | `02_nav_history.csv` |
| `amfi_code` | `INTEGER` | **Composite Primary Key**. Reference to `dim_fund(amfi_code)`. | `02_nav_history.csv` |
| `nav` | `REAL` | Net Asset Value (NAV) of the fund scheme. | `02_nav_history.csv` |

---

### Table: `fact_transactions`
Contains retail transaction records for investor activities.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `transaction_id` | `INTEGER` | **Primary Key**. Auto-incrementing identifier. | Derived |
| `investor_id` | `TEXT` | Unique identifier for each retail investor. | `08_investor_transactions.csv` |
| `transaction_date` | `TEXT` | Date of the transaction. Reference to `dim_date(date)`. | `08_investor_transactions.csv` |
| `amfi_code` | `INTEGER` | Scheme code transacted. Reference to `dim_fund(amfi_code)`. | `08_investor_transactions.csv` |
| `transaction_type` | `TEXT` | Transaction transaction type (`SIP`, `Lumpsum`, `Redemption`). | `08_investor_transactions.csv` |
| `amount_inr` | `REAL` | Financial transaction amount in INR. | `08_investor_transactions.csv` |
| `units` | `REAL` | Number of mutual fund units transacted. | Derived (amount_inr / 100 as proxy) |
| `state` | `TEXT` | Indian State of the investor. | `08_investor_transactions.csv` |
| `city` | `TEXT` | City of the investor. | `08_investor_transactions.csv` |
| `city_tier` | `TEXT` | Classification tier of the city (e.g., Tier 1, Tier 2). | `08_investor_transactions.csv` |
| `age_group` | `TEXT` | Age range bracket of the investor. | `08_investor_transactions.csv` |
| `gender` | `TEXT` | Gender of the investor. | `08_investor_transactions.csv` |
| `annual_income_lakh` | `REAL` | Annual income of the investor in Lakhs INR. | `08_investor_transactions.csv` |
| `payment_mode` | `TEXT` | Payment method used (e.g., UPI, Net Banking, Cheque). | `08_investor_transactions.csv` |
| `kyc_status` | `TEXT` | KYC verification status (`Verified`, `Pending`, `Failed`). | `08_investor_transactions.csv` |

---

### Table: `fact_performance`
Analytical metrics evaluating risk and returns for each scheme.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | **Primary Key**. Reference to `dim_fund(amfi_code)`. | `07_scheme_performance.csv` |
| `scheme_name` | `TEXT` | Scheme name. | `07_scheme_performance.csv` |
| `fund_house` | `TEXT` | AMC Name. | `07_scheme_performance.csv` |
| `category` | `TEXT` | Asset category. | `07_scheme_performance.csv` |
| `plan` | `TEXT` | Direct vs Regular. | `07_scheme_performance.csv` |
| `return_1yr_pct` | `REAL` | 1-year historical annualized return %. | `07_scheme_performance.csv` |
| `return_3yr_pct` | `REAL` | 3-year historical annualized return %. | `07_scheme_performance.csv` |
| `return_5yr_pct` | `REAL` | 5-year historical annualized return %. | `07_scheme_performance.csv` |
| `benchmark_3yr_pct` | `REAL` | Benchmark index 3-year return %. | `07_scheme_performance.csv` |
| `alpha` | `REAL` | Alpha risk-adjusted return metric (Jensen's Alpha). | `07_scheme_performance.csv` |
| `beta` | `REAL` | Beta systematic market volatility index. | `07_scheme_performance.csv` |
| `sharpe_ratio` | `REAL` | Sharpe ratio evaluating return per unit of volatility. | `07_scheme_performance.csv` |
| `sortino_ratio` | `REAL` | Sortino ratio evaluating return per unit of downside risk. | `07_scheme_performance.csv` |
| `std_dev_ann_pct` | `REAL` | Annualised return standard deviation %. | `07_scheme_performance.csv` |
| `max_drawdown_pct` | `REAL` | Maximum peak-to-trough historical drop %. | `07_scheme_performance.csv` |
| `aum_crore` | `REAL` | Scheme scale size (AUM) in Crores. | `07_scheme_performance.csv` |
| `expense_ratio_pct` | `REAL` | Fund expense ratio percentage. | `07_scheme_performance.csv` |
| `morningstar_rating` | `INTEGER` | Morningstar performance star score (1 to 5). | `07_scheme_performance.csv` |
| `risk_grade` | `TEXT` | Volatility grading metric. | `07_scheme_performance.csv` |

---

### Table: `fact_aum`
Quarterly assets under management of each fund house.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `date` | `TEXT` | **Composite Primary Key**. Reference to `dim_date(date)`. | `03_aum_by_fund_house.csv` |
| `fund_house` | `TEXT` | **Composite Primary Key**. Name of the AMC. | `03_aum_by_fund_house.csv` |
| `aum_lakh_crore` | `REAL` | AMC assets size in Lakh Crores INR. | `03_aum_by_fund_house.csv` |
| `aum_crore` | `REAL` | AMC assets size in Crores INR. | `03_aum_by_fund_house.csv` |
| `num_schemes` | `INTEGER` | Active schemes number run by the AMC. | `03_aum_by_fund_house.csv` |

---

## 3. Supporting Tables

### Table: `sip_inflows`
Industry-wide monthly SIP inflows.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `month` | `TEXT` | **Primary Key**. Month index in `YYYY-MM` format. | `04_monthly_sip_inflows.csv` |
| `sip_inflow_crore` | `REAL` | Aggregate monthly SIP inflows in Crores INR. | `04_monthly_sip_inflows.csv` |
| `active_sip_accounts_crore` | `REAL` | Number of active investor accounts in Crores. | `04_monthly_sip_inflows.csv` |
| `new_sip_accounts_lakh` | `REAL` | Number of new registrations in Lakhs. | `04_monthly_sip_inflows.csv` |
| `sip_aum_lakh_crore` | `REAL` | SIP assets base in Lakh Crores. | `04_monthly_sip_inflows.csv` |
| `yoy_growth_pct` | `REAL` | Year-over-Year percentage growth. | `04_monthly_sip_inflows.csv` |

---

### Table: `category_inflows`
Monthly net category-wise fund inflows.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `month` | `TEXT` | **Composite Primary Key**. Month in `YYYY-MM`. | `05_category_inflows.csv` |
| `category` | `TEXT` | **Composite Primary Key**. Scheme classification. | `05_category_inflows.csv` |
| `net_inflow_crore` | `REAL` | Net inflows in Crores INR. | `05_category_inflows.csv` |

---

### Table: `industry_folio_count`
Broad mutual fund industry aggregate folio counts.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `month` | `TEXT` | **Primary Key**. Month in `YYYY-MM`. | `06_industry_folio_count.csv` |
| `total_folios_crore` | `REAL` | Aggregate folios in Crores. | `06_industry_folio_count.csv` |
| `equity_folios_crore` | `REAL` | Equity segment folios in Crores. | `06_industry_folio_count.csv` |
| `debt_folios_crore` | `REAL` | Debt segment folios in Crores. | `06_industry_folio_count.csv` |
| `hybrid_folios_crore` | `REAL` | Balanced/Hybrid folios in Crores. | `06_industry_folio_count.csv` |
| `others_folios_crore` | `REAL` | Index/ETF/Liquid folios in Crores. | `06_industry_folio_count.csv` |

---

### Table: `portfolio_holdings`
Stock holdings concentration of equity mutual fund portfolios.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `amfi_code` | `INTEGER` | **Composite Primary Key**. Reference to `dim_fund(amfi_code)`. | `09_portfolio_holdings.csv` |
| `stock_symbol` | `TEXT` | **Composite Primary Key**. NSE/BSE stock symbol. | `09_portfolio_holdings.csv` |
| `stock_name` | `TEXT` | Name of the stock company. | `09_portfolio_holdings.csv` |
| `sector` | `TEXT` | Industry sector of the company (e.g., Banking, IT, FMCG). | `09_portfolio_holdings.csv` |
| `weight_pct` | `REAL` | Stock weight as a % of the total fund portfolio value. | `09_portfolio_holdings.csv` |
| `market_value_cr` | `REAL` | Valuation of the stock holding in Crores INR. | `09_portfolio_holdings.csv` |
| `current_price_inr` | `REAL` | Current price per share in INR. | `09_portfolio_holdings.csv` |
| `portfolio_date` | `TEXT` | **Composite Primary Key**. Portfolio timestamp in `YYYY-MM-DD`. | `09_portfolio_holdings.csv` |

---

### Table: `benchmark_indices`
Daily index price close values.

| Column Name | SQLite Data Type | Description | Source File / Reference |
| :--- | :--- | :--- | :--- |
| `date` | `TEXT` | **Composite Primary Key**. Date in `YYYY-MM-DD`. | `10_benchmark_indices.csv` |
| `index_name` | `TEXT` | **Composite Primary Key**. Benchmark index (e.g., NIFTY50). | `10_benchmark_indices.csv` |
| `close_value` | `REAL` | Daily close value of the index. | `10_benchmark_indices.csv` |
