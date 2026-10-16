-- Run against data/processed/snapshots/<snapshot>/operations.sqlite.
-- All monetary storage is integer cents. No item/payment fan-out.

-- 1. Where is the largest late-delivery workload in the historical snapshot?
SELECT "State", SUM("Delivery Eligible") AS eligible_deliveries,
       SUM("Late") AS late_deliveries,
       ROUND(100.0 * SUM("Late") / NULLIF(SUM("Delivery Eligible"), 0), 2) AS late_percent
FROM "Orders"
GROUP BY "State"
ORDER BY late_deliveries DESC;

-- 2. Which categories contribute delivered merchandise and freight?
SELECT "Category", COUNT(*) AS delivered_item_lines,
       ROUND(SUM("Price Cents") / 100.0, 2) AS merchandise_brl,
       ROUND(SUM("Freight Cents") / 100.0, 2) AS freight_brl,
       ROUND(100.0 * SUM("Freight Cents") / NULLIF(SUM("Price Cents"), 0), 2) AS freight_to_merchandise_percent
FROM "Items"
WHERE "Status" = 'Delivered'
GROUP BY "Category"
ORDER BY merchandise_brl DESC;

-- 3. Are payments equal to merchandise plus freight? Keep discrepancies visible.
SELECT COUNT(*) AS orders_with_payment_difference,
       SUM("Payment Difference Cents") / 100.0 AS net_difference_brl
FROM "Orders"
WHERE "Payment Difference Cents" != 0;

-- 4. Month trends use purchase date consistently, not delivery month.
SELECT SUBSTR("Purchase Date", 1, 7) AS purchase_month,
       COUNT(*) AS orders, SUM("Delivery Eligible") AS eligible_deliveries,
       SUM("Late") AS late_deliveries
FROM "Orders"
GROUP BY purchase_month
ORDER BY purchase_month;
