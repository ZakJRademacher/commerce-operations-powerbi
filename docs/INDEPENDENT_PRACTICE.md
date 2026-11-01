# Independent Commerce SQL practice

Use a disposable copy. Finish your attempt before consulting [the worked investigation](SQL_INVESTIGATION.md). Running the supplied query alone is setup, not an assessment of independent skill.

## Your task

Choose June 2018 rather than the worked July example. Write your own query returning every state's eligible count, late count, late rate and workload rank. Join item context without multiplying orders. Then change the rate-ranking display threshold to 200 for this exercise only; preserve all original populations and rates.

Record: the business question; what one row represents before and after each join; the highest-workload state; a different rate-based lead; and the extra source evidence needed before assigning cause. Explain one small-population row and one tie.

## Acceptance checks

- Your June counts reconcile independently to Orders, and your item totals reconcile to Items for the same order population.
- One order with two items contributes one eligible/late flag, not two.
- Raising the display threshold changes only rank eligibility; counts, rates and exported rows remain unchanged.
- Zero eligible deliveries produce a blank rate. Ties share a rank, and state sorting makes the output deterministic.
- Explain why neither destination nor rank proves a carrier caused the issue, and why the month is based on purchase date.

Keep your SQL, output, checks and a short explanation together. Mark it as completed only after you can change the query and diagnose a deliberate duplicate-join mistake without the solution open. This repository provides the exercise, not evidence that it has been completed.
