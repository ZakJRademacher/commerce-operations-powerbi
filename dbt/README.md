# Commerce SQL/dbt workflow

This extends the existing Commerce report with a local DuckDB database and modular SQL transformations. It answers the same delivery-workload question and preserves the existing business definitions. It is an educational analytics-engineering workflow using historical data, not a live warehouse service.

## Start here

On Zak's computer, double-click **Run Demo SQL.cmd** at the repository root. It builds, tests, compares with the original report data, generates local documentation and publishes a separate snapshot under `data/dbt`. Source data and useful results stay in this project library; the installed Python environment and disposable build files stay outside it.

Then work through [the first SQL lesson](../docs/SQL_DBT_FIRST_LESSON.md). That lesson starts with reading a table and calculating a rate before asking you to modify SQL.

## Set up another computer

Use Python 3.12 and an isolated environment. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r dbt/requirements-lock.txt
```

Linux/macOS use `.venv/bin/python`. The tested stack is dbt Core 1.12.6, dbt-duckdb 1.11.1 and DuckDB 1.5.6. This project uses the Python dbt Core adapter; dbt v2 installation instructions describe a different runtime.

The six raw source files are not committed. Obtain them using the existing [source instructions](../docs/source-and-license.md) and `python src/download_data.py`. `--compare-demo` requires the exact six original source hashes recorded in the published sample archive. A changed download fails that comparison visibly.

```powershell
.venv\Scripts\python.exe src/run_dbt.py --compare-demo --docs
.venv\Scripts\python.exe src/query_dbt.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

For a new complete source snapshot, use `--raw path/to/six/files` and omit `--compare-demo`. The build still runs dbt tests and compares every order, item and exception value with the independent Python transformation. The first version uses full-snapshot rebuilds; it does not append exports or use incremental materialization.

## What each layer does

```mermaid
flowchart LR
  CSV[Six historical source CSVs] --> RAW[Raw DuckDB tables and source hashes]
  RAW --> STG[Staging: names, types, keys]
  STG --> INT[Intermediate: separate item and payment aggregates]
  INT --> FACT[Order and item facts, dimensions, exceptions]
  FACT --> CHECK[dbt tests and independent reconciliation]
  CHECK --> SNAP[Verified snapshot and Power BI CSV contract]
```

- **Raw landing:** Python copies relevant raw columns as strings, records logical source-row numbers, file SHA-256 and input counts. It excludes unnecessary customer/location fields. It does not calculate delivery metrics.
- **Staging:** six readable SQL models normalize keys, timestamps and exact monetary cents. Invalid mandatory values fail tests. Money accepts nonnegative plain decimal text with no nonzero fractions of a cent; redundant trailing zeros are allowed. Scientific notation is deliberately outside this SQL input contract.
- **Intermediate:** aggregate payments and item totals independently before joining at order grain. Category ranking uses delivered merchandise over the entire snapshot, with source occurrence breaking ties.
- **Marts:** `analytics_marts.fct_orders` has one row per order; `fct_order_items` has one per order/item pair. Dimensions, exception events, quality counts and refresh metadata support reporting and handoff.
- **Tests:** required values, unique/composite keys, relationships, accepted values, nonnegative amounts, source-to-fact counts, exact monetary sums, payment differences and delivery denominators.
- **Reference:** compare all order, item and exception fields to the existing independent Python rules. Demo mode additionally compares seven exported business tables against the checksum-verified published archive. Refresh metadata intentionally changes with the new build.

`models/schema.yml` documents model grains and important columns. `source()` names landed raw tables; `ref()` names another dbt model and creates its dependency in the graph. The SQL files contain SELECT queries; dbt creates the views/tables in dependency order.

## Outputs and safe refresh

The runner first freezes copies of the six inputs and checks their hashes, then builds in a disposable candidate database. A source changed during copying or a transformation changed during the build stops publication. It runs `dbt build`, verifies the results and writes an immutable directory at `data/dbt/snapshots/<fingerprint>/`. A new `data/dbt/latest.json` pointer is published only after the snapshot is complete and its artifact hashes have been checked. Failed attempts retain useful diagnostics under `data/dbt/failures/` and preserve the previous pointer. Existing corrupted outputs are rejected rather than silently overwritten.

An unchanged run still rebuilds and tests a candidate, then verifies and reuses the prior immutable result. It does not accumulate totals. A source correction or transformation change produces another fingerprint. A lock file records the tested dependency set. Run only one builder at a time and do not refresh Power BI during publication.

Each snapshot contains:

- `commerce.duckdb`: raw, staging, intermediate and reporting relations.
- `Orders.csv`, `Items.csv`, `Dates.csv`, `States.csv`, `Categories.csv`, `Exceptions.csv`, `Quality.csv`, `Refresh.csv`: existing display-column contract.
- `manifest.json`: source/logic hashes, counts, package versions, test results and reconciliation evidence.
- `dbt-artifacts/`: model manifest and test results; `--docs` also adds the catalog and self-contained `static_index.html` lineage/documentation page.

## Query the result

Run the default state workload/rate query:

```powershell
.venv\Scripts\python.exe src/query_dbt.py
```

Or supply a SELECT query:

```powershell
.venv\Scripts\python.exe src/query_dbt.py --sql "select order_id, item_count, payment_cents from analytics_marts.fct_orders order by order_id limit 5"
```

The query helper opens the current verified database read-only. For exploratory SQL edits, use the helper or a separate database copy; published snapshots are immutable. Direct dbt experimentation should target a separate working database rather than the published one.

## Power BI handoff

The new exports preserve the existing CSV names and columns. To trial the SQL outputs in a copy of the report, set its **DataRoot** parameter to the project's `data/dbt` folder and refresh. Keep the original report and `data/processed` source available for comparison. No PBIX has been switched or desktop refresh certified by this extension; field-for-field data reconciliation verifies the handoff data, not the application session. Cloud scheduling, gateways and row-level access are outside this local phase.

## Licensing and scope

The original code is MIT licensed. Olist source records and derived data/reports retain **CC BY-NC-SA 4.0**. This is a noncommercial educational demonstration; the sample data is not a licensed paid-client dataset. Test fixtures are fictional. The snapshot dates describe historical purchases; ingestion time records this local load and does not imply the business data is current.

Implementation references: [dbt-duckdb adapter](https://github.com/duckdb/dbt-duckdb), [dbt sources](https://docs.getdbt.com/docs/build/sources), [data tests](https://docs.getdbt.com/docs/build/data-tests), [DuckDB SQL](https://duckdb.org/docs/stable/sql/introduction).
