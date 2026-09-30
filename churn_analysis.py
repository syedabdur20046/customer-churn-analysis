"""Churn Analysis & Customer Intelligence - MySQL + pandas pipeline."""

import os
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sqlalchemy import create_engine


# ================================================================
# 1. SETTINGS
# ================================================================

sns.set_theme(style="whitegrid")

# Create output folder
os.makedirs("visuals", exist_ok=True)


# ================================================================
# 2. MYSQL CONNECTION
# ================================================================

# Your MySQL credentials
USER = "root"
PWD = "password"
HOST = "localhost"
PORT = 3306
DATABASE = "customer_churn"

# Encode password safely
encoded_password = quote_plus(PWD)

# Create SQLAlchemy connection
connection_url = (
    f"mysql+pymysql://{USER}:{encoded_password}"
    f"@{HOST}:{PORT}/{DATABASE}"
)

engine = create_engine(connection_url)

print("Connecting to MySQL...")

try:
    with engine.connect() as connection:
        print("MySQL connection successful!")
except Exception as e:
    print("\nMySQL connection failed.")
    print("Error:", e)
    raise SystemExit


# ================================================================
# 3. IMPORT DATA FROM MYSQL
# ================================================================

query = """
SELECT
    c.customerid,
    c.country,
    c.State,
    c.gender,
    c.dob,

    s.subscription_start_date,
    s.plan_type,
    s.contract_type,
    s.cancellation_date,
    s.cancellation_reason,
    s.monthly_charges,
    s.cltv,
    s.churn_score,

    COALESCE(sp.complaints, 0) AS complaints,
    COALESCE(sp.escalations, 0) AS escalations,
    sp.avg_csat

FROM db_customer c

LEFT JOIN db_subscription s
    ON c.customerid = s.customerid

LEFT JOIN (
    SELECT
        customerid,
        COUNT(*) AS complaints,
        SUM(Escalations) AS escalations,
        AVG(csat_score) AS avg_csat
    FROM db_support
    GROUP BY customerid
) sp
    ON c.customerid = sp.customerid
"""


print("\nLoading data from MySQL...")

df = pd.read_sql(query, engine)

print("Raw shape:", df.shape)


# ================================================================
# 4. CLEANING
# ================================================================

print("\nCleaning data...")

# Convert column names to lowercase
df.columns = df.columns.str.lower()

# Convert dates
date_columns = [
    "dob",
    "subscription_start_date",
    "cancellation_date"
]

for col in date_columns:
    df[col] = pd.to_datetime(
        df[col],
        errors="coerce"
    )


# Convert numeric columns
numeric_columns = [
    "monthly_charges",
    "cltv",
    "churn_score",
    "complaints",
    "escalations"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# Data quality check
print("\n===== NULL VALUES =====")

nulls = df.isna().sum()

print(
    nulls[nulls > 0]
)


print(
    "\nDuplicate customers:",
    df["customerid"].duplicated().sum()
)


# Remove duplicate customers
df = df.drop_duplicates(
    subset="customerid"
)


# Fill missing values
df["cancellation_reason"] = (
    df["cancellation_reason"]
    .fillna("Active")
)

df["avg_csat"] = (
    df["avg_csat"]
    .fillna(df["avg_csat"].median())
)


# Clean categorical columns
df["plan_type"] = (
    df["plan_type"]
    .astype(str)
    .str.strip()
    .str.title()
)

df["contract_type"] = (
    df["contract_type"]
    .astype(str)
    .str.strip()
    .str.title()
)


# ================================================================
# 5. FEATURE ENGINEERING
# ================================================================

print("\nCreating features...")

today = pd.Timestamp.now().normalize()


# Churn flag
df["churned"] = (
    df["cancellation_date"]
    .notna()
    .astype(int)
)


# Tenure
df["tenure_days"] = (
    df["cancellation_date"]
    .fillna(today)
    - df["subscription_start_date"]
).dt.days


# Age
df["age"] = (
    (today - df["dob"]).dt.days // 365
)


# Age groups
df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 25, 35, 50, 100],
    labels=[
        "<25",
        "25-35",
        "35-50",
        "50+"
    ]
)


# Tenure buckets
df["tenure_bucket"] = pd.cut(
    df["tenure_days"],
    bins=[
        -1,
        180,
        365,
        730,
        1460,
        10000
    ],
    labels=[
        "0-6m",
        "6-12m",
        "1-2y",
        "2-4y",
        "4y+"
    ]
)


# Risk tier
df["risk_tier"] = pd.cut(
    df["churn_score"],
    bins=[0, 40, 70, 100],
    labels=[
        "Low",
        "Med",
        "High"
    ],
    include_lowest=True
)


# Revenue at risk
df["revenue_at_risk"] = np.where(
    df["churn_score"] > 70,
    df["monthly_charges"],
    0
)


# Escalation flag
df["has_escalation"] = (
    df["escalations"] >= 1
).astype(int)


# Cancellation month
df["cancel_month"] = (
    df["cancellation_date"]
    .dt.to_period("M")
)


