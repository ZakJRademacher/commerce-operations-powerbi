"""Independent CSV/SQLite reconciliation and slicer expectations for desktop QA."""
import csv
import hashlib
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    processed = ROOT / "data/processed"
    pointer = json.loads((processed / "latest.json").read_text(encoding="utf-8"))
    snapshot = processed / "snapshots" / pointer["snapshot"]
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    for filename, sha in manifest["export_hashes"].items():
        assert hashlib.sha256((snapshot / filename).read_bytes()).hexdigest() == sha, filename
    with (snapshot / "Orders.csv").open(encoding="utf-8") as f:
        orders = list(csv.DictReader(f))
    with (snapshot / "Items.csv").open(encoding="utf-8") as f:
        items = list(csv.DictReader(f))
    assert len({r["Order ID"] for r in orders}) == len(orders) == manifest["source_rows"]["orders"]
    assert len({(r["Order ID"], r["Item Number"]) for r in items}) == len(items) == manifest["source_rows"]["items"]
    delivered_items = [r for r in items if r["Status"] == "Delivered"]
    assert sum(int(r["Price Cents"]) for r in delivered_items) == manifest["delivered_merchandise_cents"]
    assert sum(int(r["Price Cents"]) for r in items) == sum(int(r["Merchandise Cents"]) for r in orders)
    expected = {}
    for label, rows in {
        "all": orders,
        "SP": [r for r in orders if r["State"] == "SP"],
        "2018-01": [r for r in orders if r["Purchase Date"].startswith("2018-01")],
        "SP 2018-01": [r for r in orders if r["State"] == "SP" and r["Purchase Date"].startswith("2018-01")],
    }.items():
        eligible = sum(int(r["Delivery Eligible"]) for r in rows)
        late = sum(int(r["Late"]) for r in rows)
        expected[label] = {"orders": len(rows), "delivered_merchandise_brl": sum(int(r["Merchandise Cents"]) for r in rows if r["Status"] == "Delivered") / 100,
            "eligible": eligible, "late": late, "on_time_rate": (eligible-late)/eligible,
            "median_delivery_days": statistics.median(int(r["Delivery Days"]) for r in rows if r["Delivery Eligible"] == "1")}
    by_state = Counter()
    for r in orders:
        by_state[r["State"]] += int(r["Late"])
    by_category = Counter()
    for r in delivered_items:
        by_category[r["Category"]] += int(r["Price Cents"])
    category = "Health Beauty"
    category_rows = [r for r in delivered_items if r["Category"] == category]
    freight = sum(int(r["Freight Cents"]) for r in delivered_items)
    result = {"snapshot": pointer["snapshot"], "order_slicer_expectations": expected,
        "delivered_item_lines": len(delivered_items), "delivered_freight_brl": freight / 100,
        "freight_to_merchandise": freight / manifest["delivered_merchandise_cents"],
        "top_late_states": by_state.most_common(5), "top_categories_cents": by_category.most_common(5),
        "category_slicer": {"category": category, "delivered_item_lines": len(category_rows), "merchandise_brl": sum(int(r["Price Cents"]) for r in category_rows) / 100}}
    db = sqlite3.connect(snapshot / "operations.sqlite")
    assert db.execute('SELECT COUNT(*) FROM Orders').fetchone()[0] == len(orders)
    assert db.execute('SELECT SUM("Merchandise Cents") FROM Orders').fetchone()[0] == manifest["all_merchandise_cents"]
    assert db.execute('SELECT SUM("Price Cents") FROM Items WHERE Status=\'Delivered\'').fetchone()[0] == manifest["delivered_merchandise_cents"]
    db.close()
    (ROOT / "docs/reconciliation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
