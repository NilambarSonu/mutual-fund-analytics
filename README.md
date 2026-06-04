# Bluestock Mutual Fund Analytics Capstone Project

This repository contains the project codebase for the **Bluestock Fintech Mutual Fund Analytics** capstone project.
The goal of this project is to build an ETL data pipeline, perform database mappings, evaluate performance metrics, and create an analytical dashboard for mutual fund schemes.

# Project Structure

The project directory is structured as follows:

```
. (Repository Root)
├── data/
│   ├── raw/        ← Contains raw CSV datasets & fetched API NAV data
│   ├── processed/  ← Will contain cleaned/transformed CSV datasets
│   └── db/         ← Will contain the SQLite database
├── notebooks/      ← Jupyter notebooks for EDA and validation
├── scripts/        ← Python scripts for data ingestion, fetching, and validation
├── sql/            ← SQL schemas and queries
├── dashboard/      ← Dashboard configurations and code
├── reports/        ← Analysis reports and data quality reviews
└── README.md       ← Project documentation (this file)
```

## Setup and Installation

### 1. Prerequisites
- Python 3.10+
- `pip` package manager

### 2. Installation
Install the project dependencies from the root directory:
```bash
pip install -r requirements.txt
```

## Running the Pipelines

### Day 1: Project Setup + Data Ingestion (ETL)

The Day 1 pipeline performs setup, ingestion, API fetching, and AMFI code validation.

#### Step 1: Data Ingestion & Directory Initialization
Run `data_ingestion.py` from the root directory to create the project directory structure, load the 10 CSV datasets, check for anomalies, and write an ingestion summary:
```bash
python scripts/data_ingestion.py
```
*Outputs:*
- Folder structure created under `./`
- Datasets copied to `data/raw/`
- Summary report saved as `data/raw/ingestion_summary.txt`

#### Step 2: Fetch Live NAV
Run `live_nav_fetch.py` to retrieve the historical and live NAV records for 6 key schemes from `mfapi.in`:
```bash
python scripts/live_nav_fetch.py
```
*Outputs:*
- `live_nav_125497.csv` (HDFC Top 100 Direct)
- `live_nav_119551.csv` (SBI Bluechip Direct)
- `live_nav_120503.csv` (ICICI Bluechip Direct)
- `live_nav_118632.csv` (Nippon Large Cap Direct)
- `live_nav_119092.csv` (Axis Bluechip Direct)
- `live_nav_120841.csv` (Kotak Bluechip Direct)

#### Step 3: Validate AMFI Codes
Run `validate_amfi.py` to check the data integrity of AMFI code mappings between the fund master and historical NAV datasets:
```bash
python scripts/validate_amfi.py
```
*Outputs:*
- Data quality report saved as `data/raw/data_quality_report.txt`

#### Step 4: Jupyter Notebook Exploration
Explore the `01_data_ingestion.ipynb` notebook under `notebooks/` to view distributions of funds per fund house and metadata summaries.
To open the notebook:
```bash
jupyter notebook notebooks/01_data_ingestion.ipynb
```
