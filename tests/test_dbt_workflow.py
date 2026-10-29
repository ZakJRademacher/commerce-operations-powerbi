"""Real DuckDB/dbt integration: fan-out, timing, corrections, bad data and publication.

Run separately in the dbt environment. Uses fictional fixtures and disposable folders.
"""
import copy
import csv
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import duckdb
import run_dbt
from run_dbt import SOURCES, build


def fixture():
    def order(oid, actual, status="delivered"):
        return {"order_id": oid, "customer_id": "c", "order_status": status,
                "order_purchase_timestamp": "2018-01-01 10:00:00",
                "order_delivered_customer_date": actual,
                "order_estimated_delivery_date": "2018-01-03 00:00:00"}
    return {
        "orders": [order("a", "2018-01-03 23:59:59"), order("b", "2018-01-04 00:01:00"),
                   order("c", "2018-01-02 10:00:00", "canceled"), order("d", "2018-01-01 09:59:59")],
        "customers": [{"customer_id": "c", "customer_state": "SP"}],
        "items": [
            {"order_id": "a", "order_item_id": "1", "product_id": "p", "price": "10.10", "freight_value": "1.20"},
            {"order_id": "a", "order_item_id": "2", "product_id": "p", "price": "20.20", "freight_value": "2.30"},
            {"order_id": "b", "order_item_id": "1", "product_id": "p", "price": "1.00", "freight_value": "0.00"},
            {"order_id": "d", "order_item_id": "1", "product_id": "q", "price": "0.00", "freight_value": "0.00"}],
        "payments": [
            {"order_id": "a", "payment_sequential": "1", "payment_value": "10.00"},
            {"order_id": "a", "payment_sequential": "2", "payment_value": "23.80"},
            {"order_id": "b", "payment_sequential": "1", "payment_value": "0.00"}],
        "products": [{"product_id": "p", "product_category_name": "casa"},
                     {"product_id": "q", "product_category_name": ""}],
        "translations": [{"product_category_name": "casa", "product_category_name_english": "home"}],
    }


def write_raw(raw, data):
    raw.mkdir(exist_ok=True)
    for name, (filename, _) in SOURCES.items():
        with (raw / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[name][0]))
            writer.writeheader()
            writer.writerows(data[name])


class DbtWorkflowTests(unittest.TestCase):
    def test_source_change_during_input_freeze_preserves_pointer(self):
        with tempfile.TemporaryDirectory(prefix="commerce-dbt-source-race-") as temp:
            folder = Path(temp)
            raw, output = folder / "raw", folder / "output"
            write_raw(raw, fixture())
            output.mkdir()
            pointer = b'{"snapshot":"previous-good","contract_version":1}'
            (output / "latest.json").write_bytes(pointer)
            copy_file = run_dbt.shutil.copy2

            def altered_copy(source, destination):
                result = copy_file(source, destination)
                with Path(destination).open("ab") as stream:
                    stream.write(b"changed during copy")
                return result

            with patch("run_dbt.shutil.copy2", side_effect=altered_copy):
                with self.assertRaisesRegex(ValueError, "Source changed while freezing inputs"):
                    build(raw, output)
            self.assertEqual((output / "latest.json").read_bytes(), pointer)

    def test_snapshot_lifecycle_and_business_edges(self):
        with tempfile.TemporaryDirectory(prefix="commerce-dbt-integration-") as temp:
            folder = Path(temp)
            raw, output = folder / "raw", folder / "output"
            data = fixture()
            write_raw(raw, data)
            first = build(raw, output)
            first_path = output / "snapshots" / first["snapshot"]
            with duckdb.connect(str(first_path / "commerce.duckdb"), read_only=True) as db:
                rows = {r[0]: r[1:] for r in db.execute("""select order_id, merchandise_cents,
                    payment_cents, delivery_eligible, late, delivery_days
                    from analytics_marts.fct_orders""").fetchall()}
            self.assertEqual(rows["a"], (3030, 3380, 1, 0, 2))  # Two items/two payments: no fan-out.
            self.assertEqual(rows["b"], (100, 0, 1, 1, 3))  # Observed zero is not a missing payment.
            self.assertEqual(rows["c"], (0, None, 0, 0, None))
            self.assertEqual(rows["d"], (0, None, 0, 0, None))  # Reversed timestamp excluded.
            replay = build(raw, output)
            self.assertEqual(replay, first)
            self.assertEqual(len(list((output / "snapshots").iterdir())), 1)

            # A new order and a late correction arrive together as a replacement source snapshot.
            changed = copy.deepcopy(data)
            changed["orders"][1]["order_delivered_customer_date"] = "2018-01-03 23:59:59"
            changed["orders"].append({**changed["orders"][0], "order_id": "e"})
            changed["items"].append({**changed["items"][0], "order_id": "e"})
            changed["payments"].append({"order_id": "e", "payment_sequential": "1", "payment_value": "11.30"})
            write_raw(raw, changed)
            second = build(raw, output)
            self.assertNotEqual(first["snapshot"], second["snapshot"])
            self.assertEqual((second["orders"], second["items"], second["late_orders"]), (5, 5, 0))
            self.assertEqual(second["all_merchandise_cents"], first["all_merchandise_cents"] + 1010)
            self.assertTrue(first_path.exists())
            pointer = (output / "latest.json").read_bytes()

            for label, mutate in [
                ("duplicate key", lambda x: x["orders"].append(copy.deepcopy(x["orders"][0]))),
                ("fractional cent", lambda x: x["items"][0].update(price="0.001")),
                ("fractional item number", lambda x: x["items"][0].update(order_item_id="1.5")),
                ("malformed timestamp", lambda x: x["orders"][0].update(order_delivered_customer_date="not-a-date")),
                ("orphan customer", lambda x: x["orders"][0].update(customer_id="missing")),
            ]:
                invalid = copy.deepcopy(changed)
                mutate(invalid)
                write_raw(raw, invalid)
                with self.subTest(label=label), self.assertRaises(RuntimeError):
                    build(raw, output)
                self.assertEqual((output / "latest.json").read_bytes(), pointer)

            write_raw(raw, changed)
            corrupt = output / "snapshots" / second["snapshot"] / "Orders.csv"
            corrupt.write_text("corrupted output", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Existing output changed"):
                build(raw, output)
            self.assertEqual((output / "latest.json").read_bytes(), pointer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
