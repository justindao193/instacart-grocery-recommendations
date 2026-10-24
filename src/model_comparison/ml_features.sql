-- SQLite query; the Python runner supplies the POWER function.
-- 1. Give training and validation their own target basket and earlier-history cutoff.
WITH prediction_points AS (
    SELECT e.user_id,'training' AS stage,o.order_id AS target_order_id,
           o.order_number AS target_order_number,o.order_number-1 AS history_max_order
    FROM evaluation_plan e JOIN orders o ON o.user_id=e.user_id
      AND o.order_number=e.validation_history_max_order_number
    WHERE o.eval_set='prior' AND o.order_number>=2
    UNION ALL
    SELECT e.user_id,'validation',e.validation_order_id,
           e.validation_history_max_order_number+1,e.validation_history_max_order_number
    FROM evaluation_plan e
-- 2. Count the actual earlier orders available at each prediction point.
), history_sizes AS (
    SELECT p.user_id,p.stage,COUNT(*) AS history_orders
    FROM prediction_points p JOIN orders o ON o.user_id=p.user_id
      AND o.eval_set='prior' AND o.order_number<=p.history_max_order
    GROUP BY p.user_id,p.stage
-- 3. Only previously bought products can become candidates. Build clues from history.
), features AS (
    SELECT p.user_id,p.stage,p.target_order_id,p.target_order_number,p.history_max_order,
           i.product_id,COUNT(*) AS purchase_orders,
           MAX(o.order_number) AS last_purchase_order,
           ROUND(SUM(POWER(0.5,(p.history_max_order-o.order_number)/5.0)),12)
               AS recency_score
    FROM prediction_points p JOIN orders o ON o.user_id=p.user_id
      AND o.eval_set='prior' AND o.order_number<=p.history_max_order
    JOIN order_products__prior i ON i.order_id=o.order_id
    GROUP BY p.user_id,p.stage,p.target_order_id,p.target_order_number,
             p.history_max_order,i.product_id
)
-- 4. Attach next-basket answers after making the clues. Never use these as inputs.
SELECT f.*,h.history_orders,
       f.purchase_orders*1.0/h.history_orders AS purchase_share,
       f.history_max_order-f.last_purchase_order AS orders_since_last_purchase,
       CAST(t.product_id IS NOT NULL AS INTEGER) AS bought_next
FROM features f JOIN history_sizes h ON h.user_id=f.user_id AND h.stage=f.stage
LEFT JOIN order_products__prior t ON t.order_id=f.target_order_id
  AND t.product_id=f.product_id;
