# Commerce Operations | Power BI

**Where should delivery operations investigate, considering both workload and late rate?**

**6,534 of 96,470 eligible historical deliveries were late** (93.2% on time). SP and RJ contain **50.7%** of late deliveries, but their late rates differ: **4.5% versus 12.1%**. These are investigation leads, not explanations of cause or current service performance.

A two-page Power BI report uses Python/SQLite preparation, separate order/item grains and exact monetary cents over six related Olist sources.

[View current preview](deliverables/delivery-priorities-preview.png) · [Download current PBIX](deliverables/Commerce%20Delivery%20Priorities.pbix) · [SQL investigation and memo](docs/SQL_INVESTIGATION.md) · [Reproduce](#open-and-refresh)

![Current Power BI delivery priorities: counts and eligible rates](deliverables/delivery-priorities-preview.png)

The report's selectors update its metrics; text marked **unfiltered snapshot** remains a historical reference. The [new state/month SQL companion](sql/delivery_priorities.sql) uses safe item aggregation and dense rankings, retaining small populations. In July 2018, SP has 100 late deliveries among 2,712 eligible; AL has four among 22 and is not rate-ranked. [Full results and control totals](deliverables/delivery-investigation) · [Independent practice](docs/INDEPENDENT_PRACTICE.md).

The [earlier four-page PDF](deliverables/Commerce%20Operations%20Dashboard.pdf), [earlier PBIX](deliverables/Commerce%20Operations%20Dashboard.pbix) and [original case study](docs/case-study.md) are preserved as broader historical references. The source also contains **1,348** payment-versus-merchandise/freight differences, retained for reconciliation.

## Inspect the model

The snapshot contains **99,441 orders and 112,650 item lines**. Dates and States filter both facts; Categories filter item measures only. Payments aggregate to order grain before joining, preventing multiplied totals. Amounts remain integer cents through preparation.

[Model and table grains](docs/data-dictionary.md) · [DAX measures](powerbi/measures.dax) · [SQL review queries](sql/operations_review.sql) · [Editable Power BI project](powerbi/Commerce.pbip)

## Open and refresh


Download and extract the repository ZIP, then open the PBIX; its sample is already imported. To unpack and validate the included refresh inputs, run from the repository root with Python 3.11+:

```powershell
python src/prepare_demo.py
python src/verify_snapshot.py
python tools/investigate_delivery.py
```

Set Power Query's **DataRoot** parameter to your local `data/processed` folder, then select **Home > Refresh**. [Current two-page report guide](powerbi-rebuild/README.md). The [broader historical report guide](docs/user-guide.md) remains available.

The analysis companion reads the published SQLite snapshot without changing it; no dbt or warehouse service is required. [Query walkthrough, findings and limits](docs/SQL_INVESTIGATION.md).

## Technical detail

- [Reproduction, validation and licensing detail](docs/PROJECT_GUIDE.md)
- [Cleaning rules and metric definitions](docs/cleaning-rules.md)
- [Validation record](docs/qa.md) · [Reconciliation evidence](docs/reconciliation.json)
- [Python pipeline](src/pipeline.py) · [Tests](tests)
- [Source and license](docs/source-and-license.md)

## Scope

Independent demonstration using Olist's historical 2016–2018 data. Final purchase months are partial; the trend is not evidence of a current business decline. Statuses describe the recorded snapshot, not milestone history. Merchandise excludes freight and is not profit or recognized revenue.

Refresh runs on demand; cloud scheduling is not configured. Original code is [MIT](LICENSE); source data and derived report data retain **CC BY-NC-SA 4.0**, including noncommercial and share-alike conditions. See the source guide before reusing data.


## Presentation history

[Cover preview](deliverables/portfolio-cover-wide.png) · [Motion cover](deliverables/portfolio-motion.webm) · [Design maintenance](docs/VISUAL_DESIGN.md) · [November 1 release record](docs/DASHBOARD_RELEASE.md). Covers are presentation assets; native report behavior is documented separately.
