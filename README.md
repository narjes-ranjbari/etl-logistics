# ETL Logistics Pipeline

A data engineering pipeline that combines data from multiple sources.

## Data Sources
- SQL Server (customers & orders)
- CSV file (shipping costs)
- REST API (currency exchange rates)

## Pipeline Steps
1. Extract data from all 3 sources
2. Clean missing values
3. Merge and transform data
4. Calculate total costs in IRR and USD
5. Generate reports

## Tech Stack
- Python, Pandas, SQLAlchemy, Requests
- SQL Server

## Output
- `city_report.csv` — revenue per city
- `monthly_report.csv` — revenue per month  
- `top_customers.csv` — top 3 customers