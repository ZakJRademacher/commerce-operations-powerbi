# Validation record

Validated in the installed Windows Power BI Desktop on 16 October 2026.

## Automated checks

- Fifteen unit tests cover grain-safe joins, split payments, exact currency,
  keys, missing values, calendar-day deadlines, invalid dates and failure recovery.
- The snapshot verifier independently reconciles exported CSVs and SQLite,
  validates manifest hashes/counts, and compares expected filter populations.
- The included demo archive is checksum verified before extraction. A clean
  handoff test runs extraction and verification without the raw Kaggle download.

## Native report checks

All four report pages rendered with populated visuals. Desktop refresh completed.
The saved `Commerce Operations Dashboard.pbix` was closed and reopened; imported
data and headline values persisted without requiring a refresh.

| Selection / visual | Observed result |
|---|---|
| Full Overview | 99,441 orders; BRL 13,221,498.11; 93.2%; median 10 days |
| January 2018 | 7,269 orders; BRL 924,645.00; 94.3%; median 12 days |
| January 2018 + SP | 3,052 orders; 96.6%; median 8 days |
| Delivery, full | 96,470 eligible; 6,534 late; 93.2% on time; 10.6 average late days |
| Delivery state table | SP 40,494 eligible / 1,820 late; RJ 12,350 / 1,495 |
| Health Beauty chart selection | 9,465 delivered item lines; 14.5% freight ratio |
| Health Beauty detail table | BRL 1,233,131.72 merchandise |
| Quality headline counts | 99,441 orders; 112,650 items; 1,366 affected orders; 2,138 exception events |
| Quality check table | Individual counts populated; mixed-grain grand total suppressed |

Filters were cleared after interaction checks. The monthly late-rate chart
suppresses groups with fewer than 100 eligible deliveries; cards and tables
retain those observations. Expected exact values are in `reconciliation.json`.

## Limits of verification

Power BI Desktop interaction was checked manually; the Python workflow does not
compile DAX or render Power BI. No Service deployment, gateway or unattended
cloud refresh was tested. Exported PDF/images are static previews; the PBIX is
the interactive deliverable. Source history is 2016–2018 and has partial final
purchase months. Timing analysis is descriptive, not causal.

## SQL companion — November 1, 2026

The three new investigation tests and 15 existing pipeline tests pass (18 total). Independent raw-CSV/datetime/Decimal/Fraction calculations agree with all 565 state/month output rows, monetary sums, eligible/late flags and dense rankings. The 100-eligible display rule changes only rate-rank participation. [Exact controls](SQL_VERIFICATION.json) · [Walkthrough](SQL_INVESTIGATION.md). Current Power BI files are unchanged; these checks are not a new native DAX or refresh claim.

### Current two-page report recheck

On November 1, a disposable copy of `Commerce Delivery Priorities.pbix` rendered in Power BI Desktop. With both selectors at All: 96,470 eligible, 6,534 late, 6.8% late and eight delivered orders excluded from timing. Selecting AL changed cards and charts to 397 eligible, 85 late, 21.4% late and zero timing exclusions. Restoring All restored the baseline. Home > Refresh completed without a visible error and preserved that population. The explicitly unfiltered SP/RJ narrative remained fixed as labeled.

The saved local DataRoot and existing public-sample inputs were used. This does not establish clean-machine path configuration, changed-source refresh, every slicer combination, or cloud behavior. No refreshed binary or report design was saved into this release.
