import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pipeline import SOURCES, build, money, transform


def fixture():
    return {
        "orders": [{"order_id": "a", "customer_id": "c", "order_status": "delivered", "order_purchase_timestamp": "2018-01-01 10:00:00", "order_delivered_customer_date": "2018-01-03 23:59:59", "order_estimated_delivery_date": "2018-01-03 00:00:00"}],
        "customers": [{"customer_id": "c", "customer_state": "SP"}],
        "items": [{"order_id": "a", "order_item_id": "1", "product_id": "p", "price": "10.10", "freight_value": "1.20"}, {"order_id": "a", "order_item_id": "2", "product_id": "p", "price": "20.20", "freight_value": "2.30"}],
        "payments": [{"order_id": "a", "payment_sequential": "1", "payment_value": "10.00"}, {"order_id": "a", "payment_sequential": "2", "payment_value": "23.80"}],
        "products": [{"product_id": "p", "product_category_name": "casa"}],
        "translations": [{"product_category_name": "casa", "product_category_name_english": "home"}],
    }


class PipelineTests(unittest.TestCase):
    def test_money_uses_exact_cents(self):
        self.assertEqual(money("999.99"), 99999)
        self.assertEqual(money("0.10") + money("0.20"), 30)

    def test_invalid_money_rejected(self):
        for value in ("-1.00", "0.001", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money(value)

    def test_items_and_payments_do_not_fan_out(self):
        orders, items, flags = transform(fixture())
        self.assertEqual((len(orders), len(items)), (1, 2))
        self.assertEqual(orders[0]["Merchandise Cents"], 3030)
        self.assertEqual(orders[0]["Payment Cents"], 3380)
        self.assertEqual(orders[0]["Payment Difference Cents"], 0)
        self.assertEqual(flags, [])

    def test_calendar_day_deadline_is_inclusive(self):
        order = transform(fixture())[0][0]
        self.assertEqual((order["Late"], order["Delivery Days"]), (0, 2))

    def test_next_calendar_day_is_late(self):
        data = fixture()
        data["orders"][0]["order_delivered_customer_date"] = "2018-01-04 00:01:00"
        order = transform(data)[0][0]
        self.assertEqual((order["Late"], order["Late Days"]), (1, 1))

    def test_missing_actual_retained_not_imputed(self):
        data = fixture()
        data["orders"][0]["order_delivered_customer_date"] = ""
        orders, _, flags = transform(data)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["Delivery Eligible"], 0)
        self.assertIsNone(orders[0]["Delivery Days"])
        self.assertTrue(flags)

    def test_reversed_timestamp_excluded(self):
        data = fixture()
        data["orders"][0]["order_delivered_customer_date"] = "2018-01-01 09:59:59"
        self.assertEqual(transform(data)[0][0]["Delivery Eligible"], 0)

    def test_canceled_status_not_in_delivery_denominator(self):
        data = fixture()
        data["orders"][0]["order_status"] = "canceled"
        orders, _, flags = transform(data)
        self.assertEqual(orders[0]["Delivery Eligible"], 0)
        self.assertIn("Status/date conflict", {r["Rule"] for r in flags})

    def test_missing_category_is_visible(self):
        data = fixture()
        data["products"][0]["product_category_name"] = ""
        self.assertEqual(transform(data)[1][0]["Category"], "Uncategorized")

    def test_unmapped_category_retains_source_label(self):
        data = fixture()
        data["translations"] = []
        row = transform(data)[1][0]
        self.assertEqual((row["Category"], row["Category Mapping"]), ("Casa", "Portuguese fallback"))

    def test_all_duplicate_keys_rejected(self):
        for table in fixture():
            data = fixture()
            data[table].append(copy.deepcopy(data[table][0]))
            with self.subTest(table=table), self.assertRaises(ValueError):
                transform(data)

    def test_orphan_item_rejected(self):
        data = fixture()
        data["items"][0]["order_id"] = "unknown"
        with self.assertRaises(ValueError):
            transform(data)

    def test_no_items_or_payment_retained_and_flagged(self):
        data = fixture()
        data["items"], data["payments"] = [], []
        orders, items, flags = transform(data)
        self.assertEqual((len(orders), len(items)), (1, 0))
        self.assertEqual(orders[0]["Merchandise Cents"], 0)
        self.assertIsNone(orders[0]["Payment Cents"])
        self.assertEqual(len(flags), 2)

    def test_missing_column_rejected(self):
        data = fixture()
        del data["orders"][0]["order_status"]
        with self.assertRaises(ValueError):
            transform(data)

    def test_failed_refresh_preserves_pointer_and_unchanged_rerun_is_immutable(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            raw, output = Path(folder) / "raw", Path(folder) / "processed"
            raw.mkdir()
            data = fixture()
            for name, (filename, _) in SOURCES.items():
                with (raw / filename).open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(data[name][0]))
                    writer.writeheader()
                    writer.writerows(data[name])
            first = build(raw, output)
            pointer = (output / "latest.json").read_bytes()
            self.assertEqual(build(raw, output), first)
            path = raw / SOURCES["items"][0]
            path.write_text(path.read_text(encoding="utf-8").replace("10.10", "-10.10"), encoding="utf-8")
            with self.assertRaises(ValueError):
                build(raw, output)
            self.assertEqual((output / "latest.json").read_bytes(), pointer)


if __name__ == "__main__":
    unittest.main()
