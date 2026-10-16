# Commerce operations: from linked CSVs to decisions

## Problem and deliverable

An operations reviewer needs a quick way to compare delivery workload, service
rates and merchandise categories without repeatedly joining six source files.
This independent portfolio project uses Olist's historical Kaggle data, not paid
client work. The deliverable is a four-page native Power BI report backed by a
repeatable Python cleaning pipeline and independently reconciled SQLite tables.

## Findings worth investigating

- São Paulo and Rio de Janeiro account for 3,315 of 6,534 late deliveries (50.7%).
  Their late rates differ: 4.5% and 12.1%, respectively. Review volume alongside
  population and rate; the largest workload does not imply the worst service.
- Health Beauty contributes BRL 1,233,131.72 in delivered merchandise across
  9,465 item lines. Its freight-to-merchandise ratio is about 14.5%, compared
  with 16.6% across all delivered items. This is a descriptive comparison, not
  a profitability measure.
- Eight delivered orders lack valid timing. Excluding them explicitly makes
  the delivery denominator auditable rather than silently treating them as on time.
- 1,348 orders have a payment-versus-items-and-freight difference. The report
  calls item price merchandise value, not collected cash or recognized revenue.

These observations suggest where to investigate. The data cannot establish
causes, current backlog, operating costs, inventory, margin or verified savings.

## Technical approach

Orders and item lines remain separate facts. Payments aggregate to order grain
before joining, avoiding multiplication of amounts when orders contain several
items or payments. Currency remains integer cents through Python and SQLite.
Source rows are retained; exceptions are exported and counted at their stated
grains. Duplicate keys, orphan references and invalid amounts stop publication.

An immutable snapshot contains typed CSVs, SQLite, hashes and reconciliation
results. Only a successful build replaces `latest.json`. Power Query reads that
pointer; DAX recalculates under month, state and product filter context.

## A two-minute demonstration

1. Open Overview and explain the 99,441-order population and 93.2% on-time rate.
2. Select January 2018: confirm 7,269 orders and 94.3% on time. Clear the filter.
3. Open Delivery and compare SP volume with RJ rate using the state table.
4. Open Products, select Health Beauty, and explain merchandise versus freight.
5. Open Quality & Refresh: explain overlapping checks, excluded timing, snapshot
   identity and the distinction between rebuilding data and refreshing Desktop.

See the user guide and skills walkthrough for maintenance and interview practice.
Source data and derived report data retain CC BY-NC-SA 4.0; reusable original
code is MIT licensed. This historical example is for noncommercial demonstration.
