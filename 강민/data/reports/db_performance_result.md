# DB Lookup Benchmark Result

- Imported rows: 10000
- Iterations per query: 1000
- Unit: milliseconds

## Indexed DB

| query | avg_ms | p95_ms | min_ms | max_ms |
| --- | ---: | ---: | ---: | ---: |
| brand_exact | 0.0385 | 0.048 | 0.0334 | 0.1655 |
| category_exact | 0.054 | 0.09 | 0.0358 | 0.3064 |
| price_range | 0.0967 | 0.1737 | 0.035 | 0.4828 |
| name_keyword | 3.5477 | 4.7106 | 0.1953 | 6.424 |
| price_order_page | 0.245 | 0.3663 | 0.094 | 0.8422 |

## No-Index DB

| query | avg_ms | p95_ms | min_ms | max_ms |
| --- | ---: | ---: | ---: | ---: |
| brand_exact | 3.6456 | 4.0671 | 3.261 | 5.2915 |
| category_exact | 3.5974 | 3.9936 | 3.2204 | 4.9591 |
| price_range | 3.5438 | 3.9366 | 3.1453 | 5.1802 |
| name_keyword | 3.3862 | 4.6637 | 0.1781 | 10.1165 |
| price_order_page | 7.7822 | 9.6389 | 3.8944 | 12.0014 |

## Note

When the dataset is small, the index difference can look small. With a larger dataset, brand/category/price/name indexes usually show clearer lookup benefits.
