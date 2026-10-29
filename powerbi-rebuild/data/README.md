# Delivery Priorities refresh inputs

The PBIX in deliverables contains imported data and can be viewed immediately. To avoid duplicating the same full snapshot, this new reporting folder does not include a second copy of the CSVs/database.

From the repository root run:

```sh
python src/prepare_demo.py
python src/verify_snapshot.py
```

Set Power Query's DataRoot parameter to the absolute path of data/processed in the repository root. Keep its latest.json and complete snapshots directory together. The queries read Orders, Items, Dates, States, Categories, Quality and Refresh from that original validated snapshot. Refresh, reconcile both pages, then save a replacement PBIX.

Expected baseline: 99,441 orders, 96,470 eligible deliveries, 6,534 late and 8 timing exclusions. AL: 397 eligible, 85 late and 21.4%. This report uses the original Python/SQLite preparation, not the separate local SQL/dbt extension.

Historical Olist data retains CC BY-NC-SA 4.0. Read [source and license](../../docs/source-and-license.md). No scheduled service refresh is configured.