# ================================================================
# 6. KPI ANALYSIS
# ================================================================

print("\nCalculating KPIs...")

total = len(df)

churned_n = int(
    df["churned"].sum()
)

churn_rate = (
    churned_n / total
    if total > 0
    else 0
)

active = df[
    df["churned"] == 0
]


# Avoid division by zero
if len(active) > 0:
    arpu_active = (
        active["monthly_charges"].sum()
        / len(active)
    )
else:
    arpu_active = 0


total_complaints = df["complaints"].sum()

if total_complaints > 0:
    escalation_rate = (
        df["escalations"].sum()
        / total_complaints
        * 100
    )
else:
    escalation_rate = 0


total_mrr = (
    df["monthly_charges"].sum()
)

mrr_lost = (
    df.loc[
        df["churned"] == 1,
        "monthly_charges"
    ].sum()
)


if total_mrr > 0:
    revenue_loss_percentage = (
        mrr_lost
        / total_mrr
        * 100
    )
else:
    revenue_loss_percentage = 0


kpi = {

    "Total customers":
        total,

    "Churned customers":
        churned_n,

    "Churn rate %":
        round(
            churn_rate * 100,
            1
        ),

    "Retention rate %":
        round(
            (1 - churn_rate) * 100,
            1
        ),

    "ARPU (active)":
        round(
            arpu_active,
            1
        ),

    "Avg tenure (days)":
        round(
            df["tenure_days"].mean()
        ),

    "Total MRR":
        round(
            total_mrr,
            2
        ),

    "MRR lost to churn":
        round(
            mrr_lost,
            2
        ),

    "% revenue loss":
        round(
            revenue_loss_percentage,
            1
        ),

    "CLTV lost":
        round(
            df.loc[
                df["churned"] == 1,
                "cltv"
            ].sum()
        ),

    "Revenue at risk (score>70)":
        round(
            df["revenue_at_risk"].sum(),
            2
        ),

    "Avg complaints / customer":
        round(
            df["complaints"].sum()
            / df["customerid"].nunique(),
            2
        ),

    "Escalation rate %":
        round(
            escalation_rate,
            1
        )
}


# ================================================================
# 7. CHURN BREAKDOWNS
# ================================================================

by_plan = (
    df.groupby(
        "plan_type",
        observed=False
    )["churned"]
    .mean()
    .mul(100)
    .round(1)
)


by_contract = (
    df.groupby(
        "contract_type",
        observed=False
    )["churned"]
    .mean()
    .mul(100)
    .round(1)
)


by_state = (
    df.groupby(
        "state",
        observed=False
    )["churned"]
    .agg(["mean", "sum"])
    .sort_values(
        "mean",
        ascending=False
    )
)

by_state["mean"] = (
    by_state["mean"]
    * 100
).round(1)


by_esc = (
    df.groupby(
        "has_escalation",
        observed=False
    )["churned"]
    .mean()
    .mul(100)
    .round(1)
)


monthly_trend = (
    df[df["churned"] == 1]
    .groupby("cancel_month")
    .size()
)


reasons = (
    df[df["churned"] == 1]
    ["cancellation_reason"]
    .value_counts()
)


# ================================================================
# 8. MONTHLY VS ANNUAL CONTRACT
# ================================================================

if {
    "Monthly",
    "Annual"
}.issubset(
    set(by_contract.index)
):

    kpi[
        "Monthly vs Annual churn %"
    ] = (
        f"{by_contract['Monthly']} vs "
        f"{by_contract['Annual']}"
    )

    annual_churn = max(
        by_contract["Annual"],
        0.1
    )

    kpi[
        "Monthly/Annual multiple"
    ] = round(
        by_contract["Monthly"]
        / annual_churn,
        1
    )


# ================================================================
# 9. PRINT KPIs
# ================================================================

print("\n")
print("=" * 60)
print("                    CHURN KPIs")
print("=" * 60)

for key, value in kpi.items():

    print(
        f"{key:35s}: {value}"
    )


print("\n")
print("=" * 60)
print("CHURN BY PLAN (%)")
print("=" * 60)

print(by_plan)


print("\n")
print("=" * 60)
print("CHURN BY STATE (%)")
print("=" * 60)

print(by_state)


print("\n")
print("=" * 60)
print("ESCALATION → CHURN (%)")
print("=" * 60)

print(by_esc)


# ================================================================
# 10. PLAN × CONTRACT PIVOT
# ================================================================

pivot_plan_contract = (
    df.pivot_table(
        index="plan_type",
        columns="contract_type",
        values="churned",
        aggfunc="mean",
        observed=False
    )
    .mul(100)
    .round(1)
)


print("\n")
print("=" * 60)
print("PLAN × CONTRACT CHURN (%)")
print("=" * 60)

print(
    pivot_plan_contract
)


# ================================================================
# 11. SAVE KPI CSV
# ================================================================

pd.Series(kpi).to_csv(
    "kpi_summary.csv",
    header=["value"]
)


# ================================================================
# 12. CHART FUNCTION
# ================================================================

