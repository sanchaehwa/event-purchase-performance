import argparse
import csv
import random
import sqlite3
import statistics
import time
from pathlib import Path


BENCHMARKS = {
    "brand_exact": "SELECT COUNT(*) FROM products WHERE brand = ?",
    "category_exact": "SELECT COUNT(*) FROM products WHERE category = ?",
    "price_range": "SELECT COUNT(*) FROM products WHERE price BETWEEN ? AND ?",
    "name_keyword": "SELECT id, product_name, brand, price FROM products WHERE product_name LIKE ? LIMIT 50",
    "price_order_page": "SELECT id, product_name, brand, price FROM products ORDER BY price DESC LIMIT 50 OFFSET ?",
}


def percentile(values, ratio):
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * ratio))
    return ordered[index]


def pick_values(connection):
    brands = [row[0] for row in connection.execute("SELECT DISTINCT brand FROM products WHERE brand != ''")]
    categories = [row[0] for row in connection.execute("SELECT DISTINCT category FROM products WHERE category != ''")]
    names = [row[0] for row in connection.execute("SELECT product_name FROM products WHERE product_name != ''")]
    prices = [row[0] for row in connection.execute("SELECT price FROM products WHERE price IS NOT NULL ORDER BY price")]
    count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    return brands, categories, names, prices, count


def timed_query(connection, sql, params):
    start = time.perf_counter()
    list(connection.execute(sql, params))
    return (time.perf_counter() - start) * 1000


def benchmark(db_path, iterations):
    with sqlite3.connect(db_path) as connection:
        brands, categories, names, prices, count = pick_values(connection)
        max_offset = max(count - 50, 0)
        results = []
        for name, sql in BENCHMARKS.items():
            durations = []
            for _ in range(iterations):
                if name == "brand_exact":
                    params = (random.choice(brands) if brands else "",)
                elif name == "category_exact":
                    params = (random.choice(categories) if categories else "",)
                elif name == "price_range":
                    low = random.choice(prices) if prices else 0
                    high = random.choice(prices) if prices else 999999999
                    params = (min(low, high), max(low, high))
                elif name == "name_keyword":
                    token = random.choice(names).split()[0] if names else ""
                    params = (f"%{token}%",)
                else:
                    params = (random.randint(0, max_offset),)
                durations.append(timed_query(connection, sql, params))
            results.append(
                {
                    "query": name,
                    "iterations": iterations,
                    "avg_ms": round(statistics.mean(durations), 4),
                    "p95_ms": round(percentile(durations, 0.95), 4),
                    "min_ms": round(min(durations), 4),
                    "max_ms": round(max(durations), 4),
                }
            )
    return results


def write_csv_report(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["query", "iterations", "avg_ms", "p95_ms", "min_ms", "max_ms"])
        writer.writeheader()
        writer.writerows(results)


def write_markdown_report(indexed_results, no_index_results, output_path, row_count):
    def table(results):
        lines = ["| query | avg_ms | p95_ms | min_ms | max_ms |", "| --- | ---: | ---: | ---: | ---: |"]
        for row in results:
            lines.append(
                f"| {row['query']} | {row['avg_ms']} | {row['p95_ms']} | {row['min_ms']} | {row['max_ms']} |"
            )
        return "\n".join(lines)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        "\n".join(
            [
                "# DB Lookup Benchmark Result",
                "",
                f"- Imported rows: {row_count}",
                "- Iterations per query: 1000",
                "- Unit: milliseconds",
                "",
                "## Indexed DB",
                "",
                table(indexed_results),
                "",
                "## No-Index DB",
                "",
                table(no_index_results),
                "",
                "## Note",
                "",
                "When the dataset is small, the index difference can look small. With a larger dataset, brand/category/price/name indexes usually show clearer lookup benefits.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Benchmark SQLite product lookup queries.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--output", required=True)
    parser.add_argument("--compare-db")
    parser.add_argument("--compare-output")
    parser.add_argument("--summary-output")
    args = parser.parse_args()

    results = benchmark(args.db, args.iterations)
    write_csv_report(results, args.output)
    if args.compare_db and args.compare_output:
        compare_results = benchmark(args.compare_db, args.iterations)
        write_csv_report(compare_results, args.compare_output)
        if args.summary_output:
            with sqlite3.connect(args.db) as connection:
                row_count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            write_markdown_report(results, compare_results, args.summary_output, row_count)
    for row in results:
        print(
            f"{row['query']}: avg={row['avg_ms']}ms "
            f"p95={row['p95_ms']}ms min={row['min_ms']}ms max={row['max_ms']}ms"
        )
    print(f"Saved report to {args.output}")
    if args.compare_output:
        print(f"Saved compare report to {args.compare_output}")
    if args.summary_output:
        print(f"Saved summary report to {args.summary_output}")


if __name__ == "__main__":
    main()
