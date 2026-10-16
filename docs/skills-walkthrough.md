# Supporting the portfolio in an interview or client call

## Five-minute demonstration

1. Open Overview and explain all four cards, including the delivery denominator.
2. Select SP. Explain why absolute late volume and late rate answer different questions.
3. Open Delivery and sort the state table by Late Rate; explain small denominators.
4. Open Products, select Health Beauty, then explain why freight is not margin.
5. Open Quality & Refresh. Show one exception in the CSV and trace it to its source order.
6. Clear filters and show the matching snapshot fingerprint and reconciliation file.

## What you need to know

| Skill | Be able to do it yourself |
|---|---|
| Python | Read CSVs with encoding/newlines, validate keys, use dictionaries to aggregate, Decimal for money, parse dates, follow an exception stack trace |
| SQL | GROUP BY, COUNT vs DISTINCT COUNT, SUM, joins and their grain, NULLIF for safe rates, filter historical dates |
| Power Query | Find the DataRoot parameter, explain pointer -> snapshot -> CSV, change types explicitly, diagnose a missing-path error |
| Model | Explain one-to-many, single-direction relationships, why Orders and Items are separate facts, why category reaches only Items |
| DAX | Read CALCULATE, SUM, COUNTROWS, DIVIDE and MEDIAN; explain how slicers change filter context |
| Data quality | Show a failed refresh that leaves the previous pointer unchanged; distinguish overlapping events from distinct affected orders |
| Operations | Translate a count/rate into an investigation question without inventing a root cause or claimed savings |
| Handoff | Move the project, set DataRoot, refresh, reconcile and document a metric change |

## Practice tasks

- Run the tests and explain the split-payment/two-item fixture: merchandise is
  BRL 30.30, freight BRL 3.50, payments BRL 33.80, exactly one order.
- Modify a **copy** of that fixture so the delivery occurs at 23:59 on the promised
  day. Explain why it is on time. Move it to the next day and observe the late flag.
- Write a SQL query for RJ late volume and rate, then check Desktop's RJ filter.
- Add a documented explicit DAX measure for delivered-order share of all orders.
- Explain why an absent payment is blank but an order with no item lines has zero
  merchandise in this model, and why both conditions are flagged.
- Describe how you would adapt the pipeline for a client's real schema, data rights,
  update cadence and KPI definitions before quoting implementation work.

If you cannot yet complete a task independently, rehearse it with the documentation
before advertising that specific skill as production-ready. This project can
demonstrate a small, well-scoped cleanup/reporting workflow without implying
advanced statistical modeling or enterprise Power BI administration experience.
