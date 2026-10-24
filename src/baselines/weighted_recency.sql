-- Fixed first experiment: weight halves every five order positions, not days.
-- 1. Add purchase weights for each customer/product: newer orders count more.
WITH history AS (
    SELECT o.user_id,i.product_id,
           -- A purchase five order positions older gets half the weight; round for stable ties.
           ROUND(SUM(POWER(0.5,
               (e.validation_history_max_order_number-o.order_number)/5.0)),12) AS recency_score,
           COUNT(*) AS purchase_orders,
           MAX(o.order_number) AS last_purchase_order_number
    FROM orders o JOIN evaluation_plan e ON o.user_id=e.user_id
    JOIN order_products__prior i ON i.order_id=o.order_id
    -- Exclude validation and final baskets from the purchase weights.
    WHERE o.eval_set='prior'
      AND o.order_number<=e.validation_history_max_order_number
    GROUP BY o.user_id,i.product_id
-- 2. Rank each customer's products by weighted score, then recency and product ID.
), ranked AS (
    SELECT *,ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY recency_score DESC,last_purchase_order_number DESC,product_id
    ) AS recommendation_rank FROM history
)
-- 3. Add product names and return up to five products for each customer.
SELECT r.*,p.product_name FROM ranked r JOIN products p USING(product_id)
WHERE recommendation_rank<=5 ORDER BY user_id,recommendation_rank;
