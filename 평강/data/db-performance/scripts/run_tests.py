import argparse
import csv
import os
import statistics
import time

import pg8000.dbapi
import pymysql
from pymongo import MongoClient

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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../results"))

DEFAULT_WARMUP = 10
DEFAULT_RUNS = 100

TEST_CATEGORY = "가디건"
TEST_BRAND = "쇼퍼랜드"

results = []


def parse_args():
    parser = argparse.ArgumentParser(description="Run DB benchmark queries and save the aggregated timings.")
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR, help="Directory for the output CSV.")
    parser.add_argument("--results-file", default="performance_results.csv", help="Output CSV filename.")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP, help="Warmup iterations per test.")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="Measured iterations per test.")
    return parser.parse_args()


def clear_mysql_cache(conn):
    cur = conn.cursor()
    cur.execute("FLUSH TABLES")
    cur.close()


def clear_postgres_cache(conn):
    try:
        conn.rollback()
    except Exception:
        pass
    old_autocommit = conn.autocommit
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DISCARD ALL")
    cur.close()
    conn.autocommit = old_autocommit


def clear_mongo_cache(col):
    col.database.command("planCacheClear", col.name)


def measure(fn, warmup, runs, clear_fn=None):
    for _ in range(warmup):
        if clear_fn:
            clear_fn()
        fn()

    times = []
    for _ in range(runs):
        if clear_fn:
            clear_fn()
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)

    return {
        "avg": round(statistics.mean(times), 3),
        "min": round(min(times), 3),
        "max": round(max(times), 3),
        "stddev": round(statistics.stdev(times), 3),
    }


def record(db, test_name, stats, note=""):
    results.append({"db": db, "test": test_name, "note": note, **stats})
    note_text = f" ({note})" if note else ""
    print(
        f"  [{db}] {test_name}{note_text} "
        f"avg={stats['avg']}ms min={stats['min']}ms "
        f"max={stats['max']}ms std={stats['stddev']}ms"
    )


