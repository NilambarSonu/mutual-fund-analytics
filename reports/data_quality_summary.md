# Data Quality Summary Report (Day 1)

This report details the inspection and validation results for the 10 mutual fund datasets ingested.

## Ingested Datasets

The following CSV datasets have been moved to `data/raw/` and successfully loaded into Pandas:

| Dataset File Name | Identifier/Name | Shape | Primary Key / Index Column | Missing Values / Anomalies |
| :--- | :--- | :--- | :--- | :--- |
| `01_fund_master.csv` | `fund_master` | (40, 15) | `amfi_code` | None |
| `02_nav_history.csv` | `nav_history` | (46000, 3) | (`amfi_code`, `date`) | None |
| `03_aum_by_fund_house.csv` | `aum_by_fund_house` | (90, 5) | `date`, `fund_house` | None |
| `04_monthly_sip_inflows.csv` | `monthly_sip_inflows` | (48, 6) | `month` | `yoy_growth_pct`: 12 missing (25.00%) |
| `05_category_inflows.csv` | `category_inflows` | (144, 3) | `month`, `category` | None |
| `06_industry_folio_count.csv` | `industry_folio_count` | (21, 6) | `month` | None |
| `07_scheme_performance.csv` | `scheme_performance` | (40, 19) | `amfi_code` | None |
| `08_investor_transactions.csv` | `investor_transactions` | (32778, 13) | `investor_id`, `transaction_date` | None |
| `09_portfolio_holdings.csv` | `portfolio_holdings` | (322, 8) | `amfi_code`, `stock_symbol` | None |
| `10_benchmark_indices.csv` | `benchmark_indices` | (8050, 3) | `date`, `index_name` | None |

## Observations and Anomalies

1. **YoY Growth Missing Values in Monthly SIP Inflows**:
   - `04_monthly_sip_inflows.csv` contains 12 missing values in `yoy_growth_pct`.
   - **Explanation**: This is expected because the dataset starts at 2022-01, meaning the first 12 months of observations (Jan 2022 to Dec 2022) do not have a prior year's corresponding month to calculate Year-over-Year (YoY) growth percentage. The values starting Jan 2023 are fully populated.

2. **Clean Data Status**:
   - No duplicate rows were detected in any of the 10 datasets.
   - All numerical columns (e.g., NAV values, transaction amounts, folio counts) are correctly formatted and have no missing entries.

## AMFI Code Validation

We verified the integrity of the AMFI code mapping between `01_fund_master.csv` and `02_nav_history.csv`:

* **Fund Master Unique Codes**: 40
* **NAV History Unique Codes**: 40
* **Validation Outcome**: **100% Match (SUCCESS)**. Every single scheme code present in the Fund Master database is fully represented with corresponding historical NAV records in the NAV History database.
* **Duplicates Check**: No duplicate `amfi_code` values exist in the Fund Master dataset.

## Conclusion

The quality of the raw data is exceptionally high. Data ingestion is complete and ready for downstream ETL, database mapping, and analysis.
