import argparse
import math
import os

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(SCRIPT_DIR, "../../result/ably_products.csv")
DEFAULT_TARGET = os.path.join(SCRIPT_DIR, "../../result/ably_products_100k.csv")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a larger benchmark CSV by repeating rows.")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Source CSV path.")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Target CSV path.")
    parser.add_argument("--rows", type=int, default=100000, help="Target row count.")
    return parser.parse_args()


def main():
    args = parse_args()
    source = os.path.abspath(args.source)
    target = os.path.abspath(args.target)

    df = pd.read_csv(source, encoding="utf-8-sig")
    base_count = len(df)
    if base_count == 0:
        raise ValueError("source CSV is empty")

    repeat = math.ceil(args.rows / base_count)
    scaled = pd.concat([df] * repeat, ignore_index=True).iloc[: args.rows].copy()

    os.makedirs(os.path.dirname(target), exist_ok=True)
    scaled.to_csv(target, index=False, encoding="utf-8-sig")

    print(f"source: {source}")
    print(f"target: {target}")
    print(f"base_rows: {base_count}")
    print(f"generated_rows: {len(scaled)}")


if __name__ == "__main__":
    main()
