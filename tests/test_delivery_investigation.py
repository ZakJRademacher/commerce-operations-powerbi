"""Counterexamples for fan-out, ranking populations, ties and zero denominators."""
import importlib.util
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('delivery_investigation', ROOT / 'tools/investigate_delivery.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class InvestigationTests(unittest.TestCase):
    def database(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript('CREATE TABLE Orders("Order ID" TEXT, State TEXT, "Purchase Date" TEXT, "Delivery Eligible" INTEGER, Late INTEGER, "Merchandise Cents" INTEGER); CREATE TABLE Items("Order ID" TEXT, "Item Number" INTEGER, "Price Cents" INTEGER);')
        return db

    def test_item_rollup_preserves_order_counts_and_money(self):
        db = self.database()
        db.execute('INSERT INTO Orders VALUES ("one","SP","2018-01-01",1,1,300)')
        db.executemany('INSERT INTO Items VALUES (?,?,?)', [('one',1,100),('one',2,200)])
        row = m.query(db)[0]
        self.assertEqual((row['orders'],row['eligible_deliveries'],row['late_deliveries'],row['item_lines'],row['merchandise_cents']), (1,1,1,2,300))

    def test_ties_and_threshold_do_not_drop_small_or_empty_populations(self):
        db = self.database()
        for state, n, late in [('AA',100,20),('BB',100,20),('CC',99,30)]:
            db.executemany('INSERT INTO Orders VALUES (?,?,?,?,?,?)', [(state+str(i),state,'2018-01-01',1,int(i<late),0) for i in range(n)])
        db.execute('INSERT INTO Orders VALUES ("none","DD","2018-01-01",0,0,0)')
        data = {r['state']:r for r in m.query(db)}
        self.assertEqual(len(data),4)
        self.assertEqual((data['AA']['rate_rank'], data['BB']['rate_rank']), (1,1))
        self.assertEqual((data['AA']['workload_rank'],data['BB']['workload_rank']), (2,2))
        self.assertIsNone(data['CC']['rate_rank']); self.assertAlmostEqual(data['CC']['late_rate'],30/99)
        self.assertIsNone(data['DD']['late_rate']); self.assertEqual(data['DD']['orders_without_items'],1)

    def test_rank_resets_by_month_and_boundary_is_explicit(self):
        db = self.database()
        db.executemany('INSERT INTO Orders VALUES (?,?,?,?,?,?)', [('a','SP','2018-01-01',1,1,0),('b','RJ','2018-02-01',1,0,0)])
        results=m.query(db)
        self.assertEqual([r['workload_rank'] for r in results],[1,1])
        self.assertTrue(all('boundary' in r['coverage_note'] for r in results))


if __name__ == '__main__': unittest.main()