def run_rdb(label, cfg, warmup, runs, is_mysql=True):
    print(f"\n{'=' * 50}\n[{label}] 테스트 시작")
    conn = pymysql.connect(**cfg) if is_mysql else pg8000.dbapi.connect(**cfg)
    clear = (lambda: clear_mysql_cache(conn)) if is_mysql else (lambda: clear_postgres_cache(conn))

    def q(sql, params=None):
        cur = conn.cursor()
        cur.execute(sql, params or ())
        cur.fetchall()
        cur.close()

    record(label, "단순조회_ID단건", measure(lambda: q("SELECT * FROM products WHERE id = %s", (1,)), warmup, runs, clear))
    record(label, "전체조회", measure(lambda: q("SELECT * FROM products"), warmup, runs, clear))
    record(
        label,
        "필터조회_카테고리+가격범위",
        measure(
            lambda: q(
                "SELECT * FROM products WHERE category = %s AND price BETWEEN %s AND %s",
                (TEST_CATEGORY, 10000, 50000),
            ),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        label,
        "정렬조회_가격낮은순",
        measure(lambda: q("SELECT * FROM products ORDER BY price ASC LIMIT 100"), warmup, runs, clear),
    )
    record(
        label,
        "정렬조회_리뷰많은순",
        measure(lambda: q("SELECT * FROM products ORDER BY review_count DESC LIMIT 100"), warmup, runs, clear),
    )
    record(
        label,
        "집계_브랜드별평균가격",
        measure(lambda: q("SELECT brand, AVG(price) FROM products GROUP BY brand"), warmup, runs, clear),
    )
    record(
        label,
        "집계_카테고리별상품수",
        measure(lambda: q("SELECT category, COUNT(*) FROM products GROUP BY category"), warmup, runs, clear),
    )
    record(
        label,
        "복합조건",
        measure(
            lambda: q(
                """
                SELECT *
                FROM products
                WHERE category = %s AND brand = %s AND price BETWEEN %s AND %s
                ORDER BY price ASC
                LIMIT 20
                """,
                (TEST_CATEGORY, TEST_BRAND, 10000, 100000),
            ),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        label,
        "인덱스없음_필터조회",
        measure(
            lambda: q(
                "SELECT * FROM products WHERE category = %s AND price BETWEEN %s AND %s",
                (TEST_CATEGORY, 10000, 50000),
            ),
            warmup,
            runs,
            clear,
        ),
        note="인덱스전",
    )

    cur = conn.cursor()
    try:
        cur.execute("CREATE INDEX idx_cat_price ON products (category, price)")
        cur.execute("CREATE INDEX idx_brand ON products (brand)")
        conn.commit()
        print(f"  [{label}] 인덱스 생성 완료")
    except Exception as exc:
        print(f"  [{label}] 인덱스가 이미 존재하거나 생성 실패: {exc}")
        conn.rollback()
    finally:
        cur.close()

    record(
        label,
        "인덱스있음_필터조회",
        measure(
            lambda: q(
                "SELECT * FROM products WHERE category = %s AND price BETWEEN %s AND %s",
                (TEST_CATEGORY, 10000, 50000),
            ),
            warmup,
            runs,
            clear,
        ),
        note="인덱스후",
    )
    record(
        label,
        "인덱스있음_복합조건",
        measure(
            lambda: q(
                """
                SELECT *
                FROM products
                WHERE category = %s AND brand = %s AND price BETWEEN %s AND %s
                ORDER BY price ASC
                LIMIT 20
                """,
                (TEST_CATEGORY, TEST_BRAND, 10000, 100000),
            ),
            warmup,
            runs,
            clear,
        ),
        note="인덱스후",
    )
    record(
        label,
        "JOIN_브랜드통계",
        measure(
            lambda: q(
                """
                SELECT p.*, b.avg_price, b.total
                FROM products p
                JOIN (
                    SELECT brand, AVG(price) AS avg_price, COUNT(*) AS total
                    FROM products
                    GROUP BY brand
                ) b
                    ON p.brand = b.brand
                WHERE p.category = %s
                LIMIT 50
                """,
                (TEST_CATEGORY,),
            ),
            warmup,
            runs,
            clear,
        ),
    )

    def rdb_transaction():
        cur = conn.cursor()
        try:
            cur.execute("UPDATE products SET price = price + 1 WHERE id = %s", (1,))
            cur.execute("UPDATE products SET price = price - 1 WHERE id = %s", (1,))
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            cur.close()

    record(label, "트랜잭션_UPDATE2건", measure(rdb_transaction, warmup, runs))
    conn.close()


def run_mongodb(warmup, runs):
    print(f"\n{'=' * 50}\n[MongoDB] 테스트 시작")
    client = MongoClient(MONGO_URI)
    col = client["shopdb"]["products"]
    clear = lambda: clear_mongo_cache(col)

    first_id = col.find_one({}, {"_id": 1})["_id"]

    record("MongoDB", "단순조회_ID단건", measure(lambda: col.find_one({"_id": first_id}), warmup, runs, clear))
    record("MongoDB", "전체조회", measure(lambda: list(col.find()), warmup, runs, clear))
    record(
        "MongoDB",
        "필터조회_카테고리+가격범위",
        measure(
            lambda: list(col.find({"category": TEST_CATEGORY, "price": {"$gte": 10000, "$lte": 50000}})),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        "MongoDB",
        "정렬조회_가격낮은순",
        measure(lambda: list(col.find().sort("price", 1).limit(100)), warmup, runs, clear),
    )
    record(
        "MongoDB",
        "정렬조회_리뷰많은순",
        measure(lambda: list(col.find().sort("review_count", -1).limit(100)), warmup, runs, clear),
    )
    record(
        "MongoDB",
        "집계_브랜드별평균가격",
        measure(
            lambda: list(col.aggregate([{"$group": {"_id": "$brand", "avg_price": {"$avg": "$price"}}}])),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        "MongoDB",
        "집계_카테고리별상품수",
        measure(
            lambda: list(col.aggregate([{"$group": {"_id": "$category", "count": {"$sum": 1}}}])),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        "MongoDB",
        "복합조건",
        measure(
            lambda: list(
                col.find(
                    {
                        "category": TEST_CATEGORY,
                        "brand": TEST_BRAND,
                        "price": {"$gte": 10000, "$lte": 100000},
                    }
                )
                .sort("price", 1)
                .limit(20)
            ),
            warmup,
            runs,
            clear,
        ),
    )
    record(
        "MongoDB",
        "인덱스없음_필터조회",
        measure(
            lambda: list(col.find({"category": TEST_CATEGORY, "price": {"$gte": 10000, "$lte": 50000}})),
            warmup,
            runs,
            clear,
        ),
        note="인덱스전",
    )

    col.create_index([("category", 1), ("price", 1)])
    col.create_index([("brand", 1)])
    print("  [MongoDB] 인덱스 생성 완료")

    record(
        "MongoDB",
        "인덱스있음_필터조회",
        measure(
            lambda: list(col.find({"category": TEST_CATEGORY, "price": {"$gte": 10000, "$lte": 50000}})),
            warmup,
            runs,
            clear,
        ),
        note="인덱스후",
    )
    record(
        "MongoDB",
        "인덱스있음_복합조건",
        measure(
            lambda: list(
                col.find(
                    {
                        "category": TEST_CATEGORY,
                        "brand": TEST_BRAND,
                        "price": {"$gte": 10000, "$lte": 100000},
                    }
                )
                .sort("price", 1)
                .limit(20)
            ),
            warmup,
            runs,
            clear,
        ),
        note="인덱스후",
    )
    record(
        "MongoDB",
        "Lookup_브랜드통계",
        measure(
            lambda: list(
                col.aggregate(
                    [
                        {"$match": {"category": TEST_CATEGORY}},
                        {
                            "$lookup": {
                                "from": "products",
                                "let": {"brand": "$brand"},
                                "pipeline": [
                                    {"$match": {"$expr": {"$eq": ["$brand", "$$brand"]}}},
                                    {
                                        "$group": {
                                            "_id": None,
                                            "avg_price": {"$avg": "$price"},
                                            "total": {"$sum": 1},
                                        }
                                    },
                                ],
                                "as": "brand_stats",
                            }
                        },
                        {"$limit": 50},
                    ]
                )
            ),
            warmup,
            runs,
            clear,
        ),
    )

    def mongo_transaction():
        col.update_one({"_id": first_id}, {"$inc": {"price": 1}})
        col.update_one({"_id": first_id}, {"$inc": {"price": -1}})

    record("MongoDB", "트랜잭션_UPDATE2건", measure(mongo_transaction, warmup, runs), note="세션없음")
    client.close()


def save_results(results_dir, results_file):
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, results_file)
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["db", "test", "note", "avg", "min", "max", "stddev"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n결과 저장 완료: {path}")


def main():
    args = parse_args()
    run_rdb("MySQL", MYSQL_CFG, args.warmup, args.runs, is_mysql=True)
    run_rdb("MariaDB", MARIADB_CFG, args.warmup, args.runs, is_mysql=True)
    run_rdb("PostgreSQL", POSTGRES_CFG, args.warmup, args.runs, is_mysql=False)
    run_mongodb(args.warmup, args.runs)
    save_results(os.path.abspath(args.results_dir), args.results_file)
    print("\n전체 테스트 완료!")


if __name__ == "__main__":
    main()
