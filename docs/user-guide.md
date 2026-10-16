# Dashboard handoff

## Open and explore

Open `deliverables/Commerce Operations Dashboard.pbix` in Power BI Desktop. Its imported
snapshot works offline. Use the page tabs along the bottom:

1. **Overview:** size of the order population, delivered merchandise, on-time rate,
   typical delivery duration, purchase-month trend and source status mix.
2. **Delivery:** late-order volume by state, late-rate trend and a sortable state
   review table. Compare volume and rate before deciding where to investigate.
   The trend shows months with at least 100 eligible deliveries in the current
   selection. Smaller groups remain in cards and tables; a missing trend point
   means insufficient population, not zero late deliveries.
3. **Products:** delivered item merchandise, freight, unit lines and category detail.
   The category dropdown affects every item metric on this page.
4. **Quality & Refresh:** unfiltered snapshot counts, overlapping quality checks,
   build timestamp, fingerprint, refresh steps and metric limitations.

Purchase Month and State dropdowns filter their current page. Expand a dropdown,
select one or more values, or use its eraser to clear. Selections on one page are
independent of other pages. Click a chart to inspect a contribution; click its
selected mark again or blank canvas to clear. Hover for exact values. Tables can
be sorted by their column headings and scrolled. Clear selections before sharing
an all-data screenshot. A blank rate means no eligible observations, not 0%.

The Order status chart is a snapshot: an order recorded as Delivered contributes
only to Delivered. Shipped contains orders still recorded in that state. The
source does not provide a complete history of status transitions, so this chart
does not count all orders that were ever shipped.

## Refresh on this computer

The automated part is the validation, cleaning, joins, metrics and report
recalculation. Refresh is deliberately **on demand**:

```powershell
python src/download_data.py
python -m unittest discover -s tests -v
python src/pipeline.py
python src/verify_snapshot.py
```

Then choose **Home > Refresh** in Power BI Desktop. Check the imported fingerprint
and build time on Quality & Refresh against `data/processed/latest.json` and the
matching `manifest.json`. Save the PBIX when satisfied. An unchanged rebuild reuses
the verified snapshot, so its original build time remains unchanged.

`download_data.py` caches the source archive and skips existing CSVs. To use a
newly downloaded Kaggle version, download it separately and provide its six
required CSVs in a new raw folder. Run `python src/pipeline.py --raw <folder>`.
Supply complete snapshots with the same source schema and meaning. Arbitrary
client CSVs with similar headers require a new mapping and validation contract.

For a recurring business export, agree on a full-snapshot or incremental delivery
contract first. This implementation rebuilds from a complete snapshot; it does
not merge a weekly delta into earlier orders. A weekly-only file could remove
older history from the dashboard. Incremental updates require a separate merge
step with stable keys and explicit rules for changed orders and removals.

## Move to another computer

1. Download/extract the full repository or delivery ZIP, preserving its folders.
   Run `python src/prepare_demo.py` to unpack the bundled clean snapshot.
2. Open the PBIX for immediate offline exploration, or `powerbi/Commerce.pbip`
   for the editable report/model project.
3. In Desktop choose **Home > Transform data > Edit parameters**. Set **DataRoot**
   to the absolute path of your extracted `data/processed` folder. Use forward
   slashes, for example `C:/Portfolio/commerce-operations-powerbi/data/processed`.
4. Apply and Refresh. First-time source permission prompts require the local
   user's decision. This project does not disable privacy or security protections.
5. Run the Python commands above if changing the source snapshot. Python 3.11+
   and the standard library are sufficient; no API key or paid runtime is required.

The report sources CSVs through the `latest.json` pointer. Moving only the PBIP
file will not work: its Report and SemanticModel folders must remain beside it.
Keep processed snapshots on disk until a successful new refresh has been saved.
Do not edit CSV amounts by hand and expect the manifest checks to pass.

## Scheduling and service publication

No cloud publication, live Kaggle connection or recurring scheduler is included.
Power BI Service refresh of local files generally needs an appropriately configured
gateway, accessible source paths, credentials and account capacity/licensing.
Those are separate deployment choices. A dataset refresh does not download new
Kaggle source data or run Python automatically. This handoff demonstrates a
reproducible local data-to-dashboard workflow, not a production hosted service.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| File not found on refresh | Correct DataRoot; retain processed/latest.json and its snapshot subfolder |
| All visuals blank after opening PBIP | Refresh; PBIP source control excludes the local imported-data cache |
| First PBIP refresh reports a cyclic query reference | Open Transform data, then Close & Apply to initialize the parameter context; choose Home > Refresh again. The packaged PBIX already contains the imported model |
| Pipeline fails on duplicates/keys | Investigate the source snapshot; previous pointer remains unchanged |
| Existing snapshot changed | Restore the published export or use a separately versioned clean build; do not bypass hash checking |
| Figures differ from README | Clear page slicers and chart selections; compare snapshot fingerprints |
| Rate blank | No eligible delivery population in the current selection |
| Category seems to have no effect on Overview | Category only filters item metrics on Products by design |
| Payment and merchandise differ | Inspect Exceptions.csv; do not relabel item prices as collected cash |
| Desktop offers TMDL upgrade | Optional format conversion; retain source control/backup before conversion |

## Maintain and explain this project

Be ready to explain fact-table grain, key validation, payment aggregation before
joins, integer cents, missing-value denominators, one-direction relationships,
filter context in DAX, and the difference between Refresh and rerunning Python.
Use `docs/skills-walkthrough.md` for a practical rehearsal. Never claim this
demonstration was paid client work or that it produced verified financial savings.
