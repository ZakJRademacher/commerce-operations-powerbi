# Cleaning and metric rules

The six source files are complete snapshots, not incremental uploads. Never append a
second copy of a snapshot. Original CSV files remain unchanged in `data/raw`.

| Decision | Implemented behavior | Why it matters |
|---|---|---|
| Encoding and whitespace | UTF-8 with optional BOM; trim field edges | Handles the translation file's BOM without losing its key |
| Required fields and keys | Fail on missing required columns, blank keys, or any duplicate key | No silent deduplication or conflicting records |
| Referential integrity | Reject orphan items/payments and missing order customers/products | Prevent incomplete joins |
| Currency | Parse Decimal, require nonnegative values with at most two decimals, store integer cents | Exact reconciliation before display rounding |
| Grain | Orders: one/order. Items: one/order + item number | No multiplication of order totals |
| Payments | Sum sequential payment rows by order before comparison | Split payments do not duplicate item prices |
| Missing item/payment rows | Retain order; zero merchandise if no item lines; blank payment if no payment rows | Distinguishes absent data from observed zero payment |
| Payment reconciliation | Flag every nonzero cents difference; do not force it to zero | Source differences remain auditable |
| Categories | Use supplied English mapping; missing source category becomes Uncategorized; unmapped Portuguese label retained | No invented product taxonomy |
| Top categories | Fixed top ten by full-snapshot delivered item price, remaining labels grouped as Other categories | Group membership does not change silently with slicers |
| Dates | Parse source local timestamps; retain dates; no timezone conversion | Source does not provide a reliable timezone contract |
| Timing eligibility | Delivered status, actual and estimated dates present, actual timestamp >= purchase timestamp | Invalid timing is excluded, never filled with an average |
| Late delivery | Actual calendar date > estimated calendar date | A delivery at 23:59 on the promised day counts as on time |
| Delivery days | Actual calendar date minus purchase calendar date | Calendar-day operational measure, not elapsed 24-hour periods |
| Status/date conflict | Flag actual delivery date on a non-delivered order | Status remains the source of delivered population selection |
| Privacy and relevance | Exclude names, ZIPs, cities, review narratives, customer unique IDs and geolocation | Only pseudonymous order/product keys and state are needed |
| Publication | Validate and export snapshot, then atomically replace latest.json | Failed transformation preserves the previous data pointer |

Snapshots use a source-content fingerprint plus a transformation revision. An
unchanged rerun checks export hashes and reuses the previous snapshot. Change the
transformation revision when business logic changes. Do not run two builders or
start a Power BI refresh while publishing a new snapshot. Retain the last good
snapshot until the new one passes desktop reconciliation.

The pipeline writes an event-level `Exceptions.csv`. One order can have several
events; summing check counts does **not** give distinct affected orders. Category
check counts are item lines. Snapshot source counts and quality checks do not
respond to report slicers.

Delivered merchandise is the sum of item prices for orders whose source status
is Delivered. It excludes freight and is not an accounting definition of revenue
or profit. Freight-to-merchandise is freight / merchandise, not gross checkout
share or margin. No cost, inventory, staffing or causation metric is available.
