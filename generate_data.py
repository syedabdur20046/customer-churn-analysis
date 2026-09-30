"""Creates the customer_churn DB in MySQL and loads 210 synthetic OTT customers.
Skip this script if you already have the real 3 tables."""
import os
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

USER = os.getenv("DB_USER", "root")
PWD = os.getenv("DB_PASS", "mypassword")
HOST = os.getenv("DB_HOST", "localhost")
DB = "customer_churn"

# 1) run schema.sql
conn = pymysql.connect(host=HOST, user=USER, password=PWD)
with open(os.path.join(os.path.dirname(__file__), "schema.sql")) as f:
    with conn.cursor() as cur:
        for stmt in f.read().split(";"):
            if stmt.strip():
                cur.execute(stmt)
conn.commit()
conn.close()

# 2) generate data
rng = np.random.default_rng(42)
N = 210
ids = np.arange(1001, 1001 + N)

states = ["Karnataka", "Maharashtra", "Delhi", "Tamil Nadu", "Telangana", "Gujarat"]
state = rng.choice(states, N, p=[0.25, 0.2, 0.15, 0.15, 0.15, 0.10])
plan = rng.choice(["Basic", "Standard", "Premium"], N, p=[0.45, 0.30, 0.25])
contract = rng.choice(["Monthly", "Annual"], N, p=[0.6, 0.4])
price = {"Basic": 149, "Standard": 299, "Premium": 499}
charges = np.array([price[p] for p in plan], dtype=float)

start = pd.to_datetime("2019-01-01") + pd.to_timedelta(rng.integers(0, 365 * 5, N), unit="D")

p_churn = (0.08 + 0.22 * (plan == "Basic") + 0.05 * (plan == "Standard")
           + 0.25 * (contract == "Monthly") - 0.05 * (contract == "Annual")
           + 0.10 * (state == "Karnataka")).clip(0.02, 0.9)
churned = rng.random(N) < p_churn

# cancellation dates: spike in Sep 2024
months = pd.date_range("2023-06-01", "2024-12-01", freq="MS")
w = np.where(months == pd.Timestamp("2024-09-01"), 6, 1).astype(float)
w /= w.sum()
cancel = []
for i in range(N):
    if churned[i]:
        d = rng.choice(months, p=w) + pd.Timedelta(days=int(rng.integers(0, 28)))
        d = max(d, start[i] + pd.Timedelta(days=30))
        cancel.append(d)
    else:
        cancel.append(pd.NaT)
cancel = pd.Series(cancel)
reasons = rng.choice(["Competitor", "Pricing", "Content", "Technical issue"], N, p=[0.25, 0.35, 0.3, 0.1])

end = cancel.fillna(pd.Timestamp.now().normalize())
tenure_m = ((end - pd.Series(start)).dt.days / 30).clip(lower=1)
cltv = (charges * tenure_m * rng.uniform(0.9, 1.3, N)).round(2)

score = (25 + 20 * (plan == "Basic") + 20 * (contract == "Monthly") + 10 * (state == "Karnataka")
         + 25 * churned + rng.normal(0, 8, N)).clip(1, 100).astype(int)

customer = pd.DataFrame({
    "customerid": ids,
    "name": [f"Customer_{i}" for i in ids],
    "country": "India",
    "State": state,
    "gender": rng.choice(["Male", "Female"], N),
    "dob": pd.to_datetime("1970-01-01") + pd.to_timedelta(rng.integers(0, 365 * 35, N), unit="D"),
    "interests": rng.choice(["Movies", "Sports", "Series", "Kids", "News"], N),
    "pincode": rng.integers(110001, 800000, N).astype(str),
})
subscription = pd.DataFrame({
    "customerid": ids,
    "subscription_start_date": start,
    "subscription_type": np.where(contract == "Monthly", "Monthly Plan", "Annual Plan"),
    "renewal_date": start + pd.to_timedelta(np.where(contract == "Monthly", 30, 365), unit="D"),
    "plan_type": plan,
    "contract_type": contract,
    "cancellation_date": cancel,
    "cancellation_reason": np.where(churned, reasons, None),
    "monthly_charges": charges,
    "cltv": cltv,
    "churn_score": score,
})

rows = []
for i in range(N):
    n_c = rng.choice([0, 1, 2, 3], p=[0.35, 0.3, 0.2, 0.15]) if not churned[i] else rng.choice([1, 2, 3], p=[0.3, 0.4, 0.3])
    for _ in range(n_c):
        esc = int(rng.random() < (0.6 if churned[i] else 0.05))
        rows.append({
            "customerid": ids[i],
            "complaint_date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(rng.integers(0, 700))),
            "Escalations": esc,
            "csat_score": int(rng.integers(1, 3) if esc else rng.integers(2, 6)),
            "col_1": rng.choice(["Billing", "Streaming", "Content", "App"]),
            "comment": "Auto-generated complaint",
        })
support = pd.DataFrame(rows)

# 3) load
engine = create_engine(f"mysql+pymysql://{USER}:{PWD}@{HOST}/{DB}")
customer.to_sql("db_customer", engine, if_exists="append", index=False)
subscription.to_sql("db_subscription", engine, if_exists="append", index=False)
support.to_sql("db_support", engine, if_exists="append", index=False)
print(f"Loaded {len(customer)} customers, {len(support)} complaints into {DB}")
