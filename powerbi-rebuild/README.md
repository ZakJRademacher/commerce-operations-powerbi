# Commerce Delivery Priorities — Power BI guide

**Business question:** Where should delivery operations investigate first?

Open [the ready-to-use PBIX](../deliverables/Commerce%20Delivery%20Priorities.pbix). Imported data is included. The editable [PBIP source](DeliveryPriorities.pbip) is kept beside its Report and SemanticModel folders. Use Power BI Desktop's current project support. The PBIX is distributed through GitHub. No Power BI Service hosting or scheduled cloud refresh is configured.

## Reading the report

On page 1, compare late-delivery counts with rates before choosing a state to investigate. Dropdowns update the metrics and charts, and tooltips show the population behind the result. Text marked as an unfiltered snapshot stays fixed.

Page 2 documents populations, exclusions and limitations. Its evidence represents the complete historical population, not the selections on page 1. Restore every dropdown to All before saving the default view. Use the report's fit-to-page view for readability; State charts scroll to include all states.

## Refresh and handoff

Keep this complete folder together. On a new machine, set DataRoot through Transform data > Edit parameters to the absolute path of the prepared input folder described below. Choose Home > Refresh. Read [data instructions](data/README.md) before replacing any input. Refresh the PBIP first, check both pages and filters, then save a new PBIX into deliverables; saving the source does not automatically update the exported PBIX.

The report uses a historical snapshot. Check the period and exclusions when interpreting it; it is not a live backlog. The original workbook and reporting files remain available.

## Your practice task

Select Alabama. Confirm 397 eligible deliveries, 85 late deliveries and 21.4% late rate. Explain why SP leads by workload while AL leads by rate. Restore All.

Acceptance: explain the denominator, identify an excluded population, and describe the additional data needed for a follow-up. Change the chart sort in a practice copy, then confirm the totals still agree. Read the DAX measure for one headline metric and explain it in plain language.

Native Power BI Desktop refresh, both report pages and the filter example above were checked on October 29, 2026. See verification.json and the report previews for evidence.
