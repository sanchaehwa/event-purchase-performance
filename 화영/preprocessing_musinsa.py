import pandas as pd

file_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/강민/data/processed/musinsa_products_clean.csv"

#csv 읽기 
df = pd.read_csv(file_path)

columns_order = [
    "product_name",
    "brand",
    "category",
    "price",
    "discount_rate",
    "rating",
    "review_count",
    "image_url",
    "source",
    "source_url"
]

df = df[columns_order]

output_path = "/Users/yanghwayeong/Desktop/system-design-interview-study/data/musinsa_data.csv"

df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

print("무신사 전처리 데이터 저장 - 컬럼 순서 정렬 완료",output_path)





