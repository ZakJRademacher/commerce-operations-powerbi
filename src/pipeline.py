"""Validated Olist snapshot -> a consistent, refreshable Power BI data contract.

Python 3.11+, standard library only. See docs/cleaning-rules.md for decisions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

SOURCES = {
    "orders": ("olist_orders_dataset.csv", ("order_id",)),
    "customers": ("olist_customers_dataset.csv", ("customer_id",)),
    "items": ("olist_order_items_dataset.csv", ("order_id", "order_item_id")),
    "payments": ("olist_order_payments_dataset.csv", ("order_id", "payment_sequential")),
    "products": ("olist_products_dataset.csv", ("product_id",)),
    "translations": ("product_category_name_translation.csv", ("product_category_name",)),
}
REQUIRED = {
    "orders": {"order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"},
    "customers": {"customer_id", "customer_state"},
    "items": {"order_id", "order_item_id", "product_id", "price", "freight_value"},
    "payments": {"order_id", "payment_sequential", "payment_value"},
    "products": {"product_id", "product_category_name"},
    "translations": {"product_category_name", "product_category_name_english"},
}
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())


def money(value: str) -> int:
    amount = Decimal(value)
    if not amount.is_finite() or amount < 0 or amount * 100 != (amount * 100).to_integral_value():
        raise ValueError(f"Invalid nonnegative two-decimal money: {value!r}")
    return int(amount * 100)


def timestamp(value: str):
    return datetime.fromisoformat(value) if value else None


def unique(rows, key, label):
    result = {}
    for row in rows:
        k = tuple(row[c] for c in key)
        if any(not v for v in k):
            raise ValueError(f"{label}: missing key")
        # Even identical duplicates require source investigation; no silent drop.
        if k in result:
            raise ValueError(f"{label}: duplicate key {k}")
        result[k] = row
    return result


def transform(tables):
    """Pure transformation used by both production and edge-case tests."""
    for name, rows in tables.items():
        for row in rows:
            if not REQUIRED[name] <= row.keys():
                raise ValueError(f"{name}: missing columns {REQUIRED[name] - row.keys()}")
    indexes = {name: unique(tables[name], key, name) for name, (_, key) in SOURCES.items()}
    orders_idx = indexes["orders"]
    customers = indexes["customers"]
    products = indexes["products"]
    translations = {k[0]: v["product_category_name_english"] for k, v in indexes["translations"].items()}
    item_totals = defaultdict(lambda: [0, 0, 0])
    payment_totals = defaultdict(int)
    items = []
    exceptions = []

    def flag(order_id, rule, detail):
        exceptions.append({"Order ID": order_id, "Rule": rule, "Detail": detail})

    for r in tables["payments"]:
        if (r["order_id"],) not in orders_idx:
            raise ValueError("Payment has no source order")
        payment_totals[r["order_id"]] += money(r["payment_value"])
    for r in tables["items"]:
        if (r["order_id"],) not in orders_idx or (r["product_id"],) not in products:
            raise ValueError("Item has no source order/product")
        price, freight = money(r["price"]), money(r["freight_value"])
        totals = item_totals[r["order_id"]]
        totals[0] += price
        totals[1] += freight
        totals[2] += 1
        order = orders_idx[(r["order_id"],)]
        customer = customers.get((order["customer_id"],))
        if not customer:
            raise ValueError("Order has no customer")
        category = products[(r["product_id"],)]["product_category_name"]
        mapped = translations.get(category)
        label = mapped.replace("_", " ").title() if mapped else category.replace("_", " ").title() if category else "Uncategorized"
        items.append({
            "Order ID": r["order_id"], "Item Number": int(r["order_item_id"]),
            "Product ID": r["product_id"], "Purchase Date": timestamp(order["order_purchase_timestamp"]).date().isoformat(),
            "State": customer["customer_state"], "Status": order["order_status"].title(),
            "Category": label, "Category Mapping": "Missing source category" if not category else "Portuguese fallback" if not mapped else "English translation",
            "Price Cents": price, "Freight Cents": freight,
        })

    orders = []
    for r in tables["orders"]:
        oid = r["order_id"]
        customer = customers.get((r["customer_id"],))
        if not customer or customer["customer_state"] not in STATES:
            raise ValueError("Missing customer or invalid Brazilian state")
        purchased = timestamp(r["order_purchase_timestamp"])
        if not purchased:
            raise ValueError("Missing purchase timestamp")
        actual = timestamp(r["order_delivered_customer_date"])
        estimated = timestamp(r["order_estimated_delivery_date"])
        delivered = r["order_status"] == "delivered"
        eligible = delivered and actual is not None and estimated is not None and actual >= purchased
        if delivered and not eligible:
            flag(oid, "Delivered order excluded from timing", "Missing actual/estimated date or actual delivery precedes purchase")
        if actual and actual < purchased:
            flag(oid, "Delivery precedes purchase", "Source timestamp retained; timing excluded")
        if not delivered and actual:
            flag(oid, "Status/date conflict", "Actual delivery present for a non-delivered status")
        price, freight, count = item_totals[oid]
        if not count:
            flag(oid, "No item lines", "Order retained with zero merchandise and zero freight")
        if oid not in payment_totals:
            flag(oid, "No payment rows", "Payment amount left blank")
        payment = payment_totals.get(oid)
        delta = payment - price - freight if payment is not None else None
        if delta not in (None, 0):
            flag(oid, "Payment differs from items plus freight", f"Difference BRL {delta / 100:.2f}; no forced reconciliation")
        days = (actual.date() - purchased.date()).days if eligible else None
        late = max(0, (actual.date() - estimated.date()).days) if eligible else None
        orders.append({
            "Order ID": oid, "Purchase Date": purchased.date().isoformat(),
            "State": customer["customer_state"], "Status": r["order_status"].title(),
            "Delivered Date": actual.date().isoformat() if actual else "",
            "Estimated Date": estimated.date().isoformat() if estimated else "",
            "Item Count": count, "Merchandise Cents": price, "Freight Cents": freight,
            "Payment Cents": payment, "Payment Difference Cents": delta,
            "Delivery Eligible": int(eligible), "Late": int(late > 0) if eligible else 0,
            "Delivery Days": days, "Late Days": late,
            "Delivery Band": "Not eligible" if not eligible else "01 | 0-7 days" if days <= 7 else "02 | 8-14 days" if days <= 14 else "03 | 15-30 days" if days <= 30 else "04 | 31+ days",
        })
    category_sales = Counter()
    for row in items:
        if row["Status"] == "Delivered":
            category_sales[row["Category"]] += row["Price Cents"]
    top_categories = {name for name, _ in category_sales.most_common(10)}
    for row in items:
        row["Category Group"] = row["Category"] if row["Category"] in top_categories else "Other categories"
    if len(orders) != len(tables["orders"]) or len(items) != len(tables["items"]):
        raise AssertionError("Row count changed during joins")
    if sum(r["Merchandise Cents"] for r in orders) != sum(r["Price Cents"] for r in items):
        raise AssertionError("Merchandise reconciliation failed")
    return orders, items, exceptions


def write_csv(path, rows, columns=None):
    columns = columns or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def build(raw: Path, output: Path):
    tables, hashes = {}, {}
    for name, (filename, _) in SOURCES.items():
        path = raw / filename
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not REQUIRED[name] <= set(reader.fieldnames or []):
                raise ValueError(f"{filename}: required columns missing")
            tables[name] = [{k: v.strip() for k, v in row.items()} for row in reader]
    orders, items, exceptions = transform(tables)
    # Include contract version so future logic changes cannot silently reuse old data.
    fingerprint = hashlib.sha256(("contract-v2|" + json.dumps(hashes, sort_keys=True)).encode()).hexdigest()[:16]
    snapshot = output / "snapshots" / fingerprint
    existing = snapshot / "manifest.json"
    if existing.exists():
        prior = json.loads(existing.read_text(encoding="utf-8"))
        for filename, expected in prior["export_hashes"].items():
            if hashlib.sha256((snapshot / filename).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Existing snapshot has changed: {filename}; restore it before refresh")
        pending = output / "latest.pending.json"
        pending.write_text(json.dumps({"snapshot": fingerprint, "contract_version": 1}, indent=2) + "\n", encoding="utf-8")
        os.replace(pending, output / "latest.json")
        return prior
    snapshot.mkdir(parents=True, exist_ok=True)
    start, end = min(r["Purchase Date"] for r in orders), max(r["Purchase Date"] for r in orders)
    days = []
    d = date.fromisoformat(start)
    while d <= date.fromisoformat(end):
        days.append({"Date": d.isoformat(), "Month": d.strftime("%Y-%m"), "Year": d.year})
        d += timedelta(days=1)
    quality = [{"Check": name, "Rows": count} for name, count in sorted(Counter(r["Rule"] for r in exceptions).items())]
    quality += [{"Check": "Item lines missing source category", "Rows": sum(r["Category Mapping"] == "Missing source category" for r in items)}, {"Check": "Item lines using Portuguese fallback", "Rows": sum(r["Category Mapping"] == "Portuguese fallback" for r in items)}]
    manifest = {
        "contract_version": 1, "snapshot": fingerprint, "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "source_license": "CC BY-NC-SA 4.0", "source_hashes": hashes,
        "source_rows": {k: len(v) for k, v in tables.items()}, "orders": len(orders), "items": len(items),
        "purchase_start": start, "purchase_end": end,
        "delivery_eligible": sum(r["Delivery Eligible"] for r in orders),
        "late_orders": sum(r["Late"] for r in orders),
        "delivered_merchandise_cents": sum(r["Merchandise Cents"] for r in orders if r["Status"] == "Delivered"),
        "all_merchandise_cents": sum(r["Merchandise Cents"] for r in orders),
        "exception_events": len(exceptions), "orders_with_exceptions": len({r["Order ID"] for r in exceptions}),
        "status_counts": dict(Counter(r["Status"] for r in orders)),
    }
    rows_by_table = {"Orders": orders, "Items": items, "Dates": days,
        "States": [{"State": s} for s in sorted(STATES)],
        "Categories": [{"Category": c} for c in sorted({r["Category"] for r in items})],
        "Quality": quality,
        "Refresh": [{"Snapshot": fingerprint, "Built UTC": manifest["built_at_utc"], "Source Orders": len(orders), "Source Items": len(items), "Exception Events": len(exceptions), "Orders With Exceptions": manifest["orders_with_exceptions"]}],
    }
    for name, rows in rows_by_table.items():
        write_csv(snapshot / f"{name}.csv", rows)
    write_csv(snapshot / "Exceptions.csv", exceptions, ["Order ID", "Rule", "Detail"])
    # SQL handoff preserves the same grains; amounts stay integer cents.
    db = sqlite3.connect(snapshot / "operations.sqlite")
    for name, rows in rows_by_table.items():
        db.execute(f'DROP TABLE IF EXISTS "{name}"')
        cols = list(rows[0])
        types = {c: "INTEGER" if any(isinstance(r[c], int) for r in rows) else "TEXT" for c in cols}
        db.execute(f'CREATE TABLE "{name}" (' + ",".join(f'"{c}" {types[c]}' for c in cols) + ")")
        db.executemany(f'INSERT INTO "{name}" VALUES (' + ",".join("?" for c in cols) + ")", ([r[c] for c in cols] for r in rows))
    db.commit()
    db.close()
    manifest["export_hashes"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.glob("*.csv")}
    (snapshot / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Publish the pointer only when every transformation and export succeeded.
    pointer = output / "latest.pending.json"
    pointer.write_text(json.dumps({"snapshot": fingerprint, "contract_version": 1}, indent=2) + "\n", encoding="utf-8")
    os.replace(pointer, output / "latest.json")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path(__file__).resolve().parents[1] / "data/raw")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/processed")
    args = parser.parse_args()
    print(json.dumps(build(args.raw, args.output), indent=2))
