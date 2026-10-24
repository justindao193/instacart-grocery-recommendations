-- Known means present in this customer's eligible history, not all prior data.
-- 1. Build the set of products seen before each validation cutoff.
WITH history_products AS (
    SELECT DISTINCT o.user_id, i.product_id
    FROM orders o JOIN evaluation_plan e ON o.user_id=e.user_id
    JOIN order_products__prior i ON o.order_id=i.order_id
    WHERE o.eval_set='prior'
      AND o.order_number<=e.validation_history_max_order_number
-- 2. Classify actual basket products as familiar/new and matched/missed.
), customer_baskets AS (
    SELECT e.user_id, e.validation_order_id,
           COUNT(*) AS actual_products,
           COUNT(*) FILTER (WHERE h.product_id IS NOT NULL) AS known_products,
           COUNT(*) FILTER (WHERE h.product_id IS NULL) AS new_products,
           COUNT(*) FILTER (WHERE r.product_id IS NOT NULL) AS matched_products,
           COUNT(*) FILTER (WHERE r.product_id IS NOT NULL AND h.product_id IS NULL) AS invalid_new_matches
    FROM evaluation_plan e
    JOIN order_products__prior i ON i.order_id=e.validation_order_id
    LEFT JOIN history_products h ON h.user_id=e.user_id AND h.product_id=i.product_id
    LEFT JOIN personal_recommendations r ON r.user_id=e.user_id AND r.product_id=i.product_id
    GROUP BY e.user_id,e.validation_order_id
)
-- 3. Separate familiar misses due to ranking from the five-slot capacity limit.
SELECT *, known_products-matched_products AS known_misses,
       GREATEST(known_products-5,0) AS known_misses_beyond_five_slot_capacity,
       LEAST(5,known_products)-matched_products AS recoverable_with_perfect_rebuy_ranking,
       -- This perfect-rank ceiling uses hidden answers for diagnosis, not prediction.
       LEAST(5,known_products)*1.0/actual_products AS perfect_rebuy_recall_at_5
FROM customer_baskets ORDER BY user_id;
