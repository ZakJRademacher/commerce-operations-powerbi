"""Write a read-only SQLite investigation over the existing published snapshot."""
import argparse
import csv
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def query(db):
    """Return deterministic results; callers can supply an in-memory test database."""
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute((ROOT / 'sql/delivery_priorities.sql').read_text(encoding='utf-8'))]


def default_database(root=ROOT):
    processed = root / 'data/processed'
    pointer = json.loads((processed / 'latest.json').read_text(encoding='utf-8'))
    snapshot = (processed / 'snapshots' / pointer['snapshot']).resolve()
    if not snapshot.is_relative_to((processed / 'snapshots').resolve()):
        raise ValueError('Snapshot pointer leaves the published snapshots folder')
    return snapshot / 'operations.sqlite'


def investigate(database, output):
    database, output = Path(database).resolve(), Path(output).resolve()
    if not database.is_file():
        raise FileNotFoundError('Prepare the published snapshot first: python src/prepare_demo.py')
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only = ON')
        # Reject ambiguous grain rather than trusting aggregate equality alone.
        if db.execute('SELECT COUNT(*) != COUNT(DISTINCT "Order ID") FROM Orders').fetchone()[0]:
            raise ValueError('Orders must have one row per Order ID')
        if db.execute('SELECT COUNT(*) FROM (SELECT "Order ID", "Item Number" FROM Items GROUP BY 1,2 HAVING COUNT(*) > 1)').fetchone()[0]:
            raise ValueError('Items must have one row per order/item pair')
        if db.execute('SELECT COUNT(*) FROM Items i LEFT JOIN Orders o ON o."Order ID"=i."Order ID" WHERE o."Order ID" IS NULL').fetchone()[0]:
            raise ValueError('Items contain an orphan Order ID')
        results = query(db)
        orders, eligible, late, merchandise = db.execute('SELECT COUNT(*), COALESCE(SUM("Delivery Eligible"),0), COALESCE(SUM(Late),0), COALESCE(SUM("Merchandise Cents"),0) FROM Orders').fetchone()
        items, item_money = db.execute('SELECT COUNT(*), COALESCE(SUM("Price Cents"),0) FROM Items').fetchone()
        actual = {k: sum(r[k] for r in results) for k in ['orders', 'eligible_deliveries', 'late_deliveries', 'item_lines', 'merchandise_cents', 'item_merchandise_cents']}
        expected = dict(zip(actual, [orders, eligible, late, items, merchandise, item_money]))
        if actual != expected or any(r['merchandise_cents'] != r['item_merchandise_cents'] for r in results):
            raise ValueError('State/month results do not reconcile to the source fact tables')
    controls = {'input_database_sha256': hashlib.sha256(database.read_bytes()).hexdigest(),
                'sql_sha256': hashlib.sha256((ROOT / 'sql/delivery_priorities.sql').read_bytes()).hexdigest(),
                'source_totals': expected, 'result_totals': actual, 'state_month_rows': len(results),
                'rate_ranking_min_eligible': 100,
                'ranking_rule': 'Within each purchase month; ties share a dense rank. The 100-eligible rule affects only rate_rank, not rows or rates; it is not a significance test.',
                'grain': 'One row per state and purchase month; items aggregated before the order join.'}
    output.mkdir(parents=True, exist_ok=True)
    if results:
        pending = output / 'state-month.csv.next'
        with pending.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, list(results[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(results)
        pending.replace(output / 'state-month.csv')
    else:
        raise ValueError('No reporting rows; no analysis published')
    controls['csv_sha256'] = hashlib.sha256((output / 'state-month.csv').read_bytes()).hexdigest()
    pending = output / 'controls.json.next'
    pending.write_text(json.dumps(controls, indent=2) + '\n', encoding='utf-8')
    pending.replace(output / 'controls.json')
    return controls


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'deliverables/delivery-investigation')
    args = parser.parse_args()
    print(json.dumps(investigate(args.database or default_database(), args.output), indent=2))
