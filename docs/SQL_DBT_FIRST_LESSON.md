# Your first Commerce SQL/dbt lesson

Allow 30–45 minutes for this session, or stop after any exercise. The goal is to understand a small part of the workflow and change it yourself. Running the finished build is setup, not a test of your knowledge.

## 1. What are we looking at?

An **order** is a purchase. An order can have several **item lines** and several **payment rows**. A table's **grain** tells you what one row represents.

Our two reporting facts have different grains:

- `fct_orders`: one row represents one order.
- `fct_order_items`: one row represents one item line within an order.

Suppose an order contains two items and uses two payment transactions. Joining the raw item rows directly to the raw payment rows creates four matches. Summing the joined payment values would count each payment twice. We first add up each table to one row per order, then join those summaries. This is why the intermediate layer exists.

**Try explaining:** Why is the number of joined rows not necessarily the number of orders? Use the two-items/two-payments example. If the answer is unclear, draw the four matching pairs before moving on.

## 2. Run the verified demonstration

Double-click **Run Demo SQL.cmd** in the project folder. The end of the output shows the row counts and build status. A failure means the checks stopped publication; it does not mean you should delete the tests.

For commands below, open PowerShell in the project folder and define this session's Python shortcut:

```powershell
$commercePython = "$env:USERPROFILE\.local\commerce-sql\venv\Scripts\python.exe"
```

Another computer should use its installed environment's Python path from `dbt/README.md`.

## 3. Read five rows

```powershell
& $commercePython src/query_dbt.py --sql "select order_id, state, item_count from analytics_marts.fct_orders order by order_id limit 5"
```

Read this SQL aloud:

- `SELECT` chooses the columns you want to see.
- `FROM` names the table.
- `ORDER BY` makes the example deterministic.
- `LIMIT 5` returns only five rows.

**Your variation:** Change the query to show `payment_cents` as well. Do not rewrite the build. Expected result: five rows, one additional column, with the original three columns still present.

## 4. Count orders, then filter

```powershell
& $commercePython src/query_dbt.py --sql "select count(*) as orders from analytics_marts.fct_orders"
& $commercePython src/query_dbt.py --sql "select count(*) as orders from analytics_marts.fct_orders where state = 'SP'"
```

`COUNT(*)` counts rows. Because the grain is one row per order, that is also the order count. `WHERE` keeps rows satisfying a condition. `AS orders` labels the result.

For the unchanged historical demo, the checks are **99,441 orders** and **41,746 SP orders**. A different source snapshot may legitimately produce different values.

**Your variation:** Count RJ orders. Then explain why counting rows in the item table would answer a different question.

## 5. Add a rate with an explicit denominator

```powershell
& $commercePython src/query_dbt.py --sql "select sum(late) as late_deliveries, sum(delivery_eligible) as eligible_deliveries, 100.0 * sum(late) / nullif(sum(delivery_eligible), 0) as late_percent from analytics_marts.fct_orders"
```

`late` and `delivery_eligible` contain 0 or 1, so adding them counts the qualifying orders. The demo has **6,534 late deliveries out of 96,470 eligible deliveries**, or approximately **6.77% late**. The complementary on-time rate is approximately **93.23%**.

Not every order belongs in that denominator. Canceled orders and delivered orders without valid timing cannot establish a delivery-on-time rate. `NULLIF(..., 0)` returns a missing value if the denominator is zero, avoiding division by zero. Missing does not mean zero percent.

**Your variation:** Filter the same calculation to SP. Explain why total orders is a less appropriate denominator for this particular metric.

## 6. Group the calculation

```powershell
& $commercePython src/query_dbt.py
```

The default query uses `GROUP BY state` to calculate counts and rates for each state. SP can have more late deliveries while another state has a worse late percentage. Workload and rate are both useful, but they answer different questions.

**Your variation:** Write a query that shows only states with more than 1,000 eligible deliveries, ordered by late percentage. You will need `HAVING` to filter an aggregated result. Try first; then use this hint:

```sql
select state,
       sum(late) as late_deliveries,
       sum(delivery_eligible) as eligible_deliveries,
       100.0 * sum(late) / nullif(sum(delivery_eligible), 0) as late_percent
from analytics_marts.fct_orders
group by state
having sum(delivery_eligible) > 1000
order by late_percent desc;
```

## 7. Locate the logic in dbt

Open these files in order:

1. `dbt/models/staging/stg_orders.sql`: where source text becomes typed timestamps and named columns.
2. `dbt/models/intermediate/int_payment_totals.sql`: where multiple payments become one order-level amount.
3. `dbt/models/intermediate/int_order_details.sql`: where aggregates join and delivery eligibility is defined.
4. `dbt/models/marts/fct_orders.sql`: where reporting fields and delivery bands are selected.
5. `dbt/tests/reconcile_money.sql`: a check that returns a row only when totals disagree.

`ref('stg_payments')` tells dbt which other model this query needs. dbt follows those references to build the dependency graph. A dbt data test passes when its query returns zero failing rows. A successful test cannot prove every business assumption is correct; the metric definition still needs to make sense.

**Check your understanding:** Find the SQL that preserves a missing payment as NULL. Why would replacing every NULL with zero hide useful information?

## What comes next

Repeat these exercises with a different state before moving on. Then practice joins using the small fictional fixtures, inspect a failing key test, and make a controlled business-rule change in a separate working database. Keep published snapshots unchanged. The next session can begin with your explanation of grain and the two-items/two-payments example; mistakes are a starting point for teaching, not a reason to rush ahead.
