-- Rebuy candidates only. No validation or final basket supplies features.
-- 1. Count purchases and find the latest purchase for each customer/product.
WITH product_history AS (
    SELECT o.user_id, i.product_id,
           COUNT(DISTINCT o.order_id) AS purchase_orders,
           MAX(o.order_number) AS last_purchase_order_number
    FROM orders o
    JOIN evaluation_plan e ON o.user_id = e.user_id
    JOIN order_products__prior i ON o.order_id = i.order_id
    -- Only purchases before that customer's validation basket may contribute.
    WHERE o.eval_set = 'prior'
      AND o.order_number <= e.validation_history_max_order_number
    GROUP BY o.user_id, i.product_id
-- 2. Rank products separately per customer: count, recency, then product ID.
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY purchase_orders DESC, last_purchase_order_number DESC, product_id
    ) AS recommendation_rank
    FROM product_history
)
-- 3. Add readable names and keep up to five suggestions per customer.
SELECT r.*, p.product_name
FROM ranked r JOIN products p ON r.product_id = p.product_id
WHERE recommendation_rank <= 5
ORDER BY user_id, recommendation_rank;
