# Sales Dashboard (Flask + SQLite + Chart.js)

Loads `customers.xlsx` and `orders.xlsx` into a relational database, joins them on `Customer_ID`
through a SQL view, and serves an interactive one-page dashboard.

## Project structure
```
schema.sql              tables, PK/FK, indexes, v_sales join view
load_data.py            reads the Excel files and loads sales.db
app.py                  Flask app: page + JSON API (SQL queries, filters)
templates/dashboard.html  dashboard page (KPIs, 5 charts, top-5 table, filters)
data/                   the two source Excel files
Dockerfile              optional container setup
```

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python load_data.py             # creates sales.db (60 customers, 240 orders)
python app.py                   # open http://localhost:5000
```
Docker alternative:
```bash
docker build -t sales-dashboard . && docker run -p 5000:5000 sales-dashboard
```

## Database design
- `customers.customer_id` = PRIMARY KEY.
- `orders.order_id` = PRIMARY KEY; `orders.customer_id` = FOREIGN KEY -> `customers` (one customer, many orders).
- Dates stored as ISO `YYYY-MM-DD`; amounts numeric; `order_status` restricted by a CHECK constraint.
- `v_sales` = `orders JOIN customers ON customer_id`; every dashboard query reads from this view.

## Metric definitions
| Metric | Definition |
|---|---|
| Total net revenue | `SUM(net_amount_inr)` (cancelled orders are 0) |
| Total orders | `COUNT(DISTINCT order_id)` (all statuses) |
| Unique customers | `COUNT(DISTINCT customer_id)` |
| Average order value | revenue / distinct non-cancelled orders |
| Repeat customers (bonus) | customers with 2+ non-cancelled orders |
| Top 5 products (bonus) | products ranked by net revenue |

## Filters
Date range (from/to), product category, customer segment, city, order status. All are
applied in SQL with parameterised queries and update every KPI and chart together.

## Assumptions
- Returned orders keep their net amount in revenue (per the brief); filter Order status = Returned to isolate them.
- "Total orders" counts all orders incl. cancelled; the card also shows the non-cancelled count used for AOV.
- Data checks passed: no duplicate IDs, no orphan `Customer_ID`, no nulls, cancelled orders all have net 0.
- 1 of the 60 customers has no orders, so unique customers (with orders) = 59.
- Chart.js loads from a CDN, so the browser needs internet access.

## Expected values with no filters
Revenue ₹11,59,206 · Orders 240 (204 non-cancelled) · Customers 59 · AOV ₹5,682.38
