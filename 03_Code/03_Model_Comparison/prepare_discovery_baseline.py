"""Prepare a history-only popularity list for the discovery experiment."""
from pathlib import Path
import json
import sqlite3

ROOT = Path(__file__).resolve().parents[2]

def main():
    # Read checked earlier purchases only. Target-basket answers aren't needed.
    source = ROOT / "02_Data/02_Prepared/v2_timing.sqlite"
    output = ROOT / "02_Data/02_Prepared/discovery_popularity.sqlite"
    report = ROOT / "05_Results/03_Checks/discovery_preparation.json"
    if output.exists() or report.exists():
        raise FileExistsError("Discovery outputs already exist; don't silently overwrite them.")
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as con:
        rows = con.execute("""
            SELECT h.product_id, COUNT(*) AS order_count
            FROM history h JOIN customers c USING(user_id)
            WHERE c.split = 'development'
            GROUP BY h.product_id
            ORDER BY order_count DESC, h.product_id ASC
        """).fetchall()
        customers, orders = con.execute("""
            SELECT COUNT(*), SUM(history_orders) FROM customers
            WHERE split = 'development'
        """).fetchone()
    # Save one general ranking. Each shopper's previously bought items must
    # be removed BEFORE taking three recommendations in the later scorer.
    assert customers == 60000 and rows and len({r[0] for r in rows}) == len(rows)
    assert all(0 < count <= orders for _, count in rows)
    with sqlite3.connect(output) as con:
        con.execute("CREATE TABLE popularity(rank INTEGER PRIMARY KEY, product_id INTEGER UNIQUE, order_count INTEGER, order_share REAL)")
        con.executemany("INSERT INTO popularity VALUES(?,?,?,?)",
                        [(i, pid, count, count / orders) for i, (pid, count) in enumerate(rows, 1)])
    # Record exactly what was prepared; this isn't an accuracy result.
    report.write_text(json.dumps({
        "status": "prepared_not_scored", "customers": customers,
        "eligible_history_orders": orders, "history_product_lines": sum(n for _, n in rows),
        "ranked_products": len(rows), "source": str(source.relative_to(ROOT)),
        "output": str(output.relative_to(ROOT)), "target_answers_read": False,
        "audit_used": False, "prototype_changed": False,
        "ranking": "Earlier development order count descending, product ID ascending",
        "next_step": "Exclude each shopper's earlier products, then select up to three; implement related-product challenger before matched scoring."
    }, indent=2) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
