-- One row per state and purchase month. Run on the published operations.sqlite.
-- Counts/rates are descriptive. Boundary months are not evidence of a trend collapse.
WITH item_rollup AS (
    SELECT "Order ID" AS order_id, COUNT(*) AS item_lines,
           SUM("Price Cents") AS item_merchandise_cents
    FROM Items
    GROUP BY "Order ID"
), order_base AS (
    SELECT o."Order ID" AS order_id, o.State AS state,
           SUBSTR(o."Purchase Date", 1, 7) AS purchase_month,
           o."Delivery Eligible" AS eligible, o.Late AS late,
           o."Merchandise Cents" AS merchandise_cents,
           COALESCE(i.item_lines, 0) AS item_lines,
           COALESCE(i.item_merchandise_cents, 0) AS item_merchandise_cents
    FROM Orders AS o
    LEFT JOIN item_rollup AS i ON i.order_id = o."Order ID"
), monthly AS (
    SELECT purchase_month, state, COUNT(*) AS orders,
           SUM(eligible) AS eligible_deliveries, SUM(late) AS late_deliveries,
           SUM(item_lines) AS item_lines,
           SUM(CASE WHEN item_lines = 0 THEN 1 ELSE 0 END) AS orders_without_items,
           SUM(merchandise_cents) AS merchandise_cents,
           SUM(item_merchandise_cents) AS item_merchandise_cents,
           1.0 * SUM(late) / NULLIF(SUM(eligible), 0) AS late_rate
    FROM order_base
    GROUP BY purchase_month, state
), workload_ranked AS (
    SELECT *, DENSE_RANK() OVER (
        PARTITION BY purchase_month ORDER BY late_deliveries DESC
    ) AS workload_rank
    FROM monthly
), rate_ranked AS (
    -- Exclude small denominators from this ranking only; retain their data below.
    SELECT purchase_month, state, DENSE_RANK() OVER (
        PARTITION BY purchase_month ORDER BY late_rate DESC
    ) AS rate_rank
    FROM monthly WHERE eligible_deliveries >= 100
)
SELECT w.*, r.rate_rank,
       CASE WHEN w.eligible_deliveries = 0 THEN 'No eligible deliveries'
            WHEN w.eligible_deliveries < 100 THEN 'Below rate-ranking display threshold'
            ELSE 'Included in rate ranking' END AS rate_rank_note,
       CASE WHEN w.purchase_month IN (
                (SELECT MIN(purchase_month) FROM monthly),
                (SELECT MAX(purchase_month) FROM monthly)
            ) THEN 'Source boundary month; coverage may be partial'
            ELSE 'Interior source month; completeness not certified' END AS coverage_note
FROM workload_ranked AS w
LEFT JOIN rate_ranked AS r USING (purchase_month, state)
ORDER BY w.purchase_month, w.workload_rank, w.state;
