-- Final inputs only: this query never reads target product contents or creates answer labels.
-- 1. Count eligible earlier orders at each customer's fixed final cutoff.
WITH sizes AS (
    SELECT t.user_id,COUNT(*) AS history_orders
    FROM targets t JOIN source.orders o ON o.user_id=t.user_id
      AND o.eval_set='prior' AND o.order_number<=t.history_max_order
    GROUP BY t.user_id
-- 2. Sum each familiar product's earlier purchases and fixed recency points.
), purchases AS (
    SELECT t.user_id,i.product_id,COUNT(*) AS purchase_orders,
           MAX(o.order_number) AS last_purchase_order,
           ROUND(SUM(POWER(0.5,(t.history_max_order-o.order_number)/5.0)),12) AS recency_score
    FROM targets t JOIN source.orders o ON o.user_id=t.user_id
      AND o.eval_set='prior' AND o.order_number<=t.history_max_order
    JOIN source.order_products__prior i ON i.order_id=o.order_id
    GROUP BY t.user_id,i.product_id
)
-- 3. Supply unchanged feature definitions using the refreshed earlier history.
SELECT p.*,s.history_orders,p.purchase_orders*1.0/s.history_orders AS purchase_share,
       t.history_max_order-p.last_purchase_order AS orders_since_last_purchase
FROM purchases p JOIN sizes s ON s.user_id=p.user_id
JOIN targets t ON t.user_id=p.user_id;
