PRAGMA foreign_keys = ON;
DROP VIEW  IF EXISTS v_sales;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id         TEXT PRIMARY KEY,
    customer_name       TEXT NOT NULL,
    email               TEXT,
    city                TEXT NOT NULL,
    state               TEXT,
    customer_segment    TEXT NOT NULL,
    join_date           DATE,            -- ISO yyyy-mm-dd
    acquisition_channel TEXT
);

CREATE TABLE orders (
    order_id        TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id),  -- 1 customer : many orders
    order_date      DATE NOT NULL,       -- ISO yyyy-mm-dd
    product_id      TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_inr  NUMERIC NOT NULL,
    discount_rate   REAL NOT NULL DEFAULT 0,
    net_amount_inr  NUMERIC NOT NULL,    -- 0 for Cancelled orders
    payment_method  TEXT,
    order_status    TEXT NOT NULL CHECK (order_status IN ('Completed','Returned','Cancelled'))
);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date     ON orders(order_date);

-- Joined dataset used by the dashboard
CREATE VIEW v_sales AS
SELECT o.order_id, o.order_date, strftime('%Y-%m', o.order_date) AS order_month,
       o.product_id, o.product_name, o.category, o.quantity, o.unit_price_inr,
       o.discount_rate, o.net_amount_inr, o.payment_method, o.order_status,
       c.customer_id, c.customer_name, c.city, c.state,
       c.customer_segment, c.acquisition_channel
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id;
