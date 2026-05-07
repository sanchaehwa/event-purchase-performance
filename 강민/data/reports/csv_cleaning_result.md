# CSV Cleaning Result

- Run date: 2026-05-02
- Raw rows: 10020
- Clean rows: 10000
- Removed invalid rows: 0
- Removed duplicates: 1
- Duplicate rule: same brand + same product_name
- Category rule: category/sub_category are kept as original source labels
- Null rule: optional missing values are saved as `None`
- Encoding: UTF-8-sig
- Final limit: 10000
- Output CSV: `data/processed/musinsa_products_clean.csv`
