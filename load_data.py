"""Create the SQLite database from schema.sql and load both Excel files."""
import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB = BASE / "sales.db"

customers = pd.read_excel(BASE / "data/customers.xlsx")
orders = pd.read_excel(BASE / "data/orders.xlsx")

# Normalise column names and dates
customers.columns = [c.lower() for c in customers.columns]
orders.columns = [c.lower() for c in orders.columns]
customers["join_date"] = pd.to_datetime(customers["join_date"]).dt.strftime("%Y-%m-%d")
orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m-%d")
# Business rule: cancelled orders have zero net amount
orders.loc[orders["order_status"] == "Cancelled", "net_amount_inr"] = 0

con = sqlite3.connect(DB)
con.executescript((BASE / "schema.sql").read_text())
customers.to_sql("customers", con, if_exists="append", index=False)  # parents first
orders.to_sql("orders", con, if_exists="append", index=False)
con.commit()
print("customers:", con.execute("SELECT COUNT(*) FROM customers").fetchone()[0])
print("orders   :", con.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("view rows:", con.execute("SELECT COUNT(*) FROM v_sales").fetchone()[0])
con.close()