def save_chart(filename):

    plt.tight_layout()

    plt.savefig(
        f"visuals/{filename}.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()


# ================================================================
# 13. CHART 1 - CHURN BY PLAN
# ================================================================

plt.figure(
    figsize=(7, 4)
)

sns.barplot(
    x=by_plan.index,
    y=by_plan.values
)

plt.title(
    "Churn % by Plan"
)

plt.xlabel(
    "Plan"
)

plt.ylabel(
    "Churn %"
)

save_chart(
    "1_churn_by_plan"
)


# ================================================================
# 14. CHART 2 - CHURN BY CONTRACT
# ================================================================

plt.figure(
    figsize=(7, 4)
)

sns.barplot(
    x=by_contract.index,
    y=by_contract.values
)

plt.title(
    "Churn % by Contract"
)

plt.xlabel(
    "Contract Type"
)

plt.ylabel(
    "Churn %"
)

save_chart(
    "2_churn_by_contract"
)


# ================================================================
# 15. CHART 3 - CHURN BY STATE
# ================================================================

plt.figure(
    figsize=(8, 5)
)

sns.barplot(
    x=by_state["mean"].values,
    y=by_state.index
)

plt.title(
    "Churn % by State"
)

plt.xlabel(
    "Churn %"
)

plt.ylabel(
    "State"
)

save_chart(
    "3_churn_by_state"
)


# ================================================================
# 16. CHART 4 - ESCALATION VS CHURN
# ================================================================

esc_values = (
    by_esc
    .reindex([0, 1])
    .fillna(0)
)

plt.figure(
    figsize=(7, 4)
)

sns.barplot(
    x=[
        "No escalation",
        "Escalated"
    ],
    y=esc_values.values
)

plt.title(
    "Escalation → Churn %"
)

plt.xlabel(
    "Customer Support Status"
)

plt.ylabel(
    "Churn %"
)

save_chart(
    "4_escalation_vs_churn"
)


# ================================================================
# 17. CHART 5 - MONTHLY CHURN TREND
# ================================================================

plt.figure(
    figsize=(9, 4)
)

if len(monthly_trend) > 0:

    monthly_trend.plot(
        marker="o"
    )

else:

    plt.text(
        0.5,
        0.5,
        "No churn data available",
        ha="center",
        va="center"
    )


plt.title(
    "Churned Customers by Month"
)

plt.xlabel(
    "Month"
)

plt.ylabel(
    "Number of Churned Customers"
)

save_chart(
    "5_monthly_churn_trend"
)


# ================================================================
# 18. CHART 6 - TENURE DISTRIBUTION
# ================================================================

plt.figure(
    figsize=(8, 5)
)

sns.histplot(
    data=df,
    x="tenure_days",
    hue="churned",
    bins=25,
    multiple="stack"
)

plt.title(
    "Tenure Distribution"
)

plt.xlabel(
    "Tenure (Days)"
)

plt.ylabel(
    "Customers"
)

save_chart(
    "6_tenure_distribution"
)


# ================================================================
# 19. CHART 7 - CANCELLATION REASONS
# ================================================================

plt.figure(
    figsize=(8, 5)
)

if len(reasons) > 0:

    reasons.sort_values().plot.barh()

else:

    plt.text(
        0.5,
        0.5,
        "No cancellation reasons available",
        ha="center",
        va="center"
    )


plt.title(
    "Cancellation Reasons"
)

plt.xlabel(
    "Number of Customers"
)

plt.ylabel(
    "Cancellation Reason"
)

save_chart(
    "7_cancellation_reasons"
)


# ================================================================
# 20. CHART 8 - CLTV GAP
# ================================================================

plt.figure(
    figsize=(7, 5)
)

sns.boxplot(
    data=df,
    x="churned",
    y="cltv"
)

plt.title(
    "CLTV: Retained (0) vs Churned (1)"
)

plt.xlabel(
    "Churned"
)

plt.ylabel(
    "CLTV"
)

save_chart(
    "8_cltv_gap"
)


# ================================================================
# 21. EXPORT CLEAN DATASET
# ================================================================

df.to_csv(
    "churn_clean_dataset.csv",
    index=False
)


# ================================================================
# 22. RETENTION PRIORITY LIST
# ================================================================

high_priority = df[
    df["risk_tier"].isin(
        ["High", "Med"]
    )
    &
    (df["churned"] == 0)
].sort_values(
    "cltv",
    ascending=False
)


high_priority[
    [
        "customerid",
        "state",
        "plan_type",
        "contract_type",
        "churn_score",
        "risk_tier",
        "cltv",
        "escalations"
    ]
].to_csv(
    "retention_priority_list.csv",
    index=False
)


# ================================================================
# 23. FINAL MESSAGE
# ================================================================

print("\n")
print("=" * 60)
print("                    ANALYSIS COMPLETE")
print("=" * 60)

print("\nGenerated files:")

print("1. kpi_summary.csv")
print("2. churn_clean_dataset.csv")
print("3. retention_priority_list.csv")
print("4. visuals/")

print("\n8 charts created inside the visuals folder.")

print("\nDone!")