-- Score one hidden PRIOR basket per evaluation customer.
-- validation_recommendations is the five-row output of popularity_baseline.sql.
-- 1. Count actual basket products and matches with the general list.
WITH basket_scores AS (
    SELECT e.user_id, e.validation_order_id,
           COUNT(DISTINCT i.product_id) AS actual_products,
           COUNT(DISTINCT CASE WHEN r.product_id IS NOT NULL
                               THEN i.product_id END) AS matched_products
    FROM evaluation_plan e
    JOIN order_products__prior i ON i.order_id = e.validation_order_id
    LEFT JOIN validation_recommendations r ON i.product_id = r.product_id
    GROUP BY e.user_id, e.validation_order_id
)
-- 2. Calculate each customer's precision, recall and any-match flag.
SELECT *,
       matched_products / 5.0 AS precision_at_5,
       matched_products * 1.0 / actual_products AS recall_at_5,
       CAST(matched_products > 0 AS INTEGER) AS hit_at_5
FROM basket_scores
ORDER BY user_id;
