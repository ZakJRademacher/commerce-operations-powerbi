"""Run a read-only SQL query against the current verified Commerce dbt snapshot."""
import argparse
import json
from pathlib import Path

import duckdb

from run_dbt import ROOT, verify_snapshot

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=ROOT / "data/dbt")
parser.add_argument("--sql", default="""select state, sum(late) as late_deliveries,
    sum(delivery_eligible) as eligible_deliveries,
    round(100.0 * sum(late) / nullif(sum(delivery_eligible), 0), 2) as late_percent
    from analytics_marts.fct_orders group by state order by late_deliveries desc""")
parser.add_argument("--limit", type=int, default=25)
args = parser.parse_args()
if not 1 <= args.limit <= 1000:
    parser.error("--limit must be between 1 and 1000")
pointer = json.loads((args.output / "latest.json").read_text(encoding="utf-8"))
snapshot = args.output / "snapshots" / pointer["snapshot"]
verify_snapshot(snapshot)
with duckdb.connect(str(snapshot / "commerce.duckdb"), read_only=True) as connection:
    result = connection.execute(args.sql)
    columns = [column[0] for column in result.description]
    rows = result.fetchmany(args.limit + 1)
print(json.dumps({"snapshot": pointer["snapshot"], "rows": [dict(zip(columns, row))
    for row in rows[:args.limit]], "truncated": len(rows) > args.limit}, indent=2, default=str))
