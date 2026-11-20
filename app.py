"""Flask backend: serves the dashboard page and a JSON API driven by SQL queries."""
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, render_template, request

BASE = Path(__file__).parent
DB = BASE / "sales.db"
app = Flask(__name__)


def query(sql, params=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def build_where():
    """Build a parameterised WHERE clause from the query-string filters."""
    clauses, params = [], []
    if request.args.get("start"):
        clauses.append("order_date >= ?"); params.append(request.args["start"])
    if request.args.get("end"):
        clauses.append("order_date <= ?"); params.append(request.args["end"])
    for arg, col in [("category", "category"), ("segment", "customer_segment"),
                     ("city", "city"), ("status", "order_status")]:
        if request.args.get(arg):
            clauses.append(f"{col} = ?"); params.append(request.args[arg])
    return ("WHERE " + " AND ".join(clauses)) if clauses else "", params


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/filters")
def filters():
    d = lambda col: [r["v"] for r in query(f"SELECT DISTINCT {col} AS v FROM v_sales ORDER BY 1")]
    rng = query("SELECT MIN(order_date) mn, MAX(order_date) mx FROM v_sales")[0]
    return jsonify(categories=d("category"), segments=d("customer_segment"),
                   cities=d("city"), statuses=d("order_status"),
                   min_date=rng["mn"], max_date=rng["mx"])


@app.route("/api/dashboard")
def dashboard():
    w, p = build_where()
    kpi = query(f"""
        SELECT COALESCE(SUM(net_amount_inr),0)                         AS revenue,
               COUNT(DISTINCT order_id)                                AS total_orders,
               COUNT(DISTINCT customer_id)                             AS unique_customers,
               COUNT(DISTINCT CASE WHEN order_status <> 'Cancelled'
                                   THEN order_id END)                  AS active_orders
        FROM v_sales {w}""", p)[0]
    kpi["avg_order_value"] = round(kpi["revenue"] / kpi["active_orders"], 2) if kpi["active_orders"] else 0

    # Repeat customers = customers with 2+ non-cancelled orders in the filtered data
    kpi["repeat_customers"] = query(f"""
        SELECT COUNT(*) AS n FROM (
            SELECT customer_id FROM v_sales {w + (' AND' if w else 'WHERE')} order_status <> 'Cancelled'
            GROUP BY customer_id HAVING COUNT(DISTINCT order_id) > 1)""", p)[0]["n"]

    def group(col, order="revenue DESC", limit=""):
        return query(f"""SELECT {col} AS label, COALESCE(SUM(net_amount_inr),0) AS revenue,
                                COUNT(DISTINCT order_id) AS orders
                         FROM v_sales {w} GROUP BY {col} ORDER BY {order} {limit}""", p)

    return jsonify(
        kpi=kpi,
        monthly=group("order_month", order="label"),
        category=group("category"),
        segment=group("customer_segment"),
        city=group("city"),
        status=query(f"""SELECT order_status AS label, COUNT(DISTINCT order_id) AS orders
                         FROM v_sales {w} GROUP BY order_status ORDER BY orders DESC""", p),
        top_products=group("product_name", limit="LIMIT 5"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
