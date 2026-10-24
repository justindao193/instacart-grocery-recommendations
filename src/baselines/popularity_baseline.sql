-- Validation baseline: the same five products for everyone.
-- Pool only the eligible history of customers in evaluation_plan.
-- Each customer's last prior basket and final train basket stay out.
-- 1. Keep only each evaluation customer's allowed earlier orders.
WITH eligible_orders AS (
    SELECT o.order_id
    FROM orders o
    JOIN evaluation_plan e ON o.user_id = e.user_id
    WHERE o.eval_set = 'prior'
      AND o.order_number <= e.validation_history_max_order_number
),
-- 2. Count how many eligible orders contain each product.
product_counts AS (
    SELECT i.product_id, COUNT(DISTINCT i.order_id) AS orders_containing_product
    FROM order_products__prior i
    JOIN eligible_orders h ON i.order_id = h.order_id
    GROUP BY i.product_id
),
-- 3. Count all eligible orders for the percentage denominator.
history_size AS (
    SELECT COUNT(*) AS eligible_history_orders FROM eligible_orders
)
-- 4. Rank products by order count; product ID breaks ties.
SELECT ROW_NUMBER() OVER (
           ORDER BY c.orders_containing_product DESC, c.product_id
       ) AS recommendation_rank,
       c.product_id,
       p.product_name,
       c.orders_containing_product,
       h.eligible_history_orders,
       100.0 * c.orders_containing_product
           / NULLIF(h.eligible_history_orders, 0) AS pct_of_history_orders
FROM product_counts c
JOIN products p ON c.product_id = p.product_id
-- Attach the same total-order denominator to every product.
CROSS JOIN history_size h
ORDER BY recommendation_rank
-- Return only the five highest-ranked products.
LIMIT 5;
