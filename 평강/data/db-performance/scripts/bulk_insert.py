import argparse
import math
import os

import pandas as pd
import pg8000.dbapi
import pymysql
from pymongo import MongoClient

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(SCRIPT_DIR, "../../result/ably_products.csv")

MYSQL_CFG = dict(
    host="localhost",
    port=3308,
    user="root",
    password="root1234",
    database="shopdb",
    charset="utf8mb4",
)
MARIADB_CFG = dict(
    host="localhost",
    port=3309,
    user="root",
    password="root1234",
    database="shopdb",
    charset="utf8mb4",
)
POSTGRES_CFG = dict(
    host="localhost",
    port=5433,
    user="postgres",
    password="root1234",
    database="shopdb",
)
MONGO_URI = "mongodb://localhost:27017"

INSERT_SQL = """
INSERT INTO products
    (product_name, brand, category, sub_category, price, discount_rate,
     rating, review_count, tags, description, image_url, source, source_url)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Bulk insert product CSV into all benchmark DBs.")
    parser.add_argument(
        "--csv",
        default=DEFAULT_CSV_PATH,
        help="Path to the source CSV file.",
    )
    return parser.parse_args()


def load_csv(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    return df.where(pd.notnull(df), None)


def to_val(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def normalize_rows(df):
    return [
        (
            to_val(row.product_name),
            to_val(row.brand),
            to_val(row.category),
            to_val(row.sub_category),
            int(row.price),
            to_val(row.discount_rate),
            (
                float(row.rating)
                if row.rating is not None and not (isinstance(row.rating, float) and math.isnan(row.rating))
                else None
            ),
            (
                int(row.review_count)
                if row.review_count is not None
                and not (isinstance(row.review_count, float) and math.isnan(row.review_count))
                else None
            ),
            to_val(row.tags),
            to_val(row.description),
            to_val(row.image_url),
            to_val(row.source),
            to_val(row.source_url),
        )
        for row in df.itertuples(index=False)
    ]


def insert_mysql(rows, cfg, label):
    conn = pymysql.connect(**cfg)
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE products")
    cur.executemany(INSERT_SQL, rows)
    conn.commit()
    print(f"[{label}] inserted {cur.rowcount} rows")
    cur.close()
    conn.close()


def insert_postgres(rows):
    conn = pg8000.dbapi.connect(**POSTGRES_CFG)
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE products RESTART IDENTITY")
    cur.executemany(INSERT_SQL, rows)
    conn.commit()
    print(f"[PostgreSQL] inserted {len(rows)} rows")
    cur.close()
    conn.close()


def insert_mongodb(df):
    client = MongoClient(MONGO_URI)
    col = client["shopdb"]["products"]
    col.drop()
    docs = [{key: to_val(value) for key, value in row._asdict().items()} for row in df.itertuples(index=False)]
    result = col.insert_many(docs)
    print(f"[MongoDB] inserted {len(result.inserted_ids)} rows")
    client.close()


def main():
    args = parse_args()
    csv_path = os.path.abspath(args.csv)
    print(f"loading CSV: {csv_path}")
    df = load_csv(csv_path)
    print(f"loaded {len(df)} rows")

    rows = normalize_rows(df)

    print("\n[1/4] inserting into MySQL")
    insert_mysql(rows, MYSQL_CFG, "MySQL")

    print("\n[2/4] inserting into MariaDB")
    insert_mysql(rows, MARIADB_CFG, "MariaDB")

    print("\n[3/4] inserting into PostgreSQL")
    insert_postgres(rows)

    print("\n[4/4] inserting into MongoDB")
    insert_mongodb(df)

    print("\nbulk insert finished")


if __name__ == "__main__":
    main()
