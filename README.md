# Churn Analysis & Customer Intelligence (MySQL)

## Setup
1. Install MySQL Server + start it.
2. `pip install pandas numpy matplotlib seaborn sqlalchemy pymysql cryptography`
3. Set credentials (or edit defaults at top of scripts):
   - Windows: `set DB_USER=root` / `set DB_PASS=yourpass`
   - Mac/Linux: `export DB_USER=root DB_PASS=yourpass`

## Run
```
python generate_data.py     # creates DB customer_churn, 3 tables, 210 customers
python churn_analysis.py    # cleaning -> features -> KPIs -> charts -> CSVs
```

## Using your own data
Skip generate_data.py. Run schema.sql in MySQL Workbench, then import your CSVs
(Table Data Import Wizard). Column names must match the spec.

## Outputs
- `visuals/` 8 charts for the PPT
- `kpi_summary.csv` all KPIs
- `retention_priority_list.csv` active High/Med risk customers sorted by CLTV
- `churn_clean_dataset.csv`

## Insights flow for PPT (Who / Why / When)
Who = plan, contract, state | Why = escalations, cancellation reasons | When = month trend, tenure buckets
Then: 4 action items + resume bullets using YOUR printed numbers.

# Churn Analysis & Customer Intelligence (MySQL)

A customer churn analytics project using **MySQL and Python** to identify churn patterns, revenue impact, customer risk, and retention opportunities.

## Setup

1. Install MySQL Server and start it.
2. Install Python dependencies:

```bash
pip install pandas numpy matplotlib seaborn sqlalchemy pymysql cryptography
```

3. Configure your MySQL credentials.

Windows:

```cmd
set DB_USER=root
set DB_PASS=yourpass
```

Mac/Linux:

```bash
export DB_USER=root
export DB_PASS=yourpass
```

**Do not upload your MySQL password to GitHub.**

## Run

```bash
python generate_data.py
```

Creates the `customer_churn` database, required tables, and sample customer/support data.

Then run:

```bash
python churn_analysis.py
```

The analysis performs:

```text
Data Cleaning
     ↓
Feature Engineering
     ↓
Churn Analysis
     ↓
Revenue & CLTV Analysis
     ↓
Customer Risk Segmentation
     ↓
KPIs + Charts + CSV Outputs
```

## Project Results

The analysis contains **210 customers** and produced the following key metrics:

| Metric                     |  Result |
| -------------------------- | ------: |
| Total Customers            |     210 |
| Churned Customers          |      77 |
| Churn Rate                 |   36.7% |
| Retention Rate             |   63.3% |
| Total MRR                  |  60,940 |
| MRR Lost to Churn          |  19,423 |
| Revenue Loss               |   31.9% |
| CLTV Lost                  | 722,599 |
| Revenue at Risk            |  13,189 |
| Avg. Complaints / Customer |    1.46 |
| Escalation Rate            |   30.3% |

Monthly-contract customers had an observed churn rate of **51.2%**, compared with **16.9%** for annual-contract customers.

> The monthly vs annual difference is an observed association in this dataset and does not by itself establish causation.

## Using Your Own Data

Skip `generate_data.py`.

Run `schema.sql` in MySQL Workbench and import your CSV files using the **Table Data Import Wizard**.

Column names should match the expected database schema.

## Outputs

The analysis generates:

* `visuals/` — 8 business charts
* `kpi_summary.csv` — calculated business KPIs
* `retention_priority_list.csv` — customer risk and retention-priority data
* `churn_clean_dataset.csv` — cleaned analytical dataset

## Visualizations

The project generates charts for:

1. Churn by plan
2. Churn by contract type
3. Churn by state
4. Escalation vs churn
5. Monthly churn trend
6. Tenure distribution
7. Cancellation reasons
8. CLTV gap

## Business Insights

### Who?

Analyze churn by:

* Plan type
* Contract type
* State

### Why?

Analyze potential churn signals through:

* Complaints
* Escalations
* Cancellation reasons

### When?

Analyze:

* Monthly churn trends
* Customer tenure
* Tenure buckets

### What?

Measure:

* MRR loss
* CLTV impact
* Revenue at risk
* Customer churn risk

## Retention Actions

1. Monitor monthly-contract customers because they show a substantially higher observed churn rate.
2. Prioritize high-risk customers with higher CLTV.
3. Monitor complaints and escalations as potential early-warning signals.
4. Investigate cancellation reasons to identify opportunities for product, pricing, and customer-support improvements.

## Technologies

* MySQL
* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* SQLAlchemy
* PyMySQL

## Resume Project

**Customer Churn Analysis & Customer Intelligence | MySQL, Python, Pandas**

* Analyzed **210 customer records** using MySQL and Python to calculate churn, retention, ARPU, MRR, CLTV, complaint, escalation, and customer-risk metrics.
* Identified **36.7% overall churn** and observed **51.2% monthly-contract churn vs 16.9% annual-contract churn**.
* Quantified **19,423 MRR associated with churn** and **722,599 CLTV associated with churned customers**.
* Built customer risk segmentation using churn scores, CLTV, contract type, plan type, complaints, and escalations.
* Developed **8 business visualizations** and automated CSV outputs using Pandas, Matplotlib, Seaborn, SQLAlchemy, and MySQL.

