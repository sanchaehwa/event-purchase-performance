import argparse
import csv
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT,
    price INTEGER NOT NULL,
    discount_rate REAL,
    rating REAL,
    review_count INTEGER,
    tags TEXT,
    description TEXT,
    image_url TEXT,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);",
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
    "CREATE INDEX IF NOT EXISTS idx_products_sub_category ON products(sub_category);",
    "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);",
    "CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);",
    "CREATE INDEX IF NOT EXISTS idx_products_source_url ON products(source, source_url);",
]


def nullable_int(value):
    return int(value) if value not in (None, "", "None") else None


def nullable_float(value):
    return float(value) if value not in (None, "", "None") else None


def nullable_text(value):
    return None if value in (None, "", "None") else value


def import_csv(csv_path, db_path, with_indexes):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(SCHEMA)
        connection.execute("DELETE FROM products")
        with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as file:
            rows = [
                (
                    row["product_name"],
                    row["brand"],
                    row["category"],
                    nullable_text(row.get("sub_category")),
                    nullable_int(row["price"]),
                    nullable_float(row.get("discount_rate")),
                    nullable_float(row.get("rating")),
                    nullable_int(row.get("review_count")),
                    nullable_text(row.get("tags")),
                    nullable_text(row.get("description")),
                    nullable_text(row.get("image_url")),
                    row["source"],
                    row["source_url"],
                )
                for row in csv.DictReader(file)
            ]
        connection.executemany(
            """
            INSERT INTO products (
                product_name, brand, category, sub_category, price, discount_rate,
                rating, review_count, tags, description, image_url, source, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        if with_indexes:
            for statement in INDEXES:
                connection.execute(statement)
        connection.commit()
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Import cleaned Musinsa CSV into SQLite.")
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--csv", default=str(root / "data/processed/musinsa_products_clean.csv"))
    parser.add_argument("--db", default=str(root / "data/db/musinsa.sqlite3"))
    parser.add_argument("--no-indexes", action="store_true")
    args = parser.parse_args()

    count = import_csv(args.csv, args.db, not args.no_indexes)
    print(f"Imported {count} products into {args.db}")


if __name__ == "__main__":
    main()
