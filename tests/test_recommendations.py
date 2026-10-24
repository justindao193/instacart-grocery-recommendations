"""Behaviour checks for the portable rules; no private data or model fitting."""
import json
from math import sqrt
from pathlib import Path
import sqlite3
import unittest

from src.recommendations import (Purchase, basket_metrics, build_connections,
                                 discovery_products, familiar_products, weighted_history)
from run import demo, saved_results

ROOT = Path(__file__).resolve().parents[1]


class FamiliarTests(unittest.TestCase):
    def test_future_basket_cannot_change_predictions(self):
        past = [Purchase(1, 1), Purchase(2, 2)]
        self.assertEqual(weighted_history(past, 2),
                         weighted_history(past + [Purchase(99, 3)], 2))

    def test_five_order_half_life_and_duplicate_lines(self):
        ranks = {r.product_id: r.score for r in weighted_history(
            [Purchase(1, 1), Purchase(1, 1), Purchase(2, 6)], 6)}
        self.assertEqual(ranks, {1: 0.5, 2: 1.0})

    def test_hide_before_select_and_no_random_filler(self):
        history = [Purchase(pid, 1) for pid in range(1, 8)]
        self.assertEqual(familiar_products(history, 1, hidden=[1]), [2, 3, 4, 5, 6])
        self.assertEqual(familiar_products(history, 1, hidden=range(1, 8),
                                          popularity=[99]), [])
        self.assertEqual(familiar_products([Purchase(1, 1)], 1, popularity=[99]), [1])

    def test_no_history_fallback_has_no_duplicates(self):
        self.assertEqual(familiar_products([], 0, popularity=[3, 3, 2]), [3, 2])

    def test_original_sql_agrees_with_reference_on_fixture(self):
        # Execute the published SQL independently in an in-memory SQLite database.
        # This query uses SQL features supported by both SQLite and DuckDB.
        rows = [(1, 1, 'prior', 1), (2, 1, 'prior', 6), (3, 1, 'prior', 7)]
        lines = [(1, 1), (2, 2), (2, 3), (3, 99)]
        with sqlite3.connect(':memory:') as con:
            con.executescript('CREATE TABLE orders(order_id, user_id, eval_set, order_number);'
                              'CREATE TABLE order_products__prior(order_id, product_id);'
                              'CREATE TABLE evaluation_plan(user_id, validation_history_max_order_number);'
                              'CREATE TABLE products(product_id, product_name);')
            con.executemany('INSERT INTO orders VALUES(?,?,?,?)', rows)
            con.executemany('INSERT INTO order_products__prior VALUES(?,?)', lines)
            con.execute('INSERT INTO evaluation_plan VALUES(1,6)')
            con.executemany('INSERT INTO products VALUES(?,?)', [(p, str(p)) for p in [1, 2, 3, 99]])
            sql = (ROOT / 'src/baselines/weighted_recency.sql').read_text(encoding='utf-8')
            sql_rows = con.execute(sql).fetchall()
        expected = weighted_history([Purchase(1, 1), Purchase(2, 6), Purchase(3, 6), Purchase(99, 7)], 6)
        self.assertEqual([(r[1], r[2], r[4]) for r in sql_rows],
                         [(r.product_id, r.score, r.last_order) for r in expected])


class DiscoveryTests(unittest.TestCase):
    def test_shared_buyers_count_people_once(self):
        links = build_connections([[1, 1, 2], [1, 2], [2, 3]], min_buyers=1, min_shared=1)
        self.assertAlmostEqual(dict(links[1])[2], 2 / sqrt(6))
        self.assertNotIn(1, dict(links[1]))

    def test_support_thresholds_and_neighbour_cap(self):
        self.assertEqual(build_connections([[1, 2]], min_buyers=2), {})
        links = build_connections([[1, 2], [1, 3]], min_buyers=1, min_shared=2)
        self.assertTrue(all(not row for row in links.values()))
        links = build_connections([[1, 2, 3]], min_buyers=1, min_shared=1, max_neighbours=1)
        self.assertEqual(links[1][0][0], 2)

    def test_exclude_all_history_even_products_outside_ten_seeds(self):
        history = [Purchase(pid, 12) for pid in range(1, 12)]
        ranked = discovery_products(history, 12, {1: [(11, 1.0), (20, 0.5)]}, [11, 21])
        self.assertEqual(ranked, [20, 21])

    def test_contributions_add_and_fallback_cannot_duplicate(self):
        history = [Purchase(1, 1), Purchase(2, 1)]
        links = {1: [(3, 0.4), (4, 0.7)], 2: [(3, 0.4)]}
        self.assertEqual(discovery_products(history, 1, links, [1, 3, 5, 5, 6]), [3, 4, 5, 6])

    def test_cutoff_and_ties(self):
        links = {1: [(4, 0.5), (3, 0.5)], 99: [(2, 1.0)]}
        self.assertEqual(discovery_products([Purchase(1, 1), Purchase(99, 2)], 1,
                                           links, []), [3, 4])

    def test_invalid_similarity_is_rejected(self):
        for value in [float('nan'), -0.5, 1.1]:
            with self.assertRaises(ValueError):
                discovery_products([Purchase(1, 1)], 1, {1: [(2, value)]}, [])


class EvidenceTests(unittest.TestCase):
    def test_metrics_keep_fixed_five_denominator_and_full_target(self):
        self.assertEqual(basket_metrics([1], [1, 2, 3, 4]),
                         {'precision': 0.2, 'recall': 0.25, 'hit': 1.0})
        self.assertEqual(basket_metrics([], [1])['hit'], 0.0)

    def test_unknown_targets_or_duplicate_suggestions_are_not_scored(self):
        for guesses, actual in [([1], []), ([1, 1], [1]), (list(range(6)), [1])]:
            with self.assertRaises(ValueError):
                basket_metrics(guesses, actual)

    def test_cli_reads_saved_evidence_without_retraining(self):
        result = saved_results()
        self.assertEqual(result['v1_shoppers'], 131209)
        self.assertAlmostEqual(result['v1_final_metrics']['weighted_recency']['recall_at_5'],
                               0.2427597467213022)
        self.assertIn('exposed', result['discovery_top_five_note'])
        self.assertIn('Invented', demo()['example'])

    def test_all_published_json_is_readable(self):
        for path in (ROOT / 'results').glob('*.json'):
            with self.subTest(report=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding='utf-8')), dict)


if __name__ == '__main__':
    unittest.main()
