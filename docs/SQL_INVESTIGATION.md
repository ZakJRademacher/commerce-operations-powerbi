# Delivery priorities: one SQL investigation

I compared destination states within each purchase month to see where late-order workload and late rates point to different priorities. The results give an operations reviewer specific source records to investigate.

## Worked result: July 2018

| State | Eligible deliveries | Late deliveries | Late rate | Workload rank | Rate rank among N ≥ 100 |
|---|---:|---:|---:|---:|---:|
| SP | 2,712 | 100 | 3.69% | 1 | 6 |
| RJ | 696 | 17 | 2.44% | 2 | 7 |
| AL | 22 | 4 | 18.18% | 9 | Not ranked |

The all-period state ranking is not the same as a monthly ranking. In this month SP supplies the largest investigation workload, while AL's high rate comes from a small denominator. Its 22 eligible deliveries and four late deliveries remain visible; only its rate ranking is suppressed. The 100-eligible rule is a display convention, not a significance test. July is an interior source month, not a certified accounting close.

**Action:** begin with the 100 late SP orders in July, check purchase/delivery dates against source records and request carrier, route and service-promise information before assigning a cause. Review AL separately as a small-population lead rather than treating its rate as the strongest established service problem. Recheck this decision for a different month; do not carry the all-period conclusion into every slice.

## Reproduce with standard-library Python

From the repository root with Python 3.11+:

```sh
python src/prepare_demo.py
python tools/investigate_delivery.py
python -m unittest discover -s tests -v
```

Read [the SQL](../sql/delivery_priorities.sql), [all 565 state/month results](../deliverables/delivery-investigation/state-month.csv) and [control totals](../deliverables/delivery-investigation/controls.json). The command reads the existing snapshot database without modifying it. An alternative snapshot can be supplied with `--database /path/to/operations.sqlite`; `--output /path/to/results` keeps a separate investigation. No dbt install or hosted warehouse is required.

## Read the query in stages

1. **item_rollup:** count and sum item lines to one row per order. Joining raw items directly would repeat an order's eligibility and late flag once per item.
2. **order_base:** left-join that single summary to each order. Orders without items remain present with zero item lines. Money stays in integer cents; no payment rows are joined here.
3. **monthly:** group by state and purchase month. Sum eligible and late flags, then divide late by eligible using `NULLIF` so an empty denominator remains blank.
4. **workload_ranked / rate_ranked:** apply `DENSE_RANK` within each month. Tied values share a rank. Rate ranking uses unrounded ratios and only groups with at least 100 eligible deliveries.
5. **final join:** attach qualifying rate ranks to all workload rows. Missing ranks do not remove a population or turn its rate into zero. First/last source months receive explicit coverage warnings.

The 565 cells sum back to 99,441 orders, 112,650 item lines, 96,470 eligible deliveries, 6,534 late deliveries and 1,359,164,370 merchandise cents. The item's sum independently matches order merchandise in every state/month cell. Counts, flags and ranks were also compared with separate raw-CSV/datetime/Decimal/Fraction controls. The included tests exercise fan-out, ties, zero denominators, small populations and rank reset across months.

## Limits and handoff

These rankings describe the historical snapshot. They help choose records to review, but do not assign fault or estimate what an intervention would achieve. Purchase month differs from delivery month. States can differ in order mix and routes. No carrier-level intervention, cost saving, profit or universal statistical confidence is established. The existing Power BI report retains its current calculations and layout; these CSVs are an analysis companion. The separate local SQL/dbt extension is outside this published workflow.

Source data and derived outputs retain [Olist's CC BY-NC-SA 4.0 terms](source-and-license.md); original code remains MIT.
