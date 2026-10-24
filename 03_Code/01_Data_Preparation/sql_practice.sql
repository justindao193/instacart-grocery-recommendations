-- Run from the project folder using: .venv/Scripts/python.exe 03_Code/01_Data_Preparation/run_sql_practice.py
-- The database is opened read-only. These are teaching examples, not business findings.

-- 1. A user's order sequence: one row per order.
-- Show one customer's orders, from earliest to latest.
SELECT user_id,order_id,order_number,eval_set,product_lines,repeat_product_lines
FROM order_summary WHERE user_id=1 ORDER BY order_number;

-- 2. Products in that user's first order: one row per product line.
-- Show the products in that customer's first basket.
SELECT order_id,product_name,add_to_cart_order,reordered
FROM learning_order_items WHERE order_number=1 ORDER BY add_to_cart_order;

-- 3. Check a counting unit across the prior history, without ranking products.
-- Add the saved prior-history counts; these are not recommendation scores.
SELECT SUM(prior_product_lines) AS prior_product_lines,
       SUM(prior_repeat_lines) AS repeat_product_lines
FROM product_history_metrics;
